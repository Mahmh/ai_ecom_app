from dataclasses import dataclass, field
from torch.utils.data import Dataset
import torch, numpy as np, pandas as pd, typing
from src.lib.modules.data.constants import MAX_CORES, EMBEDDER

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Hyperparameters for custom trained models
class model_config:
    @dataclass
    class base:
        # Training
        epochs: int = 5
        optimizer: torch.nn.Module = torch.optim.Adam
        lr: float = 3e-1
        batch_size: int = 8
        train_size: float = .7    # training data (70%)
        val_size: float = .1      # validation data (10%)
        shuffle: bool = True
        drop_last: bool = True
        # Performance
        num_workers: int = MAX_CORES
        prefetch_factor: int = 4  # number of prefetched batches for each worker
        # Saving
        persist_model_dir_name: str = 'saved_models'
        persist_optimizer_dir_name: str = 'saved_optimizers'
        persist_name_fmt: str = "%Y-%m-%d_%H-%M-%S.pt"
        load_last_chkpt: bool = True
        epochs_before_saving: bool = 1

        def todict(self):
            """Converts the object into a dictionary for parameter tracking"""
            result = {}
            attrs = [obj for obj in dir(self) if obj[0] != '_']
            for attr in attrs:
                value = self.__getattribute__(attr)
                if 'method' not in repr(value):
                    result[attr] = value
            return result


    @dataclass
    class review_analyst(base):
        csv_file: str = '../../db/data/amazon_reviews.csv'  # relative path with respect to the `lib/modules/` directory
        n_inputs: int = 4097  # 4096 (embedding vector of "review_text") + 1 ("rating")
        n_outputs: int = 1    # 1 ("sentiment")
        layers: list[int] = field(default_factory=list) # list of number of neurons in each layer

        def prep_ds(*args) -> pd.DataFrame:
            df = args[1]
            df.dropna(inplace=True)
            df.drop_duplicates(inplace=True)
            df['sentiment'] = np.where(df['overall'] >= 3.0, 1, 0)
            df.rename(columns={'overall': 'rating', 'reviewText': 'review_text'}, inplace=True)
            return df[['review_text', 'rating', 'sentiment']]

        def prep_sample(*args) -> tuple:
            review_text, overall, sentiment = args[1:]
            return EMBEDDER.embed_query(review_text) + [overall], sentiment
    
    
    @dataclass
    class recommender(base):
        NotImplemented


# Data batch loader for DataFrames
class DFDataset(Dataset):
    """Dataset class for loading Pandas DataFrames"""
    def __init__(self, df: pd.DataFrame, prep_sample: typing.Callable):
        assert len(df) > 0, 'empty DataFrame'
        self.df, self.prep_sample = df, prep_sample
        
    def __getitem__(self, i) -> torch.tensor:
        X, y = self.prep_sample(*self.df.iloc[i].tolist())
        return torch.tensor(X).to(device).float(), torch.tensor(y).to(device).float()

    def __len__(self) -> int:
        return len(self.df)