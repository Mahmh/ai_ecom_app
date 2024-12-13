from torch.multiprocessing import set_start_method; set_start_method('spawn', force=True)
import mlflow, time
from src.lib.data.constants import MLFLOW_TRACKING_URI
from src.lib.data.models import ProductRaterConfig as config
from src.lib.utils.db import todict
from src.lib.utils.models import check_mlflow_server, new_run_name, train_val_test_split, load_latest_for_training, save_checkpoint, plot_avg_losses, eval_model
from src.server.models.product_rater.model import ProductRater

if __name__ == '__main__':
    # Init experiment
    check_mlflow_server()
    mlflow.set_experiment('Product Rater Experiment')
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

    # Load the data, model, and optimizer
    train_dl, val_dl, test_dl = train_val_test_split(config)
    model, optimizer = load_latest_for_training(ProductRater, config)
    
    # Train
    with mlflow.start_run(run_name=new_run_name(config)):
        mlflow.log_params(todict(config))
        avg_train_losses, avg_val_losses = [], []

        for epoch in range(1, config.epochs+1):
            losses = []

            t1 = time.time()
            for batch_i, (X, y) in enumerate(train_dl):
                train_loss = model(X, y, training=True)
                optimizer.zero_grad()
                train_loss.backward()
                optimizer.step()
                
                losses.append(train_loss.item())
                print(f'\rFinished Batch {batch_i+1}  ', end='', flush=True)
            t2 = time.time()

            if epoch % config.epochs_before_saving == 0:
                avg_train_loss = sum(losses) / len(losses)
                avg_train_losses.append(avg_train_loss)
                save_checkpoint(model, optimizer, avg_train_loss, config)
                
                avg_val_loss = eval_model(model, val_dl, 'avg_val_loss')
                avg_val_losses.append(avg_val_loss)
                plot_avg_losses(avg_train_losses, avg_val_losses, config)

                print('\r', end='', flush=True)
                print(f'Epoch {epoch}/{config.epochs}    Average train loss: {avg_train_loss:.4f}    Average val loss: {avg_val_loss:.4f}    Time elapsed: {(t2-t1):.2f}s')