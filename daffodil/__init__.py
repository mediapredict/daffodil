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
        node = self.parse(source) if isinstance(source, basestring) else source
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
        
        def test_data_point(data_point):
            cmp_val = val
            err_ret_val = getattr(test, "onerror", False)
            
            try: dp_val = data_point[key]
            except KeyError: return err_ret_val 
            
            # if only one value is a string try to coerce the string
            #   to the other value's type
            def coerce(val, fallback_type):
                try: return float(val)
                except: pass
                return fallback_type(val)
            
            if isinstance(cmp_val, basestring) != isinstance(dp_val, basestring):
                try:
                    if isinstance(cmp_val, basestring):
                        cmp_val = coerce(cmp_val, type(dp_val))
                    else:
                        dp_val = coerce(dp_val, type(cmp_val))
                except: return err_ret_val
                    
                
            try: return test(dp_val, cmp_val)
            except: pass
            
            try: return test(type(cmp_val)(data_point[key]), cmp_val)
            except: return err_ret_val
            
        return test_data_point

    def key(self, node, children):
        'key = string / bare_key'
        return children[0]
        
    def bare_key(self, node, children):
        'bare_key = ~"[a-zA-Z0-9_-]+"'
        return node.text
        
    def test(self, node, children):
        'test = "!=" / "<=" / ">=" / "=" / "<" / ">"'
        
        ne = lambda *a: op.ne(*a)
        ne.onerror = True
            
        ops = {
          '=':  op.eq,
          '!=': ne,
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
        return unicode(node.text[1:-1])
        
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
        'number =  float / integer'
        return children[0]
    
    def integer(self, node, children):
        'integer = ~"[0-9]+"'
        return int(node.text)
    
    def float(self, node, children):
        'float = ~"[0-9]*\.[0-9]+"'
        return float(node.text)

    def _(self, node, children):
        '_ = ~"[\\n\s]*"m'
        
    def __call__(self, iterable):
        return filter(self.predicate, iterable)
