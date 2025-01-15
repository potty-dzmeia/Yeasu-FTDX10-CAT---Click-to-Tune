from typing import List
import logging
from radio.listener import RadioListener
from radio.events import *


class RadioParser:
    """
    The RadioParser class is responsible for generating commands to control a radio
    and parsing incoming data from the radio. It supports various radio operations
    such as setting/getting frequency, mode, transmit status, and reading meter values.
    The class also allows adding listeners to handle events generated from the parsed data.
    """

    # Possible radio modes
    MODES = [
        "none",
        "am",  # AM -- Amplitude Modulation
        "cw",  # CW - CW "normal" sideband
        "usb",  # USB - Upper Side Band
        "lsb",  # LSB - Lower Side Band
        "rtty",  # RTTY - Radio Teletype
        "fm",  # FM - "narrow" band FM
        "wfm",  # WFM - broadcast wide FM
        "cwr",  # CWR - CW "reverse" sideband
        "rttyr",  # RTTYR - RTTY "reverse" sideband
        "ams",  # AMS - Amplitude Modulation Synchronous
        "pktlsb",  # PKTLSB - Packet/Digital LSB mode (dedicated port)
        "pktusb",  # PKTUSB - Packet/Digital USB mode (dedicated port)
        "pktfn",  # PKTFM - Packet/Digital FM mode (dedicated port)
        "ecssusb",  # ECSSUSB - Exalted Carrier Single Sideband USB
        "ecsslsb",  # ECSSLSB - Exalted Carrier Single Sideband LSB
        "fax",  # FAX - Facsimile Mode
        "sam",  # SAM - Synchronous AM double sideband
        "sal",  # SAL - Synchronous AM lower sideband
        "sah",  # SAH - Synchronous AM upper (higher) sideband
        "dsb",  # DSB - Double sideband suppressed carrier
    ]

    #
    mode_codes = {
        "lsb": 0x01,
        "usb": 0x02,
        "cw": 0x03,
        "fm": 0x04,
        "am": 0x05,
        "rtty": 0x06,
        "cwr": 0x07,
        "rttyr": 0x09,
    }

    # Mapping of VFO letters to numbers
    VFO_NONE = -1
    VFO_A = 0
    VFO_B = 1

    def __init__(self):
        """
        Initializes the Radio class.
        """
        self.listeners: List[RadioListener] = []
        self.parsers = {
            "FA": self.__parse_frequency_vfo_a,  # VFO A frequency
            "FB": self.__parse_frequency_vfo_b,  # VFO B frequency
            "VS": self.__parse_active_vfo,  # active Vfo
            "MD": self.__parse_mode,  # Operating mode
            "IF": self.__parse_info_vfo_a,  # IF (Transceiver Information; GET only)
            "OI": self.__parse_info_vfo_b,  # IF (Transceiver Information; GET only)
            "RM": self.__parse_read_meter,  # RM - Read Meter
            "SM": self.__parse_smeter,  # S-meter values
            "PC": self.__parse_txpower,  # TX power
            "TX": self.__parse_transmit,  # Transmit status
        }

    def add_listener(self, listener: RadioListener) -> None:
        """
        Adds a listener to receive radio events.

        :param listener: An instance of RadioListener.
        """
        self.listeners.append(listener)

    def remove_all_listener(self, listener: RadioListener) -> None:
        """
        Removes a listener from receiving radio events.

        :param listener: An instance of RadioListener.
        """
        if listener in self.listeners:
            self.listeners.remove(listener)

    def generate_get_frequency(self, vfo: int) -> str:
        """
        Generates the command to get the current frequency from the radio.
        vfo: VFO_A or VFO_B
        :return: Raw data string to send to the radio.
        """

        if vfo == self.VFO_A:
            vfo = "A"
        elif vfo == self.VFO_B:
            vfo = "B"

        return "F%c;" % (vfo)

    def generate_set_frequency(self, vfo: int, frequency: int) -> str:
        """
        Generates the command to set the frequency on the radio for a specific VFO.

        :param frequency: The frequency to set in Hz(e.g., 144100000).
        :type frequency: int
        :param vfo: The VFO to set the frequency on (VFO_A or VFO_B).
        :type vfo: int
        :return: Raw data string to send to the radio.
        """
        if vfo == self.VFO_A:
            vfo = "A"
        elif vfo == self.VFO_B:
            vfo = "B"

        return "F%c%09ld;" % (vfo, frequency)

    def generate_get_mode(self) -> str:
        """
        Generates the command to get the current mode from the radio.

        :return: Raw data string to send to the radio.
        """
        return "MD0;"

    def generate_set_mode(self, mode: str) -> str:
        """
        Generates the command to set the mode on the radio.

        :param mode: The mode to set (e.g., "LSB", "USB").
        :return: Raw data string to send to the radio.
        """
        mode = str(mode).lower()
        if not self.mode_codes.__contains__(mode):
            raise ValueError("Unsupported mode: " + mode + " !")

        result = "MD0%d;" % (self.mode_codes[mode])

        return result

    def generate_get_transmit(self) -> str:
        """
        Generates the command to get the current transmit status.

        :return: Raw data string to send to the radio.
        """
        return "TX;"

    def generate_set_transmit(self, transmit: bool) -> str:
        """
        Generates the command to set the transmit status on the radio.

        :param transmit: Whether to set transmit on (`True`) or off (`False`).
        :return: Raw data string to send to the radio.
        """
        return "TX1;" if transmit else "TX0;"

    def generate_get_txpower(self) -> str:
        """
        Generates the command to read the PO (Power Output) on the radio which is currently set

        :return: Raw data string to send to the radio.
        """
        return "PC;"

    def generate_set_txpower(self, po: int) -> str:
        """
        Generates the command to set the PO (Power Output) on the radio.

        :return: Raw data string to send to the radio.
        """
        if po < 5:
            po = 5
        elif po > 100:
            po = 100
        return "PC%03d;" % po

    def generate_set_auto_information(self, enabled: bool) -> str:
        """
        Generates the command to set the auto information on the radio.

        :param enabled: Whether to set auto information on (`True`) or off (`False`).
        :return: Raw data string to send to the radio.
        """
        return "AI1;" if enabled else "AI0;"

    def generate_get_active_vfo(self) -> str:
        """

        :return: Raw data string to send to the radio.
        """

        return "VS;"

    def generate_set_active_vfo(self, activate_vfo: int) -> str:
        """
        :param activate_vfo: VFO_A or VFO_B
        :return: Raw data string to send to the radio.
        """

        if activate_vfo == self.VFO_A:
            return "VS0;"
        elif activate_vfo == self.VFO_B:
            return "VS1;"
        else:
            raise ValueError("Unsupported VFO: " + str(activate_vfo))

    def generate_get_s_meter(self) -> str:
        """
        Generates the command to get the current PO (Power Output) from the radio.

        :return: Raw data string to send to the radio.
        """
        return "RM1;"

    def generate_get_po_meter(self) -> str:
        """
        Generates the command to get the current PO (Power Output) from the radio.

        :return: Raw data string to send to the radio.
        """
        return "RM5;"

    def generate_get_comp_meter(self) -> str:
        """
        Generates the command to get the current COMP (Compressor) setting.

        :return: Raw data string to send to the radio.
        """
        return "RM3;"

    def generate_get_alc_meter(self) -> str:
        """
        Generates the command to get the current ALC (Automatic Level Control) setting.

        :return: Raw data string to send to the radio.
        """
        return "RM4;"

    def generate_get_swr_meter(self) -> str:
        """
        Generates the command to get the current SWR (Standing Wave Ratio) reading.

        :return: Raw data string to send to the radio.
        """
        return "RM6;"

    def generate_get_idd_meter(self) -> str:
        """
        Generates the command to get the current IDD (Current Drain) reading.

        :return: Raw data string to send to the radio.
        """
        return "RM7;"

    def generate_get_vdd_meter(self) -> str:
        """
        Generates the command to get the current VDD (Voltage) reading.

        :return: Raw data string to send to the radio.
        """
        return "RM8;"

    def parse(self, data: bytes) -> int:
        """
        Extracts and decodes the first radio command found within the supplied buffer.

        This method searches for the ";" character, which signals the end of a command.
        If a complete command is found, it is parsed and processed. The method returns
        the number of bytes processed.

        Example of a Yaesu command: "FB00007000000;"

        :param data: Series of bytes from which we must extract the incoming command.
        :type data: bytes
        :return: The number of bytes processed. Returns 0 if no complete command is found.
        :rtype: int
        """
        # Find the character ";" which signals the end of the command
        data_str = data.decode("utf-8")
        end = data_str.find(";")

        # The incoming data does not contain one complete transaction...
        if end == -1:
            return 0

        self.__parse(data_str[: end + 1])

        return end + 1

    def __parse(self, data: str) -> None:
        """
        Parses the string data and calls listeners based on the command.

        :param trans: A single transaction string coming from the radio that we have to parse to a meaningful JSON block
        :type trans: str
        """
        for s in self.parsers:
            if data.startswith(s):  # if we have parser for the current command...
                fn = self.parsers[s]
                fn(data)  # call the responsible parser
                return

        logging.info("Not supported command coming from the radio: " + data)
        for listener in self.listeners:
            listener.on_not_supported(NotSupportedEvent(data))

    def __parse_frequency_vfo_a(self, command: str) -> None:
        """
        Extracts the Frequency value from the command.

        :param command: String of the type "FA00007000000;"
        :type command: str
        """
        frequency = command[
            2:-1
        ]  # Extract the frequency value without stripping leading zeros
        for listener in self.listeners:
            listener.on_frequency(FrequencyEvent(frequency, self.VFO_A))

    def __parse_frequency_vfo_b(self, command: str) -> None:
        """
        Extracts the Frequency value from the command

        :param command: String of the type "FB00007000000;"
        :type command: str
        """
        for listener in self.listeners:
            listener.on_frequency(FrequencyEvent(command[2:-1], self.VFO_B))

    def __parse_active_vfo(self, command: str) -> None:
        """
        Extracts active VFO from the command

        :param command: String of the type "VS1;"
        :type command: str
        """
        if int(command[2]) == self.VFO_A:
            for listener in self.listeners:
                listener.on_active_vfo(ActiveVFOEvent(self.VFO_A))
        elif int(command[2]) == self.VFO_B:
            for listener in self.listeners:
                listener.on_active_vfo(ActiveVFOEvent(self.VFO_B))

    def __parse_mode(self, command: str) -> None:
        """
        Extracts the Mode value from the command

        :param command: String of the type "MD01;"
        :type command: str
        """

        mode = self.__mode_from_byte_to_string(int(command[3]))

        for listener in self.listeners:
            listener.on_mode(ModeEvent(mode, self.VFO_NONE))

    def __parse_info_vfo_a(self, command: str) -> None:
        """
        Parse the IF command.
        I F P1 P1 P1 P2 P2 P2 P2 P2 P2 P2 P2 P3 P3 P3 P3 P3 P4 P5 P6 P7 P8 P9 P9 P10  ;
        0 1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25  26

        P6 MODE
        P2 VFO-A Frequency
        P7 0: VFO 1: ....

        [0-1] - IF
        [3-13] - frequency
        [31] - Operating mode (refer to the MD command)

        :param command: String containing the "IF" command
        :type command: str
        """

        mode = self.__mode_from_byte_to_string(int(command[21]))
        freq = command[5:13]
        for listener in self.listeners:
            listener.on_mode(ModeEvent(mode, self.VFO_A))
        for listener in self.listeners:
            listener.on_frequency(FrequencyEvent(freq.strip("0"), self.VFO_A))

    def __parse_info_vfo_b(self, command: str) -> None:
        """
        Parse the IF command.
        O I P1 P1 P1 P2 P2 P2 P2 P2 P2 P2 P2 P3 P3 P3 P3 P3 P4 P5 P6 P7 P8 P9 P9 P10  ;
        0 1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25  26

        P6 MODE
        P2 VFO-B Frequency
        P7 0: VFO

        [0-1] - OI
        [3-13] - frequency
        [31] - Operating mode (refer to the MD command)

        :param command: String containing the "IF" command
        :type command: str
        """

        mode = self.__mode_from_byte_to_string(int(command[21]))
        freq = command[5:13]
        for listener in self.listeners:
            listener.on_mode(ModeEvent(mode, self.VFO_B))
        for listener in self.listeners:
            listener.on_frequency(FrequencyEvent(freq.strip("0"), self.VFO_B))

    def __parse_smeter(self, command: str) -> None:
        """
        Extracts the Smeter value from the command

        :param command: String starting of the type "SM0005;"
        :type command: str
        """
        smeter = command[3:-1]
        for listener in self.listeners:
            listener.on_mode(SMeterEvent(int(smeter)))

    def __parse_read_meter(self, command: str) -> None:
        """
        Parses the Read Meter command

        :param command: String is of the type "RM[P1][P2][P2][P2][P3][P3][P3];" where [P1] 1:S 2:- 3:COMP 4:ALC 5:PO 6:SWR 7:IDD 8:VDD;  [P2]: 0 - 255; [P3]: 000 (Fixed)
        :type command: str
        """

        result = dict()

        meter_types = {
            "1": "S",
            "3": "COMP",
            "4": "ALC",
            "5": "PO",
            "6": "SWR",
            "7": "IDD",
            "8": "VDD",
        }

        p1 = command[2]  # [P1]: Meter type
        p2 = command[3:6]  # [P2]: Meter reading (3 digits)

        # Map [P1] to meter type
        meter_type = meter_types.get(p1, "Unknown")
        if meter_type == "S":
            for listener in self.listeners:
                listener.on_s_meter(SMeterEvent(int(p2)))
        elif meter_type == "COMP":
            for listener in self.listeners:
                listener.on_comp_meter(COMPMeterEvent(int(p2)))
        elif meter_type == "ALC":
            for listener in self.listeners:
                listener.on_alc_meter(ALCMeterEvent(int(p2)))
        elif meter_type == "PO":
            for listener in self.listeners:
                listener.on_po_meter(POMeterEvent(int(p2)))
        elif meter_type == "SWR":
            for listener in self.listeners:
                listener.on_swr_meter(SWRMeterEvent(int(p2)))
        elif meter_type == "IDD":
            for listener in self.listeners:
                listener.on_idd_meter(IDDMeterEvent(int(p2)))
        elif meter_type == "VDD":
            for listener in self.listeners:
                listener.on_vdd_meter(VDDMeterEvent(int(p2)))
        else:
            for listener in self.listeners:
                listener.on_not_supported(NotSupportedEvent(command))

    def __parse_txpower(self, command: str) -> None:
        """
        Extracts the TX power value from the command.

        :param command: String of the type "PCXXX;"
        :type command: str
        """
        txpower = int(command[2:5])
        for listener in self.listeners:
            listener.on_tx_power(TXPowerEvent(txpower))

    def __parse_transmit(self, command: str) -> None:
        """
        Extracts the transmit status from the command.

        :param command: String of the type "TX0;", "TX1;", "TX2;"
        :type command: str
        """
        transmit = command[2] == "2"
        for listener in self.listeners:
            listener.on_transmit(TransmitEvent(transmit))

    @classmethod
    def __mode_from_byte_to_string(cls, mode: int) -> str:
        """
        Returns a string describing the current working mode
        :param mode: Integer describing the mode see cls.mode_codes
        :type mode: int
        :return: String describing the working mode cls.mode_codes
        :rtype: str
        """

        # Convert the "mode" to valid string
        for key, value in cls.mode_codes.items():
            if mode == value:
                logging.info("returns = " + key)
                return key

        # In case of unknown mode integer
        return "none"
