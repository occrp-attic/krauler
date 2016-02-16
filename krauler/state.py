import os
import re
import logging
import requests
from Queue import Queue
from threading import RLock, Thread

from krauler.page import Page
from krauler.util import normalize_url, get_list
from krauler.util import match_domain
from krauler.types import normalize_types, url_type
from krauler.signals import on_init, on_session, on_wait

log = logging.getLogger(__name__)


class Krauler(object):

    USER_AGENT = os.environ.get('KRAULER_UA',
                                'krauler (https://github.com/pudo/krauler)')

    def __init__(self, config):
        self.config = config
        self.seen = set([])
        self.seen_lock = RLock()
        self.queue = Queue()

    @property
    def hidden(self):
        return self.config.get('hidden', False)

    @property
    def proxies(self):
        _proxies = {}
        if self.hidden:
            proxy = os.environ.get('KRAULER_HTTP_PROXY')
            if proxy is not None:
                _proxies['http'] = proxy
            proxy = os.environ.get('KRAULER_HTTPS_PROXY', proxy)
            if proxy is not None:
                _proxies['https'] = proxy
        _proxies.update(self.config.get('proxies', {}))
        return _proxies

    @property
    def session(self):
        if not hasattr(self, '_session'):
            session = requests.Session()
            session.proxies = self.proxies
            session.verify = False
            ua = self.config.get('user_agent', self.USER_AGENT)
            session.headers['User-Agent'] = ua
            on_session.send(self, session=session)
            self._session = session
        return self._session

    @property
    def seeds(self):
        if not hasattr(self, '_seeds'):
            seeds = [normalize_url(s) for s in get_list(self.config, 'seed')]
            self._seeds = [s for s in seeds if s is not None]
        return self._seeds

    @property
    def depth(self):
        return self.config.get('depth')

    @property
    def threads(self):
        return int(self.config.get('threads', 2))

    def crawl(self, url, path=None):
        if path is None:
            path = []
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

    def process_queue(self):
        while True:
            url, path = self.queue.get()
            log.info("Crawling %r (%d queued, %s seen)", url,
                     self.queue.qsize(), len(self.seen))
            try:
                page = Page(self, url, path)
                page.process()
            except Exception as exc:
                log.exception(exc)
            finally:
                self.queue.task_done()

    def should_retain(self, page):
        rules = self.config.get('retain', {})
        if not self.apply_rules(page.normalized_url, rules):
            return False

        if not self.apply_type_rules(page.normalized_url, rules):
            return False
        return True

    def should_crawl(self, url):
        if self.is_seen(url):
            return False
        if not self.apply_rules(url, self.config.get('crawl', {})):
            return False
        return True

    def apply_rules(self, url, rules):
        # apply domain filters
        for domain in get_list(rules, 'domains_deny'):
            if match_domain(domain, url):
                return False

        matching_domain = False
        for domain in get_list(rules, 'domains') + self.seeds:
            matching_domain = matching_domain or match_domain(domain, url)

        if not matching_domain:
            return False

        # apply regex filters
        for regex in get_list(rules, 'pattern_deny'):
            if re.compile(regex).match(url):
                return False

        matching_regex = False
        allow_regexes = get_list(rules, 'pattern')
        if len(allow_regexes):
            for regex in allow_regexes:
                matching_regex = matching_regex or re.compile(regex).match(url)

            if not matching_regex:
                return False

        return True

    def apply_type_rules(self, url, rules):
        guessed_type = url_type(url)

        deny_types = get_list(rules, 'types_deny')
        if guessed_type in normalize_types(deny_types):
            return False

        allow_types = normalize_types(get_list(rules, 'types'))
        if not len(allow_types):
            allow_types = normalize_types(['web'])

        return guessed_type in allow_types

    def run(self):
        on_init.send(self)
        for url in self.seeds:
            self.crawl(url)

        for i in range(self.threads):
            t = Thread(target=self.process_queue)
            t.daemon = True
            t.start()

        on_wait.send(self)
        self.queue.join()

    def emit(self, page):
        log.warning("Emitted: %r, no action defined to store!")
