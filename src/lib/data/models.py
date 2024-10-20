from dataclasses import dataclass
from torch.utils.data import Dataset
import random, torch, torch.nn as nn, numpy as np, pandas as pd
from typing import List, Tuple, Callable, Optional, Union, Literal
from abc import abstractmethod
from pydantic import BaseModel
from src.lib.data.constants import MAX_CORES, VOCAB, PAD_TOKEN

torch.set_float32_matmul_precision('high')

@dataclass
class ModelConfig:
    """Base class for configuring custom trained models"""
    # General
    model_name: str
    csv_file: str  # relative path with respect to the `lib/data/` directory
    n_inputs: int
    n_outputs: int
    hidden_layers: List[int] # list of number of neurons in each hidden layer
    train_size: float 
    val_size: float
    # Training
    epochs: int
    optimizer: nn.Module
    lr: float
    batch_size: int
    dropout_p: float
    d_model: int  # number of embedding features (columns)
    seq_len: int  # max number of chars per text sequence
    vocab_size: int = len(VOCAB)  # number of unique tokens
    padding_idx: int = VOCAB[PAD_TOKEN]  # ID of the padding token in the embedding table
    shuffle: bool = True
    drop_last: bool = True
    n_samples: Union[int, Literal['all']] = 'all'
    balanced_bin_clf_ds: bool = True  # No. samples of minority class = No. samples of majority class
    # Saving
    persist_model_dir_name: str = 'artifacts/saved_models'
    persist_optimizer_dir_name: str = 'artifacts/saved_optimizers'
    avg_train_loss_filename: str = 'artifacts/avg_train_losses.jpg'
    avg_val_loss_filename: str = 'artifacts/avg_val_losses.jpg'
    # Performance
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    num_workers: int = MAX_CORES
    prefetch_factor: int = 4  # number of prefetched batches per worker
    persist_name_fmt: str = "%Y-%m-%d_%H-%M-%S.pt"
    load_last_chkpt: bool = True
    epochs_before_printing: int = 1
    epochs_before_saving: int = 1
    
    @classmethod
    def _prep_text(cls, text: str) -> List[int]:
        """Preprocesses text by tokenizing and padding/truncating it to have a length of `self.seq_len`"""
        text = list(text)

        if len(text) < cls.seq_len:
            text += [PAD_TOKEN] * (cls.seq_len - len(text))
        elif len(text) > cls.seq_len:
            text = text[:cls.seq_len]
    
        return [VOCAB[token] for token in text]
    
    @classmethod
    @abstractmethod
    def prep_ds(cls, df: pd.DataFrame) -> pd.DataFrame: ...
    @classmethod
    @abstractmethod
    def prep_sample(cls, *args) -> Tuple: ...


class ReviewAnalystConfig(ModelConfig):
    model_name = 'review_analyst'
    csv_file = '../../../db/data/amazon_reviews.csv'
    n_inputs = 257 # d_model*seq_len (embedding vector of "review_text") + 1 ("rating")
    n_outputs = 1   # 1 ("sentiment")
    hidden_layers = [2, 4]
    epochs = 32
    optimizer = torch.optim.Adam
    lr = 3e-2
    batch_size = 16
    dropout_p = .3
    d_model = 4
    seq_len = 64
    n_samples = 'all'
    epochs_before_printing = 8
    epochs_before_saving = 4
    prefetch_factor = 16
    # 70% training, 10% validation, 20% testing
    train_size = .7
    val_size = .1
    
    @classmethod
    def prep_ds(cls, df: pd.DataFrame) -> pd.DataFrame:
        df.drop_duplicates(inplace=True)
        df.rename(columns={'overall': 'rating', 'reviewText': 'review_text'}, inplace=True)
        df['sentiment'] = np.where(df['rating'] >= 3.0, 1, 0)

        if cls.balanced_bin_clf_ds:
            # Make the majority class have the same number of samples as the minority class
            indices = df[df['sentiment'] == 1].index.tolist()
            undersampled_indices = random.sample(indices, df['sentiment'].value_counts().to_dict()[0.0])
            undersampled_df = df.loc[undersampled_indices]
            df.loc[df['sentiment'] == 1, :] = undersampled_df.iloc[:]
            df.dropna(inplace=True)
        return df[['review_text', 'rating', 'sentiment']]

    @classmethod
    def prep_sample(cls, review_text: str, rating: float, sentiment: Optional[int] = None) -> Tuple:
        X = [
            torch.tensor(cls._prep_text(review_text)).to(cls.device).int(), 
            torch.tensor(rating).to(cls.device).float()
        ]
        y = torch.tensor(sentiment).to(cls.device).int() if sentiment else None
        return X, y


