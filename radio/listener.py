from radio.events import *


class RadioListener:
    def on_not_supported(self, event: NotSupportedEvent) -> None:
        pass

    def on_confirmation(self, event: ConfirmationEvent) -> None:
        pass

    def on_frequency(self, event: FrequencyEvent) -> None:
        pass

    def on_mode(self, event: ModeEvent) -> None:
        pass

    def on_active_vfo(self, event: ActiveVFOEvent) -> None:
        pass

    def on_s_meter(self, event: SMeterEvent) -> None:
        pass

    def on_po_meter(self, event: POMeterEvent) -> None:
        pass

    def on_swr_meter(self, event: SWRMeterEvent) -> None:
        pass

    def on_vdd_meter(self, event: VDDMeterEvent) -> None:
        pass

    def on_idd_meter(self, event: IDDMeterEvent) -> None:
        pass

    def on_comp_meter(self, event: COMPMeterEvent) -> None:
        pass

    def on_alc_meter(self, event: ALCMeterEvent) -> None:
        pass

    def on_tx_power(self, event: TXPowerEvent) -> None:
        pass

    def on_transmit(self, event: TransmitEvent) -> None:
        """
        Called when a transmit event is received.

        :param event: An instance of TransmitEvent.
        """
        pass
