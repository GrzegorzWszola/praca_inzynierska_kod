import logging

# Create and configure the top-level package logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Attach handler & format once
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] [BookParser]: %(message)s"))
logger.addHandler(handler)