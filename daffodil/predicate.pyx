from .parser cimport Token, BaseDaffodilDelegate


cdef bint _in(a, b):
    return b.__contains__(a)

cdef bint _not_in(a, b):
    return not b.__contains__(a)

cdef bint _eq(a, b):
    return a == b

cdef bint _ne(a, b):
    return a != b

cdef bint _lt(a, b):
    return a < b

cdef bint _le(a, b):
    return a <= b

cdef bint _gt(a, b):
    return a > b

cdef bint _ge(a, b):
    return a >= b


_do_nothing_predicate = lambda: True


# type for a func that takes an object (list in this case) and returns a bool
ctypedef bint (*CMP_Func)(object, object)

cdef class CMPFunctionHandler:
    cdef CMP_Func test
    cdef str key
    cdef object val
    cdef bint err_ret_val

    def __call__(self, dict data_point):
        return self._call(data_point)

    cdef bint _call(self, dict data_point):
        cdef object dp_val
        cdef object cmp_val

        if data_point is None:
            return self.err_ret_val

        try: dp_val = data_point[self.key]
        except KeyError: return self.err_ret_val

        cmp_val = self.val

        if isinstance(cmp_val, list):
            if isinstance(cmp_val[0], str) != isinstance(dp_val, str):
                try:
                    if isinstance(cmp_val[0], str):
                        cmp_val = coerce_list(cmp_val, type(dp_val))
                    else:
                        dp_val = coerce(dp_val, type(cmp_val))
                except:
                    return self.err_ret_val

        elif isinstance(cmp_val, str) != isinstance(dp_val, str):
            try:
                if isinstance(cmp_val, str):
                    cmp_val = coerce(cmp_val, type(dp_val))
                else:
                    dp_val = coerce(dp_val, type(cmp_val))
            except: return self.err_ret_val


        try: return self.test(dp_val, cmp_val)
        except: pass

        try: return self.test(type(cmp_val)(data_point[self.key]), cmp_val)
        except: return self.err_ret_val


cdef class DPCMPFunctionHandler(CMPFunctionHandler):
    cdef bint _call(self, dict data_point):
        if data_point is None:
            return not self.val

        if self.val:
            return data_point.__contains__(self.key)
        else:
            return not data_point.__contains__(self.key)


def _any(data_point, children):
    for child_p in children:
        if child_p is _do_nothing_predicate:
            continue
        if child_p(data_point):
            return True
    return False


cdef object _mk_any_all(children, any_all):
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


cdef class DictionaryPredicateDelegate(BaseDaffodilDelegate):
    def mk_any(self, children):
        return _mk_any_all(children, any)

    def mk_all(self, children):
        return _mk_any_all(children, all)

    def mk_not_any(self, children):
        return lambda data_point: not self.mk_any(children)(data_point)

    def mk_not_all(self, children):
        return lambda data_point: not self.mk_all(children)(data_point)

    def mk_comment(self, str comment, bint is_inline):
        return _do_nothing_predicate

    cdef mk_cmp(self, Token key, Token test, Token val):
        cdef CMPFunctionHandler cmp
        cdef str test_str = test.content

        if test_str == "?=":
            cmp = DPCMPFunctionHandler.__new__(DPCMPFunctionHandler)
            cmp.key = key.content
            cmp.val = val.content
            cmp.err_ret_val = False
            return cmp

        cmp = CMPFunctionHandler.__new__(CMPFunctionHandler)

        cmp.key = key.content
        cmp.val = val.content
        cmp.err_ret_val = False

        if test_str == '=':
            cmp.test = _eq
        elif test_str == '!=':
            cmp.test = _ne
            cmp.err_ret_val = True
        elif test_str == '<':
            cmp.test = _lt
        elif test_str == '<=':
            cmp.test = _le
        elif test_str == '>':
            cmp.test = _gt
        elif test_str == '>=':
            cmp.test = _ge
        elif test_str == 'in':
            cmp.test = _in
        elif test_str == '!in':
            cmp.test = _not_in
            cmp.err_ret_val = True
        else:
            raise ValueError('"{}" is not a valid operator')

        return cmp

    cpdef call(self, predicate, iterable):
        return [item for item in iterable if predicate(item)]
