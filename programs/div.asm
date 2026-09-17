; Divide 20 by 4 using repeated subtraction.
; Result: R3 = quotient, R2 = remainder.

LDI R0, 20       ; Dividend
LDI R1, 4        ; Divisor
MOV R2, R0       ; Remainder = dividend
LDI R3, 0        ; Quotient = 0

DIV_LOOP:
    SUB R4, R2, R1   ; Trial remainder = remainder - divisor
    BC DIV_END       ; If borrow/carry, remainder < divisor, so stop
    MOV R2, R4       ; Commit new remainder
    ADI R3, 1        ; Quotient++
    JMP DIV_LOOP

DIV_END:
    STR R3, R15, 250 ; Show quotient
    HLT
