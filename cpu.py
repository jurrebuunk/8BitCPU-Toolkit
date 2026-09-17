"""Headless CPU core for the 8BitCPU Toolkit.

This module intentionally contains no GUI code. It is the reliable, testable CPU
core used by the command-line runner and by the graphical Tkinter emulator.
"""

from __future__ import annotations

import argparse
import ast
from pathlib import Path
from typing import Iterable


Instruction = tuple[int, int | None, int | None, int | None]
Program = list[Instruction]
MemoryImage = dict[int, int]


# Base 4-bit opcodes kept compatible with the original project.
OP_NOP = 0x00
OP_HLT = 0x01
OP_ADD = 0x02
OP_SUB = 0x03
OP_NOR = 0x04
OP_AND = 0x05
OP_XOR = 0x06
OP_RSH = 0x07
OP_LDI = 0x08
OP_ADI = 0x09
OP_JMP = 0x0A
OP_BRH = 0x0B
OP_CAL = 0x0C
OP_RET = 0x0D
OP_LOD = 0x0E
OP_STR = 0x0F

# Extended opcodes. These require the 32-bit binary instruction encoding, but
# also work in the human-readable `.mc` tuple format.
OP_MOV = 0x10
OP_PUSH = 0x11
OP_POP = 0x12

NONE_BYTE = 0xFF
INSTRUCTION_SIZE_BYTES = 4


class CPUFault(RuntimeError):
    """Raised when the emulated CPU hits an invalid/faulting state."""


class NullScreen:
    """No-op screen adapter used by the headless CPU runner and tests."""

    def display_light(self) -> None:
        pass

    def store_pixel_x(self, value: int) -> None:
        pass

    def store_pixel_y(self, value: int) -> None:
        pass

    def draw_pixel(self) -> None:
        pass

    def clear_pixel(self) -> None:
        pass

    def load_pixel(self) -> int:
        return 0

    def buffer_screen(self) -> None:
        pass

    def clear_screen_buffer(self) -> None:
        pass


