import logging

from krauler.state import Krauler
from krauler.mf import MetaFolderKrauler
from krauler.util import configure_logging

from krauler.signals import on_init, on_meta, on_parse, on_session, on_wait


def crawl_to_metafolder(config):
    configure_logging()
    mfk = MetaFolderKrauler(config)
    mfk.metafolder  # Show storage location for output
    return mfk.run()


__all__ = [Krauler, MetaFolderKrauler, crawl_to_metafolder,
           on_init, on_meta, on_parse, on_session]
