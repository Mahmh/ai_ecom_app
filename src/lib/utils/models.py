from datetime import datetime
from torch.utils.data import DataLoader
import torch, os, requests, mlflow, matplotlib.pyplot as plt, pandas as pd
from typing import List, Tuple, Union, Optional
from src.lib.data.constants import CURRENT_DIR, MLFLOW_TRACKING_URI
from src.lib.data.models import ModelConfig, ReviewAnalystConfig, NeuralNetwork, DFDataset

_locate = lambda model_name, x: os.path.join(CURRENT_DIR, f'../../server/models/{model_name}/' + x)

def _check_checkpoint_dirs(model_name: str, model_dirname: str, optimizer_dirname: str) -> Union[bool, Tuple]:
    """Checks if saved checkpoint directories exist in the current working directory"""
    try:
        return os.listdir(_locate(model_name, model_dirname)), os.listdir(_locate(model_name, optimizer_dirname))
    except FileNotFoundError:
        return False


def _check_run_dirs(model_dirname: str, optimizer_dirname: str, run_name: str, config: ModelConfig) -> None:
    """Checks if a directory with a given run name is already created in the saved artifacts directories"""
    model_run_dir = f'{_locate(config.model_name, model_dirname)}/{run_name}/'
    optimizer_run_dir = f'{_locate(config.model_name, optimizer_dirname)}/{run_name}/'
    try:
        os.listdir(model_run_dir)
        os.listdir(optimizer_run_dir)
    except FileNotFoundError:
        os.mkdir(model_run_dir)
        os.mkdir(optimizer_run_dir)


def init_mlflow(experiment_name: str, tracking_uri: str = MLFLOW_TRACKING_URI) -> None:
    """Initializes an Mlflow experiment"""
    # Raises an exception if the Mlflow server isn't either running or working
    try:
        assert requests.get(tracking_uri).status_code == 200, 'Mlflow server doesn\'t return an OK status code'
    except requests.exceptions.ConnectionError:
        raise ConnectionError('Please make sure that the Mlflow server is running')
    mlflow.set_experiment(experiment_name)
    mlflow.set_tracking_uri(tracking_uri)


def new_run_name(config: ModelConfig) -> str:
    """Returns a unique run name for recording model training"""
    return f'Run_{datetime.now().strftime(config.persist_name_fmt.replace(".pt", ""))}'


def clear_print_line() -> None:
    """Erases the output of the last printed line"""
    print('\r', end='', flush=True)
    print('                                              ', end='')
    print('\r', end='', flush=True)


def print_epoch_result(
        model: NeuralNetwork, 
        train_losses: List[float], 
        val_dl: DataLoader, 
        epoch: int, 
        t1: float, 
        t2: float, 
        config: ModelConfig
    ) -> Tuple[float]:
    """Prints the result of an epoch in one line"""
    avg_train_loss = sum(train_losses) / len(train_losses)
    avg_val_loss = eval_model(model, val_dl, 'avg_val_loss', epoch)

    clear_print_line()
    print(f'{epoch}/{config.epochs}\t│ {avg_train_loss:.4f}\t │ {avg_val_loss:.4f}\t│ {(t2-t1):.2f}s')
    return avg_train_loss, avg_val_loss


def train_val_test_split(config: ModelConfig, return_loaders: bool = True) -> Tuple[DataLoader | pd.DataFrame]:
    """Returns `torch.utils.data.DataLoader`s for training, validation, and test datasets with the `config` provided"""
    df = pd.read_csv(_locate(config.model_name, config.csv_file))
    df = config.prep_ds(df if config.n_samples == 'all' else df.sample(config.n_samples))
    train_rows = int(config.train_size*len(df))
    val_rows = train_rows + int(config.val_size*len(df))
    train_df, val_df, test_df = df[train_rows:], df[train_rows:val_rows], df[val_rows:]

    loader = lambda any_df: DataLoader(
        DFDataset(any_df, config.prep_sample), 
        batch_size=config.batch_size,
        num_workers=config.num_workers,
        prefetch_factor=config.prefetch_factor,
        shuffle=config.shuffle,
        drop_last=config.drop_last,
        persistent_workers=(config.num_workers > 1)
    )
    return loader(train_df), loader(val_df), loader(test_df) if return_loaders else train_df, val_df, test_df
        

