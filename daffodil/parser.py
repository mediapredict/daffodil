"""
Parsing Daffodil:
 - Expressions
    Containers
    Comparisons
    ** May have a comment at the end of any line
 - Containers (contain 0 or more comments and expressions, separated by newline or comma)
    All {}
    Any []
    Not All !{}
    Not Any ![]
 - Comparisons
    key
    operator
    value
 - Key
    unquoted alpha-numeric
    double or single quoted string
 - Operators (literals)
    =
    !=
    ?=
    >
    >=
    <
    <=
    in
    !in
 - Values
    single or double quoted strings
    integers
    floats
    booleans
    array
    
"""

class Daffodil(object):
    def __init__(self, src):
        self.src = src
        self.open = []
        self.pos = 0

        self.tokens = []
        self.main(src)

    def char(self, n=0):
        return self.src[self.pos + n]

    def chars(self, n):
        return self.src[self.pos:self.pos+n]

    def main(self, src):
        end = len(self.src)

        while self.pos < end:
            c = self.char()
            if c == "!" and self.chars(+1) in "{[":
                self.tokens.append(self.chars(2))
                self.pos += 2
                continue

            if c in '{[]}':
                self.tokens.append(c)
                self.pos += 1
                continue
            
