import cgi
import logging
from urlparse import urljoin
from lxml import html

from krauler.util import normalize_url

log = logging.getLogger(__name__)


class KraulerPage(object):

    def __init__(self, state, url, path):
        self.state = state
        self.url = url
        self.path = path

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
            url = normalize_url(url)
        return url

    @property
    def id(self):
        return self.normalized_url

    @property
    def next_path(self):
        return self.path + [self.normalized_url]

    @property
    def mime_type(self):
        content_type = self.response.headers.get('content-type')
        if content_type is None:
            return 'text/html'
        mime_type, _ = cgi.parse_header(content_type)
        return mime_type

    @property
    def is_html(self):
        if 'html' in self.mime_type:
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
                url = normalize_url(urljoin(self.normalized_url, attr))
                if url is not None:
                    urls.add(url)

        for url in urls:
            self.state.crawl(url, self.next_path)

    def process(self):
        if not self.state.should_crawl(self.normalized_url):
            return

        self.state.mark_seen(self.normalized_url)
        if self.response.status_code > 300:
            return
        self.state.mark_seen(self.normalized_url)

        if self.state.should_retain(self):
            self.retain()
        if self.is_html:
            self.parse()

    def retain(self):
        self.state.emit(self)
