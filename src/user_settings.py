# Please modify the settings below according to your needs.

# List of source URLs to fetch proxy configurations from.
# Add or remove URLs as needed. All URLs in this list are automatically enabled.
SOURCE_URLS = [
    "https://t.me/s/meli_proxyy",
    "https://t.me/s/V2rayNG3",
    "https://t.me/s/V2pedia",
    "https://t.me/s/Awlix_ir",
    "https://t.me/s/free4allVPN",
    "https://t.me/s/ViProxys",
    "https://t.me/s/proxy_shadosocks",
    "https://t.me/s/heyatserver",
    "https://t.me/s/vpnfail_vless",
    "https://t.me/s/prrofile_purple",
    "https://t.me/s/DailyV2RY",
    "https://t.me/s/shadowproxy66",
    "https://t.me/s/configV2rayForFree",
    "https://t.me/s/Hope_Net",
    "https://t.me/s/VmessProtocol",
    "https://t.me/s/v2ray_free_conf",
    "https://t.me/s/FreakConfig"
]

# Set to True to fetch the maximum possible number of configurations.
# If True, SPECIFIC_CONFIG_COUNT will be ignored.
USE_MAXIMUM_POWER = True

# Desired number of configurations to fetch.
# This is used only if USE_MAXIMUM_POWER is False.
SPECIFIC_CONFIG_COUNT = 100

# Dictionary of protocols to enable or disable.
# Set each protocol to True to enable, False to disable.
ENABLED_PROTOCOLS = {
    "wireguard://": False,
    "hysteria2://": True,
    "vless://": True,
    "vmess://": False,
    "ss://": True,
    "trojan://": False,
    "tuic://": True,
}

# Maximum age of configurations in days.
# Configurations older than this will be considered invalid.
MAX_CONFIG_AGE_DAYS = 30
