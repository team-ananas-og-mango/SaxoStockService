import logging
class LoggingService:
    def __init__(self, name) -> None:
        
        self.logger = logging.getLogger(name)
        self.handler = logging.StreamHandler()
        self.formatter = logging.Formatter(
            '%(asctime)s [%(name)-12s] %(levelname)-8s %(message)s')
        self.handler.setFormatter(self.formatter)
        self.logger.addHandler(self.handler)
        self.logger.setLevel(logging.DEBUG)
