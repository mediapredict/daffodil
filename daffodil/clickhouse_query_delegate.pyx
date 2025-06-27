from .parser cimport Token, BaseDaffodilDelegate
from .parser import TimeStamp

cdef class ClickHouseQueryDelegate(BaseDaffodilDelegate):
    cdef public str field

    def __cinit__(self, str map_field_name):
        self.field = map_field_name

    def mk_any(self, children):
        children = [c for c in children if c]
        if not children:
            return "0"
        return " OR ".join(f"({child})" for child in children)

    def mk_all(self, children):
        children = [c for c in children if c]
        if not children:
            return "1"
        return " AND ".join(f"({child})" for child in children)

    def mk_not_any(self, children):
        return f"NOT ({self.mk_any(children)})"

    def mk_not_all(self, children):
        return f"NOT ({self.mk_all(children)})"

    def mk_comment(self, comment, bint is_inline):
        return ""

    def mk_test(self, test_str):
        return test_str

    cdef mk_cmp(self, Token key, Token test, Token val):
        return self._mk_cmp(key.content, val, test.content)

    def _mk_cmp(self, str key, object val, str test):
        val = val.content
        if test == "?=":
            if val:
                return f"has({self.field}, '{key}')"
            else:
                return f"NOT has({self.field}, '{key}')"

        value = self.format_value(val)
        map_expr = f"{self.field}['{key}']"
        if test == "in":
            return f"{map_expr} IN {value}"
        elif test == "!in":
            return f"{map_expr} NOT IN {value}"
        else:
            return f"{map_expr} {test} {value}"

    def format_value(self, val):
        if isinstance(val, list):
            formatted = ", ".join(self.format_value(v) for v in val)
            return f"({formatted})"
        elif isinstance(val, str):
            return "'{}'".format(val.replace("'", "''"))
        elif isinstance(val, TimeStamp):
            return str(val.content)
        elif isinstance(val, bool):
            return "1" if val else "0"
        else:
            return str(val)

    def call(self, predicate, *args):
        return predicate
