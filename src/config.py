from typing import Dict, List
from datetime import datetime
import re

class ChannelMetrics:
    def __init__(self):
        self.total_configs = 0
        self.valid_configs = 0
        self.unique_configs = 0
        self.avg_response_time = 0
        self.last_success_time = None
        self.fail_count = 0
        self.success_count = 0
        self.overall_score = 0.0

class ChannelConfig:
    def __init__(self, url: str, enabled: bool = True):
        self.url = url
        self.enabled = enabled
        self.metrics = ChannelMetrics()
        self.is_telegram = bool(re.match(r'^https://t\.me/s/', url))
        
    def calculate_overall_score(self):
        if self.metrics.success_count + self.metrics.fail_count == 0:
            reliability_score = 0
        else:
            reliability_score = (self.metrics.success_count / (self.metrics.success_count + self.metrics.fail_count)) * 35
        
        if self.metrics.total_configs == 0:
            quality_score = 0
        else:
            quality_score = (self.metrics.valid_configs / self.metrics.total_configs) * 25
        
        if self.metrics.valid_configs == 0:
            uniqueness_score = 0
        else:
            uniqueness_score = (self.metrics.unique_configs / self.metrics.valid_configs) * 25
        
        if self.metrics.avg_response_time == 0:
            response_score = 15
        else:
            response_score = max(0, min(15, 15 * (1 - (self.metrics.avg_response_time / 10))))
        
        self.metrics.overall_score = reliability_score + quality_score + uniqueness_score + response_score