class CPU:
    """A small 8-bit CPU emulator.

    CPU state:
    - 16 general-purpose 8-bit registers: R0-R15
    - 256 bytes of RAM
    - program counter (`pc`) pointing at an instruction index
    - zero and carry/borrow flags (`Z`, `C`)
    - a RAM-backed downward-growing stack

    Branch condition codes:
    - 0: Z  - zero flag set
    - 1: C  - carry/borrow flag set
    - 2: NZ - zero flag clear
    - 3: NC - carry/borrow flag clear
    """

    MEMORY_SIZE = 256
    REGISTER_COUNT = 16
    STACK_START = 239  # Keep 240-255 available for memory-mapped I/O.

    COND_Z = 0
    COND_C = 1
    COND_NZ = 2
    COND_NC = 3

    def __init__(self, screen: object | None = None):
        self.screen = screen if screen is not None else NullScreen()
        self.registers = [0] * self.REGISTER_COUNT
        self.memory = [0] * self.MEMORY_SIZE
        self.pc = 0
        self.sp = self.STACK_START
        self.flags = {"Z": 0, "C": 0}
        self.number_display = 0
        self.signed_mode = False
        self.halted = False

    @property
    def stack_depth(self) -> int:
        return self.STACK_START - self.sp

    @property
    def stack(self) -> list[int]:
        """Debug view of the RAM-backed stack, top first.

        Kept as a property so older tests/tools can still inspect `cpu.stack`
        without the emulator using a Python list for actual call behavior.
        """

        return [self.memory[address] for address in range(self.sp + 1, self.STACK_START + 1)]

    def reset(self) -> None:
        self.registers = [0] * self.REGISTER_COUNT
        self.memory = [0] * self.MEMORY_SIZE
        self.pc = 0
        self.sp = self.STACK_START
        self.flags = {"Z": 0, "C": 0}
        self.number_display = 0
        self.signed_mode = False
        self.halted = False

    def load_memory_image(self, memory_image: MemoryImage) -> None:
        for address, value in memory_image.items():
            if not 0 <= address < self.MEMORY_SIZE:
                raise CPUFault(f"Memory image address out of range: {address}")
            if not 0 <= value <= 0xFF:
                raise CPUFault(f"Memory image value out of range at {address}: {value}")
            self.memory[address] = value

    def execute(self, opcode: int, operand1: int | None = None, operand2: int | None = None, operand3: int | None = None) -> int | None:
        """Execute one decoded instruction.

        Returns a jump target for control-flow instructions, or `None` when the
        caller should advance to the next instruction.
        """

        if opcode == OP_NOP:
            return None

        if opcode == OP_HLT:
            self.screen.display_light()
            self.halted = True
            return None

        if opcode == OP_ADD:  # ADD dest, left, right
            dest = self._require_register(operand1, "ADD destination")
            left = self._read_register(operand2, "ADD left operand")
            right = self._read_register(operand3, "ADD right operand")
            result = left + right
            self._write_result(dest, result, carry=result > 0xFF)
            return None

        if opcode == OP_SUB:  # SUB dest, left, right
            dest = self._require_register(operand1, "SUB destination")
            left = self._read_register(operand2, "SUB left operand")
            right = self._read_register(operand3, "SUB right operand")
            result = left - right
            self._write_result(dest, result, carry=result < 0)
            return None

        if opcode == OP_NOR:  # NOR dest, left, right
            dest = self._require_register(operand1, "NOR destination")
            left = self._read_register(operand2, "NOR left operand")
            right = self._read_register(operand3, "NOR right operand")
            self._write_result(dest, ~(left | right), carry=False)
            return None

        if opcode == OP_AND:  # AND dest, left, right
            dest = self._require_register(operand1, "AND destination")
            left = self._read_register(operand2, "AND left operand")
            right = self._read_register(operand3, "AND right operand")
            self._write_result(dest, left & right, carry=False)
            return None

        if opcode == OP_XOR:  # XOR dest, left, right
            dest = self._require_register(operand1, "XOR destination")
            left = self._read_register(operand2, "XOR left operand")
            right = self._read_register(operand3, "XOR right operand")
            self._write_result(dest, left ^ right, carry=False)
            return None

        if opcode == OP_RSH:  # RSH dest, source
            dest = self._require_register(operand1, "RSH destination")
            source = self._read_register(operand2, "RSH source operand")
            self._write_result(dest, source >> 1, carry=bool(source & 0b1))
            return None

        if opcode == OP_LDI:  # LDI dest, immediate
            dest = self._require_register(operand1, "LDI destination")
            value = self._require_immediate(operand2, "LDI immediate")
            self._write_result(dest, value, carry=not 0 <= value <= 0xFF)
            return None

        if opcode == OP_ADI:  # ADI dest, immediate
            dest = self._require_register(operand1, "ADI destination")
            value = self._require_immediate(operand2, "ADI immediate")
            result = self.registers[dest] + value
            self._write_result(dest, result, carry=result > 0xFF or value < 0)
            return None

        if opcode == OP_JMP:  # JMP address
            return self._require_address(operand1, "JMP target")

        if opcode == OP_BRH:  # BRH condition, address
            condition = self._require_immediate(operand1, "BRH condition")
            target = self._require_address(operand2, "BRH target")
            return target if self.check_condition(condition) else None

        if opcode == OP_CAL:  # CAL address
            target = self._require_address(operand1, "CAL target")
            self._push_byte(self.pc + 1)
            return target

        if opcode == OP_RET:
            return self._pop_byte("RET")

        if opcode == OP_LOD:  # LOD dest, base_register, offset
            dest = self._require_register(operand1, "LOD destination")
            address = self._address_from_register_plus_offset(operand2, operand3, "LOD")
            self.registers[dest] = self.handle_special_load(address)
            self._write_result(dest, self.registers[dest], carry=False)
            return None

        if opcode == OP_STR:  # STR source, base_register, offset
            source = self._require_register(operand1, "STR source")
            address = self._address_from_register_plus_offset(operand2, operand3, "STR")
            value = self.registers[source]
            self.memory[address] = value
            self.handle_special_store(address, value)
            return None

        if opcode == OP_MOV:  # MOV dest, source
            dest = self._require_register(operand1, "MOV destination")
            value = self._read_register(operand2, "MOV source")
            self._write_result(dest, value, carry=False)
            return None

        if opcode == OP_PUSH:  # PUSH source
            source = self._require_register(operand1, "PUSH source")
            self._push_byte(self.registers[source])
            return None

        if opcode == OP_POP:  # POP destination
            dest = self._require_register(operand1, "POP destination")
            self._write_result(dest, self._pop_byte("POP"), carry=False)
            return None

        raise CPUFault(f"Unknown opcode: 0x{opcode:02X}")

    def step(self, program: Program) -> bool:
        """Execute one fetch/decode/execute step.

        Returns `True` when an instruction executed, or `False` when the CPU was
        already halted or the program counter is past the end of the program.
        """

        if self.halted or self.pc >= len(program):
            return False
        if self.pc < 0:
            raise CPUFault(f"Program counter moved before start of program: {self.pc}")

        opcode, operand1, operand2, operand3 = program[self.pc]
        next_pc = self.execute(opcode, operand1, operand2, operand3)
        self.pc = next_pc if next_pc is not None else self.pc + 1
        return True

    def run(self, program: Program, *, max_steps: int = 10000, trace: bool = False) -> int:
        """Run until HLT, program end, or `max_steps` is reached.

        Returns the number of executed instructions.
        """

        steps = 0
        while not self.halted and 0 <= self.pc < len(program):
            if steps >= max_steps:
                raise CPUFault(f"Step limit reached ({max_steps}); possible infinite loop")
            if trace:
                self.print_compact_state()
            self.step(program)
            steps += 1
        return steps

    def check_condition(self, cond: int) -> bool:
        if cond == self.COND_Z:
            return self.flags["Z"] == 1
        if cond == self.COND_C:
            return self.flags["C"] == 1
        if cond == self.COND_NZ:
            return self.flags["Z"] == 0
        if cond == self.COND_NC:
            return self.flags["C"] == 0
        raise CPUFault(f"Unknown branch condition code: {cond}")

    def handle_special_load(self, address: int) -> int:
        if address == 244:  # Load Pixel
            return self.screen.load_pixel() & 0xFF
        return self.memory[address]

    def handle_special_store(self, address: int, value: int) -> None:
        if address == 240:  # Store Pixel X
            self.screen.store_pixel_x(value)
        elif address == 241:  # Store Pixel Y
            self.screen.store_pixel_y(value)
        elif address == 242:  # Draw Pixel
            self.screen.draw_pixel()
        elif address == 243:  # Clear Pixel
            self.screen.clear_pixel()
        elif address == 245:  # Buffer Screen
            self.screen.buffer_screen()
        elif address == 246:  # Clear Screen Buffer
            self.screen.clear_screen_buffer()
        elif address == 250:  # Show Number
            self.number_display = value
        elif address == 251:  # Clear Number
            self.number_display = 0
        elif address == 252:  # Signed Mode
            self.signed_mode = True
        elif address == 253:  # Unsigned Mode
            self.signed_mode = False

    def load_program(self, filename: str | Path) -> Program:
        return load_program(filename)

    def _push_byte(self, value: int) -> None:
        if self.sp < 0:
            raise CPUFault("Stack overflow: stack pointer moved below RAM address 0")
        self.memory[self.sp] = value & 0xFF
        self.sp -= 1

    def _pop_byte(self, instruction: str) -> int:
        if self.sp >= self.STACK_START:
            raise CPUFault(f"Stack underflow: {instruction} executed with an empty stack")
        self.sp += 1
        return self.memory[self.sp]

    def _write_result(self, register: int, result: int, *, carry: bool) -> None:
        value = result & 0xFF
        self.registers[register] = value
        self.flags["Z"] = 1 if value == 0 else 0
        self.flags["C"] = 1 if carry else 0

    def _require_register(self, value: int | None, name: str) -> int:
        if value is None or not 0 <= value < self.REGISTER_COUNT:
            raise CPUFault(f"{name} must be register R0-R15, got {value}")
        return value

    def _read_register(self, value: int | None, name: str) -> int:
        return self.registers[self._require_register(value, name)]

    def _require_immediate(self, value: int | None, name: str) -> int:
        if value is None:
            raise CPUFault(f"{name} is required")
        return value

    def _require_address(self, value: int | None, name: str) -> int:
        if value is None or value < 0:
            raise CPUFault(f"{name} must be a non-negative program address, got {value}")
        return value

    def _address_from_register_plus_offset(self, base_register: int | None, offset: int | None, instruction: str) -> int:
        base = self._read_register(base_register, f"{instruction} base register")
        address = base + (offset if offset is not None else 0)
        if not 0 <= address < self.MEMORY_SIZE:
            raise CPUFault(f"{instruction} memory address out of range: {address}")
        return address

    def print_compact_state(self) -> None:
        registers = " ".join(f"R{i}:{value:02X}" for i, value in enumerate(self.registers))
        print(f"PC:{self.pc:04} SP:{self.sp:02X} Z:{self.flags['Z']} C:{self.flags['C']} {registers}")

    def print_memory_grid(self) -> None:
        print("RAM (256 bytes):")
        print("     " + " ".join(f"{i:02X}" for i in range(16)))
        for row in range(16):
            row_values = " ".join(f"{self.memory[row * 16 + col]:02X}" for col in range(16))
            print(f"{row * 16:02X}: {row_values}")
        print()
        self.print_compact_state()
        print(f"Number Display: {self.number_display} (Signed Mode: {self.signed_mode})")


