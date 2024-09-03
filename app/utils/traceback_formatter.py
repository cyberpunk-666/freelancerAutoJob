import logging
import traceback

class TracebackFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, max_length=None):
        super().__init__(fmt, datefmt)
        self.max_length = max_length 

    def format(self, record):
        # Call the original format method to get the initial formatted message
        formatted_message = super().format(record)

        # If there's an exception, append the formatted traceback to the message
        if record.exc_info:
            formatted_message += f"\n{traceback.format_exc()}"

        # Truncate the message if it exceeds max_length
        if self.max_length and len(formatted_message) > self.max_length:
            formatted_message = formatted_message[:self.max_length] + '...'

        return formatted_message

# Example usage
# if __name__ == "__main__":
#     # Create a logger
#     logger = logging.getLogger(__name__)
#     logger.setLevel(logging.DEBUG)

#     # Create a console handler
#     console_handler = logging.StreamHandler()

#     # Create and set the custom formatter
#     formatter = TracebackFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#     console_handler.setFormatter(formatter)

#     # Add the handler to the logger
#     logger.addHandler(console_handler)

#     # Example log with an exception
#     try:
#         1 / 0
#     except Exception:
#         logger.error("An error occurred", exc_info=True)




