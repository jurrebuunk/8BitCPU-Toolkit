LDI R0, 5        ; a = 5
LDI R1, 3        ; b = 3
LDI R2, 0        ; result = 0
LDI R6, 1	 ; decrement 1
CAL multiply
HLT
multiply:
multiply_loop:
BRH Z, end_multiply ; if b == 0, end loop
ADD R3, R3, R0   ; result = result + temp
SUB R1, R1, R6   ; b = b - 1
JMP multiply_loop
end_multiply:
RET