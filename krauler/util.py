import urlnorm
from urlparse import urldefrag, urlparse


def as_list(attr):
    if attr is None:
        return []
    if isinstance(attr, (list, set, tuple)):
        return attr
    return [attr]


def normalize_url(url):
    # TODO: learn from https://github.com/hypothesis/h/blob/master/h/api/uri.py
    try:
        url = urlnorm.norm(url)
        url, _ = urldefrag(url)
        url = url.rstrip('/')
        return url
    except:
        return None


def match_domain(domain, url):
    domain = domain.strip('.').lower()
    hostname = urlparse(url).hostname.lower()
    if hostname == domain:
        return True
    sub_domain = '.%s' % domain
    if hostname.endswith(sub_domain):
        return True
    return False
