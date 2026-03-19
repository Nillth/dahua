"""
Select entity platform for dahua.
https://developers.home-assistant.io/docs/core/entity/select
Requires HomeAssistant 2021.7.0 or greater
"""
from homeassistant.core import HomeAssistant
from homeassistant.components.select import SelectEntity
from custom_components.dahua import DahuaDataUpdateCoordinator

from .const import DOMAIN, STROBE_ICON, MOTION_DETECTION_ICON
from .entity import DahuaBaseEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_devices):
    """Setup select platform."""
    coordinator: DahuaDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    devices = []

    if coordinator.is_amcrest_doorbell() and coordinator.supports_security_light():
        devices.append(DahuaDoorbellLightSelect(coordinator, entry))

    #if coordinator._supports_ptz_position:
    devices.append(DahuaCameraPresetPositionSelect(coordinator, entry))

    # Per-rule strobe selects (Remote rules only)
    for rule in coordinator.get_ivs_rules():
        if rule["has_lighting_link"] and rule["is_remote"]:
            devices.append(DahuaStrobeLightTypeSelect(coordinator, entry, rule))
            devices.append(DahuaStrobeLightModeSelect(coordinator, entry, rule))

    # SMD Sensitivity select
    if coordinator.supports_smart_motion_detection():
        devices.append(DahuaSMDSensitivitySelect(coordinator, entry))

    async_add_devices(devices)


class DahuaDoorbellLightSelect(DahuaBaseEntity, SelectEntity):
    """allows one to turn the doorbell light on/off/strobe"""

    def __init__(self, coordinator: DahuaDataUpdateCoordinator, config_entry):
        DahuaBaseEntity.__init__(self, coordinator, config_entry)
        SelectEntity.__init__(self)
        self._coordinator = coordinator
        self._attr_name = f"{coordinator.get_device_name()} Security Light"
        self._attr_unique_id = f"{coordinator.get_serial_number()}_security_light"
        self._attr_options = ["Off", "On", "Strobe"]

    @property
    def current_option(self) -> str:
        mode = self._coordinator.data.get("table.Lighting_V2[0][0][1].Mode", "")
        state = self._coordinator.data.get("table.Lighting_V2[0][0][1].State", "")

        if mode == "ForceOn" and state == "On":
            return "On"

        if mode == "ForceOn" and state == "Flicker":
            return "Strobe"

        return "Off"

    async def async_select_option(self, option: str) -> None:
        await self._coordinator.client.async_set_lighting_v2_for_amcrest_doorbells(option)
        await self._coordinator.async_refresh()

    @property
    def name(self):
        return self._attr_name

    @property
    def unique_id(self):
        """ https://developers.home-assistant.io/docs/entity_registry_index/#unique-id-requirements """
        return self._attr_unique_id


class DahuaCameraPresetPositionSelect(DahuaBaseEntity, SelectEntity):
    """allows """

    def __init__(self, coordinator: DahuaDataUpdateCoordinator, config_entry):
        DahuaBaseEntity.__init__(self, coordinator, config_entry)
        SelectEntity.__init__(self)
        self._coordinator = coordinator
        self._attr_name = f"{coordinator.get_device_name()} Preset Position"
        self._attr_unique_id = f"{coordinator.get_serial_number()}_preset_position"
        self._attr_options = ["Manual","1","2","3","4","5","6","7","8","9","10"]

    @property
    def current_option(self) -> str:
        presetID = self._coordinator.data.get("status.PresetID", "0")
        if presetID == "0":
            return "Manual"
        return presetID

    async def async_select_option(self, option: str) -> None:
        channel = self._coordinator.get_channel()
        await self._coordinator.client.async_goto_preset_position(channel, int(option))
        await self._coordinator.async_refresh()

    @property
    def name(self):
        return self._attr_name

    @property
    def unique_id(self):
        """ https://developers.home-assistant.io/docs/entity_registry_index/#unique-id-requirements """
        return self._attr_unique_id


