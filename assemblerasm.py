import argparse
import os
from dataclasses import dataclass, field

from cpu import (
    OP_ADD,
    OP_ADI,
    OP_AND,
    OP_BRH,
    OP_CAL,
    OP_HLT,
    OP_JMP,
    OP_LDI,
    OP_LOD,
    OP_MOV,
    OP_NOP,
    OP_NOR,
    OP_POP,
    OP_PUSH,
    OP_RET,
    OP_RSH,
    OP_STR,
    OP_SUB,
    OP_XOR,
    write_binary_program,
    write_memory_image,
)

opcode_map = {
    'NOP': OP_NOP,
    'HLT': OP_HLT,
    'ADD': OP_ADD,
    'SUB': OP_SUB,
    'NOR': OP_NOR,
    'AND': OP_AND,
    'XOR': OP_XOR,
    'RSH': OP_RSH,
    'LDI': OP_LDI,
    'ADI': OP_ADI,
    'JMP': OP_JMP,
    'BRH': OP_BRH,
    'CAL': OP_CAL,
    'RET': OP_RET,
    'LOD': OP_LOD,
    'STR': OP_STR,
    'MOV': OP_MOV,
    'PUSH': OP_PUSH,
    'POP': OP_POP,
}

register_map = {
    'R0': 0, 'R1': 1, 'R2': 2, 'R3': 3,
    'R4': 4, 'R5': 5, 'R6': 6, 'R7': 7,
    'R8': 8, 'R9': 9, 'R10': 10, 'R11': 11,
    'R12': 12, 'R13': 13, 'R14': 14, 'R15': 15,
}

condition_map = {
    'Z': 0,
    'C': 1,
    'NZ': 2,
    'NC': 3,
}

branch_aliases = {
    'BZ': 'Z',
    'BC': 'C',
    'BNZ': 'NZ',
    'BNC': 'NC',
}


@dataclass
class AssembledProgram:
    instructions: list[tuple[int, int | None, int | None, int | None]] = field(default_factory=list)
    memory_image: dict[int, int] = field(default_factory=dict)
    symbols: dict[str, int] = field(default_factory=dict)


def strip_comment(line):
    return line.split(';', 1)[0].strip()


def split_tokens(line):
    return line.replace(',', ' ').split()


def parse_number(value):
    try:
        return int(value, 0)
    except ValueError as exc:
        raise ValueError(f"Expected number, got '{value}'") from exc


def is_register(value):
    return value.upper() in register_map


def parse_register(value):
    upper_value = value.upper()
    if upper_value not in register_map:
        raise ValueError(f"Expected register R0-R15, got '{value}'")
    return register_map[upper_value]


def parse_value(value, symbols):
    if value in symbols:
        return symbols[value]
    upper_value = value.upper()
    if upper_value in symbols:
        return symbols[upper_value]
    return parse_number(value)


def require_range(value, name, low=0, high=254):
    if not low <= value <= high:
        raise ValueError(f"{name} must be in range {low}-{high}, got {value}")
    return value


def parse_byte(value, symbols, name="value"):
    return require_range(parse_value(value, symbols), name, 0, 254)


def parse_data_bytes(tokens, symbols):
    values = []
    for token in tokens:
        if token.startswith('"') or token.startswith("'"):
            # Basic convenience for: .byte "A"
            text = token.strip('"\'')
            if len(text) != 1:
                raise ValueError(".byte string tokens must contain exactly one character")
            values.append(ord(text))
        else:
            values.append(parse_byte(token, symbols, ".byte value"))
    return values


def parse_ascii_from_line(line):
    first_quote = line.find('"')
    last_quote = line.rfind('"')
    if first_quote == -1 or last_quote == first_quote:
        raise ValueError('.ascii expects a double-quoted string')
    return [ord(ch) for ch in line[first_quote + 1:last_quote]]


def preprocess_lines(assembly_code):
    return [(line_number, strip_comment(line)) for line_number, line in enumerate(assembly_code.splitlines(), start=1)]


