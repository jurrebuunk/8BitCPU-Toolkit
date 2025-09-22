; Initialize Turing machine
LDI R0, 0      ; Head position
LDI R1, 0      ; Initial state
LDI R2, 1      ; Example tape symbol (initially 1)

; Main loop
MAIN_LOOP:
    ; Read current symbol from tape
    LOD R3, R0, 0  ; Load tape symbol at head position into R3

    ; Transition function for state 0
    SUB R4, R1, R1 ; Compare current state with 0 (R4 = R1 - R1)
    BRH Z, STATE0  ; Branch to STATE0 if Zero flag is set (R1 == 0)

    ; Transition function for state 1
    SUB R4, R1, 1  ; Compare current state with 1 (R4 = R1 - 1)
    BRH Z, STATE1  ; Branch to STATE1 if Zero flag is set (R1 == 1)

    JMP HALT       ; Halt if no valid state

STATE0:
    ; Handle state 0 transitions
    SUB R4, R3, 1  ; Compare current symbol with 1 (R4 = R3 - 1)
    BRH Z, WRITE0  ; Branch to WRITE0 if Zero flag is set (R3 == 1)

    JMP HALT       ; Halt if no valid symbol

WRITE0:
    ; Write 0, move right, and change state to 1
    LDI R4, 0
    STR R4, R0, 0  ; Write 0 to tape
    ADI R0, 1      ; Move head to the right
    LDI R1, 1      ; Change state to 1
    JMP MAIN_LOOP  ; Repeat loop

STATE1:
    ; Handle state 1 transitions
    SUB R4, R3, 0  ; Compare current symbol with 0 (R4 = R3 - 0)
    BRH Z, WRITE1  ; Branch to WRITE1 if Zero flag is set (R3 == 0)

    JMP HALT       ; Halt if no valid symbol

WRITE1:
    ; Write 1, move left, and change state to 0
    LDI R4, 1
    STR R4, R0, 0  ; Write 1 to tape
    SUB R0, R0, 1  ; Move head to the left (R0 = R0 - 1)
    LDI R1, 0      ; Change state to 0
    JMP MAIN_LOOP  ; Repeat loop

HALT:
    HLT            ; Halt the machine
