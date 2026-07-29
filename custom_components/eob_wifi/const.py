import logging

DOMAIN = "eob_wifi"
MANUFACTURER = "Elektrobock"
LOGGER = logging.getLogger(__name__)

BASE_SERVER_URL = "https://data.elektrobock.cz"
HISTORY_SERVER_URL = "https://history.elektrobock.cz"

API_LOGIN = "/api/Auth/login"
API_REGISTER = "/api/Auth/registerIdentity"
API_USER_UPDATE = "/api/User/update"
_API_USER_DELETE = "/api/User/delete"
API_DEVICES_WITH_FCM = "/api/UsersDevices/withFcmData"
API_DEVICES_USERS = "/api/DevicesUsers"
API_PAIR_DEVICE = "/api/UserDevices/Register"
API_ADD_USER_DEVICE = "/api/UserDevices/AddUserToDeviceUsingPass"
API_DELETE_USER_DEVICE = "/api/UserDevices/Delete"
API_DEVICE = "/api/Device"
API_DEVICE_RENAME = "/api/Device/Rename"
API_DEVICE_FW_UPDATE = "/api/Device/UpdateFwStringTypeAndVariant"
API_FCM_LIST = "/api/Fcm/GetByUserDevicePair"
API_FCM_ADD = "/api/Fcm/AddToUserDevicePair"
API_FCM_DELETE = "/api/Fcm/DeleteFromUserDevicePair"
API_FORGOT_PSWD = "/api/UserEmail/forgotPswd"
API_CHANGE_PSWD = "/api/UserEmail/changePswd"

DEVICE_TYPE_PT32_WIFI = 0
DEVICE_TYPE_PT32_GSM = 1
DEVICE_TYPE_BPT725 = 2
DEVICE_TYPE_PHCJ37 = 3
DEVICE_TYPE_PHCJ39 = 4
DEVICE_TYPE_PHCJ38 = 5
DEVICE_TYPE_BT52W_OPT = 6
DEVICE_TYPE_U2 = 7
DEVICE_TYPE_TS11_WIFI = 8
DEVICE_TYPE_PT59 = 10
DEVICE_TYPE_GST_SOCKET = 11
DEVICE_TYPE_GSM_MODULE = 12
DEVICE_TYPE_PT41_MQTT = 13
DEVICE_TYPE_PT14 = 14
DEVICE_TYPE_PT14_WIF_ONLY = 20
DEVICE_TYPE_UNKNOWN = 255
DEVICE_TYPE_PT_THERMOSTAT = 256

DEVICE_TYPES_USED_IN_APP = [
    DEVICE_TYPE_TS11_WIFI,
    DEVICE_TYPE_PT14,
    DEVICE_TYPE_PT14_WIF_ONLY,
    DEVICE_TYPE_U2,
]

CONF_USERNAME = "username"
CONF_PASSWORD = "password"

ATTR_DEVICE_ID = "device_id"
ATTR_DEVICE_TYPE = "device_type"
ATTR_FIRMWARE = "firmware"
ATTR_ADMIN_ID = "admin_id"
ATTR_DEVICE_VARIANT = "device_variant"

MODE_AUTO = "auto"
MODE_MANU = "manu"
MODE_OFF = "off"
