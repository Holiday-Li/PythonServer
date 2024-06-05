import logging, os
from Utils import get_current_dir_path

def generate_log_folder():
        base_dir = get_current_dir_path()
        log_folder = os.path.join(base_dir, "log\\")
        if not os.path.exists(log_folder):
            os.mkdir(log_folder)
        return log_folder


def init_logger(log_folder, logger_name):
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

def get_logger(logger_name):
     log_folder = generate_log_folder()
     logger = init_logger(log_folder=log_folder, logger_name=logger_name)
     return logger

'''
class Logger:
    def __generate_log_folder(self):
        base_dir = get_current_dir_path()
        log_folder = os.path.join(base_dir, "log\\")
        if not os.path.exists(log_folder):
            os.mkdir(log_folder)
        return log_folder

    def __init_logger(self, log_folder, logger_name):
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
    
    def __init__(self, logger_name):
        log_folder = self.__generate_log_folder()
        self.logger = self.__init_logger(log_folder=log_folder,
                                         logger_name=logger_name)
        
    def __del__(self):
        del self.logger
    

    def debug(self, message):
        self.logger.debug(message)
        return
    
    def info(self, message):
        self.logger.info(message)
        return

    def warning(self, message):
        self.warning(message)
        return
    
    def error(self, message):
        self.error(message)
        return
    
    def critical(self, message):
        self.critical(message)
        return
    '''


if __name__ == "__main__":
    logger = get_logger("123")
    logger.info("info message")
    logger.debug("debug message")
    logger.error("error message")
    del logger