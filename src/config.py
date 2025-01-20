from typing import Dict, List
from datetime import datetime
import re

class ChannelMetrics:
    """
    Class to store and track metrics for each proxy config channel.
    All metrics start with default values of 0 or None.
    """
    def __init__(self):
        self.total_configs = 0          # Total number of configs found in channel (default: 0)
        self.valid_configs = 0          # Number of valid configs after validation (default: 0)
        self.unique_configs = 0         # Number of unique configs (not duplicates) (default: 0)
        self.avg_response_time = 0      # Average response time in seconds (default: 0)
        self.last_success_time = None   # Timestamp of last successful fetch (default: None)
        self.fail_count = 0             # Number of failed fetch attempts (default: 0)
        self.success_count = 0          # Number of successful fetch attempts (default: 0)
        self.overall_score = 0.0        # Overall channel performance score 0-100 (default: 0.0)
        self.protocol_counts = {}       # Count of configs per protocol (default: empty dict)

class ChannelConfig:
    """
    Class to store channel configuration and associated metrics.
    Default state for each channel is enabled (True).
    """
    def __init__(self, url: str, enabled: bool = True):
        self.url = url
        self.enabled = enabled
        self.metrics = ChannelMetrics()
        # Check if channel is a Telegram channel by URL pattern
        self.is_telegram = bool(re.match(r'^https://t\.me/s/', url))
        
    def calculate_overall_score(self):
        """
        Calculate overall channel score based on multiple factors:
        - Reliability (35%): Success rate of fetch attempts
        - Quality (25%): Ratio of valid configs to total configs
        - Uniqueness (25%): Ratio of unique configs to valid configs
        - Response Time (15%): Score based on average response time
        
        Total score ranges from 0 to 100. Channel is disabled if score falls below 25.
        """
        reliability_score = (self.metrics.success_count / (self.metrics.success_count + self.metrics.fail_count)) * 35 if (self.metrics.success_count + self.metrics.fail_count) > 0 else 0
        quality_score = (self.metrics.valid_configs / self.metrics.total_configs) * 25 if self.metrics.total_configs > 0 else 0
        uniqueness_score = (self.metrics.unique_configs / self.metrics.valid_configs) * 25 if self.metrics.valid_configs > 0 else 0
        response_score = max(0, min(15, 15 * (1 - (self.metrics.avg_response_time / 10)))) if self.metrics.avg_response_time > 0 else 15
        
        self.metrics.overall_score = reliability_score + quality_score + uniqueness_score + response_score

