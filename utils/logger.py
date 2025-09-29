import logging
import sys
from colorama import Fore, Style, init

# Initializing colorama for Windows compatibility
init(autoreset=True)

class ColoredFormatter(logging.Formatter):
    '''Custom log formatter for colored output'''

    COLORS = {
        "DEBUG": Fore.BLUE,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.RED + Style.BRIGHT,
    }

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, Fore.WHITE)
        record.msg = f"{log_color}{record.msg}{Style.RESET_ALL}"
        return super().format(record)

# Create logger
logger = logging.getLogger("BVT_logger")
logger.setLevel(logging.DEBUG)

# Formatter with line number
formatter = logging.Formatter("%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s")

# File Handler (Logs to a file)
file_handler = logging.FileHandler("./runtime_logs/app.log")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# Console Handler (Logs to console with colors)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(ColoredFormatter("%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"))

# Add both handlers
logger.addHandler(file_handler)
logger.addHandler(console_handler)