# Backwards-compatible alias for older code/comments that used ALU.
ALU = CPU


def encode_instruction(instruction: Instruction) -> bytes:
    """Encode one instruction as four bytes: opcode, op1, op2, op3.

    `None` operands are encoded as 0xFF. This is intentionally simple and easy
    to inspect with a hex editor, while still being real binary machine code.
    """

    encoded = []
    for part in instruction:
        if part is None:
            encoded.append(NONE_BYTE)
        elif 0 <= part <= 0xFE:
            encoded.append(part)
        else:
            raise CPUFault(f"Instruction value out of binary encoding range 0-254: {part}")
    return bytes(encoded)


def decode_instruction(data: bytes) -> Instruction:
    if len(data) != INSTRUCTION_SIZE_BYTES:
        raise CPUFault(f"Binary instruction must be {INSTRUCTION_SIZE_BYTES} bytes")
    values = [None if byte == NONE_BYTE else byte for byte in data]
    opcode = values[0]
    if opcode is None:
        raise CPUFault("Binary instruction cannot have an empty opcode")
    return (opcode, values[1], values[2], values[3])


def write_binary_program(filename: str | Path, program: Program) -> None:
    with open(filename, "wb") as file:
        for instruction in program:
            file.write(encode_instruction(instruction))


def load_binary_program(filename: str | Path) -> Program:
    data = Path(filename).read_bytes()
    if len(data) % INSTRUCTION_SIZE_BYTES != 0:
        raise CPUFault(f"Binary program size must be a multiple of {INSTRUCTION_SIZE_BYTES} bytes")
    return [decode_instruction(data[i:i + INSTRUCTION_SIZE_BYTES]) for i in range(0, len(data), INSTRUCTION_SIZE_BYTES)]


