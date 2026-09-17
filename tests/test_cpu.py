import tempfile
import unittest
from pathlib import Path

from cpu import CPU, CPUFault, load_program, write_binary_program, load_binary_program


REPO_ROOT = Path(__file__).resolve().parents[1]


class ScreenSpy:
    def __init__(self):
        self.hlt = False
        self.x = 0
        self.y = 0
        self.draw_calls = 0
        self.buffer_calls = 0
        self.pixel = 1

    def display_light(self):
        self.hlt = True

    def store_pixel_x(self, value):
        self.x = value & 0x1F

    def store_pixel_y(self, value):
        self.y = value & 0x1F

    def draw_pixel(self):
        self.draw_calls += 1

    def clear_pixel(self):
        pass

    def load_pixel(self):
        return self.pixel

    def buffer_screen(self):
        self.buffer_calls += 1

    def clear_screen_buffer(self):
        pass


class CPUTest(unittest.TestCase):
    def test_add_wraps_and_sets_carry(self):
        cpu = CPU()
        cpu.registers[0] = 250
        cpu.registers[1] = 10

        cpu.execute(0b0010, 2, 0, 1)

        self.assertEqual(cpu.registers[2], 4)
        self.assertEqual(cpu.flags, {"Z": 0, "C": 1})

    def test_sub_wraps_and_sets_borrow_carry(self):
        cpu = CPU()
        cpu.registers[0] = 1
        cpu.registers[1] = 2

        cpu.execute(0b0011, 2, 0, 1)

        self.assertEqual(cpu.registers[2], 255)
        self.assertEqual(cpu.flags, {"Z": 0, "C": 1})

    def test_sub_sets_zero_flag(self):
        cpu = CPU()
        cpu.registers[0] = 42
        cpu.registers[1] = 42

        cpu.execute(0b0011, 2, 0, 1)

        self.assertEqual(cpu.registers[2], 0)
        self.assertEqual(cpu.flags, {"Z": 1, "C": 0})

    def test_branch_zero_and_carry_conditions(self):
        cpu = CPU()
        program = [
            (0b1000, 0, 1, None),      # R0 = 1
            (0b1000, 1, 2, None),      # R1 = 2
            (0b0011, 2, 0, 1),         # R2 = R0 - R1 -> C=1
            (0b1011, CPU.COND_C, 6, None),
            (0b1000, 3, 99, None),     # skipped
            (0b1010, 7, None, None),   # skipped
            (0b0011, 4, 0, 0),         # R4 = 0 -> Z=1
            (0b1011, CPU.COND_Z, 9, None),
            (0b1000, 3, 88, None),     # skipped
            (0b0001, None, None, None),
        ]

        steps = cpu.run(program)

        self.assertEqual(steps, 7)
        self.assertTrue(cpu.halted)
        self.assertEqual(cpu.registers[3], 0)
        self.assertEqual(cpu.pc, 10)

    def test_call_and_return_uses_ram_backed_stack(self):
        cpu = CPU()
        start_sp = cpu.sp
        program = [
            (0b1000, 0, 1, None),      # R0 = 1
            (0b1100, 4, None, None),   # call add_two
            (0b0001, None, None, None),
            (0b0000, None, None, None),
            (0b1001, 0, 2, None),      # add_two: R0 += 2
            (0b1101, None, None, None),
        ]

        cpu.run(program)

        self.assertTrue(cpu.halted)
        self.assertEqual(cpu.registers[0], 3)
        self.assertEqual(cpu.stack, [])
        self.assertEqual(cpu.sp, start_sp)
        self.assertEqual(cpu.memory[start_sp], 2)

    def test_mov_push_and_pop(self):
        cpu = CPU()
        program = [
            (0b1000, 0, 123, None),
            (0x10, 1, 0, None),
            (0x11, 1, None, None),
            (0b1000, 1, 0, None),
            (0x12, 2, None, None),
            (0b0001, None, None, None),
        ]

        cpu.run(program)

        self.assertEqual(cpu.registers[1], 0)
        self.assertEqual(cpu.registers[2], 123)
        self.assertEqual(cpu.stack, [])

    def test_return_without_call_is_fault(self):
        cpu = CPU()

        with self.assertRaises(CPUFault):
            cpu.execute(0b1101)

    def test_halt_works_without_screen(self):
        cpu = CPU()

        cpu.execute(0b0001)

        self.assertTrue(cpu.halted)

    def test_memory_mapped_io_uses_optional_screen(self):
        screen = ScreenSpy()
        cpu = CPU(screen=screen)
        cpu.registers[0] = 12
        cpu.registers[15] = 0

        cpu.execute(0b1111, 0, 15, 240)
        cpu.execute(0b1111, 0, 15, 242)
        cpu.execute(0b1110, 1, 15, 244)

        self.assertEqual(screen.x, 12)
        self.assertEqual(screen.draw_calls, 1)
        self.assertEqual(cpu.registers[1], 1)

    def test_load_program_parses_tuple_machine_code(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "program.mc"
            path.write_text("(0b1000, 0, 42, None)\n(0b0001, None, None, None)\n")

            program = load_program(path)

        self.assertEqual(program, [(0b1000, 0, 42, None), (0b0001, None, None, None)])

    def test_binary_machine_code_round_trip(self):
        program = [(0b1000, 0, 42, None), (0x10, 1, 0, None), (0b0001, None, None, None)]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "program.bin"
            write_binary_program(path, program)

            loaded = load_binary_program(path)
            loaded_via_auto = load_program(path)

        self.assertEqual(loaded, program)
        self.assertEqual(loaded_via_auto, program)

    def test_programs_test_mc_halts(self):
        cpu = CPU()
        program = load_program(REPO_ROOT / "programs" / "test.mc")

        cpu.run(program, max_steps=1000)

        self.assertTrue(cpu.halted)
        self.assertEqual(cpu.registers[4], 30)
        self.assertEqual(cpu.registers[5], 10)

    def test_programs_multiplication_mc_halts_with_expected_result(self):
        cpu = CPU()
        program = load_program(REPO_ROOT / "programs" / "multiplication.mc")

        cpu.run(program, max_steps=1000)

        self.assertTrue(cpu.halted)
        self.assertEqual(cpu.registers[2], 28)
        self.assertEqual(cpu.number_display, 28)

    def test_programs_div_mc_halts_with_expected_result(self):
        cpu = CPU()
        program = load_program(REPO_ROOT / "programs" / "div.mc")

        cpu.run(program, max_steps=1000)

        self.assertTrue(cpu.halted)
        self.assertEqual(cpu.registers[3], 5)
        self.assertEqual(cpu.number_display, 5)

    def test_all_example_machine_code_programs_halt(self):
        for path in sorted((REPO_ROOT / "programs").glob("*.mc")):
            with self.subTest(program=path.name):
                cpu = CPU()
                cpu.run(load_program(path), max_steps=1000)
                self.assertTrue(cpu.halted)


if __name__ == "__main__":
    unittest.main()
