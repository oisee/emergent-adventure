"""
ForthLisp Parser

Parses tokens into an Abstract Syntax Tree (AST).

The AST represents:
- S-expressions as lists
- Forth words as sequences
- Control structures (if/else/then, loops)
- Word definitions (: name ... ;)
"""

from dataclasses import dataclass, field
from enum import IntEnum, auto
from typing import List, Optional, Union, Any

from .lexer import Token, TokenType, Lexer


class NodeType(IntEnum):
    """AST node types"""
    # Literals
    INTEGER = auto()
    FLOAT = auto()
    STRING = auto()
    BOOLEAN = auto()
    SYMBOL = auto()

    # Compound
    SEXPR = auto()      # (fn arg1 arg2 ...)
    SEQUENCE = auto()   # sequence of words/expressions
    QUOTE = auto()      # 'expr

    # Control flow
    IF = auto()         # if ... else ... then
    LOOP = auto()       # do ... loop
    BEGIN_UNTIL = auto()  # begin ... until
    BEGIN_WHILE = auto()  # begin ... while ... repeat

    # Definition
    WORD_DEF = auto()   # : name body ;

    # Special
    PROGRAM = auto()    # Top-level program


@dataclass
class ASTNode:
    """AST node"""
    type: NodeType
    value: Any = None
    children: List['ASTNode'] = field(default_factory=list)
    line: int = 0
    column: int = 0

    def __repr__(self):
        if self.children:
            return f"({self.type.name} {self.value} [{len(self.children)} children])"
        return f"({self.type.name} {self.value!r})"

    def pretty_print(self, indent: int = 0) -> str:
        """Pretty print the AST"""
        prefix = "  " * indent
        lines = [f"{prefix}{self.type.name}"]

        if self.value is not None:
            lines[0] += f": {self.value!r}"

        for child in self.children:
            lines.append(child.pretty_print(indent + 1))

        return '\n'.join(lines)


class ParseError(Exception):
    """Parse error with location"""
    def __init__(self, message: str, token: Token):
        super().__init__(f"{message} at line {token.line}, column {token.column}")
        self.token = token


