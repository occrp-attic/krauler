import six
from urlparse import urlparse

from krauler.rules import Rule, RuleParsingException


class DomainRule(Rule):
    """Match all pages from a particular domain."""

    def clean_domain(self, domain):
        pr = urlparse(domain)
        domain = pr.hostname or pr.path
        domain = domain.strip('.').lower()
        return domain

    def configure(self):
        if not isinstance(self.value, six.string_types):
            raise RuleParsingException("Not a domain: %r", self.value)
        self.domain = self.clean_domain(self.value)
        self.sub_domain = '.%s' % self.domain

    def apply(self, page):
        hostname = self.clean_domain(page.url)
        if hostname == self.domain:
            return True
        if hostname.endswith(self.sub_domain):
            return True
        return False
