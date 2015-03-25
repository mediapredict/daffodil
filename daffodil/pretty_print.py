import operator as op
import re
from UserList import UserList



def to_daffodil_str(s):
    # escape quotes
    s = s.replace(u'"', u'\\"')
    
    # wrap string in quotes
    return u'"{0}"'.format(s)

class DaffodilWrapper(UserList):
    grouping = "all"
    dense = True
    
    @property
    def opener(self):
        return u"{" if self.grouping == "all" else u"["
    
    @property
    def closer(self):
        return u"}" if self.grouping == "all" else u"]"
        
    @property
    def sep(self):
        return u"," if self.dense else u"\n"
    
    def __unicode__(self):
        def sort_key(obj):
            return obj
        
        # Fix unnecessarily nested wrappers...
        
        # Wrapper containing 1 wrapper has no effect
        if len(self) == 1 and isinstance(self[0], DaffodilWrapper):
            return unicode(self[0])
           
        # Sort so that different filters with the same expressions will
        # print the same way
        children = sorted(self, key=sort_key)
        
        if self.dense:
            children = self.sep.join(children)
            result = u"{1}{0}{2}".format(children, self.opener, self.closer)
        else:
            children = self.sep.join(u"  {0}".format(c) for c in children)
            result = u"{1}\n{0}\n{2}".format(children, self.opener, self.closer)

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
