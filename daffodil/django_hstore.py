class HStoreQueryDelegate(object):
    
    def __init__(self, hstore_field_name):
        self.field = hstore_field_name

    def mk_any(self, children):
        return " OR ".join( "(" + child_exp + ")" for child_exp in children)

    def mk_all(self, children):
        return " AND ".join( "(" + child_exp + ")" for child_exp in children if child_exp )

    def mk_test(self, test_str):
        return lambda k, v: "{0}{1}{2}".format(k, test_str, v)

    def mk_cmp(self, key, val, test):
        def cond_cast(v):
            # there should not be non-strings but...
            v = str(v) if not isinstance(v, str) else v
            if v.isdigit():
                return "::integer"
            else:
                if '.' in v:
                    # could be float
                    try:
                        f = float(v)
                        return "::real"
                    except ValueError:
                        pass
            return ""

        key = "({0}->'{1}'){2}".format(self.field, key, cond_cast(val))
        return test( key, val )

    def call(self, predicate, queryset):
        return queryset.extra(where=[predicate]) if predicate else queryset
