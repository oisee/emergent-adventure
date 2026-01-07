"""
ForthLisp Lexer

Tokenizes ForthLisp source into tokens.

Token types:
- Numbers: integers and floats
- Strings: "double quoted"
- Symbols: identifiers, operators
- S-expressions: (parenthesized lists)
- Comments: ; to end of line
"""

from dataclasses import dataclass
from enum import IntEnum, auto
from typing import List, Optional
import re


class TokenType(IntEnum):
    """Token types for ForthLisp"""
    # Literals
    INTEGER = auto()
    FLOAT = auto()
    STRING = auto()
    SYMBOL = auto()
    BOOLEAN = auto()

    # S-expression delimiters
    LPAREN = auto()
    RPAREN = auto()

    # Control flow
    IF = auto()
    ELSE = auto()
    THEN = auto()
    DO = auto()
    LOOP = auto()
    BEGIN = auto()
    UNTIL = auto()
    WHILE = auto()
    REPEAT = auto()

    # Definition
    COLON = auto()      # : name ... ;
    SEMICOLON = auto()
    QUOTE = auto()      # '

    # Special
    EOF = auto()
    ERROR = auto()


@dataclass
class Token:
    """A lexical token"""
    type: TokenType
    value: any
    line: int
    column: int

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r})"


# Keywords that map to specific token types
KEYWORDS = {
    'if': TokenType.IF,
    'else': TokenType.ELSE,
    'then': TokenType.THEN,
    'do': TokenType.DO,
    'loop': TokenType.LOOP,
    'begin': TokenType.BEGIN,
    'until': TokenType.UNTIL,
    'while': TokenType.WHILE,
    'repeat': TokenType.REPEAT,
    'true': TokenType.BOOLEAN,
    'false': TokenType.BOOLEAN,
}


class Lexer:
    """
    Tokenizer for ForthLisp.

    Handles:
    - Forth-style postfix: 2 3 + dup *
    - Lisp-style S-expressions: (belief "key" 0.8)
    - Comments: ; line comment
    - Strings: "hello world"
    """

    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []

    def peek(self, offset: int = 0) -> str:
        """Look at character without consuming"""
        idx = self.pos + offset
        if idx >= len(self.source):
            return '\0'
        return self.source[idx]

    def advance(self) -> str:
        """Consume and return current character"""
        ch = self.peek()
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def skip_whitespace(self):
        """Skip whitespace and comments"""
        while self.pos < len(self.source):
            ch = self.peek()

            # Whitespace
            if ch in ' \t\n\r':
                self.advance()
                continue

            # Line comment: ; to end of line
            if ch == ';':
                while self.peek() not in '\n\0':
                    self.advance()
                continue

            # Block comment: ( ... ) when followed by space
            # Note: We need to distinguish (word) from ( comment )
            # For simplicity, we only treat ; as comment start

            break

    def make_token(self, type: TokenType, value: any) -> Token:
        """Create token at current position"""
        return Token(type, value, self.line, self.column)

    def scan_string(self) -> Token:
        """Scan a double-quoted string"""
        start_line = self.line
        start_col = self.column

        self.advance()  # consume opening "
        chars = []

        while True:
            ch = self.peek()
            if ch == '\0':
                return Token(TokenType.ERROR, "Unterminated string", start_line, start_col)
            if ch == '"':
                self.advance()  # consume closing "
                break
            if ch == '\\':
                self.advance()
                escape = self.peek()
                if escape == 'n':
                    chars.append('\n')
                elif escape == 't':
                    chars.append('\t')
                elif escape == '\\':
                    chars.append('\\')
                elif escape == '"':
                    chars.append('"')
                else:
                    chars.append(escape)
                self.advance()
            else:
                chars.append(ch)
                self.advance()

        return Token(TokenType.STRING, ''.join(chars), start_line, start_col)

    def scan_number(self) -> Token:
        """Scan an integer or float"""
        start_line = self.line
        start_col = self.column
        chars = []

        # Optional negative sign
        if self.peek() == '-':
            chars.append(self.advance())

        # Integer part
        while self.peek().isdigit():
            chars.append(self.advance())

        # Check for float
        if self.peek() == '.' and self.peek(1).isdigit():
            chars.append(self.advance())  # consume .
            while self.peek().isdigit():
                chars.append(self.advance())

            value = float(''.join(chars))
            return Token(TokenType.FLOAT, value, start_line, start_col)

        value = int(''.join(chars))
        return Token(TokenType.INTEGER, value, start_line, start_col)

    def scan_symbol(self) -> Token:
        """Scan an identifier/symbol"""
        start_line = self.line
        start_col = self.column
        chars = []

        # Symbol can contain letters, digits, and special chars
        # But cannot start with digit (handled by number scanning)
        symbol_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-!?@#$%&*+/<>=.')

        while self.peek() in symbol_chars:
            chars.append(self.advance())

        value = ''.join(chars)

        # Check for keywords
        if value.lower() in KEYWORDS:
            token_type = KEYWORDS[value.lower()]
            # Special handling for booleans
            if token_type == TokenType.BOOLEAN:
                return Token(token_type, value.lower() == 'true', start_line, start_col)
            return Token(token_type, value.lower(), start_line, start_col)

        return Token(TokenType.SYMBOL, value, start_line, start_col)

    def tokenize(self) -> List[Token]:
        """Tokenize entire source into list of tokens"""
        self.tokens = []

        while self.pos < len(self.source):
            self.skip_whitespace()

            if self.pos >= len(self.source):
                break

            ch = self.peek()

            # String
            if ch == '"':
                self.tokens.append(self.scan_string())
                continue

            # Number (including negative)
            if ch.isdigit() or (ch == '-' and self.peek(1).isdigit()):
                self.tokens.append(self.scan_number())
                continue

            # S-expression delimiters
            if ch == '(':
                self.tokens.append(self.make_token(TokenType.LPAREN, '('))
                self.advance()
                continue

            if ch == ')':
                self.tokens.append(self.make_token(TokenType.RPAREN, ')'))
                self.advance()
                continue

            # Definition
            if ch == ':':
                self.tokens.append(self.make_token(TokenType.COLON, ':'))
                self.advance()
                continue

            # Quote (for Lisp-style quoting)
            if ch == "'":
                self.tokens.append(self.make_token(TokenType.QUOTE, "'"))
                self.advance()
                continue

            # Symbol/identifier
            if ch.isalpha() or ch in '_-!?@#$%&*+/<>=':
                self.tokens.append(self.scan_symbol())
                continue

            # Unknown character - error
            self.tokens.append(Token(TokenType.ERROR, f"Unknown character: {ch}", self.line, self.column))
            self.advance()

        # Add EOF
        self.tokens.append(Token(TokenType.EOF, None, self.line, self.column))

        return self.tokens


# =============================================================================
# Demo
# =============================================================================

def demo():
    """Demo the lexer"""
    source = '''
    ; NPC behavior script
    (belief "hero-trustworthy" 0.8)
    (desire "protect-village" 0.9)

    ; Conditional based on trust
    hero trust@ 0.5 > if
        "I will help you" say
    else
        "Prove yourself first" say
    then

    ; Memory check
    "helped-me" remembered? if
        hero trust@ 0.2 + hero trust!
    then

    : greet  ; Define a word
        "Hello, traveler!" say
    ;
    '''

    lexer = Lexer(source)
    tokens = lexer.tokenize()

    print("=== ForthLisp Lexer Demo ===\n")
    for token in tokens:
        if token.type != TokenType.EOF:
            print(f"  {token}")


if __name__ == "__main__":
    demo()
