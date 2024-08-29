import logging
import traceback

class TracebackFormatter(logging.Formatter):
    def format(self, record):
        # Format the original log message
        formatted_message = super().format(record)
        # Check if the log level is ERROR and exception info is present
        if record.levelno == logging.ERROR and record.exc_info:
            # Format the traceback
            error_details = ''.join(traceback.format_exception(*record.exc_info))
            # Append the traceback to the original message
            formatted_message = f"{formatted_message}\n{error_details}"
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