def collect_symbols(lines):
    symbols = {}
    section = '.text'
    pc = 0
    data_address = 0

    for line_number, line in lines:
        if not line:
            continue

        # Constants: NAME = value
        if '=' in line and not line.startswith('.') and ':' not in line.split('=', 1)[0]:
            name, value = [part.strip() for part in line.split('=', 1)]
            if not name:
                raise ValueError(f"Line {line_number}: empty constant name")
            symbols[name] = parse_value(value, symbols)
            symbols[name.upper()] = symbols[name]
            continue

        tokens = split_tokens(line)
        if not tokens:
            continue
        directive = tokens[0].lower()

        if directive in ('.text', '.data'):
            section = directive
            continue
        if directive == '.equ':
            if len(tokens) != 3:
                raise ValueError(f"Line {line_number}: .equ expects: .equ NAME, value")
            symbols[tokens[1]] = parse_value(tokens[2], symbols)
            symbols[tokens[1].upper()] = symbols[tokens[1]]
            continue
        if directive == '.org':
            if len(tokens) != 2:
                raise ValueError(f"Line {line_number}: .org expects one address")
            if section == '.text':
                pc = parse_value(tokens[1], symbols)
            else:
                data_address = parse_value(tokens[1], symbols)
            continue

        # Label handling.
        if ':' in line:
            label, remainder = line.split(':', 1)
            label = label.strip()
            if not label:
                raise ValueError(f"Line {line_number}: empty label")
            if label in symbols or label.upper() in symbols:
                raise ValueError(f"Line {line_number}: duplicate symbol '{label}'")
            symbols[label] = pc if section == '.text' else data_address
            symbols[label.upper()] = symbols[label]
            line = remainder.strip()
            if not line:
                continue
            tokens = split_tokens(line)
            directive = tokens[0].lower()

        if directive == '.byte':
            if section != '.data':
                raise ValueError(f"Line {line_number}: .byte is only valid in .data")
            data_address += len(tokens) - 1
        elif directive == '.word':
            if section != '.data':
                raise ValueError(f"Line {line_number}: .word is only valid in .data")
            data_address += 2 * (len(tokens) - 1)
        elif directive == '.ascii':
            if section != '.data':
                raise ValueError(f"Line {line_number}: .ascii is only valid in .data")
            data_address += len(parse_ascii_from_line(line))
        elif directive.startswith('.'):
            raise ValueError(f"Line {line_number}: unknown directive '{tokens[0]}'")
        else:
            if section != '.text':
                raise ValueError(f"Line {line_number}: instructions are only valid in .text")
            mnemonic = tokens[0].upper()
            if mnemonic not in opcode_map and mnemonic not in branch_aliases:
                raise ValueError(f"Line {line_number}: unknown instruction '{tokens[0]}'")
            pc += 1

    return symbols


def build_instruction(line_number, tokens, symbols):
    mnemonic = tokens[0].upper()
    operands = tokens[1:]

    if mnemonic in branch_aliases:
        if len(operands) != 1:
            raise ValueError(f"Line {line_number}: {mnemonic} expects exactly one target")
        return (OP_BRH, condition_map[branch_aliases[mnemonic]], parse_value(operands[0], symbols), None)

    opcode = opcode_map[mnemonic]

    if mnemonic in ('NOP', 'HLT', 'RET'):
        if operands:
            raise ValueError(f"Line {line_number}: {mnemonic} does not take operands")
        return (opcode, None, None, None)

    if mnemonic in ('ADD', 'SUB', 'NOR', 'AND', 'XOR'):
        if len(operands) != 3:
            raise ValueError(f"Line {line_number}: {mnemonic} expects: {mnemonic} <dest>, <left>, <right>")
        return (opcode, parse_register(operands[0]), parse_register(operands[1]), parse_register(operands[2]))

    if mnemonic == 'RSH':
        if len(operands) != 2:
            raise ValueError(f"Line {line_number}: RSH expects: RSH <dest>, <source>")
        return (opcode, parse_register(operands[0]), parse_register(operands[1]), None)

    if mnemonic in ('LDI', 'ADI'):
        if len(operands) != 2:
            raise ValueError(f"Line {line_number}: {mnemonic} expects: {mnemonic} <register>, <immediate>")
        return (opcode, parse_register(operands[0]), parse_byte(operands[1], symbols, f"{mnemonic} immediate"), None)

    if mnemonic == 'MOV':
        if len(operands) != 2:
            raise ValueError(f"Line {line_number}: MOV expects: MOV <dest>, <source>")
        return (opcode, parse_register(operands[0]), parse_register(operands[1]), None)

    if mnemonic in ('JMP', 'CAL'):
        if len(operands) != 1:
            raise ValueError(f"Line {line_number}: {mnemonic} expects exactly one target")
        return (opcode, parse_value(operands[0], symbols), None, None)

    if mnemonic == 'BRH':
        if len(operands) != 2:
            raise ValueError(f"Line {line_number}: BRH expects: BRH <condition>, <target>")
        condition = operands[0].upper()
        if condition not in condition_map:
            known = ', '.join(condition_map)
            raise ValueError(f"Line {line_number}: unknown branch condition '{operands[0]}'. Expected one of: {known}")
        return (opcode, condition_map[condition], parse_value(operands[1], symbols), None)

    if mnemonic in ('LOD', 'STR'):
        if len(operands) not in (2, 3):
            raise ValueError(f"Line {line_number}: {mnemonic} expects: {mnemonic} <reg>, <base_reg>, [offset]")
        offset = parse_byte(operands[2], symbols, f"{mnemonic} offset") if len(operands) == 3 else 0
        return (opcode, parse_register(operands[0]), parse_register(operands[1]), offset)

    if mnemonic == 'PUSH':
        if len(operands) != 1:
            raise ValueError(f"Line {line_number}: PUSH expects one source register")
        return (opcode, parse_register(operands[0]), None, None)

    if mnemonic == 'POP':
        if len(operands) != 1:
            raise ValueError(f"Line {line_number}: POP expects one destination register")
        return (opcode, parse_register(operands[0]), None, None)

    raise ValueError(f"Line {line_number}: unknown instruction '{mnemonic}'")


