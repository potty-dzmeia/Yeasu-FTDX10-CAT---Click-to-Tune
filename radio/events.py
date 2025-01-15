class NotSupportedEvent:
    def __init__(self, response: str):
        self.response = response


class ConfirmationEvent:
    def __init__(self, response: str):
        self.response = response


class FrequencyEvent:
    def __init__(self, frequency: str, vfo: int):
        self.frequency = frequency
        self.vfo = vfo


class ModeEvent:
    def __init__(self, mode: int, vfo: int):
        self.mode = mode
        self.vfo = vfo


class ActiveVFOEvent:
    def __init__(self, vfo: int):
        self.vfo = vfo


class SMeterEvent:
    def __init__(self, value: int):
        self.value = value


class POMeterEvent:
    def __init__(self, value: int):
        self.value = value


class SWRMeterEvent:
    def __init__(self, value: int):
        self.value = value


class VDDMeterEvent:
    def __init__(self, value: int):
        self.value = value


class IDDMeterEvent:
    def __init__(self, value: int):
        self.value = value


class COMPMeterEvent:
    def __init__(self, value: int):
        self.value = value


class ALCMeterEvent:
    def __init__(self, value: int):
        self.value = value


class TXPowerEvent:
    def __init__(self, value: int):
        self.value = value


class TransmitEvent:
    def __init__(self, transmit: bool):
        self.transmit = transmit

    def __str__(self):
        return f"TransmitEvent(transmit={self.transmit})"