class ProxyConfig:
    def __init__(self):
        # List of channels or URLs to fetch proxy configurations from
        self.SOURCE_URLS = list({
            ChannelConfig("https://t.me/s/v2ray_free_conf"),
            ChannelConfig("https://t.me/s/v2Source"),
            ChannelConfig("https://t.me/s/oneclickvpnkeys"),
            ChannelConfig("https://t.me/s/ShadowProxy66"),
            ChannelConfig("https://t.me/s/OutlineReleasedKey"),
            ChannelConfig("https://t.me/s/GetConfigIR"),
            ChannelConfig("https://t.me/s/PrivateVPNs"),
            ChannelConfig("https://t.me/s/prrofile_purple"),
            ChannelConfig("https://t.me/s/proxy_shadosocks"),
            ChannelConfig("https://t.me/s/DirectVPN"),
            ChannelConfig("https://t.me/s/Parsashonam"),
            ChannelConfig("https://t.me/s/ArV2ray"),
            ChannelConfig("https://t.me/s/VmessProtocol"),
            ChannelConfig("https://t.me/s/vpnfail_v2ray"),
            ChannelConfig("https://t.me/s/vpnkanfik"),
            ChannelConfig("https://t.me/s/vpnmega1"),
            ChannelConfig("https://t.me/s/vpnowl"),
            ChannelConfig("https://t.me/s/vpnx1x"),
            ChannelConfig("https://t.me/s/wxgmrjdcc"),
            ChannelConfig("https://t.me/s/zibanabz"),
            ChannelConfig("https://t.me/s/antifilterjadid"),
            ChannelConfig("https://t.me/s/canfigv2ray"),
            ChannelConfig("https://t.me/s/cnlv2rayng"),
            ChannelConfig("https://t.me/s/configfa"),
            ChannelConfig("https://t.me/s/configshub"),
            ChannelConfig("https://t.me/s/confing_v2rayy"),
            ChannelConfig("https://t.me/s/customv2ray"),
            ChannelConfig("https://t.me/s/dgkbza"),
            ChannelConfig("https://t.me/s/elitevpnv2"),
            ChannelConfig("https://t.me/s/entrynet"),
            ChannelConfig("https://t.me/s/expressvpn_420"),
            ChannelConfig("https://t.me/s/external_net"),
            ChannelConfig("https://t.me/s/falcunargo"),
            ChannelConfig("https://t.me/s/farahvpn"),
            ChannelConfig("https://t.me/s/fast_2ray"),
            ChannelConfig("https://t.me/s/fastkanfig"),
            ChannelConfig("https://t.me/s/fix_proxy"),
            ChannelConfig("https://t.me/s/flyv2ray"),
            ChannelConfig("https://t.me/s/free1_vpn"),
            ChannelConfig("https://t.me/s/free_outline_keys"),
            ChannelConfig("https://t.me/s/freeconfig01"),
            ChannelConfig("https://t.me/s/freevirgoolnet"),
            ChannelConfig("https://t.me/s/gh_v2rayng"),
            ChannelConfig("https://t.me/s/givevpn"),
            ChannelConfig("https://t.me/s/guard_revil"),
            ChannelConfig("https://t.me/s/hiddenvpnchannel"),
            ChannelConfig("https://t.me/s/hl_proxy"),
            ChannelConfig("https://t.me/s/hope_net"),
            ChannelConfig("https://t.me/s/hopev2ray"),
            ChannelConfig("https://t.me/s/huiguo62"),
            ChannelConfig("https://t.me/s/IP_CF_Config"),
            ChannelConfig("https://t.me/s/irv2rey"),
            ChannelConfig("https://t.me/s/jiedianf"),
            ChannelConfig("https://t.me/s/jiujied"),
            ChannelConfig("https://t.me/s/king_network7"),
            ChannelConfig("https://t.me/s/kingofilter"),
            ChannelConfig("https://t.me/s/kurdistan_vpn_perfectt"),
            ChannelConfig("https://t.me/s/lonup_m"),
            ChannelConfig("https://t.me/s/masirbazz"),
            ChannelConfig("https://t.me/s/meli_proxyy"),
            ChannelConfig("https://t.me/s/moftinet"),
            ChannelConfig("https://t.me/s/mtpproxy0098"),
            ChannelConfig("https://t.me/s/new_mtproxi2"),
            ChannelConfig("https://t.me/s/nofiltering2"),
            ChannelConfig("https://t.me/s/outline_ir"),
            ChannelConfig("https://t.me/s/poroxybaz"),
            ChannelConfig("https://t.me/s/proxy_v2box"),
            ChannelConfig("https://t.me/s/proxyfacts"),
            ChannelConfig("https://t.me/s/prroxyng"),
            ChannelConfig("https://t.me/s/satafkompani"),
            ChannelConfig("https://t.me/s/satellitenewspersian"),
            ChannelConfig("https://t.me/s/server_nekobox"),
            ChannelConfig("https://t.me/s/shadowsockskeys"),
            ChannelConfig("https://t.me/s/skivpn"),
            ChannelConfig("https://t.me/s/socks5tobefree"),
            ChannelConfig("https://t.me/s/strongprotocol"),
            ChannelConfig("https://t.me/s/tehranargo"),
            ChannelConfig("https://t.me/s/uvpn_org"),
            ChannelConfig("https://t.me/s/v2aryng_vpn"),
            ChannelConfig("https://t.me/s/v2fre"),
            ChannelConfig("https://t.me/s/v2mystery"),
            ChannelConfig("https://t.me/s/v2rang_255"),
            ChannelConfig("https://t.me/s/v2ray1_ng"),
            ChannelConfig("https://t.me/s/v2ray_alpha"),
            ChannelConfig("https://t.me/s/v2ray_raha"),
            ChannelConfig("https://t.me/s/v2ray_v_vpn"),
            ChannelConfig("https://t.me/s/v2rayminer"),
            ChannelConfig("https://t.me/s/v2rayngrit"),
            ChannelConfig("https://t.me/s/v2rayngseven"),
            ChannelConfig("https://t.me/s/v2rayngvp"),
            ChannelConfig("https://t.me/s/v2rayprotocol"),
            ChannelConfig("https://t.me/s/v2rayproxy"),
            ChannelConfig("https://t.me/s/v2rayvlp"),
            ChannelConfig("https://t.me/s/vistav2ray"),
            ChannelConfig("https://t.me/s/alpha_v2ray_fazayi"),
            ChannelConfig("https://t.me/s/astrovpn_official"),
            ChannelConfig("https://t.me/s/free4allvpn"),
            ChannelConfig("https://t.me/s/freev2rays"),
            ChannelConfig("https://t.me/s/v2rayng_vpn"),
            ChannelConfig("https://t.me/s/directvpn"),
            ChannelConfig("https://t.me/s/appsooner"),
            ChannelConfig("https://t.me/s/dailyv2ry"),
            ChannelConfig("https://t.me/s/vpnhubmarket"),
            ChannelConfig("https://t.me/s/artemisvpn1"),
            ChannelConfig("https://t.me/s/lightconnect_m"),
            ChannelConfig("https://t.me/s/v2rayng_vpnn"),
            ChannelConfig("https://t.me/s/v2line"),
            ChannelConfig("https://t.me/s/VlessConfig"),
            ChannelConfig("https://t.me/s/V2pedia"),
            ChannelConfig("https://t.me/s/v2rayNG_Matsuri"),
            ChannelConfig("https://t.me/s/proxystore11"),
            ChannelConfig("https://t.me/s/OutlineVpnOfficial"),
            ChannelConfig("https://t.me/s/networknim"),
            ChannelConfig("https://t.me/s/beiten"),
            ChannelConfig("https://t.me/s/MsV2ray"),
            ChannelConfig("https://t.me/s/foxrayiran"),
            ChannelConfig("https://t.me/s/DailyV2RY"),
            ChannelConfig("https://t.me/s/yaney_01"),
            ChannelConfig("https://t.me/s/EliV2ray"),
            ChannelConfig("https://t.me/s/ServerNett"),
            ChannelConfig("https://t.me/s/v2rayng_fa2"),
            ChannelConfig("https://t.me/s/v2rayng_org"),
            ChannelConfig("https://t.me/s/V2rayNGvpni"),
            ChannelConfig("https://t.me/s/custom_14"),
            ChannelConfig("https://t.me/s/v2rayNG_VPNN"),
            ChannelConfig("https://t.me/s/v2ray_outlineir"),
            ChannelConfig("https://t.me/s/v2_vmess"),
            ChannelConfig("https://t.me/s/FreeVlessVpn"),
            ChannelConfig("https://t.me/s/vmess_vless_v2rayng"),
            ChannelConfig("https://t.me/s/freeland8"),
            ChannelConfig("https://t.me/s/vmessiran"),
            ChannelConfig("https://t.me/s/Outline_Vpn"),
            ChannelConfig("https://t.me/s/vmessq"),
            ChannelConfig("https://t.me/s/WeePeeN"),
            ChannelConfig("https://t.me/s/V2rayNG3"),
            ChannelConfig("https://t.me/s/ShadowsocksM"),
            ChannelConfig("https://t.me/s/shadowsocksshop"),
            ChannelConfig("https://t.me/s/v2rayan"),
            ChannelConfig("https://t.me/s/ShadowSocks_s"),
            ChannelConfig("https://t.me/s/napsternetv_config"),
            ChannelConfig("https://t.me/s/Easy_Free_VPN"),
            ChannelConfig("https://t.me/s/V2Ray_FreedomIran"),
            ChannelConfig("https://t.me/s/V2RAY_VMESS_free"),
            ChannelConfig("https://t.me/s/v2ray_for_free"),
            ChannelConfig("https://t.me/s/V2rayN_Free"),
            ChannelConfig("https://t.me/s/vpn_ocean"),
            ChannelConfig("https://t.me/s/configV2rayForFree"),
            ChannelConfig("https://t.me/s/DigiV2ray"),
            ChannelConfig("https://t.me/s/freev2rayssr"),
            ChannelConfig("https://t.me/s/v2rayn_server"),
            ChannelConfig("https://t.me/s/Shadowlinkserverr"),
            ChannelConfig("https://t.me/s/iranvpnet"),
            ChannelConfig("https://t.me/s/mahsaamoon1"),
            ChannelConfig("https://t.me/s/V2RAY_NEW"),
            ChannelConfig("https://t.me/s/v2RayChannel"),
            ChannelConfig("https://t.me/s/configV2rayNG"),
            ChannelConfig("https://t.me/s/config_v2ray"),
            ChannelConfig("https://t.me/s/vpn_proxy_custom"),
            ChannelConfig("https://t.me/s/vpnmasi"),
            ChannelConfig("https://t.me/s/v2ray_custom"),
            ChannelConfig("https://t.me/s/VPNCUSTOMIZE"),
            ChannelConfig("https://t.me/s/HTTPCustomLand"),
            ChannelConfig("https://t.me/s/ViPVpn_v2ray"),
            ChannelConfig("https://t.me/s/FreeNet1500"),
            ChannelConfig("https://t.me/s/v2ray_ar"),
            ChannelConfig("https://t.me/s/beta_v2ray"),
            ChannelConfig("https://t.me/s/vip_vpn_2022"),
            ChannelConfig("https://t.me/s/FOX_VPN66"),
            ChannelConfig("https://t.me/s/VorTexIRN"),
            ChannelConfig("https://t.me/s/YtTe3la"),
            ChannelConfig("https://t.me/s/V2RayOxygen"),
            ChannelConfig("https://t.me/s/Network_442"),
            ChannelConfig("https://t.me/s/VPN_443"),
            ChannelConfig("https://t.me/s/v2rayng_v"),
            ChannelConfig("https://t.me/s/ultrasurf_12"),
            ChannelConfig("https://t.me/s/iSeqaro"),
            ChannelConfig("https://t.me/s/frev2rayng"),
            ChannelConfig("https://t.me/s/frev2ray"),
            ChannelConfig("https://t.me/s/Awlix_ir"),
            ChannelConfig("https://t.me/s/v2rayngvpn"),
            ChannelConfig("https://t.me/s/God_CONFIG"),
            ChannelConfig("https://t.me/s/Configforvpn01"),
            ChannelConfig("https://t.me/s/TUICity"),
            ChannelConfig("https://t.me/s/ParsRoute")
        ]

        # Minimum and maximum number of configurations per protocol
        self.PROTOCOL_CONFIG_LIMITS = {
            "min": 6000,  # Minimum number of configurations per protocol
            "max": 6000   # Maximum number of configurations per protocol
        }

        # Supported proxy protocols and their limits
        self.SUPPORTED_PROTOCOLS: Dict[str, Dict] = {
            "wireguard://": {"min_configs": self.PROTOCOL_CONFIG_LIMITS["min"], "max_configs": self.PROTOCOL_CONFIG_LIMITS["max"]},
            "hysteria2://": {"min_configs": self.PROTOCOL_CONFIG_LIMITS["min"], "max_configs": self.PROTOCOL_CONFIG_LIMITS["max"]},
            "vless://": {"min_configs": self.PROTOCOL_CONFIG_LIMITS["min"], "max_configs": self.PROTOCOL_CONFIG_LIMITS["max"]},
            "vmess://": {"min_configs": self.PROTOCOL_CONFIG_LIMITS["min"], "max_configs": self.PROTOCOL_CONFIG_LIMITS["max"]},
            "ss://": {"min_configs": self.PROTOCOL_CONFIG_LIMITS["min"], "max_configs": self.PROTOCOL_CONFIG_LIMITS["max"]},
            "trojan://": {"min_configs": self.PROTOCOL_CONFIG_LIMITS["min"], "max_configs": self.PROTOCOL_CONFIG_LIMITS["max"]}
        }

        # Minimum and maximum number of configurations fetched from each channel
        self.MIN_CONFIGS_PER_CHANNEL = 6000  # Minimum number of proxy configs required per channel
        self.MAX_CONFIGS_PER_CHANNEL = 6000  # Maximum number of proxy configs allowed per channel
        # Maximum age of configurations (in days)
        self.MAX_CONFIG_AGE_DAYS = 14  # Discard configurations older than this many days
        # Retry settings for fetching configurations
        self.CHANNEL_RETRY_LIMIT = 6  # Maximum number of retries if a channel fetch fails
        self.CHANNEL_ERROR_THRESHOLD = 0.9  # Error threshold (e.g., 50%) to disable a channel

        # Minimum ratio of configs required for a protocol to be considered valid
        self.MIN_PROTOCOL_RATIO = 0.9  # Protocol must have at least 15% of all fetched configs

        self.OUTPUT_FILE = 'configs/proxy_configs.txt'
        self.STATS_FILE = 'configs/channel_stats.json'

        # HTTP request settings
        self.MAX_RETRIES = 3  # Maximum retries for a failed HTTP request
        self.RETRY_DELAY = 2  # Delay (in seconds) between retries
        self.REQUEST_TIMEOUT = 2  # Timeout (in seconds) for HTTP requests

        self.HEADERS = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

    def is_protocol_enabled(self, protocol: str) -> bool:
        return protocol in self.SUPPORTED_PROTOCOLS

    def get_enabled_channels(self) -> List[ChannelConfig]:
        return [channel for channel in self.SOURCE_URLS if channel.enabled]

    def update_channel_stats(self, channel: ChannelConfig, success: bool, response_time: float = 0):
        if success:
            channel.metrics.success_count += 1
            channel.metrics.last_success_time = datetime.now()
        else:
            channel.metrics.fail_count += 1
        
        if response_time > 0:
            if channel.metrics.avg_response_time == 0:
                channel.metrics.avg_response_time = response_time
            else:
                channel.metrics.avg_response_time = (channel.metrics.avg_response_time * 0.7) + (response_time * 0.3)
        
        channel.calculate_overall_score()
        
        if channel.metrics.overall_score < 30:
            channel.enabled = False
