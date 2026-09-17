# 8BitCPU Toolkit

[![Pre-release](https://img.shields.io/github/v/release/jurrebuunk/8BitCPU-Toolkit?include_prereleases&label=pre-release)](https://github.com/jurrebuunk/8BitCPU-Toolkit/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/)

**8BitCPU Toolkit** is a Python toolkit for experimenting with a custom 8-bit CPU. It includes an assembly-to-machine-code assembler, a CPU emulator with memory/register inspection, a simple Tkinter screen output, and example programs for arithmetic, branching, drawing, and control flow.

Project website: [jurrebuunk.github.io/8BitCPU-Toolkit](https://jurrebuunk.github.io/8BitCPU-Toolkit/)

> Status: **alpha / pre-release**. The toolkit is usable for experimentation, but the CLI, instruction behavior, and Jutcode compiler are still evolving.
>
> See [ROADMAP.md](ROADMAP.md) for the current test findings, limitations, and recommended next fixes.

## Features

- Assemble custom `.asm` programs into `.mc` machine-code files.
- Run machine-code programs on a Python-based 8-bit CPU emulator.
- Inspect RAM, registers, program counter, flags, and number display state while programs run.
- Use labels, jumps, branches, calls, and returns in assembly programs.
- Experiment with memory-mapped screen output through a 32x32 black-and-white Tkinter display.
- Explore an early high-level **Jutcode** syntax and compiler prototype.
- Learn from included sample programs in `programs/`.

## Requirements

- Python 3.x
- Tkinter for the graphical emulator/screen display
  - Usually included with Python on Windows/macOS.
  - On some Linux distros you may need a package such as `python3-tk`.

No third-party Python packages are currently required.

## Development Environment

If you use Nix, enter a shell with Python + Tkinter available:

```bash
nix develop
```

Or with classic `nix-shell`:

```bash
nix-shell
```

Useful manual testing commands:

```bash
make test
make assemble-examples
make run-multiplication
make gui-multiplication
```

## Quick Start

```bash
git clone https://github.com/jurrebuunk/8BitCPU-Toolkit.git
cd 8BitCPU-Toolkit
```

Assemble an example assembly program:

```bash
python assemblerasm.py programs/multiplication.asm
```

This writes the generated machine code to:

```text
programs/multiplication.mc
```

Run the generated machine code in the headless CPU runner:

```bash
python cpu.py programs/multiplication.mc
```

Run the same program in the graphical Tkinter emulator:

```bash
python compute.py programs/multiplication.mc
```

Run the graphical emulator with step-by-step debugging:

```bash
python compute.py programs/multiplication.mc --step
```

Run with a fixed clock speed, for example 2 Hz:

```bash
python compute.py programs/multiplication.mc --clock 2
```

## Tools

| File | Purpose |
| --- | --- |
| `assemblerasm.py` | Assembles `.asm` source files into `.mc` machine-code files. |
| `assemblerjc.py` | Experimental Jutcode lexer/parser/code generator prototype. |
| `cpu.py` | Reliable headless CPU core and command-line runner. |
| `compute.py` | Graphical emulator using the shared CPU core with Tkinter display, clock controls, and step mode. |
| `test.py` | Tkinter color screen/buffer experiment. |
| `tests/` | Unit tests for the assembler and CPU core. |
| `programs/` | Example `.asm`, `.mc`, and `.jc` programs. |

## Assembly Example

```asm
LDI R0, 7          ; Load multiplicand into R0
LDI R1, 4          ; Load multiplier into R1
CAL MULTIPLY       ; Call the MULTIPLY subroutine
STR R2, R15, 250   ; Store result to the number display address
HLT                ; Halt the program
```

Assemble it with:

```bash
python assemblerasm.py programs/multiplication.asm
```

Machine-code output is stored as tuples like:

```text
(0b1000, 0, 7, None)
(0b1000, 1, 4, None)
```

## Instruction Set

| Mnemonic | Opcode | Description |
| --- | --- | --- |
| `NOP` | `0000` | No operation. |
| `HLT` | `0001` | Halt execution. |
| `ADD` | `0010` | Add two registers. |
| `SUB` | `0011` | Subtract one register from another. |
| `NOR` | `0100` | Bitwise NOR. |
| `AND` | `0101` | Bitwise AND. |
| `XOR` | `0110` | Bitwise XOR. |
| `RSH` | `0111` | Right-shift a register by one bit. |
| `LDI` | `1000` | Load an immediate value into a register. |
| `ADI` | `1001` | Add an immediate value to a register. |
| `JMP` | `1010` | Jump to an address or label. |
| `BRH` | `1011` | Branch when a condition is met. Supports `Z`, `C`, `NZ`, and `NC` condition codes in the CPU core. |
| `CAL` | `1100` | Call a subroutine. |
| `RET` | `1101` | Return from a subroutine. |
| `LOD` | `1110` | Load from memory. |
| `STR` | `1111` | Store to memory. |

## CPU Model

The emulator currently models:

- 16 general-purpose 8-bit registers: `R0` through `R15`
- 256 bytes of RAM
- Program counter (`PC`)
- Zero and carry flags: `Z`, `C`
- A small call stack for `CAL` / `RET`
- Memory-mapped output devices

## Memory-Mapped I/O

The emulator reserves high memory addresses for screen and display behavior:

| Address | Purpose |
| --- | --- |
| `240` | Store pixel X coordinate. |
| `241` | Store pixel Y coordinate. |
| `242` | Draw pixel. |
| `243` | Clear pixel. |
| `244` | Load pixel value. |
| `245` | Copy the screen buffer to the display. |
| `246` | Clear the screen buffer. |
| `250` | Show number. |
| `251` | Clear number. |
| `252` | Enable signed number display mode. |
| `253` | Enable unsigned number display mode. |

See `programs/line.asm` for a simple drawing example.

## Example Programs

| Program | Description |
| --- | --- |
| `programs/test.asm` | Demonstrates core instructions, memory, labels, branches, and subroutines. |
| `programs/multiplication.asm` | Multiplication example using a loop and subroutine. |
| `programs/div.asm` | Division example. |
| `programs/square.asm` | Square calculation example. |
| `programs/line.asm` | Draws pixels using memory-mapped screen addresses. |
| `programs/turing.asm` | Turing-machine-style example. |
| `programs/mult.jc` | Example Jutcode source. |

## Jutcode Status

`assemblerjc.py` is an early prototype for a small high-level language that can generate assembly-like output. It currently demonstrates lexing, parsing, and code generation from an embedded example program.

Planned improvements include:

- Reading `.jc` files from the command line.
- Writing generated assembly or machine code to output files.
- Expanding control-flow and comparison support.
- Adding tests for the lexer, parser, and code generator.

## Project Structure

```text
.
├── assemblerasm.py              # Assembly assembler
├── assemblerjc.py               # Experimental Jutcode compiler prototype
├── cpu.py                       # Headless CPU core and CLI runner
├── compute.py                   # Graphical emulator with Tkinter display
├── test.py                      # Screen/color buffer experiment
├── tests/                       # Unit tests
├── programs/                    # Example source and machine-code programs
├── Jutcode documentation.docx   # Jutcode notes/documentation
├── CHANGELOG.md                 # Release history
├── LICENSE                      # MIT license
└── README.md                    # Project overview
```

## Known Limitations

- This is an alpha release, so behavior may change.
- The Jutcode compiler is experimental and not yet a full file-based CLI tool.
- Some older example programs still need cleanup and clearer expected-output comments.
- The graphical emulator requires a working Tkinter display environment.
- There is no packaged `pip` install flow yet.

## Running Tests

```bash
python -m unittest discover -s tests -v
```

## Roadmap

- Expand automated tests for more example programs and edge cases.
- Turn the tools into cleaner command-line interfaces.
- Add packaging via `pyproject.toml`.
- Improve Jutcode file input/output.
- Expand CPU architecture documentation.
- Convert the Jutcode documentation to Markdown.
- Add more example programs and screenshots/GIFs.

## Contributing

Issues, experiments, and pull requests are welcome. Because the project is still early, please keep changes small and clearly describe what CPU behavior or tool behavior is being changed.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Author

Jurre Buunk
