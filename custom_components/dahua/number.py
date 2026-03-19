"""Number entity platform for Dahua — per-rule strobe light parameters."""
from homeassistant.components.number import NumberEntity
from homeassistant.core import HomeAssistant

from .const import DOMAIN, STROBE_ICON, IVS_RULE_ICON
from .entity import DahuaBaseEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_devices):
    """Setup number platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    devices = []

    for rule in coordinator.get_ivs_rules():
        if rule["has_lighting_link"]:
            devices.append(DahuaStrobeLightDurationNumber(coordinator, entry, rule))
            # FilckerIntevalTime only exists on RemoteVideoAnalyseRule
            if rule["is_remote"]:
                devices.append(DahuaStrobeFlickerIntervalNumber(coordinator, entry, rule))

        if rule["has_sensitivity"]:
            devices.append(DahuaIVSRuleSensitivityNumber(coordinator, entry, rule))

    async_add_devices(devices)


class DahuaStrobeLightDurationNumber(DahuaBaseEntity, NumberEntity):
    """Number entity for per-rule strobe light duration (seconds)."""

    def __init__(self, coordinator, entry, rule: dict):
        super().__init__(coordinator, entry)
        self._rule = rule
        self._config_key = rule["lighting_link_prefix"] + ".LightDuration"
        self._table_key = "table." + self._config_key

    @property
    def name(self):
        return "{0} {1} Light Duration".format(
            self._coordinator.get_device_name(), self._rule["name"]
        )

    @property
    def unique_id(self):
        return "{0}_{1}_{2}_light_duration".format(
            self._coordinator.get_serial_number(),
            self._rule["config_name"].lower().replace("videoanalyserule", "var"),
            self._rule["index"],
        )

    @property
    def icon(self):
        return STROBE_ICON

    @property
    def native_min_value(self):
        return 1

    @property
    def native_max_value(self):
        return 60

    @property
    def native_step(self):
        return 1

    @property
    def native_unit_of_measurement(self):
        return "s"

    @property
    def native_value(self):
        val = self._coordinator.data.get(self._table_key)
        if val is not None:
            try:
                return float(val)
            except (ValueError, TypeError):
                pass
        return None

    async def async_set_native_value(self, value: float):
        await self._coordinator.client.async_set_config(self._config_key, int(value))
        await self._coordinator.async_refresh()


class DahuaStrobeFlickerIntervalNumber(DahuaBaseEntity, NumberEntity):
    """Number entity for per-rule strobe flicker interval (seconds). RemoteVideoAnalyseRule only."""

    def __init__(self, coordinator, entry, rule: dict):
        super().__init__(coordinator, entry)
        self._rule = rule
        self._config_key = rule["lighting_link_prefix"] + ".FilckerIntevalTime"
        self._table_key = "table." + self._config_key

    @property
    def name(self):
        return "{0} {1} Flicker Interval".format(
            self._coordinator.get_device_name(), self._rule["name"]
        )

    @property
    def unique_id(self):
        return "{0}_{1}_{2}_flicker_interval".format(
            self._coordinator.get_serial_number(),
            self._rule["config_name"].lower().replace("videoanalyserule", "var"),
            self._rule["index"],
        )

    @property
    def icon(self):
        return STROBE_ICON

    @property
    def native_min_value(self):
        return 1

    @property
    def native_max_value(self):
        return 10

    @property
    def native_step(self):
        return 1

    @property
    def native_unit_of_measurement(self):
        return "s"

    @property
    def native_value(self):
        val = self._coordinator.data.get(self._table_key)
        if val is not None:
            try:
                return float(val)
            except (ValueError, TypeError):
                pass
        return None

    async def async_set_native_value(self, value: float):
        await self._coordinator.client.async_set_config(self._config_key, int(value))
        await self._coordinator.async_refresh()


class DahuaIVSRuleSensitivityNumber(DahuaBaseEntity, NumberEntity):
    """Number entity for per-rule IVS sensitivity (1-10)."""

    def __init__(self, coordinator, entry, rule: dict):
        super().__init__(coordinator, entry)
        self._rule = rule
        self._config_key = rule["sensitivity_key"]
        self._table_key = "table." + self._config_key

    @property
    def name(self):
        return "{0} {1} Sensitivity".format(
            self._coordinator.get_device_name(), self._rule["name"]
        )

    @property
    def unique_id(self):
        return "{0}_{1}_{2}_sensitivity".format(
            self._coordinator.get_serial_number(),
            self._rule["config_name"].lower().replace("videoanalyserule", "var"),
            self._rule["index"],
        )

    @property
    def icon(self):
        return IVS_RULE_ICON

    @property
    def native_min_value(self):
        return 1

    @property
    def native_max_value(self):
        return 10

    @property
    def native_step(self):
        return 1

    @property
    def native_value(self):
        val = self._coordinator.data.get(self._table_key)
        if val is not None:
            try:
                return float(val)
            except (ValueError, TypeError):
                pass
        return None

    async def async_set_native_value(self, value: float):
        await self._coordinator.client.async_set_config(self._config_key, int(value))
        await self._coordinator.async_refresh()
