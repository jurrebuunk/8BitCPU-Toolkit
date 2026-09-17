; Tiny Turing-machine-style state transition example.
; Uses RAM as tape. This example halts after a short state transition demo.

LDI R0, 0      ; Head position
LDI R1, 0      ; Initial state
LDI R2, 1      ; Example tape symbol value
LDI R14, 1     ; Constant 1
LDI R15, 0     ; Constant/base 0
STR R2, R0, 0  ; Store initial tape symbol at tape[head]

MAIN_LOOP:
    LOD R3, R0, 0  ; Load tape symbol at head position into R3

    ; Transition function for state 0
    SUB R4, R1, R15 ; Compare current state with 0
    BZ STATE0

    ; Transition function for state 1
    SUB R4, R1, R14 ; Compare current state with 1
    BZ STATE1

    JMP HALT       ; Halt if no valid state

STATE0:
    ; If symbol is 1, write 0, move right, change to state 1
    SUB R4, R3, R14
    BZ WRITE0
    JMP HALT

WRITE0:
    STR R15, R0, 0 ; Write 0 to tape
    ADI R0, 1      ; Move head to the right
    LDI R1, 1      ; Change state to 1
    JMP MAIN_LOOP

STATE1:
    ; If symbol is 0, write 1, move left, change to state 0
    SUB R4, R3, R15
    BZ WRITE1
    JMP HALT

WRITE1:
    STR R14, R0, 0 ; Write 1 to tape
    SUB R0, R0, R14 ; Move head to the left
    LDI R1, 0      ; Change state to 0
    JMP HALT       ; Stop the demo here

HALT:
    HLT
