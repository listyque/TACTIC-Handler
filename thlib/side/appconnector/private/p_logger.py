import logging


logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(message)s"
)

logger = logging.getLogger("connection.log")
