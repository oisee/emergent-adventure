"""
ForthLisp Virtual Machine

Stack-based bytecode interpreter for NPC behavior scripts.

Features:
- Data stack for operands
- Return stack for control flow
- Dictionary of defined words
- Built-in primitives for NPC interaction
- Hooks into NPC mind state
"""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import List, Dict, Any, Optional, Callable, Tuple
import struct

from .parser import ASTNode, NodeType


class Opcode(IntEnum):
    """VM opcodes (8-bit)"""
    # Stack manipulation (0x00-0x0F)
    NOP = 0x00
    PUSH = 0x01       # Push literal to stack
    DROP = 0x02       # Drop top of stack
    DUP = 0x03        # Duplicate top
    SWAP = 0x04       # Swap top two
    OVER = 0x05       # Copy second to top
    ROT = 0x06        # Rotate top three
    PICK = 0x07       # Pick nth item

    # Arithmetic (0x10-0x1F)
    ADD = 0x10
    SUB = 0x11
    MUL = 0x12
    DIV = 0x13
    MOD = 0x14
    NEG = 0x15        # Negate top
    ABS = 0x16        # Absolute value

    # Comparison (0x20-0x2F)
    EQ = 0x20         # Equal
    NE = 0x21         # Not equal
    LT = 0x22         # Less than
    GT = 0x23         # Greater than
    LE = 0x24         # Less or equal
    GE = 0x25         # Greater or equal

    # Logic (0x30-0x3F)
    AND = 0x30
    OR = 0x31
    NOT = 0x32
    XOR = 0x33

    # Control flow (0x40-0x4F)
    JMP = 0x40        # Unconditional jump
    JZ = 0x41         # Jump if zero/false
    JNZ = 0x42        # Jump if non-zero/true
    CALL = 0x43       # Call word
    RET = 0x44        # Return from word
    HALT = 0x4F       # Stop execution

    # Belief operations (0x50-0x5F)
    BELIEF_GET = 0x50      # Get belief value
    BELIEF_SET = 0x51      # Set belief value
    BELIEF_CONF = 0x52     # Get belief confidence
    BELIEF_EXISTS = 0x53   # Check if belief exists

    # Desire operations (0x60-0x6F)
    DESIRE_GET = 0x60      # Get desire priority
    DESIRE_SET = 0x61      # Set desire priority
    DESIRE_ADD = 0x62      # Add new desire
    DESIRE_REMOVE = 0x63   # Remove desire
    DESIRE_ACTIVE = 0x64   # Check if desire is active

    # Memory operations (0x70-0x7F)
    REMEMBER = 0x70        # Store in memory
    FORGET = 0x71          # Remove from memory
    REMEMBERED = 0x72      # Check if remembered
    RECALL = 0x73          # Recall memory value

    # Relationship operations (0x80-0x8F)
    TRUST_GET = 0x80       # Get trust for target
    TRUST_SET = 0x81       # Set trust for target
    FEAR_GET = 0x82        # Get fear of target
    FEAR_SET = 0x83        # Set fear of target
    LOYALTY_GET = 0x84     # Get loyalty to target
    LOYALTY_SET = 0x85     # Set loyalty to target

    # Actions (0x90-0x9F)
    SAY = 0x90             # Output speech
    DO_ACTION = 0x91       # Perform action
    REFUSE = 0x92          # Refuse request
    AGREE = 0x93           # Agree to request
    HESITATE = 0x94        # Show hesitation

    # S-expression handlers (0xA0-0xAF)
    SEXPR_CALL = 0xA0      # Call S-expression function

    # String operations (0xB0-0xBF)
    CONCAT = 0xB0          # Concatenate strings
    STRLEN = 0xB1          # String length
    SUBSTR = 0xB2          # Substring

    # Utility (0xF0-0xFF)
    PRINT = 0xF0           # Debug print
    RANDOM = 0xF1          # Random number 0.0-1.0
    TIME = 0xF2            # Current game time/turn


@dataclass
class VMState:
    """VM execution state"""
    data_stack: List[Any] = field(default_factory=list)
    return_stack: List[int] = field(default_factory=list)
    pc: int = 0                    # Program counter
    halted: bool = False
    error: Optional[str] = None

    # Output buffer for SAY/PRINT
    output: List[str] = field(default_factory=list)

    # Action results
    actions: List[Tuple[str, Any]] = field(default_factory=list)


