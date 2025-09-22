import argparse
import time
import tkinter as tk
import threading

class Screen:
    def __init__(self, master):
        self.master = master
        self.frame = tk.Frame(master)
        self.frame.pack(side=tk.LEFT)

        self.canvas = tk.Canvas(self.frame, width=320, height=320, bg='black')
        self.canvas.pack()

        self.ui_frame = tk.Frame(master, bg='white', width=100, height=320)
        self.ui_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # HLT light
        self.hlt_frame = tk.Frame(self.ui_frame, bg='white')
        self.hlt_frame.pack(pady=5)
        self.hlt_label = tk.Label(self.hlt_frame, text="HLT:", bg='white')
        self.hlt_label.pack(side=tk.LEFT)
        self.hlt_light = tk.Canvas(self.hlt_frame, width=20, height=20, bg='light green')
        self.hlt_light.pack(side=tk.LEFT)

        # Clock speed light
        self.clock_frame = tk.Frame(self.ui_frame, bg='white')
        self.clock_frame.pack(pady=5)
        self.clock_label = tk.Label(self.clock_frame, text="1Hz:", bg='white')
        self.clock_label.pack(side=tk.LEFT)
        self.clock_light = tk.Canvas(self.clock_frame, width=20, height=20, bg='light green')
        self.clock_light.pack(side=tk.LEFT)

        # Initialize screen buffer and display buffer
        self.buffer = [[0 for _ in range(32)] for _ in range(32)]
        self.display_buffer = [[0 for _ in range(32)] for _ in range(32)]

        # Initialize pixel coordinates
        self.pixel_x = 0
        self.pixel_y = 0

        # Initialize PhotoImage object
        self.image = tk.PhotoImage(width=320, height=320)
        self.canvas.create_image((160, 160), image=self.image, state="normal")

    def store_pixel_x(self, x):
        self.pixel_x = x & 0x1F  # Bottom 5 bits are X coordinate

    def store_pixel_y(self, y):
        self.pixel_y = y & 0x1F  # Bottom 5 bits are Y coordinate

    def draw_pixel(self):
        self.buffer[self.pixel_y][self.pixel_x] = 1

    def clear_pixel(self):
        self.buffer[self.pixel_y][self.pixel_x] = 0

    def load_pixel(self):
        return self.buffer[self.pixel_y][self.pixel_x]

    def buffer_screen(self):
        self.display_buffer = [row[:] for row in self.buffer]
        self.update_screen()

    def clear_screen_buffer(self):
        self.buffer = [[0 for _ in range(32)] for _ in range(32)]

    def update_screen(self):
        for y in range(32):
            for x in range(32):
                color = "#FFFFFF" if self.buffer[y][x] else "#000000"
                self.image.put(color, (x*10, y*10, x*10+10, y*10+10))
        self.display_buffer = [row[:] for row in self.buffer]  # Update the display buffer

    def display_light(self):
        self.hlt_light.config(bg='red')

    def update_clock_speed(self, speed):
        self.clock_label.config(text=f"{speed}Hz")

    def flash_clock_light(self):
        self.clock_light.config(bg='red')
        self.master.after(100, lambda: self.clock_light.config(bg='light green'))
        
