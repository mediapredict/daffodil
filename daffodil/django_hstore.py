

class HStoreQueryDelegate(object):
    
    def __init__(self, hstore_field_name):
        self.field = hstore_field_name

    def mk_any(self, children):
        from django.db.models import Q
        q = Q()
        for child_q in children:
            q |= child_q
        return q

    def mk_all(self, children):
        from django.db.models import Q
        q = Q()
        for child_q in children:
            q &= child_q
        return q

    def mk_test(self, test_str):
        from django.db.models import Q
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
        return test(key, self.to_n_dig_int(val) )

    def to_n_dig_int(self, num, digits=6):
        num_str = "%0" + str(digits) + "d"
        return num_str % int(num) if str(num).isdigit() else num

    def call(self, predicate, queryset):
        return queryset.filter(predicate)