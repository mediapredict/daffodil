import operator as op
from parsimonious.grammar import Grammar


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
    def __init__(self, source):
        self.predicate = self.eval("{" + source + "}")

    def parse(self, source):
        grammar = '\n'.join(v.__doc__ for k, v in vars(self.__class__).items()
                      if '__' not in k and hasattr(v, '__doc__') and v.__doc__)
        return Grammar(grammar)['program'].parse(source)

    def eval(self, source):
        node = self.parse(source) if isinstance(source, str) else source
        method = getattr(self, node.expr_name, lambda node, children: children)
        return method(node, [self.eval(n) for n in node])

    def program(self, node, children):
        'program = expr'
        return children[0]
    
    def all(self, node, children):
        'all = "{" expr* "}"'
        predicates = children[1]
        return lambda data_point: all( p(data_point) for p in predicates)
        
    def any(self, node, children):
        'any = "[" expr* "]"'
        predicates = children[1]
        return lambda data_point: any( p(data_point) for p in predicates)
        
    def expr(self, node, children):
        '''expr = _ (all / any / condition) _ ~"[\\n\,]?" _'''
        return children[1][0]
    
    def condition(self, node, children):
        'condition = _ key _ test _ value _'
        _, key, _, test, _, val, _ = children
        def test(data_point):
            try: return test(type(val)(data_point[key]), val)
            except: return False
        return lambda data_point: test(type(val)(data_point[key]), val)

    def key(self, node, children):
        'key = string / bare_key'
        return node.text
        
    def bare_key(self, node, children):
        'bare_key = ~"[a-z0-9_-]+"'
        return node.text
        
    def test(self, node, children):
        'test = "=" / "!=" / "<" / "<=" / ">" / ">="'
        ops = {
          '=':  op.eq,
          '!=': op.sub,
          '<':  op.lt,
          '<=': op.le,
          '>':  op.gt,
          '>=': op.ge,
        }
        return ops[node.text]
    
    def value(self, node, children):
        'value = number / string'
        return children[0]
        
    def string(self, node, children):
        'string = doubleString / singleString'
        return node.text[1:-1]
        
    def doubleString(self, node, children):
        '''
        doubleString = ~'"([^"]|(\"))*"'
        '''
        return node.text
    
    def singleString(self, node, children):
        '''
        singleString = ~"'([^']|(\'))*'"
        '''
        return node.text    

    def number(self, node, children):
        'number = ~"[0-9]+"'
        return int(node.text)

    def _(self, node, children):
        '_ = ~"[\\n\s]*"m'
        
    def __call__(self, iterable):
        return filter(self.predicate, iterable)
