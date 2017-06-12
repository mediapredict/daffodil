from builtins import object


class BaseDaffodilDelegate(object):

    def mk_any(self, children):
        raise NotImplementedError()

    def mk_all(self, children):
        raise NotImplementedError()

    def mk_not_any(self, children):
        raise NotImplementedError()

    def mk_not_all(self, children):
        raise NotImplementedError()

    def mk_test(self, test_str):
        raise NotImplementedError()

    def mk_comment(self, comment, is_inline):
        raise NotImplementedError()

    def mk_cmp(self, key, val, test):
        raise NotImplementedError()

    def call(self, predicate, iterable):
        raise NotImplementedError()

