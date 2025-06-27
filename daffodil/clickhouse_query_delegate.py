from .parser import BaseDaffodilDelegate, TimeStamp


class ClickHouseQueryDelegate(BaseDaffodilDelegate):
    """Render ClickHouse SQL for Daffodil expressions."""

    def __init__(self, map_field_name: str = "hs_data") -> None:
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

    def mk_comment(self, comment, is_inline: bool):
        return ""

    def mk_test(self, test_str: str):
        return test_str

    def mk_cmp(self, key, test, val):
        return self._mk_cmp(key.content, val, test.content)

    def _mk_cmp(self, key: str, val, test: str):
        val = val.content
        field_expr = f"{self.field}.{key}"

        if test == "?=":
            return f"isNotNull({field_expr})" if val else f"isNull({field_expr})"

        value = self.format_value(val)

        if test == "in":
            return f"{field_expr} IN {value}"
        elif test == "!in":
            return f"{field_expr} NOT IN {value}"
        else:
            return f"{field_expr} {test} {value}"

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

