# 8-Bit CPU Assembler Project

This project contains tools and programs for assembling and simulating code for a custom 8-bit CPU architecture. It includes multiple Python scripts for assembling source files, performing computations, and running tests, as well as a collection of example programs.

## Project Structure

- `assemblerasm.py` — Assembler for `.asm` files (assembly language)
- `assemblerjc.py` — Assembler for `.jc` files (Jutcode format)
- `compute.py` — CPU computation and simulation utilities
- `computesimple.py` — Simplified computation utilities
- `test.py` — Test scripts for validation
- `programs/` — Example programs in assembly and machine code formats
    - `.asm` — Assembly source files
    - `.mc` — Machine code files
    - `.jc` — Jutcode format files
- `Jutcode documentation.docx` — Documentation for the Jutcode format
- `New Text Document.txt` — Miscellaneous notes

## Getting Started

1. Clone this repository to your local machine.
2. Install Python 3.x if not already installed.
3. Run the assembler scripts to convert assembly or Jutcode files to machine code:
   ```powershell
   python assemblerasm.py programs/example.asm
   python assemblerjc.py programs/example.jc
   ```
4. Use `compute.py` or `computesimple.py` to simulate or analyze machine code files.

## Example Usage

```powershell
python assemblerasm.py programs/multiplication.asm
python compute.py programs/multiplication.mc
```

## Programs Folder

Contains sample programs for testing and demonstration:
- `div.asm`, `div.mc` — Division example
- `line.asm`, `line.mc` — Line drawing example
- `mult.jc`, `multiplication.asm`, `multiplication.mc` — Multiplication examples
- `square.asm`, `square.mc` — Square calculation
- `test.asm`, `test.mc`, `test2.asm`, `test2.mc` — Test programs
- `turing.asm`, `turing.mc` — Turing machine example

## Documentation

Refer to `Jutcode documentation.docx` for details on the Jutcode format and CPU architecture.

## License

Specify your license here (e.g., MIT, GPL, etc.).

## Author

Your Name
