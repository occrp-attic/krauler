import logging
import urlnorm
import requests
from urlparse import urldefrag, urlparse


def as_list(attr):
    if attr is None:
        return []
    if isinstance(attr, (list, set, tuple)):
        return attr
    return [attr]


def get_list(obj, value):
    return as_list(obj.get(value))


def normalize_url(url):
    # TODO: learn from https://github.com/hypothesis/h/blob/master/h/api/uri.py
    try:
        url = urlnorm.norm(url)
        url, _ = urldefrag(url)
        url = url.rstrip('/')
        return url
    except:
        return None


def clean_domain(domain):
    pr = urlparse(domain)
    domain = pr.hostname or pr.path
    domain = domain.strip('.').lower()
    return domain


def match_domain(domain, url):
    domain = clean_domain(domain)
    hostname = urlparse(url).hostname.lower()
    if hostname == domain:
        return True
    sub_domain = '.%s' % domain
    if hostname.endswith(sub_domain):
        return True
    return False


def configure_logging():
    requests.packages.urllib3.disable_warnings()
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('requests').setLevel(logging.WARNING)
    # logging.getLogger('dataset').setLevel(logging.WARNING)
