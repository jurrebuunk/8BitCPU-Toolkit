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
        with self.assertRaisesRegex(ValueError, "Unknown branch condition"):
            assemble("BRH MAYBE, 0")


if __name__ == "__main__":
    unittest.main()
