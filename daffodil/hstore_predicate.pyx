from collections import UserString
from .parser cimport Token, BaseDaffodilDelegate


RE_CASE = "CASE WHEN ({0}->'{1}' ~ E'"
RE_THEN = "') THEN "
RE_ELSE = "ELSE -2147483648 END"


class ExpressionStr(UserString):
    """
    Subclass of str() that allows annotations based on which key and
    test are being used.
    """
    daff_key = ''
    daff_test = ''
    daff_val = ''


def forces_existence_optimizer(children):
    if len(children) <= 1:
        return False

    return all(
        isinstance(expr, ExpressionStr) and expr.daff_test == "?=" and expr.daff_val == True
        for expr in children
    )


def breaks_existence_optimizer(children):
    def _breaks_existence_optimizer(expr):
        if not isinstance(expr, ExpressionStr):
            return True

        return (
            expr.daff_test in {"!=", "!in", "?="} or
            (expr.daff_test == "=" and isinstance(expr.daff_val, str))
        )

    return any(
        _breaks_existence_optimizer(child_exp) for child_exp in children
    )


def should_optimize_existence(children):
    if forces_existence_optimizer(children):
        return True

    if breaks_existence_optimizer(children):
        return False

    return True


def breaks_equality_optimizer(children):
    if any(not isinstance(child_exp, ExpressionStr) for child_exp in children):
        return True

    return len([
        True for child_exp in children
        if child_exp.daff_test == "=" and isinstance(child_exp.daff_val, str)
    ]) < 2


def escape_string_sql(s):
    return "'{}'".format(s)

def make_sql_array(*strings):
    return "ARRAY[{}]".format(
        ",".join(escape_string_sql(s) for s in strings)
    )

