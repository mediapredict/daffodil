from UserList import UserList


def to_daffodil_primitive(val):
    if isinstance(val, list):
        raise ValueError("lists cannot be converted to a primitive daffodil type - use a DaffodilArrayWrapper")

    if isinstance(val, bool):
        return u"true" if val else u"false"
    elif isinstance(val, basestring):
        # escape quotes
        val = val.replace(u'"', u'\\"')

        # wrap string in quotes
        return u'"{0}"'.format(val)
    else:
        return unicode(val)


def indent(s, amount=u" "):
    if isinstance(s, DaffodilWrapper):
        return unicode(s)
    else:
        return u"{0}{1}".format(amount, s)


class DaffodilWrapper(UserList):
    grouping = "all"
    dense = True
    indent_level = 1
    indent = u"  "

    WRAP_SYMBOLS = {
        "OPEN": {
            "all": u"{",
            "any": u"[",
            "in": u"(",
            "not_all": u"!{",
            "not_any": u"![",
            "!in": u"(",
        },
        "CLOSE": {
            "all": u"}",
            "any": u"]",
            "in": u")",
            "not_all": u"}",
            "not_any": u"]",
            "!in": u")",
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
        return u"," if self.dense else u"\n"
    
    @property
    def child_indent(self):
        return u"" if self.dense else (self.indent * self.indent_level)
    
    @property
    def wrapper_indent(self):
        return u"" if self.dense else (self.indent * (self.indent_level - 1))

    def format_dense(self, children):
        return u"{1}{0}{2}".format(children, self.opener, self.closer)

    def format_std(self, children):
        return u"{3}{1}\n{0}\n{3}{2}".format(children, self.opener, self.closer, self.wrapper_indent)

    def format_children(self, children):
        def is_comment(child):
            return isinstance(child, basestring) and child.startswith("#")

        # apply indent and join children
        children = self.sep.join(
            indent(c, self.child_indent)
            for c in children
            if not (is_comment(c) and self.dense)
        )

        if self.dense:
            return self.format_dense(children)

        return self.format_std(children)

    def __unicode__(self):
        # Wrapper containing 1 wrapper has no effect
        if len(self) == 1 and isinstance(self[0], DaffodilWrapper):
            return unicode(self[0])
            
        for child in self:
            if isinstance(child, DaffodilWrapper):
                child.indent_level = self.indent_level + 1

        def sort_key(obj):
            if not isinstance(obj, DaffodilWrapper):
                if obj is True:
                    return -2, obj
                elif obj is False:
                    return -1, obj
                else:
                    return 0, obj
            
            if obj.grouping == 'any':
                return 1, unicode(obj)
            
            elif obj.grouping == 'all':
                return 2, unicode(obj)
           
        # Sort so that different filters with the same expressions will
        # print the same way
        children = sorted(self, key=sort_key)

        return self.format_children(children)


class DaffodilArrayWrapper(DaffodilWrapper):
    @property
    def child_indent(self):
        return u"" if self.dense else (self.indent * (self.indent_level + 1))

    def format_children(self, children):
        children = [to_daffodil_primitive(c) for c in children]
        return super(DaffodilArrayWrapper, self).format_children(children)

    def format_std(self, children):
        return u"{3}{1}\n{0}\n{4}{2}".format(
            children, self.opener, self.closer, self.wrapper_indent, self.indent * self.indent_level
        )


class PrettyPrintDelegate(object):
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

    def mk_comment(self, comment):
        return comment

    def mk_cmp(self, key, val, test):
        key = to_daffodil_primitive(key)
        
        # values can be boolean, string, or number
        if isinstance(val, list):
            val = self._mk_wrapped(val, test, DaffodilArrayWrapper)
        else:
            val = to_daffodil_primitive(val)

        if self.dense:
            return u"{0}{1}{2}".format(key, test, val)
        else:
            return u"{0} {1} {2}".format(key, test, val)

    def call(self, predicate):
        return unicode(predicate)
