from .predicate import DictionaryPredicateDelegate
from .exceptions import ParseError


BARE_KEY_CHARS = "$-_0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
NUMBER_CHARS = "-.0123456789"
QUOTE_CHARS = "\"\'"

PAIRS = {
    "{": "}",
    "[": "]",
}

# Evaluated in this order - commonly used ones first helps performance, make
# sure anything that is a prefix of another op comes AFTER the longer version
OPERATORS = (
    "=", "?=", "!=",
    ">=", ">",
    "<=", "<",
    "!in", "in",
)

MAX_OP_LENGTH = max(len(op) for op in OPERATORS)


class Token(object):
    """
    Base class for all tokens
    """
    def __init__(self, content):
        self.content = content


class GroupStart(Token):
    def is_end(self, token):
        if not isinstance(token, GroupEnd):
            return False

        opener = self.content[-1]

        if opener not in PAIRS:
            ValueError("GroupStart contains unrecognized content: {}".format(self.content))

        return token.content == PAIRS[opener]


class Key(Token): pass
class GroupEnd(Token): pass
class LineComment(Token): pass
class TrailingComment(Token): pass
class Operator(Token): pass
class String(Token): pass
class Number(Token): pass
class Boolean(Token): pass
class ArrayStart(Token): pass
class ArrayEnd(Token): pass


class DaffodilParser(object):
    def __init__(self, src):
        self.src = "{" + src + "\n}"
        self.pos = 0
        self.end = len(self.src)

        self.tokens = []
        self.main()

    ############################################################
    # State machine
    ############################################################
    def main(self):
        can_accept_another_expression = True
        expected_closers = []

        self.consume_whitespace()
        while self.pos < self.end:
            c = self.char()

            # Fist deal with All/Any/Not All/Not Any right in the main loop...
            # then find line-comments and conditions
            if not can_accept_another_expression and c not in "}]#":
                raise ParseError("Expected a comma, newline or end of block at byte {}".format(self.pos))
            elif c == "!" and self.char(+1) in "{[":
                token_content = self.chars(2)
                self.tokens.append(GroupStart(token_content))
                expected_closers.append(PAIRS[token_content[1]])
                self.pos += 2
            elif c in '{[':
                self.tokens.append(GroupStart(c))
                expected_closers.append(PAIRS[c])
                self.pos += 1
            elif c in '}]':
                if not expected_closers:
                    raise ParseError("Found an closing brace \"{}\" without a corresponding opening brace.".format(c))
                if c != expected_closers[-1]:
                    raise ParseError("Expected a {} but found {} instead".format(expected_closers[-1], c))
                self.tokens.append(GroupEnd(c))
                expected_closers.pop()
                self.pos += 1
                can_accept_another_expression = self.separator()
            elif c == "#":
                self.comment(LineComment)
            elif c in BARE_KEY_CHARS or c in QUOTE_CHARS:
                can_accept_another_expression = self.condition()
            else:
                raise ParseError("Unrecognized input at byte {}".format(self.pos))

            # skip over non-significant whitespace
            self.consume_whitespace()

    def comment(self, token_type):
        buffer = ""
        while self.pos < self.end:
            c = self.char()
            self.pos += 1

            if c == "\n":
                break
            else:
                buffer += c

        self.tokens.append(
            token_type(buffer.strip())
        )

    def condition(self):
        c = self.char()

        if c in BARE_KEY_CHARS:
            self.bare_key()
        elif c in QUOTE_CHARS:
            self.quoted_key()
        else:
            raise ParseError("Condition expected at byte {}".format(self.pos))

        self.consume_whitespace(newlines=False)
        self.operator()
        self.consume_whitespace(newlines=True)

        self.value()
        self.consume_whitespace(newlines=False)

        if self.tokens[-2].content == "?=" and not isinstance(self.tokens[-1], Boolean):
            raise ValueError('"?=" operator requires boolean value (true/false)')

        if self.char() == "#":
            self.comment(TrailingComment)
            return True
        else:
            return self.separator()

    def value(self):
        c = self.char()

        if c == "(":
            self.array()
        elif c in QUOTE_CHARS:
            self.quoted_string()
        elif c in NUMBER_CHARS:
            self.number()
        elif c.lower() in "tf":
            self.boolean()

    def array(self):
        # skip over the opening "("
        self.pos += 1
        self.tokens.append(ArrayStart("("))

        self.consume_whitespace()

        c = self.char()
        if c in QUOTE_CHARS:
            val_type = "string"
            reader = self.quoted_string
        elif c in NUMBER_CHARS:
            val_type = "number"
            reader = self.number
        elif c.lower() in "tf":
            val_type = "boolean"
            reader = self.boolean
        else:
            raise ParseError("Couldn't parse first value in array at byte {}".format(self.pos))

        can_accept_another_value = True
        while self.pos < self.end:
            self.consume_whitespace()

            c = self.char()
            if c == ")":
                self.pos += 1
                self.tokens.append(ArrayEnd(")"))
                break

            if can_accept_another_value:
                try:
                    reader()
                except:
                    raise ParseError("Couldn't parse {} value in array at byte {}".format(val_type, self.pos))
                can_accept_another_value = self.separator()
            else:
                raise ParseError("Values must be separated by a comma or a new line, found unexpected value at byte {}".format(self.pos))
        else:
            raise ParseError("Expected to find the end of an array (closing parenthesis) but didn't")

    def quoted_string(self):
        self.tokens.append(String(self.read_quoted_string()))

    def number(self):
        num_start = self.pos

        # get local references for the inner loop
        src = self.src
        end = self.end
        pos = self.pos
        while pos < end:
            if src[pos] not in NUMBER_CHARS:
                break
            pos += 1

        self.pos = pos
        buffer = src[num_start:pos]

        if "." not in buffer:
            val = int(buffer)
        else:
            val = float(buffer)

        self.tokens.append(Number(val))

    def boolean(self):
        chunk = self.chars(5).lower()
        if chunk.startswith(("true", "false",)):
            val = (chunk != 'false')
            self.pos += (4 if val else 5)
            self.tokens.append(Boolean(val))
        else:
            raise ParseError("Expected Boolean value but found {}".format(chunk))

    def quoted_key(self):
        self.tokens.append(
            Key(self.read_quoted_string())
        )

    def bare_key(self):
        buffer = ""
        while self.pos < self.end:
            c = self.char()

            if c not in BARE_KEY_CHARS:
                break

            self.pos += 1
            buffer += c

        self.tokens.append(Key(buffer))

    def operator(self):
        chunk = self.chars(MAX_OP_LENGTH)
        for op in OPERATORS:
            if chunk.startswith(op):
                self.tokens.append(Operator(op))
                self.pos += len(op)
                break
        else:
            raise ParseError("Expected operator at byte {}".format(self.pos))

    def separator(self):
        sep_found = False
        comma_found = False

        src = self.src
        end = self.end
        while self.pos < end:
            self.consume_whitespace(newlines=sep_found)
            c = src[self.pos]
            if c in '\r\n':
                sep_found = True
            elif c == ',':
                if comma_found:
                    raise ParseError("Found multiple commas in a row at byte {}".format(self.pos))
                sep_found = True
                comma_found = True
                self.pos += 1
            else:
                break

        return sep_found

    ############################################################
    # Utility functions
    ############################################################

    def char(self, offset=0):
        try:
            return self.src[self.pos + offset]
        except IndexError:
            return ''

    def chars(self, n):
        return self.src[self.pos:self.pos+n]

    def consume_whitespace(self, newlines=True):
        """
        Discards whitespace, does not append any tokens.
        """
        chars = " \t"
        if newlines:
            chars += "\r\n"

        src = self.src
        end = self.end
        while self.pos < end:
            if src[self.pos] not in chars:
                break
            self.pos += 1

    def read_quoted_string(self):
        """
        Reads and returns a quoted string.
        
        DOES NOT APPEND A TOKEN. That is the responsibility of the caller.
        """
        quote_char = self.char()

        # (pos + 1) because we start after the quote character
        pos = self.pos + 1
        src = self.src
        end = self.end

        buffer = ""
        while pos < end:
            c = src[pos]
            pos += 1

            # Escaped quotes and backslashes
            if c == "\\" and src[pos] in "\"\'\\":
                c = src[pos]
                pos += 1
            elif c == quote_char:
                break

            buffer += c

        self.pos = pos
        return buffer


