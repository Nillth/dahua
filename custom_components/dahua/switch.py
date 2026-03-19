"""Switch platform for dahua."""
from aiohttp import ClientError
from homeassistant.core import HomeAssistant
from homeassistant.components.switch import SwitchEntity
from custom_components.dahua import DahuaDataUpdateCoordinator

from .const import (
    DOMAIN, DISARMING_ICON, MOTION_DETECTION_ICON, SIREN_ICON, BELL_ICON,
    SECURITY_LIGHT_ICON, IVS_RULE_ICON, STROBE_ICON, VOICE_ALERT_ICON, NTP_ICON,
)
from .entity import DahuaBaseEntity
from .client import SIREN_TYPE


async def async_setup_entry(hass: HomeAssistant, entry, async_add_devices):
    """Setup sensor platform."""
    coordinator: DahuaDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # I think most cameras have a motion sensor so we'll blindly add a switch for it
    devices = [
        DahuaMotionDetectionBinarySwitch(coordinator, entry),
    ]

    # But only some cams have a siren, very few do actually
    if coordinator.supports_siren():
        devices.append(DahuaSirenBinarySwitch(coordinator, entry))
    if coordinator.supports_smart_motion_detection() or coordinator.supports_smart_motion_detection_amcrest():
        devices.append(DahuaSmartMotionDetectionBinarySwitch(coordinator, entry))

    if coordinator.supports_strobe_light():
        devices.append(DahuaStrobeLightSwitch(coordinator, entry))

    try:
        await coordinator.client.async_get_disarming_linkage()
        devices.append(DahuaDisarmingLinkageBinarySwitch(coordinator, entry))
        devices.append(DahuaDisarmingEventNotificationsLinkageBinarySwitch(coordinator, entry))
    except ClientError as exception:
        pass

    # Per-rule IVS switches
    for rule in coordinator.get_ivs_rules():
        devices.append(DahuaIVSRuleSwitch(coordinator, entry, rule))
        if rule["has_lighting_link"]:
            devices.append(DahuaIVSRuleStrobeLightSwitch(coordinator, entry, rule))
        if rule["has_voice"]:
            devices.append(DahuaIVSRuleVoiceAlertSwitch(coordinator, entry, rule))
        # Per-rule event handler switches
        for prop, label, icon in [
            ("RecordEnable", "Record", "mdi:record-rec"),
            ("SnapshotEnable", "Snapshot", "mdi:camera"),
            ("AlarmOutEnable", "Alarm Out", "mdi:alarm-bell"),
            ("BeepEnable", "Beep", "mdi:volume-high"),
        ]:
            devices.append(DahuaIVSRuleEventHandlerSwitch(coordinator, entry, rule, prop, label, icon))

    # SMD object type switches
    if coordinator.supports_smart_motion_detection():
        devices.append(DahuaSMDHumanSwitch(coordinator, entry))
        devices.append(DahuaSMDVehicleSwitch(coordinator, entry))

    # NTP switch
    if coordinator.supports_ntp():
        devices.append(DahuaNTPSwitch(coordinator, entry))

    async_add_devices(devices)


class DahuaMotionDetectionBinarySwitch(DahuaBaseEntity, SwitchEntity):
    """dahua motion detection switch class. Used to enable or disable motion detection"""

    async def async_turn_on(self, **kwargs):  # pylint: disable=unused-argument
        """Turn on/enable motion detection."""
        channel = self._coordinator.get_channel()
        await self._coordinator.client.enable_motion_detection(channel, True)
        await self._coordinator.async_refresh()

    async def async_turn_off(self, **kwargs):  # pylint: disable=unused-argument
        """Turn off/disable motion detection."""
        channel = self._coordinator.get_channel()
        await self._coordinator.client.enable_motion_detection(channel, False)
        await self._coordinator.async_refresh()

    @property
    def name(self):
        """Return the name of the switch."""
        return self._coordinator.get_device_name() + " " + "Motion Detection"

    @property
    def unique_id(self):
        """
        A unique identifier for this entity. Needs to be unique within a platform (ie light.hue). Should not be configurable by the user or be changeable
        see https://developers.home-assistant.io/docs/entity_registry_index/#unique-id-requirements
        """
        return self._coordinator.get_serial_number() + "_motion_detection"

    @property
    def icon(self):
        """Return the icon of this switch."""
        return MOTION_DETECTION_ICON

    @property
    def is_on(self):
        """
        Return true if the switch is on.
        Value is fetched from api.get_motion_detection_config
        """
        return self._coordinator.is_motion_detection_enabled()