class ALU:
    def __init__(self):
        self.registers = [0] * 16  # 16 1-byte registers
        self.memory = [0] * 256  # Data memory
        self.instruction_memory = [0] * 2048  # Instruction memory
        self.stack = []
        self.pc = 0  # Program counter
        self.flags = {'Z': 0, 'C': 0}  # Zero and Carry flags
        self.step = False  # Step feature toggle
        self.number_display = 0  # Number display
        self.signed_mode = False  # Number display mode
        self.clock_speed = 0  # Clock speed in Hz (0 for unlimited)
        
        # Initialize Tkinter screen
        self.root = tk.Tk()
        self.root.title("32x32 Black and White Screen")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)  # Handle window close event
        self.root.resizable(False, False)  # Make the window non-resizable
        self.screen = Screen(self.root)
        self.halted = False  # Initialize halted state

    def on_closing(self):
        self.halted = True
        self.root.destroy()
        exit(0)

    def execute(self, opcode, operand1=None, operand2=None, operand3=None):
        if opcode == 0b0000:  # NOP
            pass
        elif opcode == 0b0001:  # HLT
            self.screen.display_light()
            self.halted = True
            return None
        elif opcode == 0b0010:  # ADD
            result = self.registers[operand2] + self.registers[operand3]
            if result > 0xFF:
                self.flags['C'] = 1
                print("Overflow Error: ADD operation result exceeds 8 bits.")
            self.registers[operand1] = result & 0xFF
            self.set_flags(self.registers[operand1])
        elif opcode == 0b0011:  # SUB
            result = self.registers[operand2] - self.registers[operand3]
            if result < 0:
                self.flags['C'] = 1
                print("Overflow Error: SUB operation result is negative.")
            self.registers[operand1] = result & 0xFF
            self.set_flags(self.registers[operand1])
        elif opcode == 0b0100:  # NOR
            self.registers[operand1] = ~(self.registers[operand2] | self.registers[operand3]) & 0xFF
            self.set_flags(self.registers[operand3])
        elif opcode == 0b0101:  # AND
            self.registers[operand1] = self.registers[operand2] & self.registers[operand3]
            self.set_flags(self.registers[operand3])
        elif opcode == 0b0110:  # XOR
            self.registers[operand1] = self.registers[operand2] ^ self.registers[operand3]
            self.set_flags(self.registers[operand3])
        elif opcode == 0b0111:  # RSH
            self.registers[operand1] = self.registers[operand2] >> 1
        elif opcode == 0b1000:  # LDI
            if operand2 > 0xFF:
                print("Overflow Error: LDI operand exceeds 8 bits.")
                self.flags['C'] = 1
            self.registers[operand1] = operand2 & 0xFF
        elif opcode == 0b1001:  # ADI
            result = self.registers[operand1] + operand2
            if result > 0xFF:
                self.flags['C'] = 1
                print("Overflow Error: ADI operation result exceeds 8 bits.")
            self.registers[operand1] = result & 0xFF
            self.set_flags(self.registers[operand1])
        elif opcode == 0b1010:  # JMP
            return operand1
        elif opcode == 0b1011:  # BRH
            if self.check_condition(operand1):
                return operand2
        elif opcode == 0b1100:  # CAL
            if len(self.stack) < 16:
                self.stack.append(self.pc + 1)
                return operand1
            else:
                print("Stack Overflow Error: Cannot push to stack.")
        elif opcode == 0b1101:  # RET
            if self.stack:
                return self.stack.pop()
            else:
                print("Stack Underflow Error: Cannot pop from stack.")
        elif opcode == 0b1110:  # LOD
            address = self.registers[operand2] + (operand3 if operand3 is not None else 0)
            self.registers[operand1] = self.memory[address]
            if address > 239:
                self.handle_special_load(address, operand2)
        elif opcode == 0b1111:  # STR
            address = self.registers[operand2] + (operand3 if operand3 is not None else 0)
            self.memory[address] = self.registers[operand1]
            if address > 239:
                self.handle_special_store(address, self.registers[operand1])
        return None

    def set_flags(self, result):
        self.flags['Z'] = 1 if result == 0 else 0
        self.flags['C'] = 1 if result > 0xFF else 0

    def check_condition(self, cond):
        if cond == 0:  # Example condition: Zero flag
            return self.flags['Z'] == 1
        # Add more conditions as needed
        return False

    def toggle_step(self):
        self.step = not self.step
        print(f"Step mode {'enabled' if self.step else 'disabled'}.")

    def load_program(self, filename):
        program = []
        with open(filename, 'r') as file:
            for line in file:
                line = line.strip()
                if line:
                    parts = line.strip('()').split(', ')
                    opcode = int(parts[0], 2)
                    operands = [int(op) if op != 'None' else None for op in parts[1:]]
                    program.append((opcode, *operands))
        return program

    def handle_special_load(self, address, reg):
        if address == 244:  # Load Pixel
            self.registers[reg] = self.screen.load_pixel()

    def handle_special_store(self, address, value):
        if address == 240:  # Store Pixel X
            self.screen.store_pixel_x(value)
        elif address == 241:  # Store Pixel Y
            self.screen.store_pixel_y(value)
        elif address == 242:  # Draw Pixel
            self.screen.draw_pixel()
        elif address == 243:  # Clear Pixel
            self.screen.clear_pixel()
        elif address == 245:  # Buffer Screen
            self.screen.buffer_screen()
        elif address == 246:  # Clear Screen Buffer
            self.screen.clear_screen_buffer()
        elif address == 250:  # Show Number
            self.number_display = value
        elif address == 251:  # Clear Number
            self.number_display = 0
        elif address == 252:  # Signed Mode
            self.signed_mode = True
        elif address == 253:  # Unsigned Mode
            self.signed_mode = False

    def set_clock_speed(self, speed):
        self.clock_speed = speed
        self.screen.update_clock_speed(speed)

    def print_full_state(self):
        print("Registers and Memory:")
        max_len = max(len(self.registers), len(self.memory))
        max_mem_len = max(len(f"M{j:03}: {self.memory[j]:03}") for j in range(len(self.memory)))

        for i in range(16):
            reg_str = f"R{i:02}: {self.registers[i]:3}" if i < len(self.registers) else ""
            mem_strs = [f"M{j:03}: {self.memory[j]:3}" for j in range(i, len(self.memory), 16)]

            # Adjust spacing dynamically for both single and
            mem_strs_adjusted = [f"{mem_str:<{max_mem_len}}" for mem_str in mem_strs[:16]]
            mem_str = " ".join(mem_strs_adjusted)

            print(f"{reg_str:<9} {mem_str}")

        print(f"\nNumber Display: {self.number_display} (Signed Mode: {self.signed_mode})")
        print(f"PC: {self.pc} | Flags: {self.flags}")



def main():
    parser = argparse.ArgumentParser(description="Simple 8-bit ALU Emulator")
    parser.add_argument("input_file", help="The input file containing the machine code")
    parser.add_argument("--step", action="store_true", help="Enable step mode for debugging")
    parser.add_argument("--clock", type=int, default=0, help="Clock speed in Hz (0 for unlimited)")

    args = parser.parse_args()

    alu = ALU()
    program = alu.load_program(args.input_file)

    if args.step:
        alu.toggle_step()

    alu.set_clock_speed(args.clock)  # Set the clock speed
    
    alu.halted = False  # Initialize the halted state

    def run_alu():
        pc = 0  # Program counter
        while pc < len(program) and not alu.halted:
            alu.screen.flash_clock_light()  # Flash the clock light
            alu.print_full_state()
            opcode, operand1, operand2, operand3 = program[pc]
            next_pc = alu.execute(opcode, operand1, operand2, operand3)
            if next_pc is not None:
                pc = next_pc
            else:
                pc += 1
            alu.pc = pc

            if alu.step:
                input("Press Enter to execute the next instruction...")
            elif alu.clock_speed > 0:
                time.sleep(1 / alu.clock_speed)

        alu.print_full_state()

    # Run the ALU execution in a separate thread
    alu_thread = threading.Thread(target=run_alu)
    alu_thread.start()

    # Start the Tkinter main loop
    alu.root.mainloop()

if __name__ == "__main__":
    main()