def init_training(ModelClass: NeuralNetwork, config: ModelConfig):
    """Sets up the model & optimizer to start training from scratch"""
    model = ModelClass(config).to(config.device)
    model = torch.compile(model)
    optimizer = config.optimizer(model.parameters(), lr=config.lr)
    return model, optimizer


def load_checkpoint(
        ModelClass: NeuralNetwork, 
        config: ModelConfig, 
        run_name: Optional[str] = None
    ) -> Optional[Tuple[torch.nn.Module | str]]:
    """Loads the model & its optimizer from the latest checkpoint saved"""
    model_dirname, optimizer_dirname, nameformat = config.persist_model_dir_name, config.persist_optimizer_dir_name, config.persist_name_fmt

    # Check if the directories to save artifacts exist
    result = _check_checkpoint_dirs(config.model_name, model_dirname, optimizer_dirname)
    if (result is False) or (len(result[0]) == 0 or len(result[1]) == 0):
        raise FileNotFoundError('Please save a checkpoint first using `src.lib.utils.models.save_checkpoint` function.')

    assert len(os.listdir(_locate(config.model_name, model_dirname))) == len(os.listdir(_locate(config.model_name, optimizer_dirname))), \
    'The saved model and the saved optimizer directories must have the same number of files.'

    # Get the latest model using its file name
    if run_name:
        chosen_run = run_name
        checkpoints = [
            datetime.strptime(checkpoint, nameformat)
            for checkpoint in os.listdir(_locate(config.model_name, f'{model_dirname}/{run_name}/'))
        ]
        if len(checkpoints) == 0: return
        checkpoint_name = run_name + datetime.strftime(max(checkpoints), nameformat)
    else:
        # Load latest run
        runs = [
            datetime.strptime(checkpoint.replace('Run_', ''), nameformat.replace('.pt', ''))
            for checkpoint in os.listdir(_locate(config.model_name, model_dirname))
        ]
        chosen_run = 'Run_' + datetime.strftime(max(runs), nameformat.replace('.pt', ''))
        checkpoints = [
            datetime.strptime(checkpoint, nameformat)
            for checkpoint in os.listdir(_locate(config.model_name, f'{model_dirname}/{chosen_run}/'))
        ]

        if len(checkpoints) == 0: return
        checkpoint_name = chosen_run + '/' + datetime.strftime(max(checkpoints), nameformat)

    # Remove the prefix `_orig_mod.` from the keys
    def _update_state_dict(state_dict):
        new_state_dict = {}
        for k, v in state_dict.items():
            new_key = k.replace('_orig_mod.', '')
            new_state_dict[new_key] = v
        return new_state_dict
    
    locate_checkpoint = lambda dirname: _locate(config.model_name, dirname + '/' + checkpoint_name)
    model_state_dict = _update_state_dict(torch.load(locate_checkpoint(model_dirname), weights_only=True))
    optimizer_state_dict = _update_state_dict(torch.load(locate_checkpoint(optimizer_dirname), weights_only=False))

    # Load the model
    model = ModelClass(config).to(config.device) 
    model.load_state_dict(model_state_dict)
    model = torch.compile(model)
    optimizer = config.optimizer(model.parameters(), lr=config.lr)
    optimizer.load_state_dict(optimizer_state_dict)
    return model, optimizer, chosen_run


def save_checkpoint(
        model: NeuralNetwork, 
        optimizer: torch.nn.Module, 
        avg_train_loss: float, 
        epoch: int,
        run_name: str,
        config: ModelConfig
    ) -> None:
    """Saves the model and other information periodically

    ---
    :param model: The PyTorch model to save.
    :param optimizer: The optimizer of the model to save.
    :param avg_train_loss: The average training loss of the model.
    :param epoch: The epoch when the average training loss was calculated.
    :param run_name: Name of the Mlflow training run.
    :param config: Settings used by the model.
    """
    model_dirname, optimizer_dirname = config.persist_model_dir_name, config.persist_optimizer_dir_name
    filename = datetime.now().strftime(config.persist_name_fmt)
    pkgs_file = os.path.join(CURRENT_DIR, '../../../requirements.txt')

    if not _check_checkpoint_dirs(config.model_name, model_dirname, optimizer_dirname):
        if '/' in model_dirname: os.mkdir(model_dirname.split('/')[0])
        os.mkdir(model_dirname)
        os.mkdir(optimizer_dirname)
    
    # Let Mlflow infer automatically the model's signature using a random example
    ex = [torch.randint(0, config.vocab_size, (1, config.seq_len)).to(config.device), torch.randn(1).to(config.device)]
    input_ex = [ex[0].float().tolist(), ex[1].float().unsqueeze(0).tolist()]
    output_ex = model(ex).tolist()
    sig = mlflow.models.infer_signature(input_ex, output_ex)

    # Save & log artifacts & metrics
    _check_run_dirs(model_dirname, optimizer_dirname, run_name, config)
    torch.save(model.state_dict(), model_dirname+f'/{run_name}/{filename}')
    torch.save(optimizer.state_dict(), optimizer_dirname+f'/{run_name}/{filename}')
    
    mlflow.log_metric('avg_train_loss', avg_train_loss, step=epoch)
    mlflow.log_param('nn_layers', repr(model.neural_net))
    mlflow.pytorch.log_model(
        pytorch_model=model,
        artifact_path=model_dirname,
        pip_requirements=pkgs_file, 
        signature=sig
    )


