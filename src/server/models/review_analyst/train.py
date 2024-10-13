from torch.multiprocessing import set_start_method; set_start_method('spawn', force=True)
import mlflow, datetime, time
from src.lib.data.model import model_config
from src.lib.utils.db import todict
from src.lib.utils.model import train_val_test_split, init_training, load_checkpoint, save_checkpoint, plot, eval_model
from src.lib.data.constants import MLFLOW_TRACKING_URI

if __name__ == '__main__':
    # Init experiment
    mlflow.set_experiment('Review Analyst Experiment')
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

    # Load the data, model, and optimizer
    config = model_config.review_analyst()
    train_ds, val_ds, test_ds = train_val_test_split(config)

    if config.load_last_chkpt:
        try:
            model, optimizer = load_checkpoint(config)
            print('--- Training using the last saved checkpoint ---')
        except FileNotFoundError:
            print('--- Failed loading the last saved checkpoint! Training from scratch ---')
            model, optimizer = init_training(config)
    else:
        model, optimizer = init_training(config)
    
    # Train
    with mlflow.start_run(run_name=f'Run {datetime.datetime.now().strftime(model_config.base.persist_name_fmt)}'):
        mlflow.log_params(todict(config))
        avg_train_losses, avg_val_losses = [], []

        for epoch in range(1, config.epochs+1):
            losses = []

            t1 = time.time()
            for batch_i, (X, y) in enumerate(train_ds):
                train_loss = model(X, y, training=True)
                optimizer.zero_grad()
                train_loss.backward()
                optimizer.step()
                
                losses.append(train_loss.item())
                print(f'\rFinished Batch {batch_i+1}', end='', flush=True)
            t2 = time.time()

            if epoch % config.epochs_before_saving == 0:
                avg_train_loss = sum(losses) / len(losses)
                avg_train_losses.append(avg_train_loss)
                save_checkpoint(model, optimizer, avg_train_loss, config)
                
                avg_val_loss = eval_model(model, val_ds, 'val_loss')
                avg_val_losses.append(avg_val_loss)

                plot(avg_train_losses, 'artifacts/avg_train_losses.jpg')
                plot(avg_val_losses, 'artifacts/avg_val_losses.jpg')

                print('\r', end='', flush=True)
                print(f'Epoch {epoch}/{config.epochs}    Average train loss: {avg_train_loss:.4f}    Average val loss: {avg_val_loss:.4f}    Time elapsed: {(t2-t1):.2f}s')