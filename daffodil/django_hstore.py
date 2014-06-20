from django.db import Q


class HStoreQueryDelegate(object):
    def __init__(self, hstore_field_name):
        self.field = hstore_field_name

    def mk_any(self, children):
        q = Q()
        for child_q in children:
            q |= child_q
        return q

    def mk_all(self, children):
        q = Q()
        for child_q in children:
            q &= child_q
        return q

    def mk_test(self, test_str):
        def mk_Q(cmp, hstore_val, negate=False):
            k = "{0}__{1}".format(self.field, cmp)
            q = Q(**{k: hstore_val})
            return q

        def existance(k, v):
            q = mk_Q("contains", [k])
            if not v:
                q = ~q
            return q

        ops = {
          '=':  lambda k, v: mk_Q("contains", {k: v}),
          '!=': lambda k, v: ~mk_Q("contains", {k: v}),
          '<':  lambda k, v: mk_Q("lt", {k: v}),
          '<=': lambda k, v: mk_Q("lte", {k: v}),
          '>':  lambda k, v: mk_Q("gt", {k: v}),
          '>=': lambda k, v: mk_Q("gte", {k: v}),
          "?=": lambda k, v: existance,
        }

        return ops[test_str]

    def mk_cmp(self, key, val, test):
        return test(key, val)