import re
import logging
import requests
from urlparse import urlparse
from Queue import Queue
from threading import RLock

from krauler.page import Page
from krauler.util import as_list, normalize_url, match_domain
from krauler.types import normalize_types, url_type

log = logging.getLogger(__name__)


class Krauler(object):

    USER_AGENT = 'krauler (https://github.com/pudo/krauler)'

    def __init__(self, config):
        self.config = config
        self.seen = set([])
        self.seen_lock = RLock()
        self.queue = Queue()

    def config_list(self, name):
        return as_list(self.config.get(name))

    @property
    def session(self):
        if not hasattr(self, '_session'):
            self._session = requests.Session()
            self._session.verify = False
            self._session.headers['User-Agent'] = self.USER_AGENT
        return self._session

    @property
    def seeds(self):
        if not hasattr(self, '_seeds'):
            seeds = [normalize_url(s) for s in self.config_list('seed')]
            self._seeds = [s for s in seeds if s is not None]
        return self._seeds

    @property
    def depth(self):
        return self.config.get('depth')

    @property
    def allow_domains(self):
        if not hasattr(self, '_allow_domains'):
            self._allow_domains = []
            domains = self.config_list('allow_domains') or self.seeds
            for domain in domains:
                pr = urlparse(domain)
                self._allow_domains.append(pr.hostname or pr.path)
        return self._allow_domains

    @property
    def deny_domains(self):
        if not hasattr(self, '_deny_domains'):
            self._deny_domains = []
            for domain in self.config_list('deny_domains'):
                pr = urlparse(domain)
                self._deny_domains.append(pr.hostname or pr.path)
        return self._deny_domains

    @property
    def allow_types(self):
        if not hasattr(self, '_allow_types'):
            types = self.config_list('allow_types')
            if not len(types):
                types = ['web']
            self._allow_types = normalize_types(types)
        return self._allow_types

    @property
    def deny_types(self):
        if not hasattr(self, '_deny_types'):
            self._deny_types = normalize_types(self.config_list('deny_types'))
        return self._deny_types

    @property
    def allow(self):
        if not hasattr(self, '_allow'):
            self._allow = []
            for regex in self.config_list('allow'):
                self._allow.append(re.compile(regex))
        return self._allow

    @property
    def deny(self):
        if not hasattr(self, '_deny'):
            self._deny = []
            for regex in self.config_list('deny'):
                self._deny.append(re.compile(regex))
        return self._deny

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
            page = Page(self, url, path)
            page.process()
        except Exception as exc:
            log.exception(exc)
        finally:
            self.queue.task_done()

    def should_retain(self, page):
        if not self.should_process(page.normalized_url):
            return False

        if page.mime_type:
            if page.mime_type in self.deny_types:
                return False

            if self.allow_types and page.mime_type not in self.allow_types:
                return False

        return True

    def should_crawl(self, url):
        if self.is_seen(url):
            return False
        if not self.should_process(url):
            return False
        return True

    def check_domain(self, url):
        for domain in self.deny_domains:
            if match_domain(domain, url):
                return False

        matching_domain = False
        for domain in self.allow_domains:
            matching_domain = matching_domain or match_domain(domain, url)

        if len(self.allow_domains) and not matching_domain:
            return False
        return True

    def check_regex(self, url):
        for regex in self.deny:
            if regex.match(url):
                return False

        matching_regex = False
        for regex in self.allow:
            matching_regex = matching_regex or regex.match(url)

        if len(self.allow) and not matching_regex:
            return False
        return True

    def check_types(self, url):
        guessed_type = url_type(url)
        if guessed_type in [None, 'text/html']:
            return True

        if guessed_type in self.deny_types:
            return False

        if not len(self.allow_types):
            return True

        if guessed_type not in self.allow_types:
            return False

        return True

    def should_process(self, url):
        if not self.check_domain(url):
            return False

        if not self.check_regex(url):
            return False

        if not self.check_types(url):
            return False

        return True

    def run(self):
        for url in self.seeds:
            self.crawl(url, [])

        while not self.queue.empty():
            self.next_page()

    def emit(self, page):
        log.warning("Emitted: %r, no action defined to store!")
