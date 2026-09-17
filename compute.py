import argparse
import time
import tkinter as tk
from tkinter import messagebox

from cpu import CPU, CPUFault, load_program


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
        self.clock_label = tk.Label(self.clock_frame, text="0Hz:", bg='white')
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
                self.image.put(color, (x * 10, y * 10, x * 10 + 10, y * 10 + 10))
        self.display_buffer = [row[:] for row in self.buffer]

    def display_light(self):
        self.hlt_light.config(bg='red')

    def update_clock_speed(self, speed):
        self.clock_label.config(text=f"{speed}Hz")

    def flash_clock_light(self):
        self.clock_light.config(bg='red')
        self.master.after(100, lambda: self.clock_light.config(bg='light green'))


def main():
    parser = argparse.ArgumentParser(description="Graphical 8-bit CPU emulator")
    parser.add_argument("input_file", help="Machine-code `.mc` file to run")
    parser.add_argument("--step", action="store_true", help="Enable step mode for debugging")
    parser.add_argument("--clock", type=int, default=0, help="Clock speed in Hz (0 for unlimited)")
    parser.add_argument("--trace", action="store_true", help="Print CPU state before every instruction")
    parser.add_argument("--max-steps", type=int, default=10000, help="Stop after this many instructions to catch infinite loops")
    args = parser.parse_args()

    root = tk.Tk()
    root.title("8BitCPU Toolkit Emulator")
    root.resizable(False, False)

    screen = Screen(root)
    screen.update_clock_speed(args.clock)
    cpu = CPU(screen=screen)
    program = load_program(args.input_file)
    steps = 0

    def on_closing():
        cpu.halted = True
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    def finish():
        print(f"Executed {steps} instruction(s). Halted: {cpu.halted}. PC: {cpu.pc}")
        cpu.print_memory_grid()

    def run_next_instruction():
        nonlocal steps
        if cpu.halted or cpu.pc >= len(program):
            finish()
            return
        if steps >= args.max_steps:
            messagebox.showerror("CPU fault", f"Step limit reached ({args.max_steps}); possible infinite loop")
            finish()
            return

        try:
            screen.flash_clock_light()
            if args.trace:
                cpu.print_compact_state()
            cpu.step(program)
            steps += 1
        except CPUFault as exc:
            messagebox.showerror("CPU fault", str(exc))
            finish()
            return

        if args.step:
            input("Press Enter to execute the next instruction...")

        delay_ms = 1 if args.clock <= 0 else max(1, int(1000 / args.clock))
        root.after(delay_ms, run_next_instruction)

    root.after(0, run_next_instruction)
    root.mainloop()


if __name__ == "__main__":
    main()