class DahuaDisarmingLinkageBinarySwitch(DahuaBaseEntity, SwitchEntity):
    """will set the camera's disarming linkage (Event -> Disarming in the UI)"""

    async def async_turn_on(self, **kwargs):  # pylint: disable=unused-argument
        """Turn on/enable linkage"""
        channel = self._coordinator.get_channel()
        await self._coordinator.client.async_set_disarming_linkage(channel, True)
        await self._coordinator.async_refresh()

    async def async_turn_off(self, **kwargs):  # pylint: disable=unused-argument
        """Turn off/disable linkage"""
        channel = self._coordinator.get_channel()
        await self._coordinator.client.async_set_disarming_linkage(channel, False)
        await self._coordinator.async_refresh()

    @property
    def name(self):
        """Return the name of the switch."""
        return self._coordinator.get_device_name() + " " + "Disarming"

    @property
    def unique_id(self):
        """
        A unique identifier for this entity. Needs to be unique within a platform (ie light.hue). Should not be
        configurable by the user or be changeable see
        https://developers.home-assistant.io/docs/entity_registry_index/#unique-id-requirements
        """
        return self._coordinator.get_serial_number() + "_disarming"

    @property
    def icon(self):
        """Return the icon of this switch."""
        return DISARMING_ICON

    @property
    def is_on(self):
        """
        Return true if the switch is on.
        Value is fetched from client.async_get_linkage
        """
        return self._coordinator.is_disarming_linkage_enabled()

class DahuaDisarmingEventNotificationsLinkageBinarySwitch(DahuaBaseEntity, SwitchEntity):
    """will set the camera's event notifications when device is disarmed (Event -> Disarming -> Event Notifications in the UI)"""

    async def async_turn_on(self, **kwargs):  # pylint: disable=unused-argument
        """Turn on/enable event notifications"""
        channel = self._coordinator.get_channel()
        await self._coordinator.client.async_set_event_notifications(channel, True)
        await self._coordinator.async_refresh()

    async def async_turn_off(self, **kwargs):  # pylint: disable=unused-argument
        """Turn off/disable event notifications"""
        channel = self._coordinator.get_channel()
        await self._coordinator.client.async_set_event_notifications(channel, False)
        await self._coordinator.async_refresh()

    @property
    def name(self):
        """Return the name of the switch."""
        return self._coordinator.get_device_name() + " " + "Event Notifications"

    @property
    def unique_id(self):
        """
        A unique identifier for this entity. Needs to be unique within a platform (ie light.hue). Should not be
        configurable by the user or be changeable see
        https://developers.home-assistant.io/docs/entity_registry_index/#unique-id-requirements
        """
        return self._coordinator.get_serial_number() + "_event_notifications"

    @property
    def icon(self):
        """Return the icon of this switch."""
        return BELL_ICON

    @property
    def is_on(self):
        """
        Return true if the switch is on.
        """
        return self._coordinator.is_event_notifications_enabled()

