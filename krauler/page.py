import os
import cgi
import logging
from urlparse import urljoin, urlparse
from lxml import html
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from krauler.util import normalize_url
from krauler.ua import get_ua
from krauler.signals import on_parse

log = logging.getLogger(__name__)


class Page(object):

    def __init__(self, state, url, path):
        self.state = state
        self.url = url
        self.path = path

    @property
    def response(self):
        if not hasattr(self, '_response'):
            headers = {}
            if self.state.hidden:
                headers['User-Agent'] = get_ua()
            self._response = self.state.session.get(self.url, stream=True,
                                                    headers=headers)
        return self._response

    @property
    def content(self):
        if not hasattr(self, '_content'):
            data = StringIO()
            try:
                for chunk in self.response.iter_content(chunk_size=1024):
                    if chunk:
                        data.write(chunk)
                self._content = data
            finally:
                self.response.close()
        return self._content.getvalue()

    @property
    def doc(self):
        if not hasattr(self, '_doc'):
            self._doc = html.fromstring(self.content)
        return self._doc

    @property
    def normalized_url(self):
        url = self.url
        if hasattr(self, '_response'):
            url = self._response.url
            url = normalize_url(url)
        return url

    @property
    def next_path(self):
        return self.path + [self.normalized_url]

    @property
    def terminate_path(self):
        if self.state.depth is None or self.state.depth < 0:
            return False
        return len(self.path) >= self.state.depth

    @property
    def mime_type(self):
        content_type = self.response.headers.get('content-type')
        if content_type is None:
            return 'text/html'
        mime_type, _ = cgi.parse_header(content_type)
        return mime_type

    @property
    def file_name(self):
        disp = self.response.headers.get('content-disposition')
        if disp is not None:
            _, attrs = cgi.parse_header(disp)
            if 'filename' in attrs:
                return attrs.get('filename')

        parsed = urlparse(self.normalized_url)
        file_name = os.path.basename(parsed.path)
        if file_name is not None and len(file_name):
            return file_name

    @property
    def is_html(self):
        if 'html' in self.mime_type:
            return True
        return False

    def parse(self):
        tags = [('a', 'href'), ('img', 'src'), ('link', 'href'),
                ('iframe', 'src')]

        # TODO: check rel="canonical"
        urls = set([])
        for tag_name, attr_name in tags:
            for tag in self.doc.findall('.//%s' % tag_name):
                attr = tag.get(attr_name)
                if attr is None:
                    continue
                url = normalize_url(urljoin(self.normalized_url, attr))
                if url is not None:
                    urls.add(url)

        on_parse.send(self, urls=urls)

        for url in urls:
            self.state.crawl(url, path=self.next_path)

    def process(self):
        if not self.state.should_crawl(self.normalized_url):
            log.info("Skipping: %r", self.normalized_url)
            return

        self.state.mark_seen(self.normalized_url)
        if self.response.status_code > 300:
            log.warning("Failure: %r, status: %r", self.normalized_url,
                        self.response.status_code)
            return
        self.state.mark_seen(self.normalized_url)

        if self.state.should_retain(self):
            self.retain()

        if self.is_html and not self.terminate_path:
            self.parse()

    def retain(self):
        self.state.emit(self)