class DahuaStrobeLightTypeSelect(DahuaBaseEntity, SelectEntity):
    """Per-rule strobe light type select (RedBlueLight, WhiteLight)."""

    def __init__(self, coordinator: DahuaDataUpdateCoordinator, config_entry, rule: dict):
        DahuaBaseEntity.__init__(self, coordinator, config_entry)
        SelectEntity.__init__(self)
        self._rule = rule
        self._config_key = rule["lighting_link_prefix"] + ".FilckerLightType"
        self._table_key = "table." + self._config_key
        self._attr_options = ["RedBlueLight", "WhiteLight"]

    @property
    def current_option(self) -> str:
        val = self._coordinator.data.get(self._table_key, "")
        if val in self._attr_options:
            return val
        return self._attr_options[0]

    async def async_select_option(self, option: str) -> None:
        await self._coordinator.client.async_set_config(self._config_key, option)
        await self._coordinator.async_refresh()

    @property
    def name(self):
        return "{0} {1} Light Type".format(
            self._coordinator.get_device_name(), self._rule["name"]
        )

    @property
    def unique_id(self):
        return "{0}_{1}_{2}_light_type".format(
            self._coordinator.get_serial_number(),
            self._rule["config_name"].lower().replace("videoanalyserule", "var"),
            self._rule["index"],
        )

    @property
    def icon(self):
        return STROBE_ICON


class DahuaStrobeLightModeSelect(DahuaBaseEntity, SelectEntity):
    """Per-rule strobe light mode select (Filcker, Steady)."""

    def __init__(self, coordinator: DahuaDataUpdateCoordinator, config_entry, rule: dict):
        DahuaBaseEntity.__init__(self, coordinator, config_entry)
        SelectEntity.__init__(self)
        self._rule = rule
        self._config_key = rule["lighting_link_prefix"] + ".LightLinkType"
        self._table_key = "table." + self._config_key
        self._attr_options = ["Filcker", "Steady"]

    @property
    def current_option(self) -> str:
        val = self._coordinator.data.get(self._table_key, "")
        if val in self._attr_options:
            return val
        return self._attr_options[0]

    async def async_select_option(self, option: str) -> None:
        await self._coordinator.client.async_set_config(self._config_key, option)
        await self._coordinator.async_refresh()

    @property
    def name(self):
        return "{0} {1} Light Mode".format(
            self._coordinator.get_device_name(), self._rule["name"]
        )

    @property
    def unique_id(self):
        return "{0}_{1}_{2}_light_mode".format(
            self._coordinator.get_serial_number(),
            self._rule["config_name"].lower().replace("videoanalyserule", "var"),
            self._rule["index"],
        )

    @property
    def icon(self):
        return STROBE_ICON


class DahuaSMDSensitivitySelect(DahuaBaseEntity, SelectEntity):
    """SMD sensitivity select (Low, Middle, High)."""

    def __init__(self, coordinator: DahuaDataUpdateCoordinator, config_entry):
        DahuaBaseEntity.__init__(self, coordinator, config_entry)
        SelectEntity.__init__(self)
        self._attr_options = ["Low", "Middle", "High"]

    @property
    def current_option(self) -> str:
        val = self._coordinator.get_smd_sensitivity()
        if val in self._attr_options:
            return val
        return "Middle"

    async def async_select_option(self, option: str) -> None:
        channel = self._coordinator.get_channel()
        await self._coordinator.client.async_set_config(
            "SmartMotionDetect[{0}].Sensitivity".format(channel), option
        )
        await self._coordinator.async_refresh()

    @property
    def name(self):
        return self._coordinator.get_device_name() + " SMD Sensitivity"

    @property
    def unique_id(self):
        return self._coordinator.get_serial_number() + "_smd_sensitivity"

    @property
    def icon(self):
        return MOTION_DETECTION_ICON
