from parsimonious.grammar import Grammar
from .predicate import DictionaryPredicateDelegate


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
        'all = _ "{" expr* _ "}" sep'
        child_expressions = children[2]
        return self.delegate.mk_all(child_expressions)

    def any(self, node, children):
        'any = _ "[" expr* _ "]" sep'
        child_expressions = children[2]
        return self.delegate.mk_any(child_expressions)

    def not_all(self, node, children):
        'not_all = _ "!{" expr* _ "}" sep'
        child_expressions = children[2]
        return self.delegate.mk_not_all(child_expressions)

    def not_any(self, node, children):
        'not_any = _ "![" expr* _ "]" sep'
        child_expressions = children[2]
        return self.delegate.mk_not_any(child_expressions)

    def expr(self, node, children):
        '''expr = (comment / all / any / not_all / not_any / condition)'''
        if isinstance(children[0], list):
            return children[0][0]
        return children[0]

    def comment(self, node, children):
        'comment = block_comment / inline_comment'
        return children[0]

    def block_comment(self, node, children):
        'block_comment = n inline_comment'
        return self.delegate.mk_comment(node.text, False)

    def inline_comment(self, node, children):
        'inline_comment = ~"[\\s]*#[^\\n]*" &n'
        return self.delegate.mk_comment(node.text, True)

    def condition(self, node, children):
        'condition = _ key _ test _ value sep'
        _, key, _, test, _, val, _ = children
        return self.delegate.mk_cmp(key, val, test)

    def key(self, node, children):
        'key = bare_key / string'
        val = children[0]
        self.keys.add(val)
        return val

    def bare_key(self, node, children):
        'bare_key = ~"[a-zA-Z0-9$_-]+"'
        return node.text

    def test(self, node, children):
        'test = "!=" / "?=" / "<=" / ">=" / "=" / "<" / ">" / "in" / "!in"'
        return self.delegate.mk_test(node.text)

    def value(self, node, children):
        'value = number / boolean / string / array'
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

    def array(self, node, children):
        'array = "(" (  _ (number / boolean / string) _ ~"[\\n\,]?" _ )+ ")"'
        vals = [
            val[0]
            for (_, val, _, whitespace, _)
            in children[1]
        ]

        arr_type = type(vals[0])
        if arr_type == list:
            raise ValueError("nested arrays are not supported")

        for val in vals:
            if type(val) != arr_type:
                raise ValueError("arrays must be all the same type")

        return vals

    def _(self, node, children):
        '_ = ~"[\\n\s]*"m'

    def n(self, node, children):
        'n = ~"\\n"'

    def sep(self, node, children):
        'sep = _ (&sep_n / sep_c)?'

    def sep_n(self, node, children):
        'sep_n = n'

    def sep_c(self, node, children):
        'sep_c = ~"[\,]"'

    def __call__(self, *args):
        return self.delegate.call(self.predicate, *args)
