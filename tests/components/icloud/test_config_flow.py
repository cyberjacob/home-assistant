"""Tests for the iCloud config flow."""
from unittest.mock import MagicMock, Mock, patch

from pyicloud.exceptions import PyiCloudFailedLoginException
import pytest

from homeassistant import data_entry_flow
from homeassistant.components.icloud import config_flow
from homeassistant.components.icloud.config_flow import (
    CONF_TRUSTED_DEVICE,
    CONF_VERIFICATION_CODE,
)
from homeassistant.components.icloud.const import (
    CONF_GPS_ACCURACY_THRESHOLD,
    CONF_MAX_INTERVAL,
    DEFAULT_GPS_ACCURACY_THRESHOLD,
    DEFAULT_MAX_INTERVAL,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_IMPORT, SOURCE_USER
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.typing import HomeAssistantType

from tests.common import MockConfigEntry

USERNAME = "username@me.com"
USERNAME_2 = "second_username@icloud.com"
PASSWORD = "password"
MAX_INTERVAL = 15
GPS_ACCURACY_THRESHOLD = 250

TRUSTED_DEVICES = [
    {"deviceType": "SMS", "areaCode": "", "phoneNumber": "*******58", "deviceId": "1"}
]


@pytest.fixture(name="service")
def mock_controller_service():
    """Mock a successful service."""
    with patch(
        "homeassistant.components.icloud.config_flow.PyiCloudService"
    ) as service_mock:
        service_mock.return_value.requires_2fa = True
        yield service_mock


@pytest.fixture(name="service_with_cookie")
def mock_controller_service_with_cookie():
    """Mock a successful service while already authenticate."""
    with patch(
        "homeassistant.components.icloud.config_flow.PyiCloudService"
    ) as service_mock:
        service_mock.return_value.requires_2fa = False
        service_mock.return_value.trusted_devices = TRUSTED_DEVICES
        service_mock.return_value.send_verification_code = Mock(return_value=True)
        service_mock.return_value.validate_verification_code = Mock(return_value=True)
        yield service_mock


@pytest.fixture(name="service_send_verification_code_failed")
def mock_controller_service_send_verification_code_failed():
    """Mock a failed service during sending verification code step."""
    with patch(
        "homeassistant.components.icloud.config_flow.PyiCloudService"
    ) as service_mock:
        service_mock.return_value.requires_2fa = False
        service_mock.return_value.trusted_devices = TRUSTED_DEVICES
        service_mock.return_value.send_verification_code = Mock(return_value=False)
        yield service_mock


@pytest.fixture(name="service_validate_verification_code_failed")
def mock_controller_service_validate_verification_code_failed():
    """Mock a failed service during validation of verification code step."""
    with patch(
        "homeassistant.components.icloud.config_flow.PyiCloudService"
    ) as service_mock:
        service_mock.return_value.requires_2fa = False
        service_mock.return_value.trusted_devices = TRUSTED_DEVICES
        service_mock.return_value.send_verification_code = Mock(return_value=True)
        service_mock.return_value.validate_verification_code = Mock(return_value=False)
        yield service_mock


def init_config_flow(hass: HomeAssistantType):
    """Init a configuration flow."""
    flow = config_flow.IcloudFlowHandler()
    flow.hass = hass
    return flow


async def test_user(hass: HomeAssistantType, service: MagicMock):
    """Test user config."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=None
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    # test with all provided
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == CONF_TRUSTED_DEVICE


async def test_user_with_cookie(
    hass: HomeAssistantType, service_with_cookie: MagicMock
):
    """Test user config with presence of a cookie."""
    # test with all provided
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == USERNAME
    assert result["data"][CONF_USERNAME] == USERNAME
    assert result["data"][CONF_PASSWORD] == PASSWORD
    assert result["data"][CONF_MAX_INTERVAL] == DEFAULT_MAX_INTERVAL
    assert result["data"][CONF_GPS_ACCURACY_THRESHOLD] == DEFAULT_GPS_ACCURACY_THRESHOLD


async def test_import(hass: HomeAssistantType, service: MagicMock):
    """Test import step."""
    # import with username and password
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data={CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "trusted_device"

    # import with all
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data={
            CONF_USERNAME: USERNAME_2,
            CONF_PASSWORD: PASSWORD,
            CONF_MAX_INTERVAL: MAX_INTERVAL,
            CONF_GPS_ACCURACY_THRESHOLD: GPS_ACCURACY_THRESHOLD,
        },
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "trusted_device"


async def test_import_with_cookie(
    hass: HomeAssistantType, service_with_cookie: MagicMock
):
    """Test import step with presence of a cookie."""
    # import with username and password
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data={CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == USERNAME
    assert result["data"][CONF_USERNAME] == USERNAME
    assert result["data"][CONF_PASSWORD] == PASSWORD
    assert result["data"][CONF_MAX_INTERVAL] == DEFAULT_MAX_INTERVAL
    assert result["data"][CONF_GPS_ACCURACY_THRESHOLD] == DEFAULT_GPS_ACCURACY_THRESHOLD

    # import with all
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data={
            CONF_USERNAME: USERNAME_2,
            CONF_PASSWORD: PASSWORD,
            CONF_MAX_INTERVAL: MAX_INTERVAL,
            CONF_GPS_ACCURACY_THRESHOLD: GPS_ACCURACY_THRESHOLD,
        },
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == USERNAME_2
    assert result["data"][CONF_USERNAME] == USERNAME_2
    assert result["data"][CONF_PASSWORD] == PASSWORD
    assert result["data"][CONF_MAX_INTERVAL] == MAX_INTERVAL
    assert result["data"][CONF_GPS_ACCURACY_THRESHOLD] == GPS_ACCURACY_THRESHOLD


async def test_two_accounts_setup(
    hass: HomeAssistantType, service_with_cookie: MagicMock
):
    """Test to setup two accounts."""
    MockConfigEntry(
        domain=DOMAIN, data={CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD}
    ).add_to_hass(hass)

    # import with username and password
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data={CONF_USERNAME: USERNAME_2, CONF_PASSWORD: PASSWORD},
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == USERNAME_2
    assert result["data"][CONF_USERNAME] == USERNAME_2
    assert result["data"][CONF_PASSWORD] == PASSWORD
    assert result["data"][CONF_MAX_INTERVAL] == DEFAULT_MAX_INTERVAL
    assert result["data"][CONF_GPS_ACCURACY_THRESHOLD] == DEFAULT_GPS_ACCURACY_THRESHOLD


async def test_abort_if_already_setup(hass: HomeAssistantType):
    """Test we abort if the account is already setup."""
    MockConfigEntry(
        domain=DOMAIN, data={CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD}
    ).add_to_hass(hass)

    # Should fail, same USERNAME (import)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data={CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "username_exists"

    # Should fail, same USERNAME (flow)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {CONF_USERNAME: "username_exists"}


async def test_login_failed(hass: HomeAssistantType):
    """Test when we have errors during login."""
    with patch(
        "pyicloud.base.PyiCloudService.authenticate",
        side_effect=PyiCloudFailedLoginException(),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["errors"] == {CONF_USERNAME: "login"}


async def test_trusted_device(hass: HomeAssistantType, service: MagicMock):
    """Test trusted_device step."""
    flow = init_config_flow(hass)
    await flow.async_step_user({CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD})

    result = await flow.async_step_trusted_device()
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == CONF_TRUSTED_DEVICE


async def test_trusted_device_success(hass: HomeAssistantType, service: MagicMock):
    """Test trusted_device step success."""
    flow = init_config_flow(hass)
    await flow.async_step_user({CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD})

    result = await flow.async_step_trusted_device({CONF_TRUSTED_DEVICE: 0})
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == CONF_VERIFICATION_CODE


async def test_send_verification_code_failed(
    hass: HomeAssistantType, service_send_verification_code_failed: MagicMock
):
    """Test when we have errors during send_verification_code."""
    flow = init_config_flow(hass)
    await flow.async_step_user({CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD})

    result = await flow.async_step_trusted_device({CONF_TRUSTED_DEVICE: 0})
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == CONF_TRUSTED_DEVICE
    assert result["errors"] == {CONF_TRUSTED_DEVICE: "send_verification_code"}


async def test_verification_code(hass: HomeAssistantType):
    """Test verification_code step."""
    flow = init_config_flow(hass)
    await flow.async_step_user({CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD})

    result = await flow.async_step_verification_code()
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == CONF_VERIFICATION_CODE


async def test_verification_code_success(
    hass: HomeAssistantType, service_with_cookie: MagicMock
):
    """Test verification_code step success."""
    flow = init_config_flow(hass)
    await flow.async_step_user({CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD})

    result = await flow.async_step_verification_code({CONF_VERIFICATION_CODE: 0})
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == USERNAME
    assert result["data"][CONF_USERNAME] == USERNAME
    assert result["data"][CONF_PASSWORD] == PASSWORD
    assert result["data"][CONF_MAX_INTERVAL] == DEFAULT_MAX_INTERVAL
    assert result["data"][CONF_GPS_ACCURACY_THRESHOLD] == DEFAULT_GPS_ACCURACY_THRESHOLD


async def test_validate_verification_code_failed(
    hass: HomeAssistantType, service_validate_verification_code_failed: MagicMock
):
    """Test when we have errors during validate_verification_code."""
    flow = init_config_flow(hass)
    await flow.async_step_user({CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD})

    result = await flow.async_step_verification_code({CONF_VERIFICATION_CODE: 0})
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == CONF_TRUSTED_DEVICE
    assert result["errors"] == {"base": "validate_verification_code"}
