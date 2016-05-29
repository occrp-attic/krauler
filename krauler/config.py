import os
import logging

from krauler.util import normalize_url, get_list

log = logging.getLogger(__name__)


class Config(object):

    def __init__(self, data):
        self.data = data

    @property
    def user_agent(self):
        if self.data.get('user_agent'):
            return self.data.get('user_agent')
        return os.environ.get('KRAULER_UA', 'krauler/bot')

    @property
    def seeds(self):
        if not hasattr(self, '_seeds'):
            seeds = [normalize_url(s) for s in get_list(self.data, 'seed')]
            self._seeds = [s for s in seeds if s is not None]
        return self._seeds

    @property
    def depth(self):
        return self.data.get('depth')

    @property
    def threads(self):
        return int(self.data.get('threads', 2))

    @property
    def hidden(self):
        return self.data.get('hidden', False)

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
        _proxies.update(self.data.get('proxies', {}))
        if len(_proxies):
            log.debug('Using proxies: %r', _proxies)
        return _proxies
