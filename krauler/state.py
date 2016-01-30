import logging
import requests
from urlparse import urlparse

from krauler.page import KraulerPage
from krauler.util import as_list, normalize_url

log = logging.getLogger(__name__)


class Krauler(object):

    def __init__(self, config):
        self.config = config
        self.seen = set([])

    @property
    def session(self):
        if not hasattr(self, '_session'):
            self._session = requests.Session()
        return self._session

    @property
    def seeds(self):
        if not hasattr(self, '_seeds'):
            seeds = as_list(self.config.get('seed'))
            self._seeds = [normalize_url(s) for s in seeds]
        return self._seeds

    def queue(self, url):
        page = KraulerPage(self, url)
        # TODO: add celery?
        page.process()

    def should_retain(self, page):
        if not self.should_process(page.normalized_url):
            return False
        return True

    def should_crawl(self, url):
        if normalize_url(url) in self.seen:
            return False
        if not self.should_process(url):
            return False
        return True

    def should_process(self, url):
        parsed = urlparse(url)

        for seed in self.seeds:
            sparsed = urlparse(seed)
            if parsed.hostname == sparsed.hostname:
                return True
            dom = '.%s' % sparsed.hostname
            if parsed.hostname.endswith(dom):
                return True
        return False

    def run(self):
        for url in self.seeds:
            self.queue(url)

    def emit(self, page):
        log.warning("Emitted: %r, no action defined to store!")
