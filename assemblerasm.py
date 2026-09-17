import argparse
import os

opcode_map = {
    'NOP': 0b0000,
    'HLT': 0b0001,
    'ADD': 0b0010,
    'SUB': 0b0011,
    'NOR': 0b0100,
    'AND': 0b0101,
    'XOR': 0b0110,
    'RSH': 0b0111,
    'LDI': 0b1000,
    'ADI': 0b1001,
    'JMP': 0b1010,
    'BRH': 0b1011,
    'CAL': 0b1100,
    'RET': 0b1101,
    'LOD': 0b1110,
    'STR': 0b1111,
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


def strip_comment(line):
    return line.split(';', 1)[0].strip()


def split_instruction(line):
    return line.replace(',', ' ').split()


def parse_number(value):
    try:
        return int(value, 0)
    except ValueError as exc:
        raise ValueError(f"Expected number, got '{value}'") from exc


def parse_register_or_number(value):
    upper_value = value.upper()
    if upper_value in register_map:
        return register_map[upper_value]
    return parse_number(value)


def parse_target(value, labels):
    if value in labels:
        return labels[value]
    upper_value = value.upper()
    if upper_value in register_map:
        return register_map[upper_value]
    return parse_number(value)


def collect_labels(lines):
    labels = {}
    pc = 0
    for line_number, raw_line in enumerate(lines, start=1):
        line = strip_comment(raw_line)
        if not line:
            continue
        if ':' in line:
            label, line = line.split(':', 1)
            label = label.strip()
            if not label:
                raise ValueError(f"Line {line_number}: empty label")
            if label in labels:
                raise ValueError(f"Line {line_number}: duplicate label '{label}'")
            labels[label] = pc
            line = line.strip()
        if line:
            pc += 1
    return labels


def assemble(assembly_code):
    lines = assembly_code.strip().split('\n')
    machine_code = []
    labels = collect_labels(lines)

    for line_number, raw_line in enumerate(lines, start=1):
        line = strip_comment(raw_line)
        if not line:
            continue
        if ':' in line:
            _, line = line.split(':', 1)
            line = line.strip()
        if not line:
            continue

        parts = split_instruction(line)
        mnemonic = parts[0].upper()
        if mnemonic not in opcode_map:
            raise ValueError(f"Line {line_number}: unknown instruction '{parts[0]}'")
        opcode = opcode_map[mnemonic]
        operands = parts[1:]

        try:
            if mnemonic == 'BRH':
                if len(operands) != 2:
                    raise ValueError("BRH expects: BRH <condition>, <target>")
                condition = operands[0].upper()
                if condition not in condition_map:
                    known = ', '.join(condition_map)
                    raise ValueError(f"Unknown branch condition '{operands[0]}'. Expected one of: {known}")
                target = parse_target(operands[1], labels)
                machine_code.append((opcode, condition_map[condition], target, None))
            elif mnemonic in ('JMP', 'CAL'):
                if len(operands) != 1:
                    raise ValueError(f"{mnemonic} expects exactly one target")
                target = parse_target(operands[0], labels)
                machine_code.append((opcode, target, None, None))
            elif mnemonic == 'RET' or mnemonic == 'HLT' or mnemonic == 'NOP':
                if operands:
                    raise ValueError(f"{mnemonic} does not take operands")
                machine_code.append((opcode, None, None, None))
            else:
                ops = [parse_register_or_number(op) for op in operands]
                while len(ops) < 3:
                    ops.append(None)
                if len(ops) > 3:
                    raise ValueError(f"{mnemonic} expects at most three operands")
                machine_code.append((opcode, *ops))
        except ValueError as exc:
            raise ValueError(f"Line {line_number}: {exc}") from exc

    return machine_code


def read_assembly_file(input_file):
    with open(input_file, 'r') as file:
        return file.read()


def write_machine_code_file(output_file, machine_code):
    with open(output_file, 'w') as file:
        for instruction in machine_code:
            opcode, *operands = instruction
            opcode_str = f"0b{opcode:04b}"
            operands_str = ', '.join(str(op) if op is not None else 'None' for op in operands)
            file.write(f"({opcode_str}, {operands_str})\n")


def main():
    parser = argparse.ArgumentParser(description='Assemble assembly code into machine code.')
    parser.add_argument('input_file', help='The input assembly file')
    args = parser.parse_args()

    input_file = args.input_file
    output_file = os.path.splitext(input_file)[0] + '.mc'

    assembly_code = read_assembly_file(input_file)
    machine_code = assemble(assembly_code)
    write_machine_code_file(output_file, machine_code)

    print(f"Assembly code from {input_file} has been assembled and written to {output_file}.")


if __name__ == '__main__':
    main()
