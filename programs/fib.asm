; ============================================================
; Fibonacci sequence
;
; Terminal output:
; 0
; 1
; 1
; 2
; 3
; 5
; 8
; 13
; 21
; 34
; 55
; 89
; 144
; 233
;
; Stops when the next addition overflows 8 bits.
;
; R0 = previous Fibonacci number
; R1 = current Fibonacci number
; R2 = next number
; R3 = address of number output (250)
; ============================================================

SHOW_NUMBER = 250

.text

start:
    LDI R0, 0
    LDI R1, 1
    LDI R3, SHOW_NUMBER

    ; Show initial 0
    STR R0, R3, 0

loop:
    ; Show current number
    STR R1, R3, 0

    ; Calculate next = previous + current
    ADD R2, R0, R1

    ; ADD sets carry when result exceeds 255.
    BRH C, finished

    ; previous = current
    MOV R0, R1

    ; current = next
    MOV R1, R2

    JMP loop

finished:
    HLT