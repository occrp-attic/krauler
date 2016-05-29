import logging
import requests
from Queue import Queue
from threading import RLock

from krauler.config import Config
from krauler.page import Page
from krauler.signals import on_init, on_session

log = logging.getLogger(__name__)


class Krauler(object):

    def __init__(self, config_data):
        self.config = Config(config_data)
        self.seen = set([])
        self.seen_lock = RLock()
        self.queue = Queue()

    @property
    def session(self):
        if not hasattr(self, '_session'):
            session = requests.Session()
            session.proxies = self.config.proxies
            session.verify = False
            session.headers['User-Agent'] = self.config.user_agent
            on_session.send(self, session=session)
            self._session = session
        return self._session

    def crawl(self, url, path=None):
        if path is None:
            path = []
        if not self.is_seen(url):
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

    def process_next(self):
        url, path = self.queue.get()
        try:
            page = Page(self, url, path)
            page.process()
        except Exception as exc:
            log.exception(exc)
        finally:
            self.queue.task_done()

    def init(self):
        on_init.send(self)
        for url in self.config.seeds:
            self.crawl(url)

    def run(self):
        self.init()
        while self.queue.qsize() > 0:
            self.process_next()

    def emit(self, page):
        log.warning("Emitted: %r, no action defined to store!")
