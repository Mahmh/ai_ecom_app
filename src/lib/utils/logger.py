import logging, os
from src.lib.data.constants import ENABLE_LOGGING

def log(msg: str, filename: str, level: int = logging.INFO) -> logging.Logger:
    """
    Create a logger to write logs (always inside the `logs/` directory) to a specific file.
    The environment variable "ENABLE_LOGGING" must be set to true first.

    ---
    :param msg: The message you want to log.
    :param filename: The name of the logging file you want to log the message to. You don't need to include the `.log` file extension.
    :param level: The logging level (INFO, WARNING, etc.).
    """
    if ENABLE_LOGGING.lower() != 'true': return
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        filename += '.log' if filename[-4:] != '.log' else ''
        filename = current_dir + '/../../server/logs/' + filename
        logging.basicConfig(filename=filename, level=level, filemode='a', format='%(asctime)s - %(levelname)s - %(message)s')
        logging.log(level, msg)
    except FileNotFoundError:
        print('[src.lib.utils.logger] FileNotFoundError: Logging did not work.')
        return


def err_log(func_name: str, e: Exception, filename: str) -> None:
    """Simple, overused function to log an error"""
    err_name = str(type(e)).split("'")[1]
    log(f'[{func_name}] {err_name}: {e}', filename, logging.ERROR)