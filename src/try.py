import logging
import structlog

# Set the level once
logging.basicConfig(level=logging.WARNING)

# Configure structlog to actually USE the standard library logger
structlog.configure(
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
)

logger = structlog.get_logger()

print("Testing log levels:")
logger.debug("DEBUG: This should not appear")
logger.info("INFO: This should not appear") 
logger.warning("WARNING: This SHOULD appear")
logger.error("ERROR: This SHOULD appear")