import urlnorm
from urlparse import urldefrag


def as_list(attr):
    if attr is None:
        return []
    if isinstance(attr, (list, set, tuple)):
        return attr
    return [attr]


def normalize_url(url):
    url = urlnorm.norm(url)
    url, _ = urldefrag(url)
    url = url.rstrip('/')
    return url
