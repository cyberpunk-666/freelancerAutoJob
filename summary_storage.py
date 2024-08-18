import os
import logging
from logging.handlers import RotatingFileHandler

class SummaryStorage:
    def __init__(self, file_path='summaries.txt', max_size=100 * 1024):
        self.file_path = file_path
        self.max_size = max_size
        self.logger = self._setup_logger()

    def _setup_logger(self):
        logger = logging.getLogger('SummaryLogger')
        logger.setLevel(logging.DEBUG)

        handler = RotatingFileHandler(
            self.file_path,
            maxBytes=self.max_size,
            backupCount=0  # Only keep the current file, no backups
        )

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def append_summary(self, content):
        self.logger.info(content)

    def read_summaries(self):
        if not os.path.exists(self.file_path):
            return []

        with open(self.file_path, 'r') as file:
            summaries = file.readlines()
        return summaries

    def delete_summary(self, content):
        if not os.path.exists(self.file_path):
            return

        with open(self.file_path, 'r') as file:
            summaries = file.readlines()

        with open(self.file_path, 'w') as file:
            for summary in summaries:
                if summary.strip() != content.strip():
                    file.write(summary)