class ForthLispVM:
    """
    Stack-based virtual machine for ForthLisp.

    Executes compiled bytecode with hooks into NPC mind state.
    """

    def __init__(self):
        self.bytecode: bytes = b''
        self.constants: List[Any] = []
        self.words: Dict[str, int] = {}  # word name -> bytecode offset
        self.state = VMState()

        # External hooks (set by NPCMind)
        self.belief_getter: Optional[Callable[[str], Tuple[Any, float]]] = None
        self.belief_setter: Optional[Callable[[str, Any, float], None]] = None
        self.desire_getter: Optional[Callable[[str], float]] = None
        self.desire_setter: Optional[Callable[[str, float], None]] = None
        self.memory_checker: Optional[Callable[[str], bool]] = None
        self.memory_recaller: Optional[Callable[[str], Any]] = None
        self.memory_storer: Optional[Callable[[str, Any], None]] = None
        self.trust_getter: Optional[Callable[[str], float]] = None
        self.trust_setter: Optional[Callable[[str, float], None]] = None
        self.fear_getter: Optional[Callable[[str], float]] = None
        self.fear_setter: Optional[Callable[[str, float], None]] = None
        self.loyalty_getter: Optional[Callable[[str], float]] = None
        self.loyalty_setter: Optional[Callable[[str, float], None]] = None

        # Built-in S-expression handlers
        self.sexpr_handlers: Dict[str, Callable] = {
            'belief': self._handle_belief,
            'desire': self._handle_desire,
            'trust': self._handle_trust,
            'fear': self._handle_fear,
            'loyalty': self._handle_loyalty,
            'if-belief': self._handle_if_belief,
            'when': self._handle_when,
        }

    def reset(self):
        """Reset VM state"""
        self.state = VMState()

    def push(self, value: Any):
        """Push value to data stack"""
        self.state.data_stack.append(value)

    def pop(self) -> Any:
        """Pop value from data stack"""
        if not self.state.data_stack:
            self.state.error = "Stack underflow"
            return None
        return self.state.data_stack.pop()

    def peek(self, offset: int = 0) -> Any:
        """Peek at stack value"""
        idx = -(1 + offset)
        if abs(idx) > len(self.state.data_stack):
            return None
        return self.state.data_stack[idx]

    def compile(self, ast: ASTNode) -> bytes:
        """Compile AST to bytecode"""
        self.bytecode = bytearray()
        self.constants = []

        self._compile_node(ast)

        # Add HALT at end
        self.bytecode.append(Opcode.HALT)

        return bytes(self.bytecode)

    def _compile_node(self, node: ASTNode):
        """Compile single AST node"""
        if node.type == NodeType.PROGRAM:
            for child in node.children:
                self._compile_node(child)

        elif node.type == NodeType.INTEGER:
            self._emit_push(node.value)

        elif node.type == NodeType.FLOAT:
            self._emit_push(node.value)

        elif node.type == NodeType.STRING:
            self._emit_push(node.value)

        elif node.type == NodeType.BOOLEAN:
            self._emit_push(node.value)

        elif node.type == NodeType.SYMBOL:
            self._compile_symbol(node.value)

        elif node.type == NodeType.SEXPR:
            self._compile_sexpr(node)

        elif node.type == NodeType.WORD_DEF:
            self._compile_word_def(node)

        elif node.type == NodeType.IF:
            self._compile_if(node)

        elif node.type == NodeType.LOOP:
            self._compile_loop(node)

        elif node.type == NodeType.BEGIN_UNTIL:
            self._compile_begin_until(node)

        elif node.type == NodeType.BEGIN_WHILE:
            self._compile_begin_while(node)

        elif node.type == NodeType.SEQUENCE:
            for child in node.children:
                self._compile_node(child)

    def _emit_push(self, value: Any):
        """Emit PUSH instruction"""
        const_idx = len(self.constants)
        self.constants.append(value)
        self.bytecode.append(Opcode.PUSH)
        # Store constant index as 2 bytes
        self.bytecode.extend(struct.pack('<H', const_idx))

    def _emit_opcode(self, opcode: Opcode):
        """Emit single opcode"""
        self.bytecode.append(opcode)

    def _emit_jump(self, opcode: Opcode) -> int:
        """Emit jump instruction, return patch location"""
        self.bytecode.append(opcode)
        patch_loc = len(self.bytecode)
        self.bytecode.extend(struct.pack('<H', 0))  # Placeholder
        return patch_loc

    def _patch_jump(self, patch_loc: int, target: int = None):
        """Patch jump target"""
        if target is None:
            target = len(self.bytecode)
        struct.pack_into('<H', self.bytecode, patch_loc, target)

    def _compile_symbol(self, name: str):
        """Compile symbol reference"""
        # Built-in operations
        builtins = {
            # Stack
            'dup': Opcode.DUP,
            'drop': Opcode.DROP,
            'swap': Opcode.SWAP,
            'over': Opcode.OVER,
            'rot': Opcode.ROT,

            # Math
            '+': Opcode.ADD,
            '-': Opcode.SUB,
            '*': Opcode.MUL,
            '/': Opcode.DIV,
            'mod': Opcode.MOD,
            'negate': Opcode.NEG,
            'abs': Opcode.ABS,

            # Compare
            '=': Opcode.EQ,
            '<>': Opcode.NE,
            '<': Opcode.LT,
            '>': Opcode.GT,
            '<=': Opcode.LE,
            '>=': Opcode.GE,

            # Logic
            'and': Opcode.AND,
            'or': Opcode.OR,
            'not': Opcode.NOT,
            'xor': Opcode.XOR,

            # Actions
            'say': Opcode.SAY,
            'refuse': Opcode.REFUSE,
            'agree': Opcode.AGREE,
            'hesitate': Opcode.HESITATE,

            # Belief
            'belief@': Opcode.BELIEF_GET,
            'belief!': Opcode.BELIEF_SET,
            'confidence@': Opcode.BELIEF_CONF,
            'belief?': Opcode.BELIEF_EXISTS,

            # Desire
            'desire@': Opcode.DESIRE_GET,
            'desire!': Opcode.DESIRE_SET,

            # Memory
            'remember': Opcode.REMEMBER,
            'forget': Opcode.FORGET,
            'remembered?': Opcode.REMEMBERED,
            'recall': Opcode.RECALL,

            # Relationships
            'trust@': Opcode.TRUST_GET,
            'trust!': Opcode.TRUST_SET,
            'fear@': Opcode.FEAR_GET,
            'fear!': Opcode.FEAR_SET,
            'loyalty@': Opcode.LOYALTY_GET,
            'loyalty!': Opcode.LOYALTY_SET,

            # Utility
            '.': Opcode.PRINT,
            'random': Opcode.RANDOM,
            'time': Opcode.TIME,
        }

        if name in builtins:
            self._emit_opcode(builtins[name])
        elif name in self.words:
            # Call user-defined word
            self.bytecode.append(Opcode.CALL)
            self.bytecode.extend(struct.pack('<H', self.words[name]))
        else:
            # Push symbol as string (for target names)
            self._emit_push(name)

    def _compile_sexpr(self, node: ASTNode):
        """Compile S-expression"""
        if not node.children:
            return

        # First child is function name
        first = node.children[0]

        if first.type == NodeType.SYMBOL:
            func_name = first.value

            # Check for built-in S-expr handlers
            if func_name in self.sexpr_handlers:
                # Push arguments in order
                for arg in node.children[1:]:
                    self._compile_node(arg)

                # Push handler name and call
                self._emit_push(func_name)
                self._emit_push(len(node.children) - 1)  # arg count
                self._emit_opcode(Opcode.SEXPR_CALL)
            else:
                # Generic S-expr: compile all, then call
                for child in node.children:
                    self._compile_node(child)
                self._emit_push(len(node.children))
                self._emit_opcode(Opcode.SEXPR_CALL)
        else:
            # Compile all children
            for child in node.children:
                self._compile_node(child)

    def _compile_word_def(self, node: ASTNode):
        """Compile word definition"""
        name = node.value

        # Jump over the definition
        jump_patch = self._emit_jump(Opcode.JMP)

        # Record word start
        self.words[name] = len(self.bytecode)

        # Compile body
        for child in node.children:
            self._compile_node(child)

        # Return from word
        self._emit_opcode(Opcode.RET)

        # Patch jump
        self._patch_jump(jump_patch)

    def _compile_if(self, node: ASTNode):
        """Compile if/else/then"""
        # Condition is already on stack
        # Structure: [true_branch, false_branch]

        # Jump if false to else branch
        else_jump = self._emit_jump(Opcode.JZ)

        # True branch
        if node.children:
            self._compile_node(node.children[0])

        # Jump over else
        end_jump = self._emit_jump(Opcode.JMP)

        # Patch else jump
        self._patch_jump(else_jump)

        # False branch
        if len(node.children) > 1:
            self._compile_node(node.children[1])

        # Patch end jump
        self._patch_jump(end_jump)

    def _compile_loop(self, node: ASTNode):
        """Compile do...loop"""
        # Stack: limit index
        loop_start = len(self.bytecode)

        # Body
        for child in node.children:
            self._compile_node(child)

        # Increment and check
        # i = i + 1; if i < limit goto start
        self._emit_push(1)
        self._emit_opcode(Opcode.ADD)  # Increment index
        self._emit_opcode(Opcode.OVER)  # Get limit
        self._emit_opcode(Opcode.OVER)  # Get index
        self._emit_opcode(Opcode.LT)    # Check if index < limit

        # Jump back if true
        self.bytecode.append(Opcode.JNZ)
        self.bytecode.extend(struct.pack('<H', loop_start))

        # Clean up stack
        self._emit_opcode(Opcode.DROP)
        self._emit_opcode(Opcode.DROP)

    def _compile_begin_until(self, node: ASTNode):
        """Compile begin...until"""
        loop_start = len(self.bytecode)

        # Body (leaves condition on stack)
        for child in node.children:
            self._compile_node(child)

        # Jump back if false
        self.bytecode.append(Opcode.JZ)
        self.bytecode.extend(struct.pack('<H', loop_start))

    def _compile_begin_while(self, node: ASTNode):
        """Compile begin...while...repeat"""
        loop_start = len(self.bytecode)

        # Condition part
        if node.children:
            self._compile_node(node.children[0])

        # Jump out if false
        exit_jump = self._emit_jump(Opcode.JZ)

        # Body
        if len(node.children) > 1:
            self._compile_node(node.children[1])

        # Jump back to start
        self.bytecode.append(Opcode.JMP)
        self.bytecode.extend(struct.pack('<H', loop_start))

        # Patch exit
        self._patch_jump(exit_jump)

    def execute(self, bytecode: bytes = None, max_steps: int = 10000) -> VMState:
        """Execute bytecode"""
        if bytecode is not None:
            self.bytecode = bytecode

        self.reset()
        steps = 0

        while not self.state.halted and steps < max_steps:
            if self.state.pc >= len(self.bytecode):
                self.state.halted = True
                break

            opcode = self.bytecode[self.state.pc]
            self.state.pc += 1

            self._execute_opcode(opcode)
            steps += 1

            if self.state.error:
                break

        return self.state

    def _execute_opcode(self, opcode: int):
        """Execute single opcode"""
        op = Opcode(opcode) if opcode in [e.value for e in Opcode] else None

        if op == Opcode.NOP:
            pass

        elif op == Opcode.PUSH:
            idx = struct.unpack('<H', self.bytecode[self.state.pc:self.state.pc + 2])[0]
            self.state.pc += 2
            if idx < len(self.constants):
                self.push(self.constants[idx])

        elif op == Opcode.DROP:
            self.pop()

        elif op == Opcode.DUP:
            v = self.peek()
            if v is not None:
                self.push(v)

        elif op == Opcode.SWAP:
            b = self.pop()
            a = self.pop()
            self.push(b)
            self.push(a)

        elif op == Opcode.OVER:
            v = self.peek(1)
            if v is not None:
                self.push(v)

        elif op == Opcode.ROT:
            c = self.pop()
            b = self.pop()
            a = self.pop()
            self.push(b)
            self.push(c)
            self.push(a)

        # Arithmetic
        elif op == Opcode.ADD:
            b = self.pop()
            a = self.pop()
            self.push(a + b)

        elif op == Opcode.SUB:
            b = self.pop()
            a = self.pop()
            self.push(a - b)

        elif op == Opcode.MUL:
            b = self.pop()
            a = self.pop()
            self.push(a * b)

        elif op == Opcode.DIV:
            b = self.pop()
            a = self.pop()
            if b == 0:
                self.state.error = "Division by zero"
            else:
                self.push(a / b)

        elif op == Opcode.MOD:
            b = self.pop()
            a = self.pop()
            self.push(a % b)

        elif op == Opcode.NEG:
            self.push(-self.pop())

        elif op == Opcode.ABS:
            self.push(abs(self.pop()))

        # Comparison
        elif op == Opcode.EQ:
            b = self.pop()
            a = self.pop()
            self.push(a == b)

        elif op == Opcode.NE:
            b = self.pop()
            a = self.pop()
            self.push(a != b)

        elif op == Opcode.LT:
            b = self.pop()
            a = self.pop()
            self.push(a < b)

        elif op == Opcode.GT:
            b = self.pop()
            a = self.pop()
            self.push(a > b)

        elif op == Opcode.LE:
            b = self.pop()
            a = self.pop()
            self.push(a <= b)

        elif op == Opcode.GE:
            b = self.pop()
            a = self.pop()
            self.push(a >= b)

        # Logic
        elif op == Opcode.AND:
            b = self.pop()
            a = self.pop()
            self.push(a and b)

        elif op == Opcode.OR:
            b = self.pop()
            a = self.pop()
            self.push(a or b)

        elif op == Opcode.NOT:
            self.push(not self.pop())

        elif op == Opcode.XOR:
            b = self.pop()
            a = self.pop()
            self.push(bool(a) != bool(b))

        # Control flow
        elif op == Opcode.JMP:
            target = struct.unpack('<H', self.bytecode[self.state.pc:self.state.pc + 2])[0]
            self.state.pc = target

        elif op == Opcode.JZ:
            target = struct.unpack('<H', self.bytecode[self.state.pc:self.state.pc + 2])[0]
            self.state.pc += 2
            if not self.pop():
                self.state.pc = target

        elif op == Opcode.JNZ:
            target = struct.unpack('<H', self.bytecode[self.state.pc:self.state.pc + 2])[0]
            self.state.pc += 2
            if self.pop():
                self.state.pc = target

        elif op == Opcode.CALL:
            target = struct.unpack('<H', self.bytecode[self.state.pc:self.state.pc + 2])[0]
            self.state.pc += 2
            self.state.return_stack.append(self.state.pc)
            self.state.pc = target

        elif op == Opcode.RET:
            if self.state.return_stack:
                self.state.pc = self.state.return_stack.pop()
            else:
                self.state.halted = True

        elif op == Opcode.HALT:
            self.state.halted = True

        # Actions
        elif op == Opcode.SAY:
            text = self.pop()
            self.state.output.append(str(text))
            self.state.actions.append(('say', text))

        elif op == Opcode.REFUSE:
            reason = self.pop() if self.state.data_stack else "No"
            self.state.actions.append(('refuse', reason))

        elif op == Opcode.AGREE:
            response = self.pop() if self.state.data_stack else "Yes"
            self.state.actions.append(('agree', response))

        elif op == Opcode.HESITATE:
            self.state.actions.append(('hesitate', None))

        # Beliefs
        elif op == Opcode.BELIEF_GET:
            key = self.pop()
            if self.belief_getter:
                value, _ = self.belief_getter(str(key))
                self.push(value)
            else:
                self.push(None)

        elif op == Opcode.BELIEF_SET:
            value = self.pop()
            key = self.pop()
            if self.belief_setter:
                self.belief_setter(str(key), value, 1.0)

        elif op == Opcode.BELIEF_CONF:
            key = self.pop()
            if self.belief_getter:
                _, confidence = self.belief_getter(str(key))
                self.push(confidence)
            else:
                self.push(0.0)

        elif op == Opcode.BELIEF_EXISTS:
            key = self.pop()
            if self.belief_getter:
                value, _ = self.belief_getter(str(key))
                self.push(value is not None)
            else:
                self.push(False)

        # Desires
        elif op == Opcode.DESIRE_GET:
            key = self.pop()
            if self.desire_getter:
                self.push(self.desire_getter(str(key)))
            else:
                self.push(0.0)

        elif op == Opcode.DESIRE_SET:
            priority = self.pop()
            key = self.pop()
            if self.desire_setter:
                self.desire_setter(str(key), float(priority))

        # Memory
        elif op == Opcode.REMEMBERED:
            key = self.pop()
            if self.memory_checker:
                self.push(self.memory_checker(str(key)))
            else:
                self.push(False)

        elif op == Opcode.RECALL:
            key = self.pop()
            if self.memory_recaller:
                self.push(self.memory_recaller(str(key)))
            else:
                self.push(None)

        elif op == Opcode.REMEMBER:
            value = self.pop()
            key = self.pop()
            if self.memory_storer:
                self.memory_storer(str(key), value)

        elif op == Opcode.FORGET:
            key = self.pop()
            if self.memory_storer:
                self.memory_storer(str(key), None)

        # Relationships
        elif op == Opcode.TRUST_GET:
            target = self.pop()
            if self.trust_getter:
                self.push(self.trust_getter(str(target)))
            else:
                self.push(0.0)

        elif op == Opcode.TRUST_SET:
            value = self.pop()
            target = self.pop()
            if self.trust_setter:
                self.trust_setter(str(target), float(value))

        elif op == Opcode.FEAR_GET:
            target = self.pop()
            if self.fear_getter:
                self.push(self.fear_getter(str(target)))
            else:
                self.push(0.0)

        elif op == Opcode.FEAR_SET:
            value = self.pop()
            target = self.pop()
            if self.fear_setter:
                self.fear_setter(str(target), float(value))

        elif op == Opcode.LOYALTY_GET:
            target = self.pop()
            if self.loyalty_getter:
                self.push(self.loyalty_getter(str(target)))
            else:
                self.push(0.0)

        elif op == Opcode.LOYALTY_SET:
            value = self.pop()
            target = self.pop()
            if self.loyalty_setter:
                self.loyalty_setter(str(target), float(value))

        # S-expression call
        elif op == Opcode.SEXPR_CALL:
            arg_count = self.pop()
            func_name = self.pop()

            if func_name in self.sexpr_handlers:
                # Collect arguments
                args = [self.pop() for _ in range(arg_count)]
                args.reverse()

                # Call handler
                result = self.sexpr_handlers[func_name](args)
                if result is not None:
                    self.push(result)

        # Utility
        elif op == Opcode.PRINT:
            value = self.pop()
            self.state.output.append(str(value))

        elif op == Opcode.RANDOM:
            import random
            self.push(random.random())

        elif op == Opcode.TIME:
            self.push(0)  # Would be set by game engine

        else:
            self.state.error = f"Unknown opcode: {opcode:#x}"

    # S-expression handlers
    def _handle_belief(self, args: List[Any]) -> Any:
        """Handle (belief key value) or (belief key value confidence)"""
        if len(args) >= 2 and self.belief_setter:
            key = str(args[0])
            value = args[1]
            confidence = float(args[2]) if len(args) > 2 else 1.0
            self.belief_setter(key, value, confidence)
        return None

    def _handle_desire(self, args: List[Any]) -> Any:
        """Handle (desire key priority)"""
        if len(args) >= 2 and self.desire_setter:
            key = str(args[0])
            priority = float(args[1])
            self.desire_setter(key, priority)
        return None

    def _handle_trust(self, args: List[Any]) -> Any:
        """Handle (trust target value)"""
        if len(args) >= 2 and self.trust_setter:
            target = str(args[0])
            value = float(args[1])
            self.trust_setter(target, value)
        return None

    def _handle_fear(self, args: List[Any]) -> Any:
        """Handle (fear target value)"""
        if len(args) >= 2 and self.fear_setter:
            target = str(args[0])
            value = float(args[1])
            self.fear_setter(target, value)
        return None

    def _handle_loyalty(self, args: List[Any]) -> Any:
        """Handle (loyalty target value)"""
        if len(args) >= 2 and self.loyalty_setter:
            target = str(args[0])
            value = float(args[1])
            self.loyalty_setter(target, value)
        return None

    def _handle_if_belief(self, args: List[Any]) -> Any:
        """Handle (if-belief key then-action else-action)"""
        if len(args) >= 2:
            key = str(args[0])
            if self.belief_getter:
                value, conf = self.belief_getter(key)
                if value and conf > 0.5:
                    return args[1]
                elif len(args) > 2:
                    return args[2]
        return None

    def _handle_when(self, args: List[Any]) -> Any:
        """Handle (when condition action)"""
        if len(args) >= 2:
            condition = args[0]
            if condition:
                return args[1]
        return None


# =============================================================================
# Demo
# =============================================================================

def demo():
    """Demo the VM"""
    from .lexer import Lexer
    from .parser import Parser

    source = '''
    ; Simple arithmetic
    2 3 + .

    ; Conditional
    5 3 > if
        "Five is greater" say
    else
        "Three is greater" say
    then

    ; Define a word
    : double
        dup +
    ;

    ; Use the word
    7 double .
    '''

    print("=== ForthLisp VM Demo ===\n")
    print("Source:")
    print(source)
    print("\n" + "=" * 50 + "\n")

    # Compile
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    vm = ForthLispVM()
    bytecode = vm.compile(ast)

    print(f"Compiled to {len(bytecode)} bytes\n")
    print(f"Constants: {vm.constants}\n")
    print(f"Words: {vm.words}\n")

    # Execute
    state = vm.execute(bytecode)

    print("Output:")
    for line in state.output:
        print(f"  {line}")

    print(f"\nStack: {state.data_stack}")
    print(f"Actions: {state.actions}")

    if state.error:
        print(f"Error: {state.error}")


if __name__ == "__main__":
    demo()
