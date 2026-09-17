# Roadmap and Current Limitations

This project is intended as a realistic learning project for understanding how CPUs work. The most valuable next step is to make the CPU model reliable and testable before adding more features.

## Current Smoke-Test Results

Tested on 2026-09-17 after the first CPU-core cleanup:

- Python unit tests pass with `python -m unittest discover -s tests -v`.
- `computesimple.py` has been renamed to `cpu.py` and now contains the headless, testable CPU core.
- `cpu.py` can run `.mc` machine-code files without Tkinter.
- `compute.py` now uses the shared CPU core instead of keeping a duplicate emulator implementation.
- `ADD`, `SUB`, `BRH Z`, `BRH C`, `CAL`, `RET`, memory-mapped I/O, and machine-code loading have unit tests.
- All `.asm` programs in `programs/` assemble successfully with `assemblerasm.py`.
- `programs/multiplication.asm` now starts with main code before the subroutine, avoiding the old stack-underflow behavior.
- The old Jutcode prototype has been moved to `experimental/jutcode/`; it still uses an embedded demo program instead of reading the provided `.jc` file argument.
- Added `docs/architecture.md` with the current CPU model, instruction encoding, flags, stack, memory-mapped I/O, and assembler directives.
- Added binary `.bin` machine-code output alongside the human-readable `.mc` format.
- Added `MOV`, `PUSH`, and `POP` instructions.
- Added assembler constants, `.text` / `.data` sections, `.org`, `.byte`, `.word`, and `.ascii` support.

## Priority 0: Fix Correctness First

These issues affect the CPU model itself and should be fixed before adding new instructions or UI features.

### 1. Carry flag behavior is incorrect — fixed in `cpu.py`

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

Status:

- Fixed in `cpu.py`.
- `ADD` sets `C` when the full result is greater than `0xFF`.
- `SUB` sets `C` when the operation borrows / goes below zero.
- Tests cover both cases.

### 2. `BRH C` is assembled but not implemented in the emulator — fixed in `cpu.py`

The assembler maps non-`Z` branch conditions to condition code `1`, but the emulator only checks condition code `0` / zero flag.

Affected example:

- `programs/div.asm` uses `BRH C`.

Status:

- Fixed in `cpu.py`.
- Branch condition codes are now:
  - `Z = 0`
  - `C = 1`
  - `NZ = 2`
  - `NC = 3`
- The assembler now rejects unknown branch conditions.

### 3. Separate the CPU core from the Tkinter UI — fixed

Currently `compute.py` creates a Tkinter window inside the `ALU` constructor. This makes the emulator hard to test and impossible to run in environments without Tkinter/display support.

Status:

- Fixed by creating `cpu.py` as the pure CPU core.
- `compute.py` is now only the graphical wrapper.
- Tests run without requiring a graphical display.

### 4. Fix `computesimple.py` — fixed by renaming it to `cpu.py`

Current problems:

- `main()` defines `run_alu()` but never calls it.
- `HLT` references `self.screen`, which does not exist in the simple emulator.
- Memory-mapped screen methods also assume `self.screen` exists.

Status:

- Fixed by replacing it with `cpu.py`.
- `python cpu.py programs/multiplication.mc` now runs the machine code headlessly and prints final CPU state.

## Priority 1: Make the Assembler Easier to Learn With

### 5. Improve parsing and errors — partially fixed

Fixed:

- `ADD R1,R2,R3` now works.
- Lowercase instructions such as `add r1, r2, r3` now work.
- Hex and binary immediates such as `0x10` and `0b1010` are now supported.
- Unknown instructions and branch conditions now produce clearer `ValueError` messages.

Still to improve:

- Add stricter operand validation per instruction.
- Add line/column style diagnostics for more syntax errors.
- Document whether labels are case-sensitive.

### 6. Add automated tests — started

Current tests cover:

- Assembler output for small programs.
- CPU arithmetic and flags.
- Branching and jumps.
- Calls and returns.
- Memory-mapped I/O.
- Machine-code loading.

Still to add:

- Tests for `LOD` / `STR` normal RAM behavior.
- Tests for each example program with expected final state.
- Tests for invalid machine-code and assembly inputs.
- Tests for the graphical wrapper where practical.

This is the most important infrastructure improvement because it lets the project grow without breaking CPU behavior.

## Priority 2: Improve Program Structure and Examples

### 7. Fix example program structure — started

Some examples are useful but confusing for learners.

Example: `programs/multiplication.asm` starts with the `MULTIPLY` subroutine before the main program. Execution starts at address `0`, so the emulator enters the subroutine before it has been called and causes a stack-underflow message before later producing the expected result.

Suggested fix:

- Put main code first and jump over subroutine definitions, or use a clear reset/start label convention.
- Add comments explaining expected final register/memory state.
- Add one small example per CPU concept.

### 8. Define the architecture in Markdown — started

The repo now contains `docs/architecture.md`, covering:

- Register file
- Memory layout
- Instruction format
- Flags
- Stack behavior
- Memory-mapped I/O
- Example instruction encodings

Still to improve:

- Add more diagrams.
- Add more annotated examples that reference the architecture document.
- Add a binary encoding walkthrough with a full program.

### 9. Rework Jutcode into a real CLI tool

Current state:

- `experimental/jutcode/assemblerjc.py` does not read `experimental/jutcode/mult.jc` from the command line.
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
2. Clear examples that teach one concept at a time.
3. Better assembler diagnostics for beginners.
4. A documented fetch/decode/execute cycle.
5. More complete tests around full example programs.
6. Optional later: binary instruction encoding closer to real hardware instead of Python tuple `.mc` files.

## Recommended Next Milestone

Milestone: **Reliable Headless CPU Core** — mostly complete

Done:

- `cpu.py` can load and execute `.mc` programs without Tkinter.
- `ADD`, `SUB`, `BRH Z`, and `BRH C` have tests.
- `computesimple.py` has been replaced by `cpu.py`.
- The README shows both headless and graphical run options.

Next milestone: **Cleaner examples and instruction encoding polish**

Definition of done:

- Add one small example program per CPU concept.
- Add expected final state comments to every example.
- Add tests for each example program's final state.
- Decide whether to keep the current 4-byte-per-instruction binary format or move toward a denser encoding later.
