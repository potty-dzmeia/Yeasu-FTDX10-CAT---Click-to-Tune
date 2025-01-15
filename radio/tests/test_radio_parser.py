import unittest

import sys
import os

# Get the directory of the current script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory of the script directory
PARENT_DIR = os.path.dirname(SCRIPT_DIR)

sys.path.append(os.path.dirname(PARENT_DIR))

from radio.radioparser import RadioParser
from radio.listener import RadioListener
from radio.events import (
    FrequencyEvent,
    ModeEvent,
    ActiveVFOEvent,
    SMeterEvent,
    POMeterEvent,
    SWRMeterEvent,
    VDDMeterEvent,
    IDDMeterEvent,
    COMPMeterEvent,
    ALCMeterEvent,
    NotSupportedEvent,
)


class MockListener(RadioListener):
    def __init__(self):
        self.event = None

    def on_frequency(self, event: FrequencyEvent):
        self.event = event

    def on_mode(self, event: ModeEvent):
        self.event = event

    def on_active_vfo(self, event: ActiveVFOEvent):
        self.event = event

    def on_s_meter(self, event: SMeterEvent):
        self.event = event

    def on_po_meter(self, event: POMeterEvent):
        self.event = event

    def on_swr_meter(self, event: SWRMeterEvent):
        self.event = event

    def on_vdd_meter(self, event: VDDMeterEvent):
        self.event = event

    def on_idd_meter(self, event: IDDMeterEvent):
        self.event = event

    def on_comp_meter(self, event: COMPMeterEvent):
        self.event = event

    def on_alc_meter(self, event: ALCMeterEvent):
        self.event = event

    def on_not_supported(self, event: NotSupportedEvent):
        self.event = event


class TestRadioParser(unittest.TestCase):
    def setUp(self):
        self.radio = RadioParser()
        self.listener = MockListener()
        self.radio.add_listener(self.listener)

    def test_parse_frequency_vfo_a(self):
        self.radio.parse(b"FA144100000;")
        self.assertIsInstance(self.listener.event, FrequencyEvent)
        self.assertEqual(self.listener.event.frequency, "144100000")
        self.assertEqual(self.listener.event.vfo, RadioParser.VFO_A)

    def test_parse_frequency_vfo_b(self):
        self.radio.parse(b"FB144100000;")
        self.assertIsInstance(self.listener.event, FrequencyEvent)
        self.assertEqual(self.listener.event.frequency, "144100000")
        self.assertEqual(self.listener.event.vfo, RadioParser.VFO_B)

    def test_parse_mode(self):
        self.radio.parse(b"MD01;")
        self.assertIsInstance(self.listener.event, ModeEvent)
        self.assertEqual(self.listener.event.mode, "lsb")

    def test_parse_txpower(self):
        self.radio.parse(b"PC056;")
        self.assertIsInstance(self.listener.event, ModeEvent)
        self.assertEqual(self.listener.event.mode, 56)

    def test_parse_active_vfo(self):
        self.radio.parse(b"VS0;")
        self.assertIsInstance(self.listener.event, ActiveVFOEvent)
        self.assertEqual(self.listener.event.vfo, RadioParser.VFO_A)

    def test_parse_active_vfo(self):
        self.radio.parse(b"VS1;")
        self.assertIsInstance(self.listener.event, ActiveVFOEvent)
        self.assertEqual(self.listener.event.vfo, RadioParser.VFO_B)

    def test_parse_smeter(self):
        self.radio.parse(b"SM005;")
        self.assertIsInstance(self.listener.event, SMeterEvent)
        self.assertEqual(self.listener.event.value, 5)

    def test_parse_read_meter(self):
        self.radio.parse(b"RM1005;")
        self.assertIsInstance(self.listener.event, SMeterEvent)
        self.assertEqual(self.listener.event.value, 5)

    def test_parse_not_supported(self):
        self.radio.parse(b"XX0000;")
        self.assertIsInstance(self.listener.event, NotSupportedEvent)
        self.assertEqual(self.listener.event.response, "XX0000;")

    def test_generate_frequency_vfo_a(self):
        command = self.radio.generate_set_frequency(RadioParser.VFO_A, 144100000)
        self.assertEqual(command, "FA144100000;")

    def test_generate_frequency_vfo_b(self):
        command = self.radio.generate_set_frequency(RadioParser.VFO_B, 144100000)
        self.assertEqual(command, "FB144100000;")

    def test_generate_mode(self):
        command = self.radio.generate_set_mode("lsb")
        self.assertEqual(command, "MD01;")

    def test_generate_set_mode_usb(self):
        command = self.radio.generate_set_mode("usb")
        self.assertEqual(command, "MD02;")

    def test_generate_mode_cw(self):
        command = self.radio.generate_set_mode("cw")
        self.assertEqual(command, "MD03;")

    def test_generate_mode_fm(self):
        command = self.radio.generate_set_mode("fm")
        self.assertEqual(command, "MD04;")

    def test_generate_mode_am(self):
        command = self.radio.generate_set_mode("am")
        self.assertEqual(command, "MD05;")

    def test_generate_mode_digital(self):
        command = self.radio.generate_set_mode("rtty")
        self.assertEqual(command, "MD06;")

    def test_generate_mode_packet(self):
        command = self.radio.generate_set_mode("cwr")
        self.assertEqual(command, "MD07;")

    def test_generate_mode_packet(self):
        command = self.radio.generate_set_mode("rttyr")
        self.assertEqual(command, "MD09;")

    def test_generate_mode(self):
        command = self.radio.generate_get_active_vfo()
        self.assertEqual(command, "VS;")

    def test_generate_active_vfo_a(self):
        command = self.radio.generate_set_active_vfo(RadioParser.VFO_A)
        self.assertEqual(command, "VS0;")

    def test_generate_active_vfo_a(self):
        command = self.radio.generate_set_active_vfo(RadioParser.VFO_B)
        self.assertEqual(command, "VS1;")

    def test_generate_get_po_meter(self):
        command = self.radio.generate_get_po_meter()
        self.assertEqual(command, "RM5;")

    def test_generate_get_s_meter(self):
        command = self.radio.generate_get_s_meter()
        self.assertEqual(command, "RM1;")

    def test_generate_get_swr_meter(self):
        command = self.radio.generate_get_swr_meter()
        self.assertEqual(command, "RM6;")

    def test_generate_get_vdd_meter(self):
        command = self.radio.generate_get_vdd_meter()
        self.assertEqual(command, "RM8;")

    def test_generate_get_idd_meter(self):
        command = self.radio.generate_get_idd_meter()
        self.assertEqual(command, "RM7;")

    def test_generate_get_comp_meter(self):
        command = self.radio.generate_get_comp_meter()
        self.assertEqual(command, "RM3;")

    def test_generate_get_alc_meter(self):
        command = self.radio.generate_get_alc_meter()
        self.assertEqual(command, "RM4;")


if __name__ == "__main__":
    unittest.main()
