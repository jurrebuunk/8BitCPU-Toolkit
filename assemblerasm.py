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


def assemble(assembly_code):
    lines = assembly_code.strip().split('\n')
    machine_code = []
    labels = {}
    pc = 0

    # First pass: handle labels
    for line in lines:
        line = line.split(';')[0].strip()  # Remove comments
        if ':' in line:
            label, instruction = line.split(':')
            labels[label.strip()] = pc
            line = instruction.strip()
        if line:
            pc += 1

    # Second pass: generate machine code
    pc = 0  # Reset program counter for the second pass
    for line in lines:
        line = line.split(';')[0].strip()  # Remove comments
        if ':' in line:
            _, line = line.split(':')
        line = line.strip()
        if not line:
            continue

        parts = line.split()
        opcode = opcode_map[parts[0]]
        operands = [op.strip(',') for op in parts[1:]]  # Remove commas

        if parts[0] == 'BRH':
            cond = 0 if operands[0] == 'Z' else 1  # Example condition mapping
            if operands[1] in labels:
                address = labels[operands[1]]
                machine_code.append((opcode, cond, address, None))
            else:
                reg = register_map[operands[1]]
                machine_code.append((opcode, cond, reg, None))
        elif parts[0] == 'JMP':
            if operands[0] in labels:
                address = labels[operands[0]]
            else:
                address = int(operands[0])
            machine_code.append((opcode, address, None, None))
        elif parts[0] == 'CAL':
            if operands[0] in labels:
                address = labels[operands[0]]
            else:
                address = int(operands[0])
            machine_code.append((opcode, address, None, None))
        elif parts[0] == 'RET':
            machine_code.append((opcode, None, None, None))
        else:
            ops = [register_map[op] if op in register_map else int(op) for op in operands]
            while len(ops) < 3:
                ops.append(None)
            machine_code.append((opcode, *ops))
        
        pc += 1  # Increment program counter for each instruction

    return machine_code

def read_assembly_file(input_file):
    with open(input_file, 'r') as file:
        return file.read()

def write_machine_code_file(output_file, machine_code):
    with open(output_file, 'w') as file:
        for instruction in machine_code:
            opcode, *operands = instruction
            opcode_str = f"0b{opcode:04b}"  # Ensure 4-bit binary representation with 0b prefix
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

