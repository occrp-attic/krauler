import logging
import requests
from urlparse import urlparse
from Queue import Queue
from threading import RLock

from krauler.page import KraulerPage
from krauler.util import as_list, normalize_url

log = logging.getLogger(__name__)


class Krauler(object):

    def __init__(self, config):
        self.config = config
        self.seen = set([])
        self.seen_lock = RLock()
        self.queue = Queue()

    @property
    def session(self):
        if not hasattr(self, '_session'):
            self._session = requests.Session()
        return self._session

    @property
    def seeds(self):
        if not hasattr(self, '_seeds'):
            seeds = as_list(self.config.get('seed'))
            seeds = [normalize_url(s) for s in seeds]
            self._seeds = [s for s in seeds if s is not None]
        return self._seeds

    def crawl(self, url, path):
        if self.should_crawl(url):
            self.queue.put((url, path))

    def mark_seen(self, url):
        self.seen_lock.acquire()
        try:
            self.seen.add(url)
        finally:
            self.seen_lock.release()

    def is_seen(self, url):
        self.seen_lock.acquire()
        try:
            return url in self.seen
        finally:
            self.seen_lock.release()

    def next_page(self):
        url, path = self.queue.get()
        log.info("Crawling %r (%d queued, %s seen)", url, self.queue.qsize(),
                 len(self.seen))
        try:
            page = KraulerPage(self, url, path)
            page.process()
        except Exception as exc:
            log.exception(exc)
        finally:
            self.queue.task_done()

    def should_retain(self, page):
        if not self.should_process(page.normalized_url):
            return False
        return True

    def should_crawl(self, url):
        if self.is_seen(url):
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
            self.crawl(url, [])

        while not self.queue.empty():
            self.next_page()

    def emit(self, page):
        log.warning("Emitted: %r, no action defined to store!")
