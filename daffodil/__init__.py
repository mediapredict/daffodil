from parsimonious.grammar import Grammar

from .predicate import DictionaryPredicateDelegate
from .hstore_predicate import HStoreQueryDelegate
from .pretty_print import PrettyPrintDelegate



# loosely based on https://github.com/halst/mini/blob/master/mini.py
class Daffodil(object):
    """
    Naming:
        "Data Filtering" -> "DataFil" -> "Daffodil"
                (shortened to)    (sounds like)
        
    
    {} - all
    [] - any
    
    women between 18 and 34:
      {
      gender = "female"
      age > 18
      age < 34
      }
    
    people who are 18 or 21
      [
        age = 18
        age = 21
      ]
      
    men between 18 and 34 and women between 25 and 34
      [
        {
          gender = "female"
          age > 25
          age < 34
        }
        {
          gender = "male"
          age > 18
          age < 34
        }
      ]
    """
    def __init__(self, source, delegate=DictionaryPredicateDelegate()):
        self.keys = set()
        self.delegate = delegate
        self.ast = self.parse("{" + source + "}")
        self.predicate = self.eval(self.ast)

    def parse(self, source):
        return self.grammar['program'].parse(source)
        
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'grammar'):
            grammar_def = '\n'.join(v.__doc__ for k, v in vars(cls).items()
                                    if '__' not in k 
                                      and hasattr(v, '__doc__') 
                                      and v.__doc__)
            cls.grammar = Grammar(grammar_def)
        return object.__new__(cls, *args, **kwargs)

    def eval(self, source):
        node = self.parse(source) if isinstance(source, basestring) else source
        method = getattr(self, node.expr_name, lambda node, children: children)
        return method(node, [self.eval(n) for n in node])

    def program(self, node, children):
        'program = expr'
        return children[0]
    
    def all(self, node, children):
        'all = "{" expr* "}"'
        child_expressions = children[1]
        return self.delegate.mk_all(child_expressions)
        
    def any(self, node, children):
        'any = "[" expr* "]"'
        child_expressions = children[1]
        return self.delegate.mk_any(child_expressions)
        
    def expr(self, node, children):
        '''expr = _ (all / any / condition) _ ~"[\\n\,]?" _'''
        return children[1][0]
    
    def condition(self, node, children):
        'condition = _ key _ test _ value _'
        _, key, _, test, _, val, _ = children
        return self.delegate.mk_cmp(key, val, test)

    def key(self, node, children):
        'key = bare_key / string'
        val = children[0]
        self.keys.add(val)
        return val
        
    def bare_key(self, node, children):
        'bare_key = ~"[a-zA-Z0-9_-]+"'
        return node.text
        
    def test(self, node, children):
        'test = "!=" / "?=" / "<=" / ">=" / "=" / "<" / ">"'
        return self.delegate.mk_test(node.text)
    
    def value(self, node, children):
        'value = number / boolean / string'
        return children[0]
        
    def string(self, node, children):
        'string = doubleString / singleString'
        return unicode(node.text[1:-1]).replace(u'\\"', u'"').replace(u"\\'", u"'")
        
    def doubleString(self, node, children):
        r'''
        doubleString = '"' ( '\\"' / ~'[^"]' )* '"'
        '''
        return node.text
    
    def singleString(self, node, children):
        r'''
        singleString = "'" ( "\\'" / ~"[^']" )* "'"
        '''
        return node.text    

    def number(self, node, children):
        'number =  float / integer'
        return children[0]
    
    def integer(self, node, children):
        'integer = ~"-?[0-9]+"'
        return int(node.text)
    
    def boolean(self, node, children):
        '''
        boolean = ~"true|false"i
        '''
        return node.text.lower() == "true"
    
    def float(self, node, children):
        'float = ~"-?[0-9]*\.[0-9]+"'
        return float(node.text)

    def _(self, node, children):
        '_ = ~"[\\n\s]*"m'
        
    def __call__(self, *args):
        return self.delegate.call(self.predicate, *args)
