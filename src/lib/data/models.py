from dataclasses import dataclass
from torch.utils.data import Dataset
from transformers import BertModel
from typing import List, Tuple, Callable, Optional, Literal, Any
from abc import abstractmethod
from pydantic import BaseModel
import torch, torch.nn as nn, pandas as pd
from src.lib.data.constants import MAX_CORES, BERT_MODEL_TYPE, BERT_EMBEDDING_DIM

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
    activation_fn: nn.Module
    train_size: float 
    val_size: float
    # Training
    epochs: int
    optimizer: nn.Module
    weight_decay: float
    lr: float
    batch_size: int
    dropout_p: float
    seq_len: int  # max number of chars per text sequence
    # d_model: int  # number of embedding features (columns)
    # vocab_size: int = len(VOCAB)  # number of unique tokens
    # padding_idx: int = VOCAB[PAD_TOKEN]  # ID of the padding token in the embedding table
    shuffle: bool = True
    drop_last: bool = True
    n_samples: int | Literal['all'] = 'all'
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
    @abstractmethod
    def prep_sample(cls, *args) -> Tuple: ...


class ProductRaterConfig(ModelConfig):
    model_name = 'product_rater'
    csv_file = '../../../db/data/datasets/product_ratings.csv'
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
        self.bert = BertModel.from_pretrained(BERT_MODEL_TYPE)
        self.batch_norm = nn.BatchNorm1d(BERT_EMBEDDING_DIM)

        # Structure the neural network based on the `config`
        self.neural_net = nn.Sequential()
        add = self.neural_net.add_module

        for i in range(len(config.hidden_layers)):
            if i == 0:
                add(f'fc{i}', nn.Linear(config.n_inputs, config.hidden_layers[i]))
            elif i != len(config.hidden_layers):
                add(f'fc{i}', nn.Linear(config.hidden_layers[i-1], config.hidden_layers[i]))
            add(f'dp{i}', nn.Dropout(config.dropout_p))
            add(f'act_fn{i}', config.activation_fn())

        add(f'fc{i+1}', nn.Linear(config.hidden_layers[i], config.n_outputs))
        add(f'dp{i+1}', nn.Dropout(config.dropout_p))
        if config.n_outputs == 1: add(f'sig{i+1}', nn.Sigmoid())

        self.apply(self._init_weights)

    @abstractmethod
    def forward(self, input_batch: List[torch.Tensor] | Any, targets: Optional[torch.Tensor] = None, training: bool = False) -> torch.Tensor: ...
    @abstractmethod
    def _init_weights(self, module) -> None: ...


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


class ChatbotInput(BaseModel):
    """Model for accepting user prompt for the chatbot"""
    sender: str
    content: str
    conversation: List = []


class ProductRaterInput(BaseModel):
    ...