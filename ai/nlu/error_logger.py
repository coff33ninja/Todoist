import logging

class ErrorLogger:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def log_error(self, message: str, exception: Exception) -> None:
        """Log an error message with exception details."""
        self.logger.error("%s: %s", message, str(exception))

    def log_warning(self, message: str, *args) -> None:
        """Log a warning message."""
        self.logger.warning(message, *args)

    def log_info(self, message: str, *args) -> None:
        """Log an informational message."""
        self.logger.info(message, *args)
