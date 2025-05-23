import logging


def setup_logger(verbosity: int):
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if verbosity > 1 else logging.INFO)

    app_logger = logging.getLogger(__package__)
    app_logger.setLevel(logging.DEBUG if verbosity else logging.INFO)

    logging.basicConfig(
        format=(
            "%(asctime)s:%(name)s:%(threadName)s:%(levelname)s:%(message)s"
            if verbosity > 1
            else "%(asctime)s:%(message)s"
        )
    )
