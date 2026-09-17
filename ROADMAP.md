# Roadmap and Current Limitations

This project is intended as a realistic learning project for understanding how CPUs work. The most valuable next step is to make the CPU model reliable and testable before adding more features.

## Current Smoke-Test Results

Tested on 2026-09-17:

- Python syntax check passed for all `.py` files using `python -m py_compile`.
- All `.asm` programs in `programs/` assemble successfully with `assemblerasm.py`.
- Re-assembling the example `.asm` files produces the committed `.mc` files unchanged.
- `assemblerjc.py` runs, but it uses an embedded demo program instead of reading the provided `.jc` file argument.
- `compute.py` could not run in a headless/no-Tkinter environment because it imports Tkinter directly.
- `computesimple.py` exits successfully but does not actually execute the loaded program because its internal `run_alu()` function is never called.

## Priority 0: Fix Correctness First

These issues affect the CPU model itself and should be fixed before adding new instructions or UI features.

### 1. Carry flag behavior is incorrect

`ADD` and `SUB` detect overflow/underflow, but then `set_flags()` resets the carry flag after the result is masked to 8 bits.

Example:

```text
250 + 10 = 260 -> stored as 4
expected C = 1
actual   C = 0
```

Why this matters:

- Carry/borrow is one of the most important CPU concepts.
- Branching on carry will not work correctly until this is fixed.
- Arithmetic examples such as division and comparisons depend on this.

Suggested fix:

- Calculate flags from the full unmasked result.
- Store the masked 8-bit result separately.
- Define whether `C` means carry for addition and borrow for subtraction.

### 2. `BRH C` is assembled but not implemented in the emulator

The assembler maps non-`Z` branch conditions to condition code `1`, but the emulator only checks condition code `0` / zero flag.

Affected example:

- `programs/div.asm` uses `BRH C`.

Suggested fix:

- Define branch condition codes clearly, for example:
  - `Z = 0`
  - `C = 1`
  - optional later: `NZ`, `NC`
- Implement those conditions in `check_condition()`.
- Make the assembler reject unknown branch conditions instead of silently mapping them to `C`.

### 3. Separate the CPU core from the Tkinter UI

Currently `compute.py` creates a Tkinter window inside the `ALU` constructor. This makes the emulator hard to test and impossible to run in environments without Tkinter/display support.

Suggested fix:

- Create a pure CPU/emulator module, for example `cpu.py`.
- Keep registers, memory, instruction execution, flags, and program loading in the pure module.
- Move Tkinter screen behavior into a separate UI module.
- Let tests run the CPU without requiring a graphical display.

### 4. Fix `computesimple.py`

Current problems:

- `main()` defines `run_alu()` but never calls it.
- `HLT` references `self.screen`, which does not exist in the simple emulator.
- Memory-mapped screen methods also assume `self.screen` exists.

Suggested fix:

- Either remove `computesimple.py` after the CPU core exists, or turn it into a real headless CLI runner.
- A useful headless mode should print final registers, flags, memory, and exit cleanly on `HLT`.

## Priority 1: Make the Assembler Easier to Learn With

### 5. Improve parsing and errors

Current limitations:

- `ADD R1, R2, R3` works, but `ADD R1,R2,R3` fails.
- Lowercase instructions such as `add R1, R2, R3` fail.
- Hex immediates such as `0x10` are not supported.
- Unknown instructions produce raw Python errors like `KeyError`.

Suggested fix:

- Add a small tokenizer/parser for assembly lines.
- Support common numeric formats: decimal, binary, and hex.
- Give beginner-friendly errors with file name and line number.
- Decide whether the assembly language should be case-sensitive or case-insensitive.

### 6. Add automated tests

Start with tests for:

- Assembler output for small programs.
- ALU arithmetic and flags.
- Branching and jumps.
- Calls and returns.
- Memory load/store.
- Example programs that should terminate.

This is the most important infrastructure improvement because it lets the project grow without breaking CPU behavior.

## Priority 2: Improve Program Structure and Examples

### 7. Fix example program structure

Some examples are useful but confusing for learners.

Example: `programs/multiplication.asm` starts with the `MULTIPLY` subroutine before the main program. Execution starts at address `0`, so the emulator enters the subroutine before it has been called and causes a stack-underflow message before later producing the expected result.

Suggested fix:

- Put main code first and jump over subroutine definitions, or use a clear reset/start label convention.
- Add comments explaining expected final register/memory state.
- Add one small example per CPU concept.

### 8. Define the architecture in Markdown

The repo should contain a clear CPU reference document, for example `docs/architecture.md`, covering:

- Register file
- Memory layout
- Instruction format
- Flags
- Stack behavior
- Memory-mapped I/O
- Example instruction encodings

This would make the project much better as a learning resource.

### 9. Rework Jutcode into a real CLI tool

Current state:

- `assemblerjc.py` does not read `programs/mult.jc` from the command line.
- It prints debug tokens and generated instructions from an embedded string.

Suggested fix:

- Accept an input `.jc` file.
- Write generated `.asm` or `.mc` output.
- Remove debug prints by default.
- Keep Jutcode experimental until the CPU and assembly layer are stable.

## Priority 3: Packaging and Developer Experience

Later improvements:

- Add `pyproject.toml`.
- Add commands such as `8bit-asm`, `8bit-run`, and `8bit-jc`.
- Add GitHub Actions to run tests on every push.
- Add screenshots or GIFs of the emulator screen.
- Add a stable release only after the CPU core and tests are reliable.

## What Is Missing for a Realistic CPU Learning Project?

The project already has a good start: registers, RAM, instructions, branching, calls, flags, and memory-mapped I/O. The most important missing pieces are:

1. A precise architecture specification.
2. Correct and well-tested flag behavior.
3. A testable CPU core independent of the GUI.
4. Clear examples that teach one concept at a time.
5. Better assembler diagnostics for beginners.
6. A documented fetch/decode/execute cycle.
7. Optional later: binary instruction encoding closer to real hardware instead of Python tuple `.mc` files.

## Recommended Next Milestone

Milestone: **Reliable Headless CPU Core**

Definition of done:

- `cpu.py` can load and execute `.mc` programs without Tkinter.
- `ADD`, `SUB`, `BRH Z`, and `BRH C` have correct tests.
- `programs/test.asm` assembles and runs in tests.
- `computesimple.py` is either fixed as a headless runner or removed.
- The README shows both headless and graphical run options.
