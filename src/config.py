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
        self.protocol_counts = {}

class ChannelConfig:
    def __init__(self, url: str, enabled: bool = True):
        self.url = url
        self.enabled = enabled
        self.metrics = ChannelMetrics()
        self.is_telegram = bool(re.match(r'^https://t\.me/s/', url))
        
    def calculate_overall_score(self):
        reliability_score = (self.metrics.success_count / (self.metrics.success_count + self.metrics.fail_count)) * 35 if (self.metrics.success_count + self.metrics.fail_count) > 0 else 0
        quality_score = (self.metrics.valid_configs / self.metrics.total_configs) * 25 if self.metrics.total_configs > 0 else 0
        uniqueness_score = (self.metrics.unique_configs / self.metrics.valid_configs) * 25 if self.metrics.valid_configs > 0 else 0
        response_score = max(0, min(15, 15 * (1 - (self.metrics.avg_response_time / 10)))) if self.metrics.avg_response_time > 0 else 15
        
        self.metrics.overall_score = reliability_score + quality_score + uniqueness_score + response_score

class ProxyConfig:
    def __init__(self):
        self.SOURCE_URLS = [
            ChannelConfig("https://t.me/s/v2ray_free_conf"),
            ChannelConfig("https://t.me/s/ShadowProxy66"),
            ChannelConfig("https://t.me/s/OutlineReleasedKey"),
            ChannelConfig("https://t.me/s/PrivateVPNs"),
            ChannelConfig("https://t.me/s/prrofile_purple"),
            ChannelConfig("https://t.me/s/proxy_shadosocks"),
            ChannelConfig("https://t.me/s/DirectVPN"),
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
            ChannelConfig("https://t.me/s/configshub"),
            ChannelConfig("https://t.me/s/customv2ray"),
            ChannelConfig("https://t.me/s/dgkbza"),
            ChannelConfig("https://t.me/s/elitevpnv2"),
            ChannelConfig("https://t.me/s/entrynet"),
            ChannelConfig("https://t.me/s/expressvpn_420"),
            ChannelConfig("https://t.me/s/external_net"),
            ChannelConfig("https://t.me/s/farahvpn"),
            ChannelConfig("https://t.me/s/fast_2ray"),
            ChannelConfig("https://t.me/s/fastkanfig"),
            ChannelConfig("https://t.me/s/flyv2ray"),
            ChannelConfig("https://t.me/s/free1_vpn"),
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
            ChannelConfig("https://t.me/s/astrovpn_official"),
            ChannelConfig("https://t.me/s/free4allvpn"),
            ChannelConfig("https://t.me/s/freev2rays"),
            ChannelConfig("https://t.me/s/directvpn"),
            ChannelConfig("https://t.me/s/appsooner"),
            ChannelConfig("https://t.me/s/dailyv2ry"),
            ChannelConfig("https://t.me/s/vpnhubmarket"),
            ChannelConfig("https://t.me/s/artemisvpn1"),
            ChannelConfig("https://t.me/s/lightconnect_m"),
            ChannelConfig("https://t.me/s/v2rayng_vpnn"),
            ChannelConfig("https://t.me/s/V2pedia"),
            ChannelConfig("https://t.me/s/networknim"),
            ChannelConfig("https://t.me/s/DailyV2RY"),
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

        self.PROTOCOL_CONFIG_LIMITS = {
            "min": 7000,
            "max": 7000
        }

        self.SUPPORTED_PROTOCOLS: Dict[str, Dict] = {
            "wireguard://": {
                "min_configs": self.PROTOCOL_CONFIG_LIMITS["min"],
                "max_configs": self.PROTOCOL_CONFIG_LIMITS["max"],
                "priority": 2,
                "flexible_max": True
            },
            "hysteria2://": {
                "min_configs": self.PROTOCOL_CONFIG_LIMITS["min"],
                "max_configs": self.PROTOCOL_CONFIG_LIMITS["max"],
                "priority": 2,
                "flexible_max": True
            },
            "vless://": {
                "min_configs": self.PROTOCOL_CONFIG_LIMITS["min"],
                "max_configs": self.PROTOCOL_CONFIG_LIMITS["max"],
                "priority": 1,
                "flexible_max": True
            },
            "vmess://": {
                "min_configs": self.PROTOCOL_CONFIG_LIMITS["min"],
                "max_configs": self.PROTOCOL_CONFIG_LIMITS["max"],
                "priority": 2,
                "flexible_max": True
            },
            "ss://": {
                "min_configs": self.PROTOCOL_CONFIG_LIMITS["min"],
                "max_configs": self.PROTOCOL_CONFIG_LIMITS["max"],
                "priority": 2,
                "flexible_max": True
            },
            "trojan://": {
                "min_configs": self.PROTOCOL_CONFIG_LIMITS["min"],
                "max_configs": self.PROTOCOL_CONFIG_LIMITS["max"],
                "priority": 1,
                "flexible_max": True
            },
            "tuic://": {
                "min_configs": self.PROTOCOL_CONFIG_LIMITS["min"],
                "max_configs": self.PROTOCOL_CONFIG_LIMITS["max"],
                "priority": 2,
                "flexible_max": True
            }
        }

        self.MIN_CONFIGS_PER_CHANNEL = 7000
        self.MAX_CONFIGS_PER_CHANNEL = 7000
        self.MAX_CONFIG_AGE_DAYS = 90
        self.CHANNEL_RETRY_LIMIT = 5
        self.CHANNEL_ERROR_THRESHOLD = 0.7
        self.MIN_PROTOCOL_RATIO = 0.1
        
        self.DYNAMIC_PROTOCOL_ADJUSTMENT = True
        self.PROTOCOL_BALANCE_FACTOR = 1.5
        
        self.OUTPUT_FILE = 'configs/proxy_configs.txt'
        self.STATS_FILE = 'configs/channel_stats.json'
        self.MAX_RETRIES = 5
        self.RETRY_DELAY = 3
        self.REQUEST_TIMEOUT = 45
        
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
        
        if channel.metrics.overall_score < 25:
            channel.enabled = False
            
    def adjust_protocol_limits(self, channel: ChannelConfig):
        if not self.DYNAMIC_PROTOCOL_ADJUSTMENT:
            return
            
        for protocol in self.SUPPORTED_PROTOCOLS:
            if protocol in channel.metrics.protocol_counts:
                count = channel.metrics.protocol_counts[protocol]
                if count >= self.SUPPORTED_PROTOCOLS[protocol]["min_configs"]:
                    new_max = min(
                        int(count * self.PROTOCOL_BALANCE_FACTOR),
                        self.MAX_CONFIGS_PER_CHANNEL
                    )
                    if self.SUPPORTED_PROTOCOLS[protocol]["flexible_max"]:
                        self.SUPPORTED_PROTOCOLS[protocol]["max_configs"] = new_max
