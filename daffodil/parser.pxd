cdef class Token:
    cpdef public object content

cdef class TimeStamp(Token):
    cpdef public str raw_content
    cpdef public bint uses_offset

cdef class GroupStart(Token): pass
cdef class GroupEnd(Token): pass
cdef class LineComment(Token): pass
cdef class TrailingComment(Token): pass
cdef class Operator(Token): pass
cdef class String(Token): pass
cdef class Number(Token): pass
cdef class Boolean(Token): pass
cdef class ArrayStart(Token): pass
cdef class ArrayEnd(Token): pass

cdef class _ArrayToken(Token):
    cpdef public object raw_content

cdef class BaseDaffodilDelegate:
    cdef mk_cmp(self, Token key, Token test, Token val)

cdef class DaffodilParser:
    cdef public str src
    cdef public tokens
    cdef int pos, end

    cdef str char(self, int offset=*)
    cdef str chars(self, int n, pos=*)
    cdef consume_whitespace(self, bint newlines=*)
    cdef str read_quoted_string(self)


cdef object _read_val(tokens)

cdef class Daffodil:
    cdef public DaffodilParser parse_result
    cdef public BaseDaffodilDelegate delegate
    cdef public object keys, predicate
