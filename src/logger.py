import logging
import sys

logger = logging.getLogger('my_project')
logger.setLevel(logging.INFO)

_formatter = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
_handler = logging.StreamHandler(sys.stdout)

_handler.setFormatter(_formatter)
logger.addHandler(_handler)