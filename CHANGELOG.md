# Changelog

## v1.0.0 - 2026-09-17

First stable learning release.

### Includes

- Reliable headless CPU core in `cpu.py`
- Assembly assembler in `assemblerasm.py`
- Graphical Tkinter emulator in `compute.py`
- Real `.bin` machine-code output plus readable `.mc` output
- Architecture documentation in `docs/architecture.md`
- RAM-backed stack with `PUSH`, `POP`, `CAL`, and `RET`
- `MOV`, branch aliases, constants, sections, `.org`, and data directives
- Unit tests for the CPU core, assembler, binary encoding, and examples
- Cleaned repo structure with legacy/experimental files separated

### Release assets

- `cpu.py`
- `assemblerasm.py`

## v0.1.0-alpha.1 - 2026-09-17

Initial alpha pre-release.

### Includes

- Assembly assembler for `.asm` files
- Jutcode assembler for `.jc` files
- CPU simulation utilities
- Example programs in `programs/`

### Known limitations

- Documentation is still incomplete
- APIs and CLI behavior may change before a stable release
- Packaging/PyPI release is not available yet
