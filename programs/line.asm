LDI R0, 10       ; X coordinate
LDI R1, 15       ; Y coordinate
LDI R2, 240      ; Address for Pixel X
LDI R3, 241      ; Address for Pixel Y
LDI R4, 242      ; Address for Draw Pixel
LDI R5, 245      ; Address for Buffer Screen

; Draw first pixel
STR R1, R3, 0    ; Store Y

LOOP:
STR R0, R2, 0    ; Store X
STR R0, R4, 0    ; Draw pixel
STR R0, R5, 0    ; Buffer screen
ADI R0, 1        ; Increment X
JMP LOOP

HLT              ; Halt
