from future import standard_library

from daffodil.parser import TimeStamp

standard_library.install_aliases()
from builtins import str
from past.builtins import basestring
from collections import UserList

from .base_delegate import BaseDaffodilDelegate


def token_to_daffodil_primitive(val):
    if isinstance(val, TimeStamp):
        return "timestamp({0})".format(val.raw_content)
    else:
        return to_daffodil_primitive(val.content)


def to_daffodil_primitive(val):
    if isinstance(val, list):
        raise ValueError("lists cannot be converted to a primitive daffodil type - use a DaffodilArrayWrapper")

    if isinstance(val, bool):
        return "true" if val else "false"
    elif isinstance(val, basestring):
        # escape quotes
        val = val.replace('"', '\\"')

        # wrap string in quotes
        return '"{0}"'.format(val)
    else:
        return str(val)


def indent(s, amount=" "):
    if isinstance(s, DaffodilWrapper):
        return str(s)
    else:
        return "{0}{1}".format(amount, s)


class DaffodilWrapper(UserList):
    grouping = "all"
    dense = True
    indent_level = 1
    indent = "  "

    WRAP_SYMBOLS = {
        "OPEN": {
            "all": "{",
            "any": "[",
            "in": "(",
            "not_all": "!{",
            "not_any": "![",
            "!in": "(",
        },
        "CLOSE": {
            "all": "}",
            "any": "]",
            "in": ")",
            "not_all": "}",
            "not_any": "]",
            "!in": ")",
        },
    }

    @property
    def opener(self):
        return self.WRAP_SYMBOLS["OPEN"][self.grouping]

    @property
    def closer(self):
        return self.WRAP_SYMBOLS["CLOSE"][self.grouping]

    @property
    def sep(self):
        return "," if self.dense else "\n"
    
    @property
    def child_indent(self):
        return "" if self.dense else (self.indent * self.indent_level)
    
    @property
    def wrapper_indent(self):
        return "" if self.dense else (self.indent * (self.indent_level - 1))

    def format_dense(self, children):
        return "{1}{0}{2}".format(children, self.opener, self.closer)

    def format_std(self, children):
        return "{3}{1}\n{0}\n{3}{2}".format(children, self.opener, self.closer, self.wrapper_indent)

    def format_children(self, children):
        if self.dense:
            # abandon comments
            children = [
                c for c in children
                if not getattr(c, "dense_hide", False)
            ]
        else:
            # join inline comments
            lcomments_indexes = [
              index for index, c in enumerate(children)
              if getattr(c, "keep_with_prev", False)
            ]

            for i in reversed(lcomments_indexes):
                children[i-1:i+1] = [" ".join(children[i-1:i+1])]

        # apply indent and join children
        children = self.sep.join(
            indent(c, self.child_indent)
            for c in children
        )

        if self.dense:
            return self.format_dense(children)

        return self.format_std(children)

    def __str__(self):
        # Wrapper containing 1 wrapper has no effect
        if len(self) == 1 and isinstance(self[0], DaffodilWrapper):
            return str(self[0])

        for child in self:
            if isinstance(child, DaffodilWrapper):
                child.indent_level = self.indent_level + 1

        return self.format_children(self)

    # only for python 2.x compatibiliy
    def __unicode__(self):
        return self.__str__()


class DaffodilArrayWrapper(DaffodilWrapper):
    @property
    def child_indent(self):
        return "" if self.dense else (self.indent * (self.indent_level + 1))

    def format_children(self, children):
        children = [token_to_daffodil_primitive(c) for c in children]
        return super(DaffodilArrayWrapper, self).format_children(children)

    def format_std(self, children):
        return "{3}{1}\n{0}\n{4}{2}".format(
            children, self.opener, self.closer, self.wrapper_indent, self.indent * self.indent_level
        )


class PrettyPrintDelegate(BaseDaffodilDelegate):
    def __init__(self, dense=True):
        self.dense = dense
    
    def _mk_wrapped(self, children, grouping, wrapper=DaffodilWrapper):
        result = wrapper(children)

        result.grouping = grouping
        result.dense = self.dense
        
        return result
        
    def mk_any(self, children):
        return self._mk_wrapped(children, "any")

    def mk_all(self, children):
        return self._mk_wrapped(children, "all")

    def mk_not_any(self, children):
        return self._mk_wrapped(children, "not_any")

    def mk_not_all(self, children):
        return self._mk_wrapped(children, "not_all")

    def mk_test(self, test_str):
        return test_str

    def mk_comment(self, comment, is_inline):
        class string(str):
            dense_hide = True
            keep_with_prev = is_inline
        return string(comment.strip())

    def mk_cmp(self, key, val, test):
        key = to_daffodil_primitive(key)
        
        # values can be boolean, string, or number
        if isinstance(val.content, list):
            val = self._mk_wrapped(val.raw_content, test, DaffodilArrayWrapper)
        else:
            val = token_to_daffodil_primitive(val)

        if self.dense:
            return "{0}{1}{2}".format(key, test, val)
        else:
            return "{0} {1} {2}".format(key, test, val)

    def call(self, predicate):
        return str(predicate)
