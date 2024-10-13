from datetime import datetime
import torch.utils
from torch.utils.data import DataLoader
import torch, os, mlflow, matplotlib.pyplot as plt, pandas as pd
import torch.utils.data
from typing import List, Tuple, Union
from src.lib.data.constants import CURRENT_DIR
from src.lib.data.model import model_config, DFDataset

_locate = lambda x: os.path.join(CURRENT_DIR, '../../server/models/review_analyst/' + x)

def _check_checkpoint_dirs(model_dirname: str, optimizer_dirname: str) -> Union[bool, Tuple]:
    """Checks if saved checkpoint directories exist in the current working directory"""
    try:
        return os.listdir(_locate(model_dirname)), os.listdir(_locate(optimizer_dirname))
    except FileNotFoundError:
        return False


def train_val_test_split(config: model_config.base) -> Tuple[DataLoader]:
    """Returns `torch.utils.data.DataLoader`s for training, validation, and test datasets with the `config` provided"""
    df = config.prep_ds(pd.read_csv(_locate(config.csv_file)).head(8*12))
    size = len(df)
    train_rows = int(config.train_size*size)
    val_rows = train_rows + int(config.val_size*size)
    train_df, val_df, test_df = df[train_rows:], df[train_rows:val_rows], df[val_rows:]

    loader = lambda any_df: DataLoader(
        DFDataset(any_df, config.prep_sample), 
        batch_size=config.batch_size,
        num_workers=config.num_workers,
        prefetch_factor=config.prefetch_factor,
        shuffle=config.shuffle,
        drop_last=config.drop_last,
        persistent_workers=(True if config.num_workers > 1 else False)
    )
    return loader(train_df), loader(val_df), loader(test_df)
        


def init_training(config: model_config.base):
    """Sets up the model & optimizer to start training from scratch"""
    model = config.model_cls(config).to(config.device)
    model = torch.compile(model)
    optimizer = config.optimizer(model.parameters(), lr=config.lr)
    return model, optimizer


def load_checkpoint(config: model_config.base) -> Union[Tuple[torch.nn.Module], None]:
    """Loads the model & its optimizer from the latest checkpoint"""
    model_dirname, optimizer_dirname, nameformat = config.persist_model_dir_name, config.persist_optimizer_dir_name, config.persist_name_fmt

    # Check if the directories to save artifacts exist
    result = _check_checkpoint_dirs(model_dirname, optimizer_dirname)
    if (result is False) or (len(result[0]) == 0 or len(result[1]) == 0):
        raise FileNotFoundError('Please save a checkpoint first using `src.lib.utils.model.save_checkpoint` function.')

    assert len(os.listdir(_locate(model_dirname))) == len(os.listdir(_locate(optimizer_dirname))), \
    "The saved model and the saved optimizer directories must have the same number of files."

    # Get the latest model using its file name
    checkpoints = [
        datetime.strptime(checkpoint, nameformat)
        for checkpoint in os.listdir(_locate(model_dirname))
    ]

    if len(checkpoints) == 0: return
    checkpoint_name = datetime.strftime(max(checkpoints), nameformat)

    # Remove the prefix `_orig_mod.` from the keys
    def _update_state_dict(state_dict):
        new_state_dict = {}
        for k, v in state_dict.items():
            new_key = k.replace('_orig_mod.', '')
            new_state_dict[new_key] = v
        return new_state_dict
    
    locate_checkpoint = lambda dirname: _locate(dirname + '/' + checkpoint_name)
    model_state_dict = _update_state_dict(torch.load(locate_checkpoint(model_dirname), weights_only=True))
    optimizer_state_dict = _update_state_dict(torch.load(locate_checkpoint(optimizer_dirname), weights_only=False))

    # Load the model
    model = config.model_cls(config).to(config.device) 
    model.load_state_dict(model_state_dict)
    model = torch.compile(model)
    optimizer = config.optimizer(model.parameters(), lr=config.lr)
    optimizer.load_state_dict(optimizer_state_dict)
    return model, optimizer


def save_checkpoint(model: torch.nn.Module, optimizer: torch.nn.Module, avg_train_loss: float, config: model_config.base) -> None:
    """Saves the model and other information periodically
    
    ---
    :param model: The PyTorch model to save.
    :param optimizer: The optimizer of the model to save.
    :param avg_train_loss: The Average training loss of the model.
    :param config: Any configuration used by the model.
    """
    model_dirname, optimizer_dirname = config.persist_model_dir_name, config.persist_optimizer_dir_name
    filename = datetime.now().strftime(config.persist_name_fmt)
    pkgs_file = os.path.join(CURRENT_DIR, '../../../requirements.txt')

    if not _check_checkpoint_dirs(model_dirname, optimizer_dirname):
        if '/' in model_dirname: os.mkdir(model_dirname.split('/')[0])
        os.mkdir(model_dirname)
        os.mkdir(optimizer_dirname)
    
    # Let Mlflow infer automatically the model's signature using a random example
    example = torch.randn(1, config.n_inputs).to(config.device)
    signature = mlflow.models.infer_signature(example.tolist(), model(example).tolist())

    # Save & log artifacts & metrics
    torch.save(model.state_dict(), model_dirname+f'/{filename}')
    torch.save(optimizer.state_dict(), optimizer_dirname+f'/{filename}')

    mlflow.log_metric('avg_train_loss', avg_train_loss)
    mlflow.pytorch.log_model(
        pytorch_model=model, 
        artifact_path=model_dirname, 
        pip_requirements=pkgs_file, 
        signature=signature
    )


def plot(losses: List[float], filename: str):
    """Plots the loss over epochs"""
    epochs = range(1, len(losses)+1)
    plt.clf()
    plt.plot(epochs, losses)
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.savefig(filename)


def eval_model(model: torch.nn.Module, dataloader: torch.utils.data.DataLoader, loss_name: str):
    """Evaluates the given model on a given dataset and returns the average loss. For metric logging, specify `loss_name` (e.g., "val_loss", "test_loss")"""
    assert len(dataloader) > 0, 'empty DataLoader'
    losses = [model(X, y).item() for X, y in dataloader]
    avg_loss = sum(losses) / len(losses)
    mlflow.log_metric(loss_name, avg_loss)
    return avg_loss 