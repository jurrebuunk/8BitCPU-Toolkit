MULTIPLY:
    LDI R2, 0       ; 1000: Initialize result to 0
    LDI R3, 0       ; 1000: Initialize counter to 0

MULT_LOOP:
    SUB R4, R1, R3  ; 0011: R4 = R1 - R3 (check if counter < multiplier)
    BRH Z, MULT_END ; 1011: If zero flag is set, jump to MULT_END
    ADD R2, R2, R0  ; 0010: R2 = R2 + R0 (add multiplicand to result)
    ADI R3, 1       ; 1001: Increment counter
    JMP MULT_LOOP   ; 1010: Repeat loop

MULT_END:
    RET             ; 1101: Return from function

LDI R0, 7          ; 1000: Load multiplicand (8) into R0
LDI R1, 4          ; 1000: Load multiplier (4) into R1
CAL MULTIPLY       ; 1100: Call MULTIPLY function
STR R2, R15, 250   ; 1111: Store the result in memory at address R3 + 0
HLT                ; 0001: Halt the program