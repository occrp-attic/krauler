import re
import logging
import requests
from Queue import Queue
from threading import RLock, Thread

from krauler.config import Config
from krauler.page import Page
from krauler.util import get_list
from krauler.util import match_domain
from krauler.types import normalize_types
from krauler.signals import on_init, on_session, on_wait

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
        rules = self.config.data.get('retain', {})

        if not self.apply_domain_rules(page.normalized_url, rules):
            log.info("Will not retain (domain mismatch): %r",
                     page.normalized_url)
            return False

        if not self.apply_pattern_rules(page.normalized_url, rules):
            log.info("Will not retain (pattern mismatch): %r",
                     page.normalized_url)
            return False

        if not self.apply_type_rules(page.mime_type, rules):
            log.info("Will not retain (type mismatch): %r",
                     page.normalized_url)
            return False

        log.info("Retaining: %r", page.normalized_url)
        return True

    def should_crawl(self, url):
        if self.is_seen(url):
            return False

        if not self.apply_domain_rules(url, self.config.data.get('crawl', {})):
            return False

        if not self.apply_pattern_rules(url, self.config.data.get('crawl', {})):
            return False
        return True

    def apply_domain_rules(self, url, rules):
        # apply domain filters
        for domain in get_list(rules, 'domains_deny'):
            if match_domain(domain, url):
                return False

        matching_domain = False
        allow_domains = get_list(rules, 'domains') + self.config.seeds
        if len(allow_domains):
            for domain in allow_domains:
                matching_domain = matching_domain or match_domain(domain, url)

            if not matching_domain:
                return False
        return True

    def apply_pattern_rules(self, url, rules):
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

    def apply_type_rules(self, guessed_type, rules):
        deny_types = get_list(rules, 'types_deny')
        if guessed_type in normalize_types(deny_types):
            return False

        allow_types = normalize_types(get_list(rules, 'types'))
        if not len(allow_types):
            allow_types = normalize_types(['web'])

        if 'any' in allow_types:
            return True
        return guessed_type in allow_types

    def run(self):
        on_init.send(self)
        for url in self.config.seeds:
            self.crawl(url)

        for i in range(self.config.threads):
            t = Thread(target=self.process_queue)
            t.daemon = True
            t.start()

        on_wait.send(self)
        self.queue.join()

    def emit(self, page):
        log.warning("Emitted: %r, no action defined to store!")