class DahuaSmartMotionDetectionBinarySwitch(DahuaBaseEntity, SwitchEntity):
    """Enables or disables the Smart Motion Detection option in the camera"""

    async def async_turn_on(self, **kwargs):  # pylint: disable=unused-argument
        """Turn on SmartMotionDetect"""
        if self._coordinator.supports_smart_motion_detection_amcrest():
            await self._coordinator.client.async_set_ivs_rule(0, 0, True)
        else:
            await self._coordinator.client.async_enabled_smart_motion_detection(True)
        await self._coordinator.async_refresh()

    async def async_turn_off(self, **kwargs):  # pylint: disable=unused-argument
        """Turn off SmartMotionDetect"""
        if self._coordinator.supports_smart_motion_detection_amcrest():
            await self._coordinator.client.async_set_ivs_rule(0, 0, False)
        else:
            await self._coordinator.client.async_enabled_smart_motion_detection(False)
        await self._coordinator.async_refresh()

    @property
    def name(self):
        """Return the name of the switch."""
        return self._coordinator.get_device_name() + " " + "Smart Motion Detection"

    @property
    def unique_id(self):
        """
        A unique identifier for this entity. Needs to be unique within a platform (ie light.hue). Should not be
        configurable by the user or be changeable see
        https://developers.home-assistant.io/docs/entity_registry_index/#unique-id-requirements
        """
        return self._coordinator.get_serial_number() + "_smart_motion_detection"

    @property
    def icon(self):
        """Return the icon of this switch."""
        return MOTION_DETECTION_ICON

    @property
    def is_on(self):
        """ Return true if the switch is on. """
        return self._coordinator.is_smart_motion_detection_enabled()


class DahuaSirenBinarySwitch(DahuaBaseEntity, SwitchEntity):
    """dahua siren switch class. Used to enable or disable camera built in sirens"""

    async def async_turn_on(self, **kwargs):  # pylint: disable=unused-argument
        """Turn on/enable the camera's siren"""
        channel = self._coordinator.get_channel()
        await self._coordinator.client.async_set_coaxial_control_state(channel, SIREN_TYPE, True)
        await self._coordinator.async_refresh()

    async def async_turn_off(self, **kwargs):  # pylint: disable=unused-argument
        """Turn off/disable camera siren"""
        channel = self._coordinator.get_channel()
        await self._coordinator.client.async_set_coaxial_control_state(channel, SIREN_TYPE, False)
        await self._coordinator.async_refresh()

    @property
    def name(self):
        """Return the name of the switch."""
        return self._coordinator.get_device_name() + " Siren"

    @property
    def unique_id(self):
        """
        A unique identifier for this entity. Needs to be unique within a platform (ie light.hue). Should not be configurable by the user or be changeable
        see https://developers.home-assistant.io/docs/entity_registry_index/#unique-id-requirements
        """
        return self._coordinator.get_serial_number() + "_siren"

    @property
    def icon(self):
        """Return the icon of this switch."""
        return SIREN_ICON

    @property
    def is_on(self):
        """
        Return true if the siren is on.
        Value is fetched from api.get_motion_detection_config
        """
        return self._coordinator.is_siren_on()


class DahuaStrobeLightSwitch(DahuaBaseEntity, SwitchEntity):
    """Switch to enable or disable the strobe/lighting link on IVS rules"""

    async def async_turn_on(self, **kwargs):  # pylint: disable=unused-argument
        """Enable the strobe light link on IVS rules"""
        await self._coordinator.client.async_set_ivs_lighting_link(
            self._coordinator._strobe_light_enable_keys, True
        )
        await self._coordinator.async_refresh()

    async def async_turn_off(self, **kwargs):  # pylint: disable=unused-argument
        """Disable the strobe light link on IVS rules"""
        await self._coordinator.client.async_set_ivs_lighting_link(
            self._coordinator._strobe_light_enable_keys, False
        )
        await self._coordinator.async_refresh()

    @property
    def name(self):
        """Return the name of the switch."""
        return self._coordinator.get_device_name() + " Strobe Light"

    @property
    def unique_id(self):
        return self._coordinator.get_serial_number() + "_strobe_light"

    @property
    def icon(self):
        """Return the icon of this switch."""
        return SECURITY_LIGHT_ICON

    @property
    def is_on(self):
        """Return true if any IVS rule has strobe light link enabled."""
        return self._coordinator.is_strobe_light_on()


