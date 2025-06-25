from .parser cimport Token, BaseDaffodilDelegate

cdef class ElasticSearchPredicate(BaseDaffodilDelegate):
    cdef public str prefix

    def __cinit__(self, prefix="hs_data"):
        self.prefix = prefix

    def _field(self, key):
        if self.prefix:
            return f"{self.prefix}.{key}"
        return key

    def mk_any(self, children):
        children = [c for c in children if c]
        flat = []
        for child in children:
            if (
                isinstance(child, dict)
                and list(child.keys()) == ["bool"]
                and isinstance(child["bool"], dict)
                and list(child["bool"].keys()) == ["should"]
            ):
                subs = child["bool"]["should"]
                if any(sub in flat for sub in subs):
                    for sub in subs:
                        if sub not in flat:
                            flat.append(sub)
                else:
                    if child not in flat:
                        flat.append(child)
            else:
                if child not in flat:
                    flat.append(child)
        if not flat:
            return {"match_none": {}}
        return {"bool": {"should": flat}}

    def mk_all(self, children):
        children = [c for c in children if c]
        if not children:
            return {"match_all": {}}
        return {"bool": {"must": children}}

    def mk_not_any(self, children):
        children = [c for c in children if c]
        if not children:
            return {"match_all": {}}
        return {"bool": {"must_not": [self.mk_any(children)]}}

    def mk_not_all(self, children):
        children = [c for c in children if c]
        if not children:
            return {"match_none": {}}
        return {"bool": {"must_not": [self.mk_all(children)]}}

    def mk_comment(self, comment, is_inline):
        return None

    cdef mk_cmp(self, Token key, Token test, Token val):
        return self._mk_cmp(key.content, val, test.content)

    def _mk_cmp(self, key, val, test):
        field = self._field(key)
        value = val.content

        if test == "?=":
            if value:
                return {"exists": {"field": field}}
            else:
                return {"bool": {"must_not": {"exists": {"field": field}}}}

        if test == "=":
            return {"term": {field: value}}
        if test == "!=":
            return {"bool": {"should": [
                {"bool": {"must_not": {"exists": {"field": field}}}},
                {"bool": {"must_not": {"term": {field: value}}}}
            ]}}
        if test == "in":
            return {"terms": {field: value}}
        if test == "!in":
            return {"bool": {"should": [
                {"bool": {"must_not": {"exists": {"field": field}}}},
                {"bool": {"must_not": {"terms": {field: value}}}}
            ]}}
        if test in {"<", "<=", ">", ">="}:
            op_map = {"<": "lt", "<=": "lte", ">": "gt", ">=": "gte"}
            return {"range": {field: {op_map[test]: value}}}

        raise ValueError(f'"{test}" is not a valid operator')

    def call(self, predicate, *args):
        return {"query": predicate}
