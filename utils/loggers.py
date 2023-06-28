import logging

# log string formats
LOGFILE_FORMAT = "%(asctime)s -- %(levelname)s -- %(name)s -- %(message)s -- module:%(module)s -- function:%(module)s"
CONSOLE_FORMAT = "%(asctime)s -- %(levelname)s -- %(name)s -- %(message)s"
PRINT_FORMAT = "%(message)s"
# TODO: improve formats, make it easy to choose different formats when instantiating the logger


class Logger:
    """
    Class for custom logger with console and file handlers
    """
    def __init__(self,
                 dunder_name,
                 console_logger=False,
                 file_logger=False,
                 print_logger=False,
                 console_log_level="INFO",
                 file_log_level="INFO",
                 print_log_level="INFO",
                 log_file_path=f"logfile.log"):

        self.logger_name = dunder_name
        self.console_logger = console_logger
        self.file_logger = file_logger
        self.print_logger = print_logger
        self.console_log_level = console_log_level
        self.file_log_level = file_log_level
        self.print_log_level = print_log_level
        self.log_file_path = log_file_path

        # set up logger
        logger = self.configure_logger()
        self.logger = logger

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)

    def configure_logger(self):

        # define output string formats
        file_formatter = logging.Formatter(LOGFILE_FORMAT)
        console_formatter = logging.Formatter(CONSOLE_FORMAT)
        print_formatter = logging.Formatter(PRINT_FORMAT)

        logger = logging.getLogger(self.logger_name)
        logger.setLevel(logging.DEBUG)
        logger.handlers = []

        # if console logging is enabled
        if self.console_logger is True:
            console_handler = logging.StreamHandler()
            set_log_level(console_handler, self.console_log_level)
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)

        # if file logging is enabled
        if self.file_logger is True:
            file_handler = logging.FileHandler(self.log_file_path)
            file_handler.setFormatter(file_formatter)
            set_log_level(file_handler, self.file_log_level)
            logger.addHandler(file_handler)

        # if print logging is enabled
        if self.print_logger is True:
            print_handler = logging.StreamHandler()
            set_log_level(print_handler, self.print_log_level)
            print_handler.setFormatter(print_formatter)
            logger.addHandler(print_handler)

        return logger


def set_log_level(handler, log_level):
    """
    Sets the log level for the given handler.
    """
    if log_level == "DEBUG":
        handler.setLevel(logging.DEBUG)
    elif log_level == "INFO":
        handler.setLevel(logging.INFO)
    elif log_level == "WARNING":
        handler.setLevel(logging.WARNING)
    elif log_level == "ERROR":
        handler.setLevel(logging.ERROR)
    elif log_level == "CRITICAL":
        handler.setLevel(logging.CRITICAL)
    else:
        handler.setLevel(logging.WARNING)
