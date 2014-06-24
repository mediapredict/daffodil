

class HStoreQueryDelegate(object):

    def __init__(self, hstore_field_name):
        self.field = hstore_field_name

    def mk_any(self, children):
        if children == []:
            return "false"
        else:
            return " OR ".join( "(" + child_exp + ")" for child_exp in children)

    def mk_all(self, children):
        if children == ['']:
            return "true"
        else:
            return " AND ".join( "(" + child_exp + ")" for child_exp in children if child_exp)

    def mk_test(self, test_str):
        if test_str == "?=":
            existance = lambda k, v: "{0}?{1}".format(k, v)
            existance.is_datapoint_test = True
            return existance
        else:
            func = lambda k, v: "{0}{1}{2}".format(k, test_str, v)
            if test_str == "!=":
                func.is_NE_test = True
            return func

    def mk_cmp(self, key, val, test):
        if getattr(test, "is_datapoint_test", False):
            # here we cover:
            # [NOT] hstore_col ? '1ukmoviestudios - Disney'
            negate = "NOT " if val == False else ""
            val = "'{0}'".format(key)
            key = "{0}{1}".format(negate, self.field)
        else:
            cast, val = self.cond_cast(val)
            if getattr(test, "is_NE_test", False):
                # here we cover:
                # NOT (hstore_col?'wrong attribute') OR (hstore_col->'wrong attribute')::integer != 2
                key_format = "NOT ({0}?'{1}') OR ({0}->'{1}'){2}"
            else:
                key_format = "({0}->'{1}'){2}"

            key = key_format.format(self.field, key, cast)
        return test( key, val )

    def cond_cast(self, v):
        if not isinstance(v, basestring):
            v = unicode(v)

        if v.isdigit():
            return "::integer", v
        elif '.' in v:
            # could be float
            try:
                f = float(v)
                return "::real", v
            except ValueError:
                pass
        return "", u"'{0}'".format(v)

    def call(self, predicate, queryset):
        return queryset.extra(where=[predicate]) if predicate else queryset