class Parser:
    """
    Parser for ForthLisp.

    Grammar (informal):
        program     := (item)*
        item        := sexpr | word_def | if_stmt | loop_stmt | atom
        sexpr       := '(' item* ')'
        word_def    := ':' SYMBOL item* ';'
        if_stmt     := 'if' item* ('else' item*)? 'then'
        loop_stmt   := 'do' item* 'loop'
                     | 'begin' item* 'until'
                     | 'begin' item* 'while' item* 'repeat'
        atom        := INTEGER | FLOAT | STRING | BOOLEAN | SYMBOL
    """

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self, offset: int = 0) -> Token:
        """Look at token without consuming"""
        idx = self.pos + offset
        if idx >= len(self.tokens):
            return self.tokens[-1]  # Return EOF
        return self.tokens[idx]

    def advance(self) -> Token:
        """Consume and return current token"""
        token = self.peek()
        if token.type != TokenType.EOF:
            self.pos += 1
        return token

    def check(self, *types: TokenType) -> bool:
        """Check if current token is one of the types"""
        return self.peek().type in types

    def match(self, *types: TokenType) -> Optional[Token]:
        """Consume token if it matches, else return None"""
        if self.check(*types):
            return self.advance()
        return None

    def expect(self, type: TokenType, message: str) -> Token:
        """Consume token of expected type or raise error"""
        if self.check(type):
            return self.advance()
        raise ParseError(message, self.peek())

    def parse(self) -> ASTNode:
        """Parse entire program"""
        items = []

        while not self.check(TokenType.EOF):
            item = self.parse_item()
            if item:
                items.append(item)

        return ASTNode(NodeType.PROGRAM, children=items)

    def parse_item(self) -> Optional[ASTNode]:
        """Parse a single item"""
        token = self.peek()

        # S-expression
        if self.check(TokenType.LPAREN):
            return self.parse_sexpr()

        # Word definition
        if self.check(TokenType.COLON):
            return self.parse_word_def()

        # Quote
        if self.check(TokenType.QUOTE):
            return self.parse_quote()

        # Control flow
        if self.check(TokenType.IF):
            return self.parse_if()

        if self.check(TokenType.DO):
            return self.parse_do_loop()

        if self.check(TokenType.BEGIN):
            return self.parse_begin()

        # Atoms
        if self.check(TokenType.INTEGER):
            token = self.advance()
            return ASTNode(NodeType.INTEGER, token.value, line=token.line, column=token.column)

        if self.check(TokenType.FLOAT):
            token = self.advance()
            return ASTNode(NodeType.FLOAT, token.value, line=token.line, column=token.column)

        if self.check(TokenType.STRING):
            token = self.advance()
            return ASTNode(NodeType.STRING, token.value, line=token.line, column=token.column)

        if self.check(TokenType.BOOLEAN):
            token = self.advance()
            return ASTNode(NodeType.BOOLEAN, token.value, line=token.line, column=token.column)

        if self.check(TokenType.SYMBOL):
            token = self.advance()
            return ASTNode(NodeType.SYMBOL, token.value, line=token.line, column=token.column)

        # Skip terminators (they're handled by containing structures)
        if self.check(TokenType.ELSE, TokenType.THEN, TokenType.LOOP,
                     TokenType.UNTIL, TokenType.WHILE, TokenType.REPEAT,
                     TokenType.SEMICOLON, TokenType.RPAREN):
            return None

        # Error on unknown
        if self.check(TokenType.ERROR):
            token = self.advance()
            raise ParseError(f"Lexer error: {token.value}", token)

        return None

    def parse_sexpr(self) -> ASTNode:
        """Parse S-expression: (fn arg1 arg2 ...)"""
        lparen = self.expect(TokenType.LPAREN, "Expected '('")
        items = []

        while not self.check(TokenType.RPAREN, TokenType.EOF):
            item = self.parse_item()
            if item:
                items.append(item)

        self.expect(TokenType.RPAREN, "Expected ')' to close S-expression")

        return ASTNode(NodeType.SEXPR, children=items, line=lparen.line, column=lparen.column)

    def parse_word_def(self) -> ASTNode:
        """Parse word definition: : name body ;"""
        colon = self.expect(TokenType.COLON, "Expected ':'")
        name_token = self.expect(TokenType.SYMBOL, "Expected word name after ':'")

        body = []
        while not self.check(TokenType.SEMICOLON, TokenType.EOF):
            item = self.parse_item()
            if item:
                body.append(item)

        self.expect(TokenType.SEMICOLON, "Expected ';' to end word definition")

        return ASTNode(
            NodeType.WORD_DEF,
            value=name_token.value,
            children=body,
            line=colon.line,
            column=colon.column
        )

    def parse_quote(self) -> ASTNode:
        """Parse quoted expression: 'expr"""
        quote = self.expect(TokenType.QUOTE, "Expected quote")
        item = self.parse_item()

        if item is None:
            raise ParseError("Expected expression after quote", quote)

        return ASTNode(NodeType.QUOTE, children=[item], line=quote.line, column=quote.column)

    def parse_if(self) -> ASTNode:
        """Parse if statement: if ... else ... then"""
        if_token = self.expect(TokenType.IF, "Expected 'if'")

        # Parse true branch
        true_branch = []
        while not self.check(TokenType.ELSE, TokenType.THEN, TokenType.EOF):
            item = self.parse_item()
            if item:
                true_branch.append(item)

        # Optional else branch
        false_branch = []
        if self.match(TokenType.ELSE):
            while not self.check(TokenType.THEN, TokenType.EOF):
                item = self.parse_item()
                if item:
                    false_branch.append(item)

        self.expect(TokenType.THEN, "Expected 'then' to end if statement")

        # Structure: children[0] = true branch sequence, children[1] = false branch sequence
        return ASTNode(
            NodeType.IF,
            children=[
                ASTNode(NodeType.SEQUENCE, children=true_branch),
                ASTNode(NodeType.SEQUENCE, children=false_branch)
            ],
            line=if_token.line,
            column=if_token.column
        )

    def parse_do_loop(self) -> ASTNode:
        """Parse do loop: do ... loop"""
        do_token = self.expect(TokenType.DO, "Expected 'do'")

        body = []
        while not self.check(TokenType.LOOP, TokenType.EOF):
            item = self.parse_item()
            if item:
                body.append(item)

        self.expect(TokenType.LOOP, "Expected 'loop' to end do loop")

        return ASTNode(
            NodeType.LOOP,
            children=body,
            line=do_token.line,
            column=do_token.column
        )

    def parse_begin(self) -> ASTNode:
        """Parse begin loop: begin ... until OR begin ... while ... repeat"""
        begin_token = self.expect(TokenType.BEGIN, "Expected 'begin'")

        # First part of body
        body1 = []
        while not self.check(TokenType.UNTIL, TokenType.WHILE, TokenType.EOF):
            item = self.parse_item()
            if item:
                body1.append(item)

        # begin ... until
        if self.match(TokenType.UNTIL):
            return ASTNode(
                NodeType.BEGIN_UNTIL,
                children=body1,
                line=begin_token.line,
                column=begin_token.column
            )

        # begin ... while ... repeat
        if self.match(TokenType.WHILE):
            body2 = []
            while not self.check(TokenType.REPEAT, TokenType.EOF):
                item = self.parse_item()
                if item:
                    body2.append(item)

            self.expect(TokenType.REPEAT, "Expected 'repeat' to end begin-while loop")

            return ASTNode(
                NodeType.BEGIN_WHILE,
                children=[
                    ASTNode(NodeType.SEQUENCE, children=body1),  # condition
                    ASTNode(NodeType.SEQUENCE, children=body2)   # body
                ],
                line=begin_token.line,
                column=begin_token.column
            )

        raise ParseError("Expected 'until' or 'while' after 'begin'", self.peek())


# =============================================================================
# Demo
# =============================================================================

def demo():
    """Demo the parser"""
    source = '''
    ; NPC behavior script
    (belief "hero-trustworthy" 0.8)
    (desire "protect-village" 0.9)

    ; Conditional
    hero trust@ 0.5 > if
        "I will help you" say
    else
        "Prove yourself first" say
    then

    ; Define a greeting word
    : greet
        "Hello, traveler!" say
        hero trust@ 0.1 + hero trust!
    ;

    ; Loop example
    10 0 do
        i .
    loop
    '''

    print("=== ForthLisp Parser Demo ===\n")
    print("Source:")
    print(source)
    print("\n" + "=" * 50 + "\n")

    lexer = Lexer(source)
    tokens = lexer.tokenize()

    parser = Parser(tokens)
    try:
        ast = parser.parse()
        print("AST:")
        print(ast.pretty_print())
    except ParseError as e:
        print(f"Parse error: {e}")


if __name__ == "__main__":
    demo()
