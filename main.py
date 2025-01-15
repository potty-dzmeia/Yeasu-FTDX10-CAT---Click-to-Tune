import logging
import tkinter as tk
from tkinter import ttk
from radio.radio import Radio
import time
import serial.tools.list_ports

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class RadioGUI:
    def __init__(self, root):
        self.radio = None
        self.root = root
        self.root.title("Radio Interface")
        self.root.geometry("400x300")  # Set the window size to fit the controls

        self.com_port_label = tk.Label(root, text="COM Port:")
        self.com_port_label.grid(row=0, column=0)
        self.com_port_selector = ttk.Combobox(root, values=self.get_serial_ports())
        self.com_port_selector.grid(row=0, column=1)
        self.com_port_selector.current(0)  # Set the first port as default

        self.baudrate_label = tk.Label(root, text="Baudrate:")
        self.baudrate_label.grid(row=1, column=0)
        self.baudrate_selector = ttk.Combobox(
            root, values=[9600, 19200, 38400, 57600, 115200]
        )
        self.baudrate_selector.grid(row=1, column=1)
        self.baudrate_selector.current(2)  # Set 38400 as default

        self.swr_meter_label = tk.Label(root, text="SWR Meter:")
        self.swr_meter_label.grid(row=6, column=0)
        self.swr_meter_value = ttk.Progressbar(
            root, orient="horizontal", length=255, mode="determinate", maximum=255
        )
        self.swr_meter_value.grid(row=6, column=1)

        self.swr_canvas = tk.Canvas(root, width=270, height=20)
        self.swr_canvas.grid(row=7, column=1)
        self.draw_swr_indications()

        self.po_meter_label = tk.Label(root, text="Power Meter:")
        self.po_meter_label.grid(row=8, column=0)
        self.po_meter_value = ttk.Progressbar(
            root, orient="horizontal", length=255, mode="determinate", maximum=255
        )
        self.po_meter_value.grid(row=8, column=1)

        self.po_canvas = tk.Canvas(root, width=270, height=20)
        self.po_canvas.grid(row=9, column=1)
        self.draw_po_indications()

        self.transmit_button = tk.Button(
            root, text="Transmit", command=self.toggle_transmit
        )
        self.transmit_button.grid(row=10, column=0, columnspan=2)

        self.is_transmitting = False
        self.original_mode = None
        self.original_txpower = None

        self.update_gui()

    def get_serial_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def draw_swr_indications(self):
        self.swr_canvas.create_text(0, 10, anchor=tk.CENTER, text="1.0")
        self.swr_canvas.create_text(64, 10, anchor=tk.CENTER, text="1.5")
        self.swr_canvas.create_text(128, 10, anchor=tk.CENTER, text="2.0")
        self.swr_canvas.create_text(192, 10, anchor=tk.CENTER, text="3.0")
        self.swr_canvas.create_text(255, 10, anchor=tk.CENTER, text="5.0")

    def draw_po_indications(self):
        self.po_canvas.create_text(35, 10, anchor=tk.CENTER, text="5")
        self.po_canvas.create_text(85, 10, anchor=tk.CENTER, text="10")
        self.po_canvas.create_text(150, 10, anchor=tk.CENTER, text="50")
        self.po_canvas.create_text(200, 10, anchor=tk.CENTER, text="100")
        self.po_canvas.create_text(255, 10, anchor=tk.CENTER, text="150")

    def transmit(self):
        self.radio.set_transmit(True)

    def toggle_transmit(self):
        try:
            if not self.is_transmitting:
                # Initialize the Radio object with the selected serial port and baudrate
                self.radio = Radio(
                    port=self.com_port_selector.get(),
                    baudrate=int(self.baudrate_selector.get()),
                    command_delay=0,
                )
                self.radio.get_active_vfo(blocking=True)  # Request the active VFO
                # Store the current mode and tx power
                self.original_mode = self.radio.get_mode(blocking=True)
                self.original_txpower = self.radio.get_txpower(blocking=True)
                # Set the mode to FM and tx power to 5 watts
                self.radio.set_mode("FM")
                self.radio.set_txpower(5)
                while self.radio.get_txpower(blocking=True) != 5:
                    pass
                # Start transmitting
                self.radio.set_transmit(True)
                self.transmit_button.config(text="Stop Transmitting")
            else:
                # Stop transmitting
                self.radio.set_transmit(False)
                while self.radio.get_transmit(blocking=True):
                    pass
                # Restore the original mode and tx power
                self.radio.set_mode(self.original_mode)
                self.radio.set_txpower(self.original_txpower)
                self.transmit_button.config(text="Transmit")
                # Disconnect the Radio object
                self.radio.disconnect()
                self.radio = None

            self.is_transmitting = not self.is_transmitting
        except Exception as e:
            logging.error(f"Error in toggle_transmit: {e}")
            if self.radio:
                self.radio.disconnect()
                self.radio = None
            self.is_transmitting = False
            return

    def update_gui(self):
        if self.is_transmitting:
            self.radio.get_swr_meter()  # Request the SWR meter value
            self.swr_meter_value["value"] = self.radio.swr or 0

            self.radio.get_po_meter()  # Request the Power meter value
            self.po_meter_value["value"] = self.radio.txpower or 0
            self.root.after(100, self.update_gui)
        else:
            self.swr_meter_value["value"] = 0
            self.po_meter_value["value"] = 0
            self.root.after(500, self.update_gui)


def main():
    # Set up the GUI
    root = tk.Tk()
    root.geometry("400x300")  # Set the window size to fit the controls
    gui = RadioGUI(root)

    # Start the GUI event loop
    root.mainloop()


if __name__ == "__main__":
    main()
