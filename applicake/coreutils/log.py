import logging

class Logger(object):
    @staticmethod
    def create(level):
        logging.basicConfig(format="- %(levelname)s - %(asctime)s - %(message)s")
        logger = logging.getLogger()
        logger.setLevel(level)
        return logger