def load_program(filename: str | Path) -> Program:
    """Load a machine-code program from `.mc` text tuples or `.bin` bytes."""

    path = Path(filename)
    if path.suffix == ".bin":
        return load_binary_program(path)

    program: Program = []
    with open(path, "r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                instruction = ast.literal_eval(stripped)
            except (SyntaxError, ValueError) as exc:
                raise CPUFault(f"Invalid machine-code syntax on line {line_number}: {stripped}") from exc
            if not isinstance(instruction, tuple) or len(instruction) != 4:
                raise CPUFault(f"Instruction on line {line_number} must be a 4-item tuple")
            opcode, operand1, operand2, operand3 = instruction
            if not isinstance(opcode, int):
                raise CPUFault(f"Opcode on line {line_number} must be an integer")
            operands = []
            for operand in (operand1, operand2, operand3):
                if operand is not None and not isinstance(operand, int):
                    raise CPUFault(f"Operands on line {line_number} must be integers or None")
                operands.append(operand)
            program.append((opcode, operands[0], operands[1], operands[2]))
    return program


def write_memory_image(filename: str | Path, memory_image: MemoryImage) -> None:
    with open(filename, "w", encoding="utf-8") as file:
        for address in sorted(memory_image):
            file.write(f"{address}: {memory_image[address]}\n")


def load_memory_image(filename: str | Path) -> MemoryImage:
    path = Path(filename)
    if not path.exists():
        return {}
    memory_image: MemoryImage = {}
    with open(path, "r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            stripped = line.split(";", 1)[0].strip()
            if not stripped:
                continue
            if ":" not in stripped:
                raise CPUFault(f"Invalid memory image syntax on line {line_number}: {line.strip()}")
            address_text, value_text = stripped.split(":", 1)
            address = int(address_text.strip(), 0)
            value = int(value_text.strip(), 0)
            if not 0 <= address < CPU.MEMORY_SIZE or not 0 <= value <= 0xFF:
                raise CPUFault(f"Memory image line {line_number} out of range")
            memory_image[address] = value
    return memory_image


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Headless 8-bit CPU emulator")
    parser.add_argument("input_file", help="Machine-code `.mc` or binary `.bin` file to run")
    parser.add_argument("--memory", help="Optional memory image file. Defaults to matching .mem if present")
    parser.add_argument("--max-steps", type=int, default=10000, help="Stop after this many instructions to catch infinite loops")
    parser.add_argument("--trace", action="store_true", help="Print CPU state before every instruction")
    parser.add_argument("--dump-memory", action="store_true", help="Print full RAM after execution")
    args = parser.parse_args(argv)

    input_path = Path(args.input_file)
    memory_path = Path(args.memory) if args.memory else input_path.with_suffix(".mem")

    cpu = CPU()
    cpu.load_memory_image(load_memory_image(memory_path))
    program = load_program(input_path)
    steps = cpu.run(program, max_steps=args.max_steps, trace=args.trace)

    print(f"Executed {steps} instruction(s). Halted: {cpu.halted}. PC: {cpu.pc}")
    cpu.print_compact_state()
    print(f"Number Display: {cpu.number_display} (Signed Mode: {cpu.signed_mode})")
    if args.dump_memory:
        cpu.print_memory_grid()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
