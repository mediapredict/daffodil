from .parser cimport Token, BaseDaffodilDelegate


# Sentinal to indicate a comment in the daffodil
COMMENT = object()


cdef class SimulationMatchingDelegate(BaseDaffodilDelegate):
    """
    For use in simulations like the QA subsystem in KF.

    The predicate takes a dict where keys are data_ids that are known to be set, and values
    are a list of possible values (or an empty list to indicate ANY key could be set).

    A value list with one item can be considered to be known to be that one value. This
    is functionally identical to string value.

    The predicate returns True if the daffodil is guaranteed to match given the possibility
    space, False if it's guaranteed not to, and None if it can't be determined.
    """
    def mk_not_any(self, children):
        wrapped = self.mk_any(children)

        def pred(poss):
            v = wrapped(poss)
            return v if v is None else not v

        return pred

    def mk_not_all(self, children):
        wrapped = self.mk_all(children)

        def pred(poss):
            v = wrapped(poss)
            return v if v is None else not v

        return pred

    def mk_any(self, children):
        def pred(poss):
            child_vals = [child(poss) for child in children if child is not COMMENT]
            if True in child_vals:
                return True
            if all(v is False for v in child_vals):
                return False
            return None
        return pred

    def mk_comment(self, comment, is_inline):
        return COMMENT

    def mk_test(self, test_str):
        return test_str

    def mk_all(self, children):
        def pred(poss):
            child_vals = [child(poss) for child in children if child is not COMMENT]
            if False in child_vals:
                return False
            if all(child_vals):
                return True
            return None
        return pred

    cdef mk_cmp(self, Token key, Token test, Token val):
        return self._mk_cmp(
            key.content,
            val.content,
            self.mk_test(test.content)
        )

    def _mk_cmp(self, str key, object val, object test):
        def pred(poss):
            if test == "?=":
                if val:
                    return key in poss
                else:
                    return key not in poss

            # First deal with the case where there is no value
            if key not in poss:
                if test in {"!=", "!in"}:
                    # These operations automatically match if there is no value
                    return True
                # Most operators can't match if there is no value
                return False

            poss_vals = poss.get(key, None)
            if isinstance(poss_vals, str):
                poss_vals = [poss_vals]

            # For open ends we can't make any guarantees beyond the ones above
            if not len(poss_vals):
                return None

            # 'poss_vals types' and 'val type' should not necessarily match.
            # do the conversion without type checking (faster?)
            val_type = type(val[0]) if isinstance(val, list) else type(val)
            if isinstance(poss_vals, list):
                poss_vals = self._conv_l_elems(poss_vals, val_type)
            else:
                poss_vals = val_type(poss_vals)

            if test == "=":
                if len(poss_vals) == 1 and poss_vals[0] == val:
                    return True
                if val not in poss_vals:
                    return False
                return None

            if test == "!=":
                if val not in poss_vals:
                    return True
                if len(poss_vals) == 1 and poss_vals[0] == val:
                    return False
                return None

            if test in {"<", "<=", ">", ">="}:

                if test == "<":
                    matches = [poss_val < val for poss_val in poss_vals]
                elif test == "<=":
                    matches = [poss_val <= val for poss_val in poss_vals]
                elif test == ">":
                    matches = [poss_val > val for poss_val in poss_vals]
                elif test == ">=":
                    matches = [poss_val >= val for poss_val in poss_vals]

                if all(matches):
                    return True
                elif not any(matches):
                    return False

            if test == "in":
                poss_vals_ = set(poss_vals)
                in_vals = set(val)

                if poss_vals_.issubset(in_vals):
                    return True
                if not poss_vals_.intersection(in_vals):
                    return False

            if test == "!in":
                poss_vals_ = set(poss_vals)
                in_vals = set(val)

                if not poss_vals_.intersection(in_vals):
                    return True
                if poss_vals_.issubset(in_vals):
                    return False

            return None
        return pred

    def _conv_l_elems(self, lst, target_type):
        def convert(src, target_type):
            try:
                return True, target_type(src)
            except:
                return False, None

        return [
            converted for is_conv, converted in
            [convert(elem, target_type) for elem in lst]
            if is_conv
        ]