class ProductRaterConfig(ModelConfig):
    model_name = 'product_rater'
    csv_file = '../../../db/data/product_ratings.csv'
    n_inputs = 2   # 1 ("price") + 1 ("discount")
    n_outputs = 1  # 1 ("product rating")
    hidden_layers = [1, 3]
    epochs = 5
    optimizer = torch.optim.Adam
    lr = 3e-1
    batch_size = 3
    # 50% training, 20% validation, 30% testing
    train_size = .5
    val_size = .2

    @classmethod
    def prep_ds(cls, df: pd.DataFrame) -> pd.DataFrame:
        df.dropna(inplace=True)
        df.drop_duplicates(inplace=True)
        return df[['price', 'discount', 'rating']]

    @classmethod
    def prep_sample(cls, price: float, discount: float, rating: Optional[int] = None) -> Tuple:
        X = torch.tensor([price, discount]).to(cls.device).float()
        y = torch.tensor(rating).to(cls.device).int() if rating else None
        return X, y


class NeuralNetwork(nn.Module):
    """Base class for custom trained feedforward neural networks"""
    def __init__(self, config: ModelConfig):
        super().__init__()
        self.config = config
        self.embd_table = nn.Embedding(config.vocab_size, config.d_model, config.padding_idx)

        # Structure the neural network based on the `config`
        self.neural_net = nn.Sequential()
        add = self.neural_net.add_module

        for i in range(len(config.hidden_layers)):
            if i == 0:
                add(f'fc{i}', nn.Linear(config.n_inputs, config.hidden_layers[i]))
            elif i != len(config.hidden_layers):
                add(f'fc{i}', nn.Linear(config.hidden_layers[i-1], config.hidden_layers[i]))
            add(f'dp{i}', nn.Dropout(config.dropout_p))
            add(f'relu{i}', nn.ReLU())
        
        add(f'fc{i+1}', nn.Linear(config.hidden_layers[i], config.n_outputs))
        add(f'dp{i+1}', nn.Dropout(config.dropout_p))      
        if config.n_outputs == 1: add(f'sig{i+1}', nn.Sigmoid())
        else: add(f'sm{i+1}', nn.Softmax())

    @abstractmethod
    def forward(self, input_batch: List[torch.Tensor], targets: Optional[torch.Tensor] = None, training: bool = False) -> torch.Tensor: ...


class DFDataset(Dataset):
    """Dataset class for loading & using a Pandas DataFrame for training a model"""
    def __init__(self, df: pd.DataFrame, prep_sample: Callable[[List], Tuple]):
        assert len(df) > 0, 'expected a non-empty `pd.DataFrame`'
        self.df, self.prep_sample = df, prep_sample
        
    def __getitem__(self, i) -> Tuple:
        return self.prep_sample(*self.df.iloc[i].tolist())

    def __len__(self) -> int:
        return len(self.df)


# Pydantic Models
class ReviewAnalystInput(BaseModel):
    """Model for accepting required input for the Review Analyst"""
    review_text: str
    rating: float


class ChatbotInput(BaseModel):
    """Model for accepting required input for the chatbot"""
    prompt: str
    conversation: List = []


class ProductRaterInput(BaseModel):
    ...