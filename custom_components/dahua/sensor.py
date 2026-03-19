"""Sensor entity platform for Dahua — NTP server, Network IP/MAC."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant

from .const import DOMAIN, NTP_ICON, NETWORK_ICON
from .entity import DahuaBaseEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_devices):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    devices = []

    if coordinator.supports_ntp():
        devices.append(DahuaNTPServerSensor(coordinator, entry))

    if coordinator.supports_network():
        devices.append(DahuaIPAddressSensor(coordinator, entry))
        devices.append(DahuaMACAddressSensor(coordinator, entry))

    async_add_devices(devices)


class DahuaNTPServerSensor(DahuaBaseEntity, SensorEntity):
    """Sensor showing the configured NTP server address."""

    @property
    def name(self):
        return self._coordinator.get_device_name() + " NTP Server"

    @property
    def unique_id(self):
        return self._coordinator.get_serial_number() + "_ntp_server"

    @property
    def icon(self):
        return NTP_ICON

    @property
    def native_value(self):
        return self._coordinator.get_ntp_server()


class DahuaIPAddressSensor(DahuaBaseEntity, SensorEntity):
    """Sensor showing the device's IP address."""

    @property
    def name(self):
        return self._coordinator.get_device_name() + " IP Address"

    @property
    def unique_id(self):
        return self._coordinator.get_serial_number() + "_ip_address"

    @property
    def icon(self):
        return NETWORK_ICON

    @property
    def native_value(self):
        return self._coordinator.get_network_ip()


class DahuaMACAddressSensor(DahuaBaseEntity, SensorEntity):
    """Sensor showing the device's MAC address."""

    @property
    def name(self):
        return self._coordinator.get_device_name() + " MAC Address"

    @property
    def unique_id(self):
        return self._coordinator.get_serial_number() + "_mac_address"

    @property
    def icon(self):
        return NETWORK_ICON

    @property
    def native_value(self):
        return self._coordinator.get_network_mac()
