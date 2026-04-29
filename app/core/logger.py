import logging
import os
from datetime import datetime

_session_logger = None


def get_session_logger() -> logging.Logger:
    """
    Returns a singleton session logger.
    Creates logs/ directory and one log file per server session.
    Also configures the root logger so all module-level loggers
    (e.g. app.evaluation.deepeval_runner) write to the same file.
    """
    global _session_logger
    if _session_logger is not None:
        return _session_logger

    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
    os.makedirs(logs_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(logs_dir, f"evaluation_session_{timestamp}.log")

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Configure root logger so all module loggers (app.*, deepeval, etc.) flow into the session log
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    # Remove pre-existing handlers added by uvicorn/other libs to avoid duplicate writes to other files
    for h in list(root.handlers):
        root.removeHandler(h)
    root.addHandler(file_handler)
    root.addHandler(console_handler)

    logger = logging.getLogger("evaluation_session")
    logger.setLevel(logging.INFO)
    logger.info(f"Session started — log file: {log_file}")

    _session_logger = logger
    return _session_logger
