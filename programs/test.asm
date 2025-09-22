; Initialize registers
LDI R0, 10       ; 1000: Load 10 into R0
LDI R1, 20       ; 1000: Load 20 into R1
LDI R2, 30       ; 1000: Load 30 into R2
LDI R3, 40       ; 1000: Load 40 into R3

; Arithmetic operations
ADD R4, R0, R1   ; 0010: R4 = R0 + R1 (R4 = 10 + 20 = 30)
SUB R5, R2, R1   ; 0011: R5 = R2 - R1 (R5 = 30 - 20 = 10)

; Logical operations
NOR R6, R0, R1   ; 0100: R6 = ~(R0 | R1)
AND R7, R0, R1   ; 0101: R7 = R0 & R1
XOR R8, R0, R1   ; 0110: R8 = R0 ^ R1

; Right shift operation
RSH R9, R1       ; 0111: R9 = R1 >> 1 (R9 = 20 >> 1 = 10)

; Add immediate
ADI R10, 5       ; 1001: R10 = R10 + 5

; Memory operations
STR R0, R3, 0    ; 1111: Store R0 at memory address R3 + 0
LOD R11, R3, 0   ; 1110: Load memory address R3 + 0 into R11

; Control flow
JMP SKIP         ; 1010: Jump to SKIP label

; Subroutine
CALL_SUB:
    LDI R12, 50  ; 1000: Load 50 into R12
    RET          ; 1101: Return from subroutine

SKIP:
    CAL CALL_SUB ; 1100: Call subroutine CALL_SUB

; Branch if zero
SUB R13, R0, R0  ; 0011: R13 = R0 - R0 (R13 = 0)
BRH Z, END       ; 1011: Branch to END if zero flag is set

; No operation
NOP              ; 0000: No operation

END:
    HLT          ; 0001: Halt the program
