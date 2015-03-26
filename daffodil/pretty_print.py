import operator as op
from UserList import UserList
import traceback


def to_daffodil_str(s):
    # escape quotes
    s = s.replace(u'"', u'\\"')
    
    # wrap string in quotes
    return u'"{0}"'.format(s)
    
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
    
    @property
    def opener(self):
        return u"{" if self.grouping == "all" else u"["
    
    @property
    def closer(self):
        return u"}" if self.grouping == "all" else u"]"
        
    @property
    def sep(self):
        return u"," if self.dense else u"\n"
    
    @property
    def child_indent(self):
        return u"" if self.dense else (self.indent * self.indent_level)
    
    @property
    def wrapper_indent(self):
        return u"" if self.dense else (self.indent * (self.indent_level - 1))
        
    
    def __unicode__(self):
        # Wrapper containing 1 wrapper has no effect
        if len(self) == 1 and isinstance(self[0], DaffodilWrapper):
            return unicode(self[0])
            
        for child in self:
            if isinstance(child, DaffodilWrapper):
                child.indent_level = self.indent_level + 1
                
        def sort_key(obj):
            if not isinstance(obj, DaffodilWrapper):
                return (0, obj)
            
            if obj.grouping == 'any':
                return (1, unicode(obj))
            
            elif obj.grouping == 'all':
                return (2, unicode(obj))
           
        # Sort so that different filters with the same expressions will
        # print the same way
        children = sorted(self, key=sort_key)
        
        # apply indent and join children
        children = self.sep.join(indent(c, self.child_indent) for c in children)
        
        if self.dense:
            result = u"{1}{0}{2}".format(children, self.opener, self.closer)
        else:
            result = u"{3}{1}\n{0}\n{3}{2}".format(children, self.opener, self.closer, self.wrapper_indent)

        return result
    
    
class PrettyPrintDelegate(object):
    def __init__(self, dense=True):
        self.dense = dense
    
    def _any_all(self, children, grouping):
        result = DaffodilWrapper(children)

        result.grouping = grouping
        result.dense = self.dense
        
        return result
        
    def mk_any(self, children):
        return self._any_all(children, "any")

    def mk_all(self, children):
        return self._any_all(children, "all")

    def mk_test(self, test_str):
        return test_str

    def mk_cmp(self, key, val, test):
        key = to_daffodil_str(key)
        
        # values can be boolean, string, or number
        if val in (True, False):
            val = u"true" if val else u"false"
        elif isinstance(val, basestring):
            val = to_daffodil_str(val)
        else:
            val = unicode(val)
        
        if self.dense:
            return u"{0}{1}{2}".format(key, test, val)
        else:
            return u"{0} {1} {2}".format(key, test, val)

    def call(self, predicate):
        return unicode(predicate)
