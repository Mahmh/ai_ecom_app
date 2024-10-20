from torch.multiprocessing import set_start_method; set_start_method('spawn', force=True)
import mlflow, time, sys
from src.server.models.review_analyst.model import ReviewAnalyst
from src.lib.data.models import ReviewAnalystConfig as config
from src.lib.utils.models import init_mlflow, clear_print_line, load_checkpoint, train_val_test_split, eval_model, log_bin_clf_metrics

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Sorry, but you missed a command-line argument.')
        print('Usage: python3 test.py <LATEST_RUN_ID>')
        exit(1)
    
    init_mlflow('Review Analyst Experiment')
    model = load_checkpoint(ReviewAnalyst, config)[0]
    test_dl = train_val_test_split(config)[2]
    
    with mlflow.start_run(run_id=sys.argv[1]):
        t1 = time.time()
        avg_test_loss = eval_model(model, test_dl, 'avg_test_loss')
        t2 = time.time()
        clear_print_line()
        print(f'Test loss: {avg_test_loss:.4f} (took {(t2-t1):.1f}s)')

        test_df = train_val_test_split(config, return_loaders=False)[2]
        log_bin_clf_metrics(model, .5, test_df, 'sentiment', config)