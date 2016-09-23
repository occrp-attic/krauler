import re
import six
import urlnorm
from urlparse import urldefrag

from krauler.rules import Rule, RuleParsingException


def normalize_url(url):
    # TODO: learn from https://github.com/hypothesis/h/blob/master/h/api/uri.py
    try:
        url = urlnorm.norm(url)
        url, _ = urldefrag(url)
        url = re.sub('[\n\r]', '', url)
        url = url.rstrip('/')
        return url
    except:
        return None


class UrlPatternRule(Rule):

    def configure(self):
        if not isinstance(self.value, six.string_types):
            raise RuleParsingException("Not a regex: %r", self.value)
        self.pattern = re.compile(self.value, re.I | re.U)

    def apply(self, page):
        if self.pattern.match(page.url):
            return True
        return False
