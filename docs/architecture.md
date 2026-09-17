# 8BitCPU Architecture

This document defines the current educational CPU architecture used by the toolkit.

The goal is not to copy one existing commercial CPU exactly. The goal is to make the important CPU ideas visible: registers, RAM, flags, branches, stack behavior, instruction encoding, and memory-mapped I/O.

## Reset and Execution Start

Execution starts at instruction address `0`.

The CPU begins with:

- `PC = 0`
- `SP = 239`
- all registers set to `0`
- all RAM bytes set to `0`, unless a `.mem` memory image is loaded
- flags `Z = 0`, `C = 0`

## Fetch / Decode / Execute Cycle

Each CPU step does this:

1. **Fetch** the instruction at `program[PC]`.
2. **Decode** the opcode and operands.
3. **Execute** the operation.
4. **Update PC**:
   - jumps, branches, calls, and returns set `PC` directly
   - all other instructions increment `PC` by `1`

## Registers

The CPU has 16 general-purpose 8-bit registers:

```text
R0 R1 R2 R3 R4 R5 R6 R7 R8 R9 R10 R11 R12 R13 R14 R15
```

Each register stores a value from `0` to `255`.

## RAM

The CPU has 256 bytes of RAM:

```text
0x00 - 0xFF
```

Addresses `0xF0` through `0xFF` / decimal `240` through `255` are reserved for memory-mapped I/O.

## Stack

The stack is stored in RAM instead of a hidden Python list.

- Stack pointer starts at `SP = 239`
- Stack grows downward
- `CAL` pushes the return address
- `RET` pops the return address
- `PUSH` and `POP` are available for manual stack use

This makes calls and returns closer to how real CPUs usually work.

## Flags

The CPU currently has two flags:

| Flag | Meaning |
| --- | --- |
| `Z` | Zero flag. Set when the written result is `0`. |
| `C` | Carry/borrow flag. Set on addition overflow, subtraction borrow, or shifted-out bit for `RSH`. |

Flag behavior:

| Instruction type | Z updated? | C updated? |
| --- | --- | --- |
| Arithmetic: `ADD`, `SUB`, `ADI` | yes | yes |
| Logic: `NOR`, `AND`, `XOR` | yes | cleared |
| Shift: `RSH` | yes | shifted-out bit |
| Load/copy: `LDI`, `LOD`, `MOV`, `POP` | yes | cleared unless `LDI` value is out of 8-bit range |
| Store/control: `STR`, `JMP`, `BRH`, `CAL`, `RET`, `PUSH`, `NOP`, `HLT` | no | no |

## Instruction Encoding

The human-readable `.mc` format stores decoded instructions as tuples:

```text
(opcode, operand1, operand2, operand3)
```

Example:

```text
(0b1000, 0, 7, None)
```

The binary `.bin` format stores each instruction as four bytes:

```text
byte 0: opcode
byte 1: operand1 or 0xFF for None
byte 2: operand2 or 0xFF for None
byte 3: operand3 or 0xFF for None
```

Example:

```asm
LDI R0, 7
```

Encodes as:

```text
08 00 07 FF
```

This is intentionally simple so the binary format is easy to inspect while still being real byte-based machine code.

## Instruction Set

| Mnemonic | Opcode | Operands | Description |
| --- | ---: | --- | --- |
| `NOP` | `0x00` | — | No operation. |
| `HLT` | `0x01` | — | Halt execution. |
| `ADD` | `0x02` | `dest, left, right` | Add two registers. |
| `SUB` | `0x03` | `dest, left, right` | Subtract `right` from `left`. |
| `NOR` | `0x04` | `dest, left, right` | Bitwise NOR. |
| `AND` | `0x05` | `dest, left, right` | Bitwise AND. |
| `XOR` | `0x06` | `dest, left, right` | Bitwise XOR. |
| `RSH` | `0x07` | `dest, source` | Right shift by one bit. |
| `LDI` | `0x08` | `dest, immediate` | Load immediate. |
| `ADI` | `0x09` | `dest, immediate` | Add immediate. |
| `JMP` | `0x0A` | `target` | Jump. |
| `BRH` | `0x0B` | `condition, target` | Branch when a flag condition is true. |
| `CAL` | `0x0C` | `target` | Call subroutine. |
| `RET` | `0x0D` | — | Return from subroutine. |
| `LOD` | `0x0E` | `dest, base, offset` | Load from RAM address `base + offset`. |
| `STR` | `0x0F` | `source, base, offset` | Store to RAM address `base + offset`. |
| `MOV` | `0x10` | `dest, source` | Copy register to register. |
| `PUSH` | `0x11` | `source` | Push register value onto the stack. |
| `POP` | `0x12` | `dest` | Pop stack value into register. |

## Branch Conditions

`BRH` supports these condition codes:

| Condition | Meaning |
| --- | --- |
| `Z` | branch if zero flag is set |
| `C` | branch if carry/borrow flag is set |
| `NZ` | branch if zero flag is clear |
| `NC` | branch if carry/borrow flag is clear |

Branch aliases are also supported:

```asm
BZ label
BC label
BNZ label
BNC label
```

## Memory-Mapped I/O

| Address | Purpose |
| ---: | --- |
| `240` | Store pixel X coordinate. |
| `241` | Store pixel Y coordinate. |
| `242` | Draw pixel. |
| `243` | Clear pixel. |
| `244` | Load pixel value. |
| `245` | Copy screen buffer to display. |
| `246` | Clear screen buffer. |
| `250` | Show number. |
| `251` | Clear number. |
| `252` | Enable signed number display mode. |
| `253` | Enable unsigned number display mode. |

## Assembler Directives

### Constants

```asm
SCREEN_NUMBER = 250
.equ SCREEN_X, 240
```

### Sections

```asm
.text
; instructions here

.data
; bytes here
```

### Origin

```asm
.org 16
```

In `.text`, `.org` inserts `NOP` instructions until the requested instruction address.

In `.data`, `.org` changes the RAM address where data bytes are emitted.

### Data

```asm
.data
.org 32
answer: .byte 42
pair: .word 0x1234
message: .ascii "HI"
```

The assembler writes data to a `.mem` memory image next to the generated `.mc` and `.bin` files.

The CPU runner automatically loads a matching `.mem` file when it exists:

```bash
python cpu.py program.mc
```

or explicitly:

```bash
python cpu.py program.mc --memory program.mem
```
