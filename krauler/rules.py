import logging
from pkg_resources import iter_entry_points

log = logging.getLogger(__name__)


class RuleParsingException(Exception):
    pass


class Rule(object):
    RULES = {}

    def __init__(self, value):
        self.value = value

    def configure(self):
        pass

    def apply(self, page):
        raise NotImplemented()

    def to_dict(self):
        return self.value

    def get_child(self, spec):
        return self.get_rule(spec)

    @classmethod
    def get_rules(cls):
        if not len(cls.RULES):
            for ep in iter_entry_points('krauler.rules'):
                rule_cls = ep.load()
                rule_cls.name = ep.name
                cls.RULES[ep.name] = rule_cls
            log.info("Loaded rules: %r", cls.RULES.keys())
        return cls.RULES

    @classmethod
    def get_rule(cls, spec):
        if not isinstance(spec, dict):
            raise RuleParsingException('Not a valid rule: %r' % spec)
        if len(spec) > 1:
            raise RuleParsingException('Ambiguous rules: %r' % spec)
        for rule_name, value in spec.items():
            rule_cls = cls.get_rules().get(rule_name)
            if rule_cls is None:
                raise RuleParsingException('Unknown rule: %s' % rule_name)
            rule = rule_cls(value)
            rule.configure()
            return rule
        raise RuleParsingException('Empty rule: %s' % spec)


class ListRule(Rule):
    """An abstract type of rules that contain a set of other rules."""

    def configure(self):
        if not isinstance(self.value, (list, set, tuple)):
            raise RuleParsingException("Not a list: %r", self.value)

    @property
    def children(self):
        for rule in self.value:
            yield self.get_child(rule)


class OrRule(ListRule):
    """Any nested rule must apply."""

    def apply(self, page):
        for rule in self.children:
            if rule.apply(page):
                return True
        return False


class AndRule(ListRule):
    """All nested rules must apply."""

    def apply(self, page):
        for rule in self.children:
            if not rule.apply(page):
                return False
        return True


class NotRule(Rule):
    """Invert a nested rule."""

    def configure(self):
        self.rule = self.get_child(self.value)

    def apply(self, page):
        return not self.rule.apply(page)


class MatchAllRule(Rule):
    """Just say yes."""

    def apply(self, page):
        return True
