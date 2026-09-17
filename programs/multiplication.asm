; Multiply R0 by R1 using repeated addition.
; Result: R2 = R0 * R1.

LDI R0, 7          ; Multiplicand
LDI R1, 4          ; Multiplier
CAL MULTIPLY       ; Call multiplication subroutine
STR R2, R15, 250   ; Show the result on the number display
HLT                ; Halt the program

MULTIPLY:
    LDI R2, 0       ; Initialize result to 0
    LDI R3, 0       ; Initialize counter to 0

MULT_LOOP:
    SUB R4, R1, R3  ; R4 = multiplier - counter
    BRH Z, MULT_END ; If zero flag is set, jump to MULT_END
    ADD R2, R2, R0  ; R2 = R2 + multiplicand
    ADI R3, 1       ; Increment counter
    JMP MULT_LOOP   ; Repeat loop

MULT_END:
    RET             ; Return from subroutine
