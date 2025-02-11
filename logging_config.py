import coloredlogs

def setup_logging():
    """
    Configures colored logging
    """

    coloredlogs.install(
        level='INFO',
        fmt='%(asctime)s %(levelname)-8s %(name)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
