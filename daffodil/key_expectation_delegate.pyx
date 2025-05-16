from .parser cimport Token, BaseDaffodilDelegate


cdef class KeyExpectationDelegate(BaseDaffodilDelegate):
    """
    Determines which keys in a daffodil are required in data dictionaries 
    in order to match and which keys have to be omitted to match. 

    Useful for making inferences like detecting when a key would never be set
    but should (or would be but shouldn't).
    """
    def _mk_group(self, children, negate):
        expect_present = set()
        expect_omitted = set()

        for child in children:
            if negate:
                child = child[::-1]
            expect_present |= child[0]
            expect_omitted |= child[1]

        # if we expect a key to be present we can't also expect it not to be
        expect_omitted -= expect_present

        return expect_present, expect_omitted

    def mk_any(self, children):
        return self._mk_group(children, False)

    def mk_all(self, children):
        return self._mk_group(children, False)

    def mk_not_any(self, children):
        return self._mk_group(children, True)

    def mk_not_all(self, children):
        return self._mk_group(children, True)

    def mk_test(self, test_str):
        return test_str

    def mk_comment(self, comment, is_inline):
        return set(), set()

    cdef mk_cmp(self, Token key, Token test, Token val):
        return self._mk_cmp(
            key.content,
            val,
            self.mk_test(test.content)
        )

    def _mk_cmp(self, key, val, test):
        val = val.content
        if test == "?=" and val is False:
            return set(), {key}
        if test in ("!=", "!in"):
            return set(), set()
        return {key}, set()
