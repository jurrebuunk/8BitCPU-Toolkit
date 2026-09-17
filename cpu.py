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
    - program counter (`pc`)
    - zero and carry/borrow flags (`Z`, `C`)
    - a small call stack for CAL/RET

    Branch condition codes:
    - 0: Z  - zero flag set
    - 1: C  - carry/borrow flag set
    - 2: NZ - zero flag clear
    - 3: NC - carry/borrow flag clear
    """

    MEMORY_SIZE = 256
    REGISTER_COUNT = 16
    STACK_LIMIT = 16

    COND_Z = 0
    COND_C = 1
    COND_NZ = 2
    COND_NC = 3

    def __init__(self, screen: object | None = None):
        self.screen = screen if screen is not None else NullScreen()
        self.registers = [0] * self.REGISTER_COUNT
        self.memory = [0] * self.MEMORY_SIZE
        self.stack: list[int] = []
        self.pc = 0
        self.flags = {"Z": 0, "C": 0}
        self.number_display = 0
        self.signed_mode = False
        self.halted = False

    def reset(self) -> None:
        self.registers = [0] * self.REGISTER_COUNT
        self.memory = [0] * self.MEMORY_SIZE
        self.stack = []
        self.pc = 0
        self.flags = {"Z": 0, "C": 0}
        self.number_display = 0
        self.signed_mode = False
        self.halted = False

    def execute(self, opcode: int, operand1: int | None = None, operand2: int | None = None, operand3: int | None = None) -> int | None:
        """Execute one decoded instruction.

        Returns a jump target for control-flow instructions, or `None` when the
        caller should advance to the next instruction.
        """

        if opcode == 0b0000:  # NOP
            return None

        if opcode == 0b0001:  # HLT
            self.screen.display_light()
            self.halted = True
            return None

        if opcode == 0b0010:  # ADD dest, left, right
            dest = self._require_register(operand1, "ADD destination")
            left = self._read_register(operand2, "ADD left operand")
            right = self._read_register(operand3, "ADD right operand")
            result = left + right
            self._write_result(dest, result, carry=result > 0xFF)
            return None

        if opcode == 0b0011:  # SUB dest, left, right
            dest = self._require_register(operand1, "SUB destination")
            left = self._read_register(operand2, "SUB left operand")
            right = self._read_register(operand3, "SUB right operand")
            result = left - right
            self._write_result(dest, result, carry=result < 0)
            return None

        if opcode == 0b0100:  # NOR dest, left, right
            dest = self._require_register(operand1, "NOR destination")
            left = self._read_register(operand2, "NOR left operand")
            right = self._read_register(operand3, "NOR right operand")
            self._write_result(dest, ~(left | right), carry=False)
            return None

        if opcode == 0b0101:  # AND dest, left, right
            dest = self._require_register(operand1, "AND destination")
            left = self._read_register(operand2, "AND left operand")
            right = self._read_register(operand3, "AND right operand")
            self._write_result(dest, left & right, carry=False)
            return None

        if opcode == 0b0110:  # XOR dest, left, right
            dest = self._require_register(operand1, "XOR destination")
            left = self._read_register(operand2, "XOR left operand")
            right = self._read_register(operand3, "XOR right operand")
            self._write_result(dest, left ^ right, carry=False)
            return None

        if opcode == 0b0111:  # RSH dest, source
            dest = self._require_register(operand1, "RSH destination")
            source = self._read_register(operand2, "RSH source operand")
            self._write_result(dest, source >> 1, carry=bool(source & 0b1))
            return None

        if opcode == 0b1000:  # LDI dest, immediate
            dest = self._require_register(operand1, "LDI destination")
            value = self._require_immediate(operand2, "LDI immediate")
            self._write_result(dest, value, carry=not 0 <= value <= 0xFF)
            return None

        if opcode == 0b1001:  # ADI dest, immediate
            dest = self._require_register(operand1, "ADI destination")
            value = self._require_immediate(operand2, "ADI immediate")
            result = self.registers[dest] + value
            self._write_result(dest, result, carry=result > 0xFF or value < 0)
            return None

        if opcode == 0b1010:  # JMP address
            return self._require_address(operand1, "JMP target")

        if opcode == 0b1011:  # BRH condition, address
            condition = self._require_immediate(operand1, "BRH condition")
            target = self._require_address(operand2, "BRH target")
            return target if self.check_condition(condition) else None

        if opcode == 0b1100:  # CAL address
            target = self._require_address(operand1, "CAL target")
            if len(self.stack) >= self.STACK_LIMIT:
                raise CPUFault("Stack overflow: cannot call because the stack is full")
            self.stack.append(self.pc + 1)
            return target

        if opcode == 0b1101:  # RET
            if not self.stack:
                raise CPUFault("Stack underflow: RET executed without a matching CAL")
            return self.stack.pop()

        if opcode == 0b1110:  # LOD dest, base_register, offset
            dest = self._require_register(operand1, "LOD destination")
            address = self._address_from_register_plus_offset(operand2, operand3, "LOD")
            self.registers[dest] = self.handle_special_load(address)
            self._set_zero_flag(self.registers[dest])
            return None

        if opcode == 0b1111:  # STR source, base_register, offset
            source = self._require_register(operand1, "STR source")
            address = self._address_from_register_plus_offset(operand2, operand3, "STR")
            value = self.registers[source]
            self.memory[address] = value
            self.handle_special_store(address, value)
            return None

        raise CPUFault(f"Unknown opcode: 0b{opcode:04b}")

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

    def _write_result(self, register: int, result: int, *, carry: bool) -> None:
        value = result & 0xFF
        self.registers[register] = value
        self.flags["Z"] = 1 if value == 0 else 0
        self.flags["C"] = 1 if carry else 0

    def _set_zero_flag(self, result: int) -> None:
        self.flags["Z"] = 1 if (result & 0xFF) == 0 else 0

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
        print(f"PC:{self.pc:04} Z:{self.flags['Z']} C:{self.flags['C']} {registers}")

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


def load_program(filename: str | Path) -> Program:
    """Load `.mc` tuple-form machine code from disk."""

    program: Program = []
    with open(filename, "r", encoding="utf-8") as file:
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


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Headless 8-bit CPU emulator")
    parser.add_argument("input_file", help="Machine-code `.mc` file to run")
    parser.add_argument("--max-steps", type=int, default=10000, help="Stop after this many instructions to catch infinite loops")
    parser.add_argument("--trace", action="store_true", help="Print CPU state before every instruction")
    parser.add_argument("--dump-memory", action="store_true", help="Print full RAM after execution")
    args = parser.parse_args(argv)

    cpu = CPU()
    program = load_program(args.input_file)
    steps = cpu.run(program, max_steps=args.max_steps, trace=args.trace)

    print(f"Executed {steps} instruction(s). Halted: {cpu.halted}. PC: {cpu.pc}")
    cpu.print_compact_state()
    print(f"Number Display: {cpu.number_display} (Signed Mode: {cpu.signed_mode})")
    if args.dump_memory:
        cpu.print_memory_grid()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
