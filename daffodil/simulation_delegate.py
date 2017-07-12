from past.builtins import basestring

from .base_delegate import BaseDaffodilDelegate


# Sentinal to indicate a comment in the daffodil
COMMENT = object()


class SimulationMatchingDelegate(BaseDaffodilDelegate):
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

    def mk_cmp(self, key, val, test):
        def pred(poss):
            if test == "?=":
                if val:
                    return key in poss
                else:
                    return key not in poss

            # First deal with the case where there is no value
            if key not in poss:
                if test in {"!=", "!in"}:
                    # These operations automaically match if there is no value
                    return True
                # Most operators can't match if there is no value
                return False

            poss_vals = poss.get(key, None)
            if isinstance(poss_vals, basestring):
                poss_vals = [poss_vals]

            # For open ends we can't make any guarantees beyond the ones above
            if not len(poss_vals):
                return None

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
