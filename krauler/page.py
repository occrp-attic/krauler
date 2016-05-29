import os
import cgi
import logging
import mimetypes
from urlparse import urljoin, urlparse
from lxml import html
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from krauler.url import normalize_url
from krauler.ua import get_ua
from krauler.signals import on_parse

log = logging.getLogger(__name__)


class Page(object):

    def __init__(self, state, url, path):
        self.state = state
        self.config = state.config
        self.raw_url = url
        self.path = path

    @property
    def response(self):
        if not hasattr(self, '_response'):
            headers = {}
            if self.config.hidden:
                headers['User-Agent'] = get_ua()
            self._response = self.state.session.get(self.url, stream=True,
                                                    headers=headers,
                                                    timeout=120)
        return self._response

    def _has_response(self):
        return hasattr(self, '_response')

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
    def url(self):
        url = self.raw_url
        if self._has_response():
            url = self._response.url
            url = normalize_url(url)
        return url

    @property
    def parsed(self):
        return urlparse(self.url)

    @property
    def next_path(self):
        return self.path + [self.url]

    @property
    def terminate_path(self):
        if self.config.depth is None or self.config.depth < 0:
            return False
        return len(self.path) >= self.config.depth

    @property
    def mime_type(self):
        if not self._has_response():
            url_type, url_class = mimetypes.guess_type(self.parsed.path)
            url_type = url_type or url_class
            if url_type is not None and url_type != 'application/octet-stream':
                return url_type.lower().strip('.')
        # fetch document implicitly
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

        parsed = urlparse(self.url)
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
                url = normalize_url(urljoin(self.url, attr))
                if url is not None:
                    urls.add(url)

        on_parse.send(self, urls=urls)

        for url in urls:
            self.state.crawl(url, path=self.next_path)

    def process(self):
        if self.state.is_seen(self.url):
            return
        self.state.mark_seen(self.url)
        if not self.config.crawl.apply(self):
            log.debug("Skipping: %r", self.url)
            return
        log.info("Crawling %r (%d queued, %s seen)", self.url,
                 self.state.queue.qsize(), len(self.state.seen))

        if self.response.status_code > 300:
            log.warning("Failure: %r, status: %r", self.url,
                        self.response.status_code)
            return
        self.state.mark_seen(self.url)

        if self.config.retain.apply(self):
            self.retain()

        if self.is_html and not self.terminate_path:
            self.parse()

    def retain(self):
        self.state.emit(self)
