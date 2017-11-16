# cython: profile=True

import operator as op

from .base_delegate import BaseDaffodilDelegate


def _test_existance(dp, str k, bint v):
    if dp is None:
        return not v

    if v:
        return k in dp
    else:
        return k not in dp


_test_ops = {
  '=':  op.eq,
  '!=': op.ne,
  '<':  op.lt,
  '<=': op.le,
  '>':  op.gt,
  '>=': op.ge,
  "?=": _test_existance,
  "in": lambda a, b: a in b,
  "!in": lambda a, b: a not in b,
}

_do_nothing_predicate = lambda: True


cdef _mk_any_all(children, any_all):
    return lambda data_point: any_all(
        predicate(data_point)
        for predicate in children
        if predicate is not _do_nothing_predicate
    )


# if only one value is a string try to coerce the string
#   to the other value's type
cdef coerce(val, fallback_type):
    try: return float(val)
    except: pass
    return fallback_type(val)


cdef coerce_list(val, fallback_type):
    return [coerce(v, fallback_type) for v in val]


class DictionaryPredicateDelegate(BaseDaffodilDelegate):
    def mk_any(self, children):
        return _mk_any_all(children, any)

    def mk_all(self, children):
        return _mk_any_all(children, all)

    def mk_not_any(self, children):
        return lambda data_point: not self.mk_any(children)(data_point)

    def mk_not_all(self, children):
        return lambda data_point: not self.mk_all(children)(data_point)

    def mk_test(self, test_str):
        return _test_ops[test_str]

    def mk_comment(self, comment, is_inline):
        return _do_nothing_predicate

    def mk_cmp(self, key, val, test):
        val = val.content
        if test is _test_existance:
            return lambda dp: test(dp, key, val)

        # When there is an error "!=" counts as matching
        err_ret_val = True if test is op.ne else False

        def test_data_point(data_point):
            cmp_val = val

            if data_point is None:
                data_point = {}

            try: dp_val = data_point[key]
            except KeyError: return err_ret_val

            if isinstance(cmp_val, list):
                if isinstance(cmp_val[0], str) != isinstance(dp_val, str):
                    try:
                        if isinstance(cmp_val[0], str):
                            cmp_val = coerce_list(cmp_val, type(dp_val))
                        else:
                            dp_val = coerce(dp_val, type(cmp_val))
                    except:
                        return err_ret_val

            elif isinstance(cmp_val, str) != isinstance(dp_val, str):
                try:
                    if isinstance(cmp_val, str):
                        cmp_val = coerce(cmp_val, type(dp_val))
                    else:
                        dp_val = coerce(dp_val, type(cmp_val))
                except: return err_ret_val


            try: return test(dp_val, cmp_val)
            except: pass

            try: return test(type(cmp_val)(data_point[key]), cmp_val)
            except: return err_ret_val
            
        return test_data_point

    def call(self, predicate, iterable):
        return [item for item in iterable if predicate(item)]
