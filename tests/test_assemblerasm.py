import unittest

from assemblerasm import assemble


class AssemblerAsmTest(unittest.TestCase):
    def test_accepts_commas_without_spaces(self):
        self.assertEqual(assemble("ADD R1,R2,R3"), [(0b0010, 1, 2, 3)])

    def test_accepts_lowercase_mnemonics_and_registers(self):
        self.assertEqual(assemble("ldi r0, 0x10"), [(0b1000, 0, 16, None)])

    def test_supports_binary_and_hex_numbers(self):
        self.assertEqual(
            assemble("LDI R0, 0b1010\nADI R0, 0x05"),
            [(0b1000, 0, 10, None), (0b1001, 0, 5, None)],
        )

    def test_branch_conditions_are_explicit(self):
        self.assertEqual(
            assemble("SUB R0, R1, R2\nBRH C, done\nNOP\ndone: HLT"),
            [
                (0b0011, 0, 1, 2),
                (0b1011, 1, 3, None),
                (0b0000, None, None, None),
                (0b0001, None, None, None),
            ],
        )

    def test_unknown_branch_condition_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown branch condition"):
            assemble("BRH MAYBE, 0")

    def test_branch_alias_and_mov(self):
        self.assertEqual(
            assemble("MOV R2, R1\nBZ done\nNOP\ndone: HLT"),
            [
                (0x10, 2, 1, None),
                (0b1011, 0, 3, None),
                (0b0000, None, None, None),
                (0b0001, None, None, None),
            ],
        )

    def test_constants_data_labels_and_org(self):
        source = """
.equ SCREEN_NUMBER, 250
.data
.org 32
answer: .byte 42
.text
.org 2
LDI R0, answer
STR R0, R15, SCREEN_NUMBER
"""
        from assemblerasm import assemble_program

        program = assemble_program(source)

        self.assertEqual(program.memory_image, {32: 42})
        self.assertEqual(
            program.instructions,
            [
                (0b0000, None, None, None),
                (0b0000, None, None, None),
                (0b1000, 0, 32, None),
                (0b1111, 0, 15, 250),
            ],
        )

    def test_strict_register_validation(self):
        with self.assertRaisesRegex(ValueError, "Expected register"):
            assemble("ADD R1, 5, R2")


if __name__ == "__main__":
    unittest.main()
