import logging


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(message)s"
)

logger = logging.getLogger("connection.log")