class DahuaIVSRuleSwitch(DahuaBaseEntity, SwitchEntity):
    """Per-rule IVS enable/disable switch."""

    def __init__(self, coordinator, entry, rule: dict):
        super().__init__(coordinator, entry)
        self._rule = rule
        self._config_key = rule["enable_key"]
        self._table_key = "table." + self._config_key

    async def async_turn_on(self, **kwargs):
        await self._coordinator.client.async_set_config(self._config_key, "true")
        await self._coordinator.async_refresh()

    async def async_turn_off(self, **kwargs):
        await self._coordinator.client.async_set_config(self._config_key, "false")
        await self._coordinator.async_refresh()

    @property
    def name(self):
        return "{0} {1}".format(
            self._coordinator.get_device_name(), self._rule["name"]
        )

    @property
    def unique_id(self):
        return "{0}_{1}_{2}_enable".format(
            self._coordinator.get_serial_number(),
            self._rule["config_name"].lower().replace("videoanalyserule", "var"),
            self._rule["index"],
        )

    @property
    def icon(self):
        return IVS_RULE_ICON

    @property
    def is_on(self):
        return self._coordinator.data.get(self._table_key, "").lower() == "true"


class DahuaIVSRuleStrobeLightSwitch(DahuaBaseEntity, SwitchEntity):
    """Per-rule strobe/lighting link enable switch."""

    def __init__(self, coordinator, entry, rule: dict):
        super().__init__(coordinator, entry)
        self._rule = rule
        self._config_key = rule["lighting_link_prefix"] + ".Enable"
        self._table_key = "table." + self._config_key

    async def async_turn_on(self, **kwargs):
        await self._coordinator.client.async_set_config(self._config_key, "true")
        await self._coordinator.async_refresh()

    async def async_turn_off(self, **kwargs):
        await self._coordinator.client.async_set_config(self._config_key, "false")
        await self._coordinator.async_refresh()

    @property
    def name(self):
        return "{0} {1} Strobe Light".format(
            self._coordinator.get_device_name(), self._rule["name"]
        )

    @property
    def unique_id(self):
        return "{0}_{1}_{2}_strobe_enable".format(
            self._coordinator.get_serial_number(),
            self._rule["config_name"].lower().replace("videoanalyserule", "var"),
            self._rule["index"],
        )

    @property
    def icon(self):
        return STROBE_ICON

    @property
    def is_on(self):
        return self._coordinator.data.get(self._table_key, "").lower() == "true"


class DahuaIVSRuleVoiceAlertSwitch(DahuaBaseEntity, SwitchEntity):
    """Per-rule voice alert enable switch."""

    def __init__(self, coordinator, entry, rule: dict):
        super().__init__(coordinator, entry)
        self._rule = rule
        self._config_key = rule["voice_key"]
        self._table_key = "table." + self._config_key

    async def async_turn_on(self, **kwargs):
        await self._coordinator.client.async_set_config(self._config_key, "true")
        await self._coordinator.async_refresh()

    async def async_turn_off(self, **kwargs):
        await self._coordinator.client.async_set_config(self._config_key, "false")
        await self._coordinator.async_refresh()

    @property
    def name(self):
        return "{0} {1} Voice Alert".format(
            self._coordinator.get_device_name(), self._rule["name"]
        )

    @property
    def unique_id(self):
        return "{0}_{1}_{2}_voice_alert".format(
            self._coordinator.get_serial_number(),
            self._rule["config_name"].lower().replace("videoanalyserule", "var"),
            self._rule["index"],
        )

    @property
    def icon(self):
        return VOICE_ALERT_ICON

    @property
    def is_on(self):
        return self._coordinator.data.get(self._table_key, "").lower() == "true"


class DahuaNTPSwitch(DahuaBaseEntity, SwitchEntity):
    """Switch to enable/disable NTP time synchronization."""

    async def async_turn_on(self, **kwargs):
        await self._coordinator.client.async_set_config("NTP.Enable", "true")
        await self._coordinator.async_refresh()

    async def async_turn_off(self, **kwargs):
        await self._coordinator.client.async_set_config("NTP.Enable", "false")
        await self._coordinator.async_refresh()

    @property
    def name(self):
        return self._coordinator.get_device_name() + " NTP"

    @property
    def unique_id(self):
        return self._coordinator.get_serial_number() + "_ntp_enable"

    @property
    def icon(self):
        return NTP_ICON

    @property
    def is_on(self):
        return self._coordinator.get_ntp_enabled()


class DahuaIVSRuleEventHandlerSwitch(DahuaBaseEntity, SwitchEntity):
    """Per-rule event handler boolean switch (RecordEnable, SnapshotEnable, etc)."""

    def __init__(self, coordinator, entry, rule: dict, prop: str, label: str, icon: str):
        super().__init__(coordinator, entry)
        self._rule = rule
        self._prop = prop
        self._label = label
        self._icon = icon
        self._config_key = rule["event_handler_prefix"] + ".{0}".format(prop)
        self._table_key = "table." + self._config_key

    async def async_turn_on(self, **kwargs):
        await self._coordinator.client.async_set_config(self._config_key, "true")
        await self._coordinator.async_refresh()

    async def async_turn_off(self, **kwargs):
        await self._coordinator.client.async_set_config(self._config_key, "false")
        await self._coordinator.async_refresh()

    @property
    def name(self):
        return "{0} {1} {2}".format(
            self._coordinator.get_device_name(), self._rule["name"], self._label
        )

    @property
    def unique_id(self):
        return "{0}_{1}_{2}_{3}".format(
            self._coordinator.get_serial_number(),
            self._rule["config_name"].lower().replace("videoanalyserule", "var"),
            self._rule["index"],
            self._prop.lower(),
        )

    @property
    def icon(self):
        return self._icon

    @property
    def is_on(self):
        return self._coordinator.data.get(self._table_key, "").lower() == "true"


class DahuaSMDHumanSwitch(DahuaBaseEntity, SwitchEntity):
    """Switch to enable/disable SMD Human detection."""

    async def async_turn_on(self, **kwargs):
        channel = self._coordinator.get_channel()
        await self._coordinator.client.async_set_config(
            "SmartMotionDetect[{0}].ObjectTypes.Human".format(channel), "true"
        )
        await self._coordinator.async_refresh()

    async def async_turn_off(self, **kwargs):
        channel = self._coordinator.get_channel()
        await self._coordinator.client.async_set_config(
            "SmartMotionDetect[{0}].ObjectTypes.Human".format(channel), "false"
        )
        await self._coordinator.async_refresh()

    @property
    def name(self):
        return self._coordinator.get_device_name() + " SMD Human"

    @property
    def unique_id(self):
        return self._coordinator.get_serial_number() + "_smd_human"

    @property
    def icon(self):
        return MOTION_DETECTION_ICON

    @property
    def is_on(self):
        return self._coordinator.is_smd_human_enabled()


class DahuaSMDVehicleSwitch(DahuaBaseEntity, SwitchEntity):
    """Switch to enable/disable SMD Vehicle detection."""

    async def async_turn_on(self, **kwargs):
        channel = self._coordinator.get_channel()
        await self._coordinator.client.async_set_config(
            "SmartMotionDetect[{0}].ObjectTypes.Vehicle".format(channel), "true"
        )
        await self._coordinator.async_refresh()

    async def async_turn_off(self, **kwargs):
        channel = self._coordinator.get_channel()
        await self._coordinator.client.async_set_config(
            "SmartMotionDetect[{0}].ObjectTypes.Vehicle".format(channel), "false"
        )
        await self._coordinator.async_refresh()

    @property
    def name(self):
        return self._coordinator.get_device_name() + " SMD Vehicle"

    @property
    def unique_id(self):
        return self._coordinator.get_serial_number() + "_smd_vehicle"

    @property
    def icon(self):
        return MOTION_DETECTION_ICON

    @property
    def is_on(self):
        return self._coordinator.is_smd_vehicle_enabled()