def assemble_program(assembly_code):
    lines = preprocess_lines(assembly_code)
    symbols = collect_symbols(lines)
    program = AssembledProgram(symbols=symbols)
    section = '.text'
    pc = 0
    data_address = 0

    for line_number, line in lines:
        if not line:
            continue

        if '=' in line and not line.startswith('.') and ':' not in line.split('=', 1)[0]:
            continue

        tokens = split_tokens(line)
        if not tokens:
            continue
        directive = tokens[0].lower()

        if directive in ('.text', '.data'):
            section = directive
            continue
        if directive == '.equ':
            continue
        if directive == '.org':
            if len(tokens) != 2:
                raise ValueError(f"Line {line_number}: .org expects one address")
            address = parse_value(tokens[1], symbols)
            if section == '.text':
                while pc < address:
                    program.instructions.append((OP_NOP, None, None, None))
                    pc += 1
            else:
                data_address = address
            continue

        if ':' in line:
            _, line = line.split(':', 1)
            line = line.strip()
            if not line:
                continue
            tokens = split_tokens(line)
            directive = tokens[0].lower()

        if directive == '.byte':
            if section != '.data':
                raise ValueError(f"Line {line_number}: .byte is only valid in .data")
            for value in parse_data_bytes(tokens[1:], symbols):
                require_range(data_address, "data address", 0, 255)
                program.memory_image[data_address] = value
                data_address += 1
        elif directive == '.word':
            if section != '.data':
                raise ValueError(f"Line {line_number}: .word is only valid in .data")
            for token in tokens[1:]:
                value = require_range(parse_value(token, symbols), ".word value", 0, 65535)
                require_range(data_address + 1, "data address", 0, 255)
                program.memory_image[data_address] = value & 0xFF
                program.memory_image[data_address + 1] = (value >> 8) & 0xFF
                data_address += 2
        elif directive == '.ascii':
            if section != '.data':
                raise ValueError(f"Line {line_number}: .ascii is only valid in .data")
            for value in parse_ascii_from_line(line):
                require_range(data_address, "data address", 0, 255)
                program.memory_image[data_address] = value
                data_address += 1
        elif directive.startswith('.'):
            raise ValueError(f"Line {line_number}: unknown directive '{tokens[0]}'")
        else:
            if section != '.text':
                raise ValueError(f"Line {line_number}: instructions are only valid in .text")
            while pc > len(program.instructions):
                program.instructions.append((OP_NOP, None, None, None))
            program.instructions.append(build_instruction(line_number, tokens, symbols))
            pc += 1

    return program


def assemble(assembly_code):
    return assemble_program(assembly_code).instructions


def read_assembly_file(input_file):
    with open(input_file, 'r') as file:
        return file.read()


def format_opcode(opcode):
    return f"0b{opcode:04b}" if opcode <= 0x0F else f"0x{opcode:02X}"


def write_machine_code_file(output_file, machine_code):
    with open(output_file, 'w') as file:
        for instruction in machine_code:
            opcode, *operands = instruction
            opcode_str = format_opcode(opcode)
            operands_str = ', '.join(str(op) if op is not None else 'None' for op in operands)
            file.write(f"({opcode_str}, {operands_str})\n")


def main():
    parser = argparse.ArgumentParser(description='Assemble assembly code into machine code.')
    parser.add_argument('input_file', help='The input assembly file')
    parser.add_argument('--no-bin', action='store_true', help='Do not write the binary .bin machine-code file')
    args = parser.parse_args()

    input_file = args.input_file
    base_output = os.path.splitext(input_file)[0]
    mc_output = base_output + '.mc'
    bin_output = base_output + '.bin'
    mem_output = base_output + '.mem'

    assembly_code = read_assembly_file(input_file)
    program = assemble_program(assembly_code)
    write_machine_code_file(mc_output, program.instructions)
    if not args.no_bin:
        write_binary_program(bin_output, program.instructions)
    if program.memory_image:
        write_memory_image(mem_output, program.memory_image)
    elif os.path.exists(mem_output):
        os.remove(mem_output)

    outputs = [mc_output]
    if not args.no_bin:
        outputs.append(bin_output)
    if program.memory_image:
        outputs.append(mem_output)
    print(f"Assembly code from {input_file} has been assembled and written to {', '.join(outputs)}.")


if __name__ == '__main__':
    main()