class Daffodil(object):
    def __init__(self, source, delegate=DictionaryPredicateDelegate()):
        if isinstance(source, DaffodilParser):
            self.parse_result = source
        else:
            if 'timestamp' in source:
                source = self.convert_timestamp_to_time(source)
            self.parse_result = DaffodilParser(source)

        self.keys = set()
        self.delegate = delegate
        self.predicate = self.make_predicate(self.parse_result.tokens)

    def _handle_group(self, parent, children):
        lookup = {
            "!{": self.delegate.mk_not_all,
            "![": self.delegate.mk_not_any,
            "{": self.delegate.mk_all,
            "[": self.delegate.mk_any,
        }
        return lookup[parent.content](children)

    def _read_val(self, tokens):
        token = tokens.pop(0)
        if isinstance(token, ArrayStart):
            children = []
            while True:
                if isinstance(tokens[0], ArrayEnd):
                    tokens.pop(0)
                    return children
                children.append(self._read_val(tokens))
        elif isinstance(token, (String, Number, Boolean)):
            return token.content
        else:
            raise ValueError("Expected Array, String, Number, or Boolean Token. Got {}". format(token))

    def convert_timestamp_to_time(self, source):
        from datetime import datetime
        import re

        timestamp = re.search(r'timestamp\(\d+-.*', source).group(0)
        date_no_day = re.findall(r'\d+-', source)
        year = re.sub(r'-', '', date_no_day[0])
        month = re.sub(r'-', '', date_no_day[1])
        extra_char_day = re.search(r'\d+\)', source).group(0)
        day = re.sub('\)', '', extra_char_day)
        final_stamp = int(datetime(int(year), int(month), int(day)).timestamp())
        new_source = re.sub(r'timestamp\(\d+-.*', str(final_stamp), source)
        return new_source

    def make_predicate(self, tokens, parent=None):
        if parent is None:
            parent = tokens[0]
            return self.make_predicate(tokens[1:], parent)

        children = []
        while tokens:
            token = tokens.pop(0)
            if parent.is_end(token):
                return self._handle_group(parent, children)
            elif isinstance(token, Key):
                self.keys.add(token.content)
                key = token.content
                test = self.delegate.mk_test(tokens.pop(0).content)
                val = self._read_val(tokens)

                children.append(
                    self.delegate.mk_cmp(key, val, test)
                )
            elif isinstance(token, LineComment):
                children.append(
                    self.delegate.mk_comment(token.content, False)
                )
            elif isinstance(token, TrailingComment):
                children.append(
                    self.delegate.mk_comment(token.content, True)
                )
            elif isinstance(token, GroupStart):
                children.append(
                    self.make_predicate(tokens, token)
                )
            else:
                raise ValueError("Unexpected token: {}".format(token))

        raise ValueError("Unexpectedly ran out of tokens")

    def __call__(self, *args):
        return self.delegate.call(self.predicate, *args)
