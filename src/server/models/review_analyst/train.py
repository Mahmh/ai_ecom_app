from torch.multiprocessing import set_start_method; set_start_method('spawn', force=True)
import mlflow, time
from src.server.models.review_analyst.model import ReviewAnalyst
from src.lib.data.models import ReviewAnalystConfig as config
from src.lib.utils.db import todict
from src.lib.utils.models import (
    init_mlflow,
    new_run_name,
    print_epoch_result,
    train_val_test_split,
    load_latest_for_training,
    save_checkpoint,
    plot_avg_losses,
    log_bin_clf_metrics
)

if __name__ == '__main__':
    init_mlflow('Review Analyst Experiment')

    # Load the data, model, and optimizer
    # train_dl, val_dl, _ = train_val_test_split(config)

    try:
        model, optimizer, run_name = load_latest_for_training(ReviewAnalyst, config)
    except:
        model, optimizer = load_latest_for_training(ReviewAnalyst, config)
        run_name = new_run_name(config)
    
    test_df = train_val_test_split(config, return_loaders=False)[2]
    print(log_bin_clf_metrics(model, .5, test_df, 'sentiment', config))
    
    # # Train
    # with mlflow.start_run(run_name=run_name):
    #     mlflow.log_params(todict(config))
    #     avg_train_losses, avg_val_losses, saved_epochs = [], [], []

    #     print('Epoch\t│ Avg train loss │ Avg val loss\t│ Time elapsed')
    #     print('────────┼────────────────┼──────────────┼─────────────')
    #     for epoch in range(1, config.epochs+1):
    #         train_losses = []

    #         t1 = time.time()
    #         for batch_i, (X, y) in enumerate(train_dl, 1):
    #             train_loss = model(X, y, training=True)
    #             optimizer.zero_grad()
    #             train_loss.backward()
    #             optimizer.step()
    #             train_losses.append(train_loss.item())
    #             print(f'\rFinished Batch {batch_i}/{len(train_dl)}', end='', flush=True)
    #         t2 = time.time()

    #         if (epoch % config.epochs_before_saving == 0) or (epoch == config.epochs):
    #             saved_epochs.append(epoch)
    #             avg_train_loss, avg_val_loss = print_epoch_result(model, train_losses, val_dl, epoch, t1, t2, config)
    #             avg_train_losses.append(avg_train_loss)
    #             avg_val_losses.append(avg_val_loss)

    #             save_checkpoint(model, optimizer, avg_train_loss, epoch, run_name, config)
    #             plot_avg_losses(saved_epochs, avg_train_losses, avg_val_losses, config)
    #         elif (epoch % config.epochs_before_printing == 0):
    #             print_epoch_result(model, train_losses, val_dl, epoch, t1, t2, config)