"""
ForthLisp - Hybrid Stack-Based Language for NPC Minds

Combines:
- Forth's postfix notation and stack operations
- Lisp's S-expressions for structured data
- Homoiconicity (code is data)

Example:
    ; Define belief with confidence
    (belief "hero-trustworthy" 0.8)

    ; Stack-based conditional
    hero trust@ 0.5 > if
      "I'll help" say
    else
      "Prove yourself" say
    then
"""

from .lexer import Lexer, Token, TokenType
from .parser import Parser, ASTNode
from .vm import ForthLispVM, Opcode

__all__ = [
    'Lexer',
    'Token',
    'TokenType',
    'Parser',
    'ASTNode',
    'ForthLispVM',
    'Opcode',
]


def compile_script(source: str) -> bytes:
    """Compile ForthLisp source to bytecode"""
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    vm = ForthLispVM()
    return vm.compile(ast)
