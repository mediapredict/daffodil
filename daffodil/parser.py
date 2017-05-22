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

# [a-zA-Z0-9$_-]+
BARE_KEY_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_$"

class Daffodil(object):
    def __init__(self, src):
        self.src = src
        self.pos = 0
        self.end = len(src)

        self.tokens = []
        self.main()

    def char(self, n=0):
        return self.src[self.pos + n]

    def chars(self, n):
        return self.src[self.pos:self.pos+n]

    def main(self):
        end = self.end

        while self.pos < end:
            self.consume_whitespace()

            c = self.char()

            # non-significant whitespace
            if c in " \t\n":
                self.pos += 1
                continue

            # negated container starts
            if c == "!" and self.chars(+1) in "{[":
                self.tokens.append(self.chars(2))
                self.pos += 2
                continue

            # container start/end
            if c in '{[]}':
                self.tokens.append(c)
                self.pos += 1
                continue

            # block comments
            if c == "#":
                self.comment()
                continue

            if c in BARE_KEY_CHARS:
                self.bare_key()

                continue

            if c in '"\'':
                self.quoted_key()
                continue

        def comment(self):
            pos = self.pos
            end = len(self.src)

            buffer = ""
            while self.pos < self.end:
                c = self.char()
                self.pos += 1

                if c == "\n":
                    break
                else:
                    buffer += c

            self.tokens.append(buffer)

        def quoted_string(self):
            pass

        def consume_whitespace(self, newlines=True):
            end = self.end
            chars = " \t"
            if newlines:
                chars += "\r\n"
            while self.pos < end:
                if self.char() in chars:
                    self.pos += 1
                    continue




if __name__ == "__main__":
    d = Daffodil("""
      x = 1
      "x" = 1
      'x' = 1
      "x" ?= true
    """)
    print d