class ProxyConfig:
    def __init__(self):
        # List of source URLs to fetch proxy configs from
        # Add or remove channels here. Each ChannelConfig takes a URL and enabled status (default: True)
        self.SOURCE_URLS = [
            ChannelConfig("https://raw.githubusercontent.com/RaymondHarris971/ssrsub/master/9a075bdee5.txt"),
            ChannelConfig("https://raw.githubusercontent.com/Tenerome/v2ray/main/vmess.txt"),
            ChannelConfig("https://raw.githubusercontent.com/ALIILAPRO/v2rayNG-Config/main/server.txt"),
            ChannelConfig("https://raw.githubusercontent.com/vxiaov/free_proxies/refs/heads/main/links.txt"),
            ChannelConfig("https://raw.githubusercontent.com/MrMohebi/xray-proxy-grabber-telegram/master/collected-proxies/row-url/actives.txt"),
            ChannelConfig("https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/main/V2RAY_SUB.txt"),
            ChannelConfig("https://raw.githubusercontent.com/ALIILAPRO/v2rayNG-Config/main/sub.txt"),
            ChannelConfig("https://raw.githubusercontent.com/MrPooyaX/VpnsFucking/main/Shenzo.txt"),
            ChannelConfig("https://raw.githubusercontent.com/sansorchi/sansorchi/refs/heads/main/data.txt"),
            ChannelConfig("https://raw.githubusercontent.com/SamanValipour1/My-v2ray-configs/refs/heads/main/MySub.txt"),
            ChannelConfig("https://raw.githubusercontent.com/MrPooyaX/SansorchiFucker/refs/heads/main/data.txt"),
            ChannelConfig("https://raw.githubusercontent.com/MrPooyaX/VpnsFucking/refs/heads/main/BeVpn.txt"),
            ChannelConfig("https://raw.githubusercontent.com/Ashkan-m/v2ray/refs/heads/main/Sub.txt"),
            ChannelConfig("https://raw.githubusercontent.com/Mohammadgb0078/IRV2ray/main/vless.txt"),
            ChannelConfig("https://raw.githubusercontent.com/Mohammadgb0078/IRV2ray/main/vmess.txt"),
            ChannelConfig("https://raw.githubusercontent.com/SANYIMOE/VPN-free/4cf1dfd9e9b1f612a60f8796f43ea17f2bca0727/conf/data.txt"),
            ChannelConfig("https://raw.githubusercontent.com/SANYIMOE/VPN-free/5b5c8c09aa665169692ffcb48fed7c786bf0e737/conf/data.txt"),
            ChannelConfig("https://raw.githubusercontent.com/SANYIMOE/VPN-free/bfd7d84e84ef6fbbd89352dea17fdbcb8ac3e29a/conf/data.txt"),
            ChannelConfig("https://raw.githubusercontent.com/SANYIMOE/VPN-free/9ecbfd0efd89256e136f7b8c4558dc94fe1905af/conf/data.txt"),
            ChannelConfig("https://raw.githubusercontent.com/SANYIMOE/VPN-free/6e93041767a76c3104062551b003f29ea55f584e/conf/data.txt"),
            ChannelConfig("https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Splitted-By-Protocol/hysteria2.txt"),
            ChannelConfig("https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/Splitted-By-Protocol/ss.txt"),
            ChannelConfig("https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/Splitted-By-Protocol/ssr.txt"),
            ChannelConfig("https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/Splitted-By-Protocol/vmess.txt"),
            ChannelConfig("https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/Splitted-By-Protocol/vless.txt"),
            ChannelConfig("https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/Splitted-By-Protocol/trojan.txt"),
            ChannelConfig("https://raw.githubusercontent.com/youfoundamin/V2rayCollector/main/vmess_iran.txt"),
            ChannelConfig("https://raw.githubusercontent.com/youfoundamin/V2rayCollector/main/ss_iran.txt"),
            ChannelConfig("https://raw.githubusercontent.com/youfoundamin/V2rayCollector/main/trojan_iran.txt"),
            ChannelConfig("https://raw.githubusercontent.com/youfoundamin/V2rayCollector/main/vless_iran.txt"),
            ChannelConfig("https://raw.githubusercontent.com/youfoundamin/V2rayCollector/main/mixed_iran.txt"),
            ChannelConfig("https://github.com/barry-far/V2ray-Configs/raw/main/Splitted-By-Protocol/ss.txt"),
            ChannelConfig("https://github.com/barry-far/V2ray-Configs/raw/main/Splitted-By-Protocol/ssr.txt"),
            ChannelConfig("https://github.com/barry-far/V2ray-Configs/raw/main/Splitted-By-Protocol/tuic.txt"),
            ChannelConfig("https://github.com/barry-far/V2ray-Configs/raw/main/Splitted-By-Protocol/vless.txt"),
            ChannelConfig("https://github.com/barry-far/V2ray-Configs/raw/main/Splitted-By-Protocol/vmess.txt"),
            ChannelConfig("https://github.com/barry-far/V2ray-Configs/raw/main/Splitted-By-Protocol/trojan.txt"),
            ChannelConfig("https://github.com/Kwinshadow/TelegramV2rayCollector/raw/main/sublinks/b64mix.txt"),
            ChannelConfig("https://github.com/Kwinshadow/TelegramV2rayCollector/raw/main/sublinks/b64ss.txt"),
            ChannelConfig("https://github.com/Kwinshadow/TelegramV2rayCollector/raw/main/sublinks/b64vmess.txt"),
            ChannelConfig("https://github.com/Kwinshadow/TelegramV2rayCollector/raw/main/sublinks/b64vless.txt"),
            ChannelConfig("https://github.com/Kwinshadow/TelegramV2rayCollector/raw/main/sublinks/b64trojan.txt"),
            ChannelConfig("https://github.com/MrMohebi/xray-proxy-grabber-telegram/raw/master/collected-proxies/row-url/all.txt"),
            ChannelConfig("https://github.com/LonUp/NodeList/raw/main/V2RAY/Latest_base64.txt"),
            ChannelConfig("https://github.com/theGreatPeter/v2rayNodes/raw/main/nodes.txt"),
            ChannelConfig("https://cdn.jsdelivr.net/gh/cry0ice/genode@main/public/all.txt"),
            ChannelConfig("https://cdn.jsdelivr.net/gh/cry0ice/genode@main/public/ss.txt"),
            ChannelConfig("https://cdn.jsdelivr.net/gh/cry0ice/genode@main/public/ssr.txt"),
            ChannelConfig("https://cdn.jsdelivr.net/gh/cry0ice/genode@main/public/vless.txt"),
            ChannelConfig("https://cdn.jsdelivr.net/gh/cry0ice/genode@main/public/vmess.txt"),
            ChannelConfig("https://cdn.jsdelivr.net/gh/cry0ice/genode@main/public/trojan.txt"),
            ChannelConfig("https://freessrnode.github.io/uploads/2024/08/0-20240822.txt"),
            ChannelConfig("https://freessrnode.github.io/uploads/2024/08/1-20240822.txt"),
            ChannelConfig("https://freessrnode.github.io/uploads/2024/08/2-20240822.txt"),
            ChannelConfig("https://freessrnode.github.io/uploads/2024/08/3-20240822.txt"),
            ChannelConfig("https://freessrnode.github.io/uploads/2024/08/4-20240822.txt"),
            ChannelConfig("https://v2rayshare.com/wp-content/uploads/2022/12/20221208.txt"),
            ChannelConfig("https://clashnode.com/wp-content/uploads/2023/03/20230310.txt"),
            ChannelConfig("https://raw.githubusercontent.com/Space-00/V2ray-configs/refs/heads/main/config.txt"),
            ChannelConfig("https://raw.githubusercontent.com/lagzian/SS-Collector/main/reality.txt"),
            ChannelConfig("https://raw.githubusercontent.com/lagzian/SS-Collector/refs/heads/main/VLESS/VL100.txt"),
            ChannelConfig("https://raw.githubusercontent.com/lagzian/new-configs-collector/main/protocols/hysteria"),
            ChannelConfig("https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/Splitted-By-Protocol/vless.txt"),
            ChannelConfig("https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/Splitted-By-Protocol/trojan.txt"),
            ChannelConfig("https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Splitted-By-Protocol/vless.txt"),
            ChannelConfig("https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Splitted-By-Protocol/trojan.txt"),
            ChannelConfig("https://raw.githubusercontent.com/Surfboardv2ray/Proxy-sorter/main/ws_tls/proxies/wstls_base64"),
            ChannelConfig("https://raw.githubusercontent.com/Surfboardv2ray/Proxy-sorter/main/custom/udp.txt"),
            ChannelConfig("https://raw.githubusercontent.com/MhdiTaheri/V2rayCollector/main/sub/vless"),
            ChannelConfig("https://raw.githubusercontent.com/wuqb2i4f/xray-config-toolkit/refs/heads/main/output/base64/mix-security-re"),
            ChannelConfig("https://raw.githubusercontent.com/wuqb2i4f/xray-config-toolkit/refs/heads/main/output/base64/mix-security-tl"),
            ChannelConfig("https://raw.githubusercontent.com/wuqb2i4f/xray-config-toolkit/refs/heads/main/output/base64/mix-network-xh"),
            ChannelConfig("https://raw.githubusercontent.com/wuqb2i4f/xray-config-toolkit/refs/heads/main/output/base64/mix-network-gr"),
            ChannelConfig("https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/one_file_vpn.txt"),
            ChannelConfig("https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/two_file_vpn.txt"),
            ChannelConfig("https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/hysteria"),
            ChannelConfig("https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/channels/protocols/hysteria"),
            ChannelConfig("https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/reality"),
            ChannelConfig("https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/channels/protocols/reality"),
            ChannelConfig("https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/vless"),
            ChannelConfig("https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/subscribe/protocols/vless"),
            ChannelConfig("https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/tuic"),
            ChannelConfig("https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/subscribe/protocols/tuic")
        ]

        # Global limits for number of configs per protocol
        # Default values: min=3, max=25
        # Adjust these values to control how many configs of each type are collected
        self.PROTOCOL_CONFIG_LIMITS = {
            "min": 6000,    # Minimum configs required per protocol (default: 3)
            "max": 16000    # Maximum configs allowed per protocol (default: 25)
        }

        # Supported proxy protocols configuration
        # For each protocol:
        # - min_configs: Minimum number of configs required (default: 3)
        # - max_configs: Maximum number of configs allowed (default: 25)
        # - priority: Higher priority means more configs kept during balancing (default: 1, high priority: 2)
        # - flexible_max: If True, max_configs can be dynamically adjusted (default: True)
        # - aliases: Alternative protocol prefixes to recognize (optional)
        self.SUPPORTED_PROTOCOLS: Dict[str, Dict] = {
            "wireguard://": {
                "min_configs": self.PROTOCOL_CONFIG_LIMITS["min"],
                "max_configs": self.PROTOCOL_CONFIG_LIMITS["max"],
                "priority": 1,
                "flexible_max": True
            },
            "hysteria2://": {
                "min_configs": self.PROTOCOL_CONFIG_LIMITS["min"],
                "max_configs": self.PROTOCOL_CONFIG_LIMITS["max"],
                "priority": 2,
                "flexible_max": True,
                "aliases": ["hy2://"]
            },
            "vless://": {
                "min_configs": self.PROTOCOL_CONFIG_LIMITS["min"],
                "max_configs": self.PROTOCOL_CONFIG_LIMITS["max"],
                "priority": 2,
                "flexible_max": True
            },
            "vmess://": {
                "min_configs": self.PROTOCOL_CONFIG_LIMITS["min"],
                "max_configs": self.PROTOCOL_CONFIG_LIMITS["max"],
                "priority": 1,
                "flexible_max": True
            },
            "ss://": {
                "min_configs": self.PROTOCOL_CONFIG_LIMITS["min"],
                "max_configs": self.PROTOCOL_CONFIG_LIMITS["max"],
                "priority": 1,
                "flexible_max": True
            },
            "trojan://": {
                "min_configs": self.PROTOCOL_CONFIG_LIMITS["min"],
                "max_configs": self.PROTOCOL_CONFIG_LIMITS["max"],
                "priority": 2,
                "flexible_max": True
            },
            "tuic://": {
                "min_configs": self.PROTOCOL_CONFIG_LIMITS["min"],
                "max_configs": self.PROTOCOL_CONFIG_LIMITS["max"],
                "priority": 1,
                "flexible_max": True
            }
        }

        # Channel-specific configuration limits
        self.MIN_CONFIGS_PER_CHANNEL = 6000     # Minimum configs required from each channel (default: 3)
        self.MAX_CONFIGS_PER_CHANNEL = 16000    # Maximum configs allowed from each channel (default: 50)
        self.MAX_CONFIG_AGE_DAYS = 30        # Maximum age of configs in days (default: 90)
        self.CHANNEL_RETRY_LIMIT = 1        # Maximum retry attempts per channel (default: 10)
        self.CHANNEL_ERROR_THRESHOLD = 0.7   # Error rate threshold to disable channel (default: 0.7 or 70%)
        self.MIN_PROTOCOL_RATIO = 0.6        # Minimum ratio of configs per protocol (default: 0.1 or 10%)

        # Dynamic protocol adjustment settings
        self.DYNAMIC_PROTOCOL_ADJUSTMENT = True   # Enable/disable dynamic adjustment (default: True)
        self.PROTOCOL_BALANCE_FACTOR = 1.6        # Factor for adjusting protocol limits (default: 1.5)

        # Output file paths (default paths shown)
        self.OUTPUT_FILE = 'configs/proxy_configs.txt'    # Path to save final configs
        self.STATS_FILE = 'configs/channel_stats.json'    # Path to save channel stats
        
        # HTTP request settings
        self.MAX_RETRIES = 1            # Maximum number of retry attempts (default: 10)
        self.RETRY_DELAY = 1            # Delay between retries in seconds (default: 15)
        self.REQUEST_TIMEOUT = 1        # Request timeout in seconds (default: 60)
        
        # HTTP request headers (default User-Agent and other headers)
        self.HEADERS = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

    def is_protocol_enabled(self, protocol: str) -> bool:
        """
        Check if a protocol is enabled in SUPPORTED_PROTOCOLS.
        Also checks protocol aliases.
        """
        if protocol in self.SUPPORTED_PROTOCOLS:
            return True
        for main_protocol, info in self.SUPPORTED_PROTOCOLS.items():
            if 'aliases' in info and protocol in info['aliases']:
                return True
        return False

    def get_enabled_channels(self) -> List[ChannelConfig]:
        """
        Return list of enabled channels only.
        Channels are enabled by default unless their score drops below 25.
        """
        return [channel for channel in self.SOURCE_URLS if channel.enabled]

    def update_channel_stats(self, channel: ChannelConfig, success: bool, response_time: float = 0):
        """
        Update channel statistics after fetch attempt.
        Disables channel if overall score drops below 25.
        
        Parameters:
        - success: True if fetch was successful (default metrics: success_count=0, fail_count=0)
        - response_time: Response time in seconds (default avg_response_time: 0)
        """
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
        """
        Dynamically adjust protocol limits based on channel performance.
        Only adjusts if DYNAMIC_PROTOCOL_ADJUSTMENT is enabled (default: True).
        Uses PROTOCOL_BALANCE_FACTOR (default: 1.5) to calculate new limits.
        """
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