def load_latest_for_training(ModelClass: NeuralNetwork, config: ModelConfig) -> Tuple:
    """Tries to load the latest trained model & optimizer"""
    if config.load_last_chkpt:
        try:
            out = load_checkpoint(ModelClass, config)
            print('--- Training using the last saved checkpoint ---')
        except FileNotFoundError:
            print('--- Failed loading the last saved checkpoint! Training from scratch ---')
            out = init_training(ModelClass, config)
    else:
        out = init_training(ModelClass, config)
    return out


def plot_avg_losses(saved_epochs: List[int], avg_train_losses: List[float], avg_val_losses: List[float], config: ModelConfig) -> None:
    """Plots both the average training & validation loss over epochs"""
    for losses, filename in zip((avg_train_losses, avg_val_losses), (config.avg_train_loss_filename, config.avg_val_loss_filename)):
        plt.clf()
        plt.plot(saved_epochs, losses)
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.savefig(filename)


def eval_model(model: NeuralNetwork, dl: DataLoader, loss_name: str, epoch: Optional[int] = None) -> float:
    """Evaluates the given model on a given dataset and returns the average loss. For metric logging, specify `loss_name` (e.g., "val_loss", "test_loss")"""
    assert len(dl) > 0, 'empty DataLoader'
    losses = []
    for batch_i, (X, y) in enumerate(dl):
        losses.append(model(X, y).item())
        print(f'\rFinished Batch {batch_i}/{len(dl)}', end='', flush=True)
    avg_loss = sum(losses) / len(losses)
    mlflow.log_metric(loss_name, avg_loss, step=(epoch if epoch else None))
    return avg_loss


def log_bin_clf_metrics(model: NeuralNetwork, threshold: float, test_df: pd.DataFrame, target_class: str, config: ModelConfig) -> None:
    """Logs & prints accuracy, recall, precision, and F1 score (in order) for a given binary classifier
    
    ---
    :param model: The binary classifier neural network.
    :param threshold: Threshold to determine if a sample is classified as positive or negative. `If prediction >= threshold: positive; else: negative`
    :param test_df: Test dataset as a Pandas DataFrame.
    :param target_class: Name of the dependent variable.
    :param config: Settings used by the model.
    """
    TP, TN, FP, FN = 0, 0, 0, 0

    for row in test_df.iterrows():
        sample = row[1].to_dict()
        y = sample[target_class]
        del sample[target_class]
        sample = config.prep_sample(**sample)[0]
        sample[0] = sample[0].unsqueeze(0)
        sample[1] = sample[1].unsqueeze(0)

        y_pred = int(model(sample) >= threshold)
        match (y_pred, y):
            case (1, 1): TP += 1
            case (1, 0): FP += 1
            case (0, 1): FN += 1
            case (0, 0): TN += 1
    
    accuracy = (TP + TN) / (TP + TN + FP + FN)
    recall = TP / (TP + FN)
    precision = TP / (TP + FP)
    f1_score = (2 * precision * recall) / (precision + recall)

    mlflow.log_metric('accuracy', accuracy)
    mlflow.log_metric('recall', recall)
    mlflow.log_metric('precision', precision)
    mlflow.log_metric('f1_score', f1_score)
    print(f'Accuracy: {accuracy:.4f}')
    print(f'Recall: {recall:.4f}')
    print(f'Precision: {precision:.4f}')
    print(f'F1 Score: {f1_score:.4f}')