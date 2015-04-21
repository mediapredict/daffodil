
RE_CASE = "CASE WHEN ({0}->'{1}' ~ E'"
RE_THEN = "') THEN "
RE_ELSE = "ELSE -2147483648 END"

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
            func = lambda k, v: "{0} {1} {2}".format(k, test_str, v)
            if test_str == "!=":
                func.is_NE_test = True
            elif test_str == "=":
                func.is_EQ_test = True
            return func

    def mk_cmp(self, key, val, test):
        if getattr(test, "is_datapoint_test", False):
            # here we cover:
            # [NOT] hstore_col ? '1ukmoviestudios - Disney'
            negate = "NOT " if val == False else ""
            val = "'{0}'".format(key)
            key = "{0}{1}".format(negate, self.field)
        else:
            cast, val, type_check = self.cond_cast(val)
            if getattr(test, "is_NE_test", False):
                # here we cover:
                # NOT (hstore_col?'wrong attribute') OR (hstore_col->'wrong attribute')::integer != 2
                key_format = "NOT ({0}?'{1}') OR %s {3} ({0}->'{1}'){2}"
                # if its cast - exclude those not matching type
                key_format = key_format % (" NOT " + type_check[0] + " OR " if cast else "")

            elif getattr(test, "is_EQ_test", False):
                # here we convert '=' to '? AND =':
                # hs_answers?'industries - luxury' AND hs_answers->'industries - luxury' = 'yes'
                key_format = "({0}?'{1}') AND {3} ({0}->'{1}'){2}"

            else:
                key_format = "{3} ({0}->'{1}'){2} "

            key = key_format.format(self.field, key, cast, type_check[0] + type_check[1]).format(self.field, key)
        return test( key, val )

    def cond_cast(self, v):
        if isinstance(v, int):
            # making sure attribute really holds an integer value
            # return "::integer", unicode(v), ["CASE WHEN ({0}->'{1' ~ E'^\\\d+$') THEN ", "ELSE -2147483648 END"]
            return "::integer", unicode(v), ["({0}->'{1}') ~ E'^[-]?\\\d+$'", " AND "]
        elif isinstance(v, float):
            return "::numeric", unicode(v), ["({0}->'{1}') ~ E'^(?=.+)(?:[1-9]\\\d*|0)?(?:\\\.\\\d+)?$'", " AND "]
        else:
            return "", u"'{0}'".format(v), ["", ""]

    def call(self, predicate, queryset):
        return queryset.extra(where=[predicate]) if predicate else queryset
