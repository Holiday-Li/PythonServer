import logging, os
from Utils import get_current_dir_path

def generate_log_folder()->str:
    base_dir = get_current_dir_path()
    log_folder = os.path.join(base_dir, "log\\")
    if not os.path.exists(log_folder):
        os.mkdir(log_folder)
    return log_folder


def init_logger(log_folder:str, logger_name:str)->logging.Logger:
    # Create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    # Create file handler
    log_filepath = os.path.join(log_folder, "{}.log".format(logger_name))
    fh = logging.FileHandler(log_filepath)
    fh.setLevel(logging.DEBUG)

    # Setting formatter
    fmt = "%(asctime)-15s [%(filename)s:%(lineno)d] [%(levelname)s] %(message)s"
    data_fmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt, data_fmt)

    # add Handler and formatter to logger
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger


def get_logger(logger_name:str)->logging.Logger:
    log_folder = generate_log_folder()
    logger = init_logger(log_folder=log_folder, logger_name=logger_name)
    return logger


def clean_log_files():
    base_path = get_current_dir_path()
    log_folder = os.path.join(base_path, "log\\")
    print("log folder path:{}".format(log_folder))
    print("log files:")
    for root, _, files in os.walk(log_folder):
        for file in files:
            log_file = os.path.join(root, file)
            print("\t{}".format(log_file))
            os.remove(log_file)
    return


if __name__ == "__main__":
    clean_log_files()
    logger = get_logger("123")
    logger.info("info message")
    logger.debug("debug message")
    logger.error("error message")
    del logger