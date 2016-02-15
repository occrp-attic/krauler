from krauler.state import Krauler
from krauler.mf import MetaFolderKrauler


def crawl_to_metafolder(config):
    mfk = MetaFolderKrauler(config)
    return mfk.run()


__all__ = [Krauler, MetaFolderKrauler, crawl_to_metafolder]
