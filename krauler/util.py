import logging
import requests


def configure_logging():
    requests.packages.urllib3.disable_warnings()
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('requests').setLevel(logging.WARNING)
    # logging.getLogger('dataset').setLevel(logging.WARNING)
