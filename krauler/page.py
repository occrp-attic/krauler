import cgi
import logging
from urlparse import urljoin
from lxml import html

from krauler.util import normalize_url

log = logging.getLogger(__name__)


class KraulerPage(object):

    def __init__(self, state, url):
        self.state = state
        self.url = url

    @property
    def response(self):
        if not hasattr(self, '_response'):
            self._response = self.state.session.get(self.url)
        return self._response

    @property
    def doc(self):
        if not hasattr(self, '_doc'):
            self._doc = html.fromstring(self.response.content)
        return self._doc

    @property
    def normalized_url(self):
        url = self.url
        if hasattr(self, '_response'):
            url = self._response.url
        return normalize_url(url)

    @property
    def id(self):
        return self.normalized_url

    @property
    def is_html(self):
        content_type = self.response.headers.get('content-type')
        if content_type is None:
            return True
        mime_type, _ = cgi.parse_header(content_type)
        if 'html' in mime_type:
            return True
        return False

    def parse(self):
        tags = [('a', 'href'), ('img', 'src'), ('link', 'href'),
                ('iframe', 'src')]

        urls = set([])
        for tag_name, attr_name in tags:
            for tag in self.doc.findall('.//%s' % tag_name):
                attr = tag.get(attr_name)
                if attr is None:
                    continue
                urls.add(urljoin(self.normalized_url, attr))

        for url in urls:
            self.state.queue(url)

    def process(self):
        if not self.state.should_crawl(self.normalized_url):
            return

        self.state.seen.add(self.normalized_url)
        if self.response.status_code > 300:
            return
        self.state.seen.add(self.normalized_url)

        if self.state.should_retain(self):
            self.retain()
        if self.is_html:
            self.parse()

    def retain(self):
        self.state.emit(self)
