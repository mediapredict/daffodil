class HStoreQueryDelegate(object):
    
    def __init__(self, hstore_field_name):
        self.field = hstore_field_name

    def mk_any(self, children):
        return " OR ".join( "(" + child_exp + ")" for child_exp in children)

    def mk_all(self, children):
        return " AND ".join( "(" + child_exp + ")" for child_exp in children if child_exp )

    def mk_test(self, test_str):

        if test_str == "?=":
            existance = lambda k, v: "{0}?{1}".format(k, v)
            existance.is_datapoint_test = True
            return existance
        else:
            return lambda k, v: "{0}{1}{2}".format(k, test_str, v)

    def mk_cmp(self, key, val, test):

        if getattr(test, "is_datapoint_test", False):
            # here we want:
            # [NOT] hstore_col ? '1ukmoviestudios - Disney'
            negate = "NOT " if val == False else ""
            val = "'{0}'".format(key)
            key = "{0}{1}".format(negate, self.field)
        else:
            cast, val = self.cond_cast(val)
            key = "({0}->'{1}'){2}".format(self.field, key, cast)
        return test( key, val )

    def cond_cast(self, v):
        # should be strings but...
        v = str(v) if not isinstance(v, str) else v
        if v.isdigit():
            return "::integer", v
        else:
            if '.' in v:
                # could be float
                try:
                    f = float(v)
                    return "::real", v
                except ValueError:
                    pass
        return "", "'{0}'".format(v)

    def call(self, predicate, queryset):
        return queryset.extra(where=[predicate]) if predicate else queryset
