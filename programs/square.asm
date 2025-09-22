; Initialize registers for screen coordinates
LDI R0, 5    ; X coordinate start (5)
LDI R1, 5    ; Y coordinate start (5)
LDI R2, 10   ; Square size (10x10)

; Loop to draw the square
DRAW_SQUARE:
    ; Set X coordinate
    STR R0, R15, 240  ; Store X coordinate in special address 240
    ; Inner loop for Y coordinate
    LDI R3, 0         ; Initialize Y loop counter
DRAW_ROW:
    ADD R4, R1, R3    ; Calculate Y coordinate
    STR R4, R15, 241  ; Store Y coordinate in special address 241
    STR R15, R15, 242 ; Draw pixel at (X, Y)
    ADI R3, 1         ; Increment Y loop counter
    SUB R5, R3, R2    ; Check if Y loop counter < square size
    BRH Z, END_ROW    ; If Y loop counter == square size, end row
    JMP DRAW_ROW      ; Otherwise, continue drawing row
END_ROW:
    ADI R0, 1         ; Increment X coordinate
    SUB R6, R0, R2    ; Check if X coordinate < square size
    BRH Z, END_SQUARE ; If X coordinate == square size, end square
    JMP DRAW_SQUARE   ; Otherwise, continue drawing square

END_SQUARE:
    ; Buffer the screen to render the square at once
    STR R15, R15, 245 ; Buffer screen

    ; Halt the program
    HLT
