; Draw a horizontal 10-pixel line and halt.

.equ SCREEN_X, 240
.equ SCREEN_Y, 241
.equ SCREEN_DRAW, 242
.equ SCREEN_BUFFER, 245

LDI R0, 10       ; X coordinate
LDI R1, 15       ; Y coordinate
LDI R6, 0        ; Counter
LDI R7, 10       ; Number of pixels to draw
LDI R15, 0       ; Base address for memory-mapped I/O

STR R1, R15, SCREEN_Y

LOOP:
    STR R0, R15, SCREEN_X
    STR R0, R15, SCREEN_DRAW
    ADI R0, 1
    ADI R6, 1
    SUB R8, R6, R7
    BNZ LOOP

STR R0, R15, SCREEN_BUFFER
HLT
