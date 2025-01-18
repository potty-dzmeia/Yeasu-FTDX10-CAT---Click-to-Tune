import threading
import serial
import time
import logging
from queue import Queue
from radio.radioparser import RadioParser
from radio.listener import RadioListener
from radio.events import *
from overrides import overrides

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class Radio(RadioListener):
    def __init__(self, port: str, baudrate: int = 9600, command_delay: float = 0.1):
        logging.info(f"Connecting to radio on port {port} at {baudrate} baud")
        self.serial_port = serial.Serial(port, baudrate, timeout=1, write_timeout=1)
        self.parser = RadioParser()
        self.parser.add_listener(self)
        self.current_frequency = None
        self.active_vfo = None
        self.txpower = None
        self.swr = None
        self.buffer = b""  # Buffer to store incomplete data
        self.command_queue = Queue()
        self.command_delay = command_delay
        self.stop_event = threading.Event()  # Event to signal the threads to stop
        self.read_thread = threading.Thread(target=self._read_from_radio)
        self.read_thread.daemon = True
        self.read_thread.start()
        self.write_thread = threading.Thread(target=self._write_to_radio)
        self.write_thread.daemon = True
        self.write_thread.start()
        self.frequency_vfo_a = None
        self.frequency_vfo_b = None
        self.mode_vfo_a = None
        self.mode_vfo_b = None
        self.s_meter = None
        self.comp = None
        self.alc = None
        self.vdd = None
        self.idd = None
        self.txpower_event = threading.Event()
        self.mode_event = threading.Event()
        self.active_vfo_event = threading.Event()
        self.transmit_event = threading.Event()

    def _read_from_radio(self):
        while not self.stop_event.is_set():
            if self.serial_port.in_waiting > 0:
                # Read all available data from the serial port
                data = self.serial_port.read(self.serial_port.in_waiting)
                logging.info(f"Received: {data}")
                # Append the new data to the buffer
                self.buffer += data
                # Process data in the buffer
                while self.buffer:
                    # Parse the data and get the number of bytes processed
                    bytes_processed = self.parser.parse(self.buffer)
                    if bytes_processed == 0:
                        break
                    # Remove the processed bytes from the buffer
                    self.buffer = self.buffer[bytes_processed:]

    def _write_to_radio(self):
        while not self.stop_event.is_set():
            try:
                # Check if the send buffer size exceeds 1000 bytes
                if self.command_queue.qsize() > 1000:
                    raise Exception(
                        "Send buffer overflow: more than 1000 bytes in the queue"
                    )

                # Get the next command from the queue
                command = self.command_queue.get()
                logging.info(f"Sending: {command}")
                # Encode the command string to bytes before sending to the serial port
                self.serial_port.write(command.encode())  # Set timeout to 500ms
                # Wait for the specified delay before sending the next command
                time.sleep(self.command_delay)
                # Mark the command as done
                self.command_queue.task_done()
            except Exception as e:
                logging.error(f"Exception: {e}")
                self.command_queue.task_done()

    def set_frequency(self, frequency: int):

        if self.active_vfo == self.parser.VFO_A:
            self.frequency_vfo_a = frequency
            command = self.parser.generate_set_frequency(self.parser.VFO_A, frequency)
        elif self.active_vfo == self.parser.VFO_B:
            self.frequency_vfo_b = frequency
            command = self.parser.generate_set_frequency(self.parser.VFO_B, frequency)

        self.command_queue.put(command)

    def get_frequency(self):
        command = self.parser.generate_get_frequency(self.active_vfo)
        self.command_queue.put(command)

    def set_mode(self, mode: str):
        command = self.parser.generate_set_mode(mode)
        self.command_queue.put(command)
        if self.active_vfo == self.parser.VFO_A:
            self.mode_vfo_a = mode
        elif self.active_vfo == self.parser.VFO_B:
            self.mode_vfo_b = mode

    def get_mode(self, blocking=False):
        if blocking:
            self.mode_event.clear()
            command = self.parser.generate_get_mode()
            self.command_queue.put(command)
            if not self.mode_event.wait(
                timeout=1
            ):  # Block until we get back from the radio the actual mode or timeout
                raise TimeoutError("Failed to get mode within 1 second")
            if self.active_vfo == self.parser.VFO_A:
                return self.mode_vfo_a
            elif self.active_vfo == self.parser.VFO_B:
                return self.mode_vfo_b
        else:
            command = self.parser.generate_get_mode()
            self.command_queue.put(command)

    def set_transmit(self, transmit: bool):
        command = self.parser.generate_set_transmit(transmit)
        self.command_queue.put(command)

    def get_transmit(self, blocking=False):
        command = self.parser.generate_get_transmit()
        self.command_queue.put(command)

        if blocking:
            self.transmit_event.clear()
            if not self.transmit_event.wait(
                timeout=1
            ):  # Block until we get back from the radio the transmit status or timeout
                raise TimeoutError("Failed to get transmit status within 1 second")
            return self.transmit

    def set_txpower(self, power: int):
        command = self.parser.generate_set_txpower(power)
        self.command_queue.put(command)
        self.txpower = power

    def get_txpower(self, blocking=False):
        command = self.parser.generate_get_txpower()
        self.command_queue.put(command)

        if blocking:
            self.txpower_event.clear()
            if not self.txpower_event.wait(
                timeout=1
            ):  # Block until we get back from the radio the transmit power or timeout
                raise TimeoutError("Failed to get tx power within 1 second")
            return self.txpower

    def set_active_vfo(self, vfo: int):
        command = self.parser.generate_set_active_vfo(vfo)
        self.command_queue.put(command)
        self.active_vfo = vfo

    def get_active_vfo(self, blocking=False):
        command = self.parser.generate_get_active_vfo()
        self.command_queue.put(command)

        if blocking:
            self.active_vfo_event.clear()
            if not self.active_vfo_event.wait(
                timeout=1
            ):  # Block until we get back from the radio the active VFO or timeout
                raise TimeoutError("Failed to get active VFO within 1 second")
            return self.active_vfo

    def get_s_meter(self):
        command = self.parser.generate_get_s_meter()
        self.command_queue.put(command)

    def get_po_meter(self):
        command = self.parser.generate_get_po_meter()
        self.command_queue.put(command)

    def get_comp_meter(self):
        command = self.parser.generate_get_comp_meter()
        self.command_queue.put(command)

    def get_alc_meter(self):
        command = self.parser.generate_get_alc_meter()
        self.command_queue.put(command)

    def get_swr_meter(self):
        command = self.parser.generate_get_swr_meter()
        self.command_queue.put(command)

    def get_idd_meter(self):
        command = self.parser.generate_get_idd_meter()
        self.command_queue.put(command)

    def get_vdd_meter(self):
        command = self.parser.generate_get_vdd_meter()
        self.command_queue.put(command)

    def set_auto_information(self, enabled: bool):
        command = self.parser.generate_set_auto_information(enabled)
        self.command_queue.put(command)

    def disconnect(self):
        self.command_queue.join()  # Wait for all commands to be processed
        # Signal the threads to stop
        self.stop_event.set()

        # Stop the read and write threads
        self.read_thread.join(timeout=1)
        self.write_thread.join(timeout=1)

        # Close the serial port
        if self.serial_port.is_open:
            self.serial_port.close()

        # Clear the command queue
        with self.command_queue.mutex:
            self.command_queue.queue.clear()

        # Reset parser listeners
        self.parser.remove_all_listener(self)

        logging.info("Radio disconnected and cleaned up.")

    @overrides
    def on_frequency(self, event: FrequencyEvent) -> None:
        if event.vfo == self.parser.VFO_A:
            self.frequency_vfo_a = event.frequency
        elif event.vfo == self.parser.VFO_B:
            self.frequency_vfo_b = event.frequency

    @overrides
    def on_mode(self, event: ModeEvent) -> None:
        if event.vfo == self.parser.VFO_A:
            self.mode_vfo_a = event.mode
        elif event.vfo == self.parser.VFO_B:
            self.mode_vfo_b = event.mode
        elif event.vfo == self.parser.VFO_NONE:
            # No information for the VFO - we need to deduce which VFO mode was changed
            if self.active_vfo == self.parser.VFO_A:
                self.mode_vfo_a = event.mode
            else:
                self.mode_vfo_b = event.mode
        self.mode_event.set()  # Set the event to unblock get_mode

    @overrides
    def on_s_meter(self, event: SMeterEvent) -> None:
        self.s_meter = event.value

    @overrides
    def on_po_meter(self, event: POMeterEvent) -> None:
        self.txpower = event.value

    @overrides
    def on_swr_meter(self, event: SWRMeterEvent) -> None:
        self.swr = event.value

    @overrides
    def on_active_vfo(self, event: ActiveVFOEvent) -> None:
        self.active_vfo = event.vfo
        self.active_vfo_event.set()  # Set the event to unblock set_active_vfo

    @overrides
    def on_not_supported(self, event: NotSupportedEvent) -> None:
        print(f"Unsupported command: {event.response}")

    @overrides
    def on_comp_meter(self, event: COMPMeterEvent) -> None:
        self.comp = event.value

    @overrides
    def on_alc_meter(self, event: ALCMeterEvent) -> None:
        self.alc = event.value

    @overrides
    def on_vdd_meter(self, event: VDDMeterEvent) -> None:
        self.vdd = event.value

    @overrides
    def on_idd_meter(self, event: IDDMeterEvent) -> None:
        self.idd = event.value

    @overrides
    def on_tx_power(self, event: TXPowerEvent) -> None:
        self.txpower = event.value
        self.txpower_event.set()  # Set the event to unblock get_txpower

    @overrides
    def on_transmit(self, event: TransmitEvent) -> None:
        self.transmit = event.transmit
        self.transmit_event.set()  # Set the event to unblock get_transmit