cdef class HStoreQueryDelegate(BaseDaffodilDelegate):
    cdef public str field

    def __cinit__(self, hstore_field_name):
        self.field = hstore_field_name

    def mk_any(self, children):
        if not children or not any(children):
            return "false"

        if isinstance(children, list):
            children = [c for c in children if c]

        sql_expr = " OR ".join(f"({child_exp})" for child_exp in children)

        if should_optimize_existence(children):
            return self.optimize_existence(children, sql_expr, "?|", "OR")
        return sql_expr

    def optimize_existence(self, children, sql_expr, hstore_oper, logical_oper):
        keys = {child_exp.daff_key for child_exp in children}
        if len(keys) <= 1:
            return sql_expr

        keys = make_sql_array(*keys)
        optimization_expr = f"{self.field} {hstore_oper} {keys}"

        sql_expr = f" {logical_oper} ".join(
            f"({child_exp})"
            for child_exp in children if child_exp.daff_test != "?="
        )
        if sql_expr:
            return f"{optimization_expr} AND ({sql_expr})"
        else:
            return optimization_expr

    def optimize_equality_and(self, children, sql_expr):
        to_optimize = [child_exp for child_exp in children if child_exp.daff_test == "="]
        if len({child_exp.daff_key for child_exp in to_optimize}) <= 1:
            return sql_expr

        keys_and_values = ", ".join(
            f'"{child_exp.daff_key}"=>"{child_exp.daff_val}"'
            for child_exp in to_optimize
        )
        optimization_expr = f"{self.field} @> '{keys_and_values}'"

        sql_expr = f" AND ".join(
            f"({child_exp})"
            for child_exp in children if child_exp.daff_test != "="
        )
        if sql_expr:
            return f"{optimization_expr} AND ({sql_expr})"
        else:
            return optimization_expr

    def mk_all(self, children):
        if not children or not any(children):
            return "true"

        if isinstance(children, list):
            children = [c for c in children if c]

        sql_expr = " AND ".join(f"({child_exp})" for child_exp in children if child_exp)

        if not breaks_existence_optimizer(children):
            return self.optimize_existence(children, sql_expr, "?&", "AND")

        if not breaks_equality_optimizer(children):
            return self.optimize_equality_and(children, sql_expr)

        return sql_expr

    def mk_not_any(self, children):
        return " NOT ({0})".format(self.mk_any(children))

    def mk_not_all(self, children):
        return " NOT ({0})".format(self.mk_all(children))

    def mk_comment(self, comment, is_inline):
        return ""

    def mk_test(self, daff_test_str):
        test_str = daff_test_str

        if test_str == "?=":
            test_fn = lambda k, v, t: "{0}?{1}".format(k, v)
            test_fn.is_datapoint_test = True
        else:
            test_fn = lambda k, v, t: "{0} {1} {2}".format(k, test_str, v)
            if test_str == "!=":
                test_fn.is_NE_test = True
            elif test_str == "=":
                test_fn = lambda k, v, t: "({0} {1}))".format(k, v) if t == str else "{0} {1} {2}".format(k, test_str, v)
                test_fn.is_EQ_test = True
            elif test_str == "!in":
                test_fn.is_NOT_IN_test = True
                test_str = "NOT IN"
            elif test_str == "in":
                test_fn.is_IN_test = True

        test_fn.test_str = daff_test_str
        return test_fn

    cdef mk_cmp(self, Token key, Token test, Token val):
        return self._mk_cmp(
            key.content,
            val,
            self.mk_test(test.content)
        )

    def _mk_cmp(self, key, val, test):
        val = val.content
        daff_key = key
        daff_test = test.test_str
        daff_val = val

        if getattr(test, "is_datapoint_test", False):
            # here we cover:
            # [NOT] hstore_col ? '1ukmoviestudios - Disney'
            negate = "NOT " if val == False else ""
            val = "'{0}'".format(key)
            key = "{0}{1}".format(negate, self.field)
            _type = None
        else:
            is_eq_test = getattr(test, "is_EQ_test", False)
            _type, cast, val, type_check = self.cond_cast(val)
            test_ignores_missing_data = (
                daff_test in {"=", "in", "<", "<=", ">", ">="}
            )

            if getattr(test, "is_NE_test", False) or getattr(test, "is_NOT_IN_test", False):
                # here we cover:
                # NOT (hstore_col?'wrong attribute') OR (hstore_col->'wrong attribute')::integer != 2
                key_format = "NOT ({0}?'{1}') OR %s {3} ({0}->'{1}'){2}"
                # if its cast - exclude those not matching type
                key_format = key_format % (" NOT " + type_check[0] + " OR " if cast else "")

            elif is_eq_test and _type == str:
                # here we convert '=' to '@>'
                # instead of:
                #   (hs_data->'univisionlanguage1') = 'both'
                # we do:
                #   hs_data @> hstore('univisionlanguage1', 'both')
                key_format = "{0} @> hstore('{1}',"

            elif test_ignores_missing_data:
                # here we convert '=' to '? AND =':
                # hs_answers?'industries - luxury' AND hs_answers->'industries - luxury' = 'yes'
                key_format = "({0}?'{1}') AND {3} ({0}->'{1}'){2}"

            else:
                key_format = "{3} ({0}->'{1}'){2} "

            key = key_format.format(self.field, key, cast, "".join(type_check)).format(self.field, key)

        expr = ExpressionStr(test(key, val, _type))
        expr.daff_key = daff_key
        expr.daff_test = daff_test
        expr.daff_val = daff_val

        return expr

    def cond_cast(self, val):
        def escape_single_quote(val):
            if isinstance(val, str):
                return val.replace("'", "''")
            return val

        def format_list(lst):
            delimiter = "'" if isinstance(lst[0], str) else ""
            formatted_list = ",".join(
                ["{1}{0}{1}".format(escape_single_quote(elem), delimiter) for elem in lst]
            )
            return "({0})".format(formatted_list)

        def get_cast_attr(val, attr=None):
            for m in CAST_AND_TYPE_MAP:
                if isinstance(val, m["type"]):

                    if attr:
                        return m[attr](val)

                    return [m["type"]] + [m[a](val) for a in ["cast", "value", "type_check"]]

        NUMERIC_TYPE_CHECK = [
                "({0}->'{1}') ~ E'^(?=.+)(?:[0-9]\\\d*|0)?(?:\\\.\\\d+)?$'",
                " AND "
        ]
        CAST_AND_TYPE_MAP = [
            {
                "type": int,
                "cast": lambda v: "::numeric",
                "value": lambda v: str(v),
                "type_check" : lambda v: NUMERIC_TYPE_CHECK,
            },
            {
                "type": float,
                "cast": lambda v: "::numeric",
                "value": lambda v: str(v),
                "type_check": lambda v: NUMERIC_TYPE_CHECK,
            },
            {
                "type": str,
                "cast": lambda v: "",
                "value": lambda v: "'{}'".format(escape_single_quote(v)),
                "type_check": lambda v: ["", ""],
            },
            {
                "type": list,
                "cast": lambda v: get_cast_attr(v[0], "cast"),
                "value": lambda v: format_list(v),
                "type_check": lambda v: get_cast_attr(v[0], "type_check"),
            },
        ]

        return get_cast_attr(val)


    def call(self, predicate, queryset):
        return queryset.extra(where=[predicate]) if predicate else queryset
