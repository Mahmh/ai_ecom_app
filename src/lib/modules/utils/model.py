from datetime import datetime
import torch.utils
from torch.utils.data import DataLoader
import torch, os, mlflow, matplotlib.pyplot as plt, pandas as pd
import torch.utils.data
from src.lib.modules.data.constants import CURRENT_DIR
from src.lib.modules.data.model import model_config, DFDataset, device

def _check_checkpoint_dirs(model_dirname: str, optimizer_dirname: str) -> bool|tuple:
    """Checks if saved checkpoint directories exist in the current working directory"""
    try:
        return os.listdir(model_dirname), os.listdir(optimizer_dirname)
    except FileNotFoundError:
        return False


def train_val_test_split(config: model_config.base) -> tuple[DataLoader]:
    """Returns `torch.utils.data.DataLoader`s for training, validation, and test datasets with the `config` provided"""
    df = config.prep_ds(pd.read_csv(os.path.join(CURRENT_DIR, config.csv_file)))
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
        


def init_training(ModelClass: torch.nn.Module, config: model_config.base):
    """Sets up the model & optimizer to start training from scratch"""
    model = ModelClass(config).to(device)
    model = torch.compile(model)
    optimizer = config.optimizer(model.parameters(), lr=config.lr)
    return model, optimizer


def load_checkpoint(ModelClass: torch.nn.Module, config: model_config.base) -> None|tuple[torch.nn.Module]:
    """Loads the model & its optimizer from the latest checkpoint
    
    ---
    :param ModelClass: The model class that inherits `torch.nn.Module` and was used to train the model.
    :param model_config: Any configuration used by the model.
    """
    model_dirname, optimizer_dirname, nameformat = config.persist_model_dir_name, config.persist_optimizer_dir_name, config.persist_name_fmt
    model_files, optimizer_files = _check_checkpoint_dirs(model_dirname, optimizer_dirname)
    if (not model_files) or (not optimizer_files) or (len(model_files) == 0) or (len(optimizer_files) == 0):
        raise FileNotFoundError('Please save a checkpoint first using `src.lib.modules.model_utils.save_checkpoint` function.')

    assert len(os.listdir(model_dirname)) == len(os.listdir(optimizer_dirname)), \
    "The saved model and the saved optimizer directories must have the same number of files."

    # Get the latest model using its file name
    checkpoints = [
        datetime.strptime(checkpoint, nameformat)
        for checkpoint in os.listdir(model_dirname)
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
    
    model_state_dict = _update_state_dict(torch.load(model_dirname + '/' + checkpoint_name, weights_only=True))
    optimizer_state_dict = _update_state_dict(torch.load(optimizer_dirname + '/' + checkpoint_name, weights_only=False))

    # Load the model
    model = ModelClass(config).to(device)
    model.load_state_dict(model_state_dict)
    model = torch.compile(model)
    optimizer = config.optimizer(model.parameters(), lr=config.lr)
    optimizer.load_state_dict(optimizer_state_dict)
    return model, optimizer


def save_checkpoint(model: torch.nn.Module, optimizer: torch.nn.Module, train_loss: torch.tensor, config: model_config.base) -> None:
    """Saves the model and other information periodically
    
    ---
    :param model: The PyTorch model to save.
    :param optimizer: The optimizer of the model to save.
    :param loss: The `torch.nn` loss of the model.
    :param config: Any configuration used by the model.
    """
    model_dirname, optimizer_dirname = config.persist_model_dir_name, config.persist_optimizer_dir_name
    filename = datetime.now().strftime(config.persist_name_fmt)
    pkgs_file = os.path.join(CURRENT_DIR, '../../../requirements.txt')

    if not _check_checkpoint_dirs(model_dirname, optimizer_dirname):
        os.mkdir(model_dirname)
        os.mkdir(optimizer_dirname)
    
    # Let Mlflow infer automatically the model's signature using a random example
    example = torch.randn(1, config.n_inputs).to(device)
    signature = mlflow.models.infer_signature(example.tolist(), model(example).tolist())

    # Save & log artifacts & metrics
    torch.save(model.state_dict(), model_dirname+f'/{filename}')
    torch.save(optimizer.state_dict(), optimizer_dirname+f'/{filename}')

    mlflow.log_metric('train_loss', train_loss.item())
    mlflow.pytorch.log_model(
        pytorch_model=model, 
        artifact_path=model_dirname, 
        pip_requirements=pkgs_file, 
        signature=signature
    )


def plot(losses: list[float], filename: str):
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