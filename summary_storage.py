import os
import logging
from logging.handlers import RotatingFileHandler

class SummaryStorage:
    def __init__(self, file_path='summaries.txt', max_size=100 * 1024):
        self.file_path = file_path
        self.max_size = max_size
        self.logger = self._setup_logger()
        self.logger.debug(f"Initialized SummaryStorage with file_path={self.file_path} and max_size={self.max_size} bytes")

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
        self.logger.debug(f"Appending summary: {content}")
        try:
            self.logger.info(content)
            self.logger.debug("Summary appended successfully.")
        except Exception as e:
            self.logger.error(f"Error appending summary: {e}")

    def read_summaries(self):
        self.logger.debug("Reading summaries from file.")
        if not os.path.exists(self.file_path):
            self.logger.warning(f"File not found: {self.file_path}. Returning empty list.")
            return []

        try:
            with open(self.file_path, 'r') as file:
                summaries = file.readlines()
            self.logger.debug(f"Read {len(summaries)} summaries from file.")
            return summaries
        except Exception as e:
            self.logger.error(f"Error reading summaries: {e}")
            return []

    def delete_summary(self, content):
        self.logger.debug(f"Deleting summary: {content}")
        if not os.path.exists(self.file_path):
            self.logger.warning(f"File not found: {self.file_path}. Cannot delete summary.")
            return

        try:
            with open(self.file_path, 'r') as file:
                summaries = file.readlines()

            with open(self.file_path, 'w') as file:
                deleted = False
                for summary in summaries:
                    if summary.strip() != content.strip():
                        file.write(summary)
                    else:
                        deleted = True

                if deleted:
                    self.logger.debug("Summary deleted successfully.")
                else:
                    self.logger.warning("Summary to delete not found in file.")
        except Exception as e:
            self.logger.error(f"Error deleting summary: {e}")
