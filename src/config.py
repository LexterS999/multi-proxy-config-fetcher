import asyncio
import aiohttp
import re
import zipfile
import io
import os
from typing import Dict, List, Optional
from datetime import datetime
from urllib.parse import urlparse
from dataclasses import dataclass
import logging
from math import inf

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Допустимые протоколы для сохранения в итоговый файл
ALLOWED_PROTOCOLS = ["vless://", "trojan://", "tuic://", "hy2://"]

def country_code_to_emoji(country_code: str) -> str:
    """
    Преобразует двухбуквенный код страны в эмодзи флага.
    """
    OFFSET = 127397
    return ''.join(chr(ord(c) + OFFSET) for c in country_code.upper())

def compute_profile_score(config: str) -> float:
    """
    Комплексная функция скоринга для профиля.
    Базовый балл зависит от протокола, дополнительно учитывается длина строки.
    """
    base_scores = {
         "vless://": 100,
         "trojan://": 90,
         "tuic://": 80,
         "hy2://": 70
    }
    for proto, base in base_scores.items():
         if config.startswith(proto):
             extra = len(config) / 10.0
             return base + extra
    return 0.0

@dataclass
class ChannelMetrics:
    total_configs: int = 0
    valid_configs: int = 0
    unique_configs: int = 0
    avg_response_time: float = 0.0
    last_success_time: Optional[datetime] = None
    fail_count: int = 0
    success_count: int = 0
    overall_score: float = 0.0
    protocol_counts: Dict[str, int] = None

    def __post_init__(self):
        if self.protocol_counts is None:
            self.protocol_counts = {}

class ChannelConfig:
    def __init__(self, url: str, enabled: bool = True):
        self.url = self._validate_url(url)
        self.enabled = enabled
        self.metrics = ChannelMetrics()
        self.is_telegram = bool(re.match(r'^https://t\.me/s/', self.url))
        self.error_count = 0
        self.last_check_time = None
        # Таймаут запроса, может регулироваться в ProxyConfig
        self.request_timeout = 60

    def _validate_url(self, url: str) -> str:
        if not url or not isinstance(url, str):
            raise ValueError("Invalid URL")
        url = url.strip()
        # Разрешены протоколы http, https и ssconf
        if not url.startswith(('http://', 'https://', 'ssconf://')):
            raise ValueError("Invalid URL protocol")
        return url

    def calculate_overall_score(self):
        try:
            total_attempts = max(1, self.metrics.success_count + self.metrics.fail_count)
            reliability_score = (self.metrics.success_count / total_attempts) * 35
            
            total_configs = max(1, self.metrics.total_configs)
            quality_score = (self.metrics.valid_configs / total_configs) * 25
            
            valid_configs = max(1, self.metrics.valid_configs)
            uniqueness_score = (self.metrics.unique_configs / valid_configs) * 25
            
            response_score = 15
            if self.metrics.avg_response_time > 0:
                response_score = max(0, min(15, 15 * (1 - (self.metrics.avg_response_time / 10))))
            
            self.metrics.overall_score = round(reliability_score + quality_score + uniqueness_score + response_score, 2)
        except Exception as e:
            logger.error(f"Error calculating score for {self.url}: {str(e)}")
            self.metrics.overall_score = 0.0

class ProxyConfig:
    def __init__(self):
        # Режим конфигурации:
        # Option 1: use_maximum_power = True для максимально возможного числа записей (наивысший приоритет)
        # Option 2: specific_config_count > 0 для задания желаемого количества (по умолчанию: 200)
        # Если use_maximum_power = True, specific_config_count игнорируется.
        self.use_maximum_power = False
        self.specific_config_count = 200

        initial_urls = [
            ChannelConfig("https://raw.githubusercontent.com/mahsanet/MahsaFreeConfig/refs/heads/main/mtn/sub_1.txt"),
            ChannelConfig("https://t.me/s/v2ray_free_conf"),
            ChannelConfig("https://t.me/s/PrivateVPNs"),
            ChannelConfig("https://t.me/s/IP_CF_Config"),
            ChannelConfig("https://t.me/s/shadowproxy66"),
            ChannelConfig("https://t.me/s/OutlineReleasedKey"),
            ChannelConfig("https://t.me/s/prrofile_purple"),
            ChannelConfig("https://t.me/s/meli_proxyy"),
            ChannelConfig("https://t.me/s/DirectVPN"),
            ChannelConfig("https://t.me/s/VmessProtocol"),
            ChannelConfig("https://t.me/s/ViProxys"),
            ChannelConfig("https://t.me/s/heyatserver"),
            ChannelConfig("https://t.me/s/vpnfail_vless"),
            ChannelConfig("https://t.me/s/DailyV2RY"),
            ChannelConfig("https://t.me/s/ShadowsocksM")
        ]

        self.SOURCE_URLS = self._remove_duplicate_urls(initial_urls)
        self.SUPPORTED_PROTOCOLS = self._initialize_protocols()
        self._initialize_settings()
        self._set_smart_limits()
        # Параметры для настройки скачивания профилей по давности и количеству
        self.PROFILE_MIN_AGE_DAYS = 1
        self.PROFILE_MAX_AGE_DAYS = 30
        self.PROFILE_MIN_COUNT = 10
        self.PROFILE_MAX_COUNT = 1000
        self.OUTPUT_FILE = 'configs/proxy_configs.txt'
        self.STATS_FILE = 'configs/channel_stats.json'

    def _initialize_protocols(self) -> Dict:
        return {
            "wireguard://": {"priority": 2, "aliases": [], "enabled": True},
            "hysteria2://": {"priority": 2, "aliases": ["hy2://"], "enabled": True},
            "vless://": {"priority": 2, "aliases": [], "enabled": True},
            "vmess://": {"priority": 1, "aliases": [], "enabled": True},
            "ss://": {"priority": 2, "aliases": [], "enabled": True},
            "trojan://": {"priority": 2, "aliases": [], "enabled": True},
            "tuic://": {"priority": 1, "aliases": [], "enabled": True}
        }

    def _initialize_settings(self):
        self.MAX_CONFIG_AGE_DAYS = min(30, max(1, 7))
        self.CHANNEL_RETRY_LIMIT = min(10, max(1, 5))
        self.CHANNEL_ERROR_THRESHOLD = min(0.9, max(0.1, 0.7))
        self.MAX_RETRIES = min(10, max(1, 5))
        self.RETRY_DELAY = min(60, max(5, 15))
        self.REQUEST_TIMEOUT = min(120, max(10, 60))
        
        self.HEADERS = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

    def _set_smart_limits(self):
        if self.use_maximum_power:
            self._set_maximum_power_mode()
        else:
            self._set_specific_count_mode()

    def _set_maximum_power_mode(self):
        max_configs = 10000
        
        for protocol in self.SUPPORTED_PROTOCOLS:
            self.SUPPORTED_PROTOCOLS[protocol].update({
                "min_configs": 1,
                "max_configs": max_configs,
                "flexible_max": True
            })
        
        self.MIN_CONFIGS_PER_CHANNEL = 1
        self.MAX_CONFIGS_PER_CHANNEL = max_configs
        self.MAX_RETRIES = min(10, max(1, 10))
        self.CHANNEL_RETRY_LIMIT = min(10, max(1, 10))
        self.REQUEST_TIMEOUT = min(120, max(30, 90))

    def _set_specific_count_mode(self):
        if self.specific_config_count <= 0:
            self.specific_config_count = 50
        
        protocols_count = len(self.SUPPORTED_PROTOCOLS)
        base_per_protocol = max(1, self.specific_config_count // protocols_count)
        
        for protocol in self.SUPPORTED_PROTOCOLS:
            self.SUPPORTED_PROTOCOLS[protocol].update({
                "min_configs": 1,
                "max_configs": min(base_per_protocol * 2, 1000),
                "flexible_max": True
            })
        
        self.MIN_CONFIGS_PER_CHANNEL = 1
        self.MAX_CONFIGS_PER_CHANNEL = min(max(5, self.specific_config_count // 2), 1000)

    def _normalize_url(self, url: str) -> str:
        try:
            if not url:
                raise ValueError("Empty URL")
                
            url = url.strip()
            if url.startswith('ssconf://'):
                url = url.replace('ssconf://', 'https://', 1)
                
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Invalid URL format")
                
            path = parsed.path.rstrip('/')
            
            if parsed.netloc.startswith('t.me/s/'):
                channel_name = parsed.path.strip('/').lower()
                return f"telegram:{channel_name}"
                
            return f"{parsed.scheme}://{parsed.netloc}{path}"
        except Exception as e:
            logger.error(f"URL normalization error: {str(e)}")
            raise

    def _remove_duplicate_urls(self, channel_configs: List[ChannelConfig]) -> List[ChannelConfig]:
        try:
            seen_urls = {}
            unique_configs = []
            
            for config in channel_configs:
                if not isinstance(config, ChannelConfig):
                    logger.warning(f"Invalid config skipped: {config}")
                    continue
                    
                try:
                    normalized_url = self._normalize_url(config.url)
                    if normalized_url not in seen_urls:
                        seen_urls[normalized_url] = True
                        unique_configs.append(config)
                except Exception:
                    continue
            
            if not unique_configs:
                self.save_empty_config_file()
                logger.error("No valid sources found. Empty config file created.")
                return []
                
            return unique_configs
        except Exception as e:
            logger.error(f"Error removing duplicate URLs: {str(e)}")
            self.save_empty_config_file()
            return []

    def is_protocol_enabled(self, protocol: str) -> bool:
        try:
            if not protocol:
                return False
                
            protocol = protocol.lower().strip()
            
            if protocol in self.SUPPORTED_PROTOCOLS:
                return self.SUPPORTED_PROTOCOLS[protocol].get("enabled", False)
                
            for main_protocol, info in self.SUPPORTED_PROTOCOLS.items():
                if protocol in info.get("aliases", []):
                    return info.get("enabled", False)
                    
            return False
        except Exception:
            return False

    def get_enabled_channels(self) -> List[ChannelConfig]:
        channels = [channel for channel in self.SOURCE_URLS if channel.enabled]
        if not channels:
            self.save_empty_config_file()
            logger.error("No enabled channels found. Empty config file created.")
        return channels

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
        
        if not any(c.enabled for c in self.SOURCE_URLS):
            self.save_empty_config_file()
            logger.error("All channels are disabled. Empty config file created.")

    def adjust_protocol_limits(self, channel: ChannelConfig):
        if self.use_maximum_power:
            return
            
        for protocol in channel.metrics.protocol_counts:
            if protocol in self.SUPPORTED_PROTOCOLS:
                current_count = channel.metrics.protocol_counts[protocol]
                if current_count > 0:
                    self.SUPPORTED_PROTOCOLS[protocol]["min_configs"] = min(
                        self.SUPPORTED_PROTOCOLS[protocol]["min_configs"],
                        current_count
                    )

    def save_empty_config_file(self) -> bool:
        try:
            with open(self.OUTPUT_FILE, 'w', encoding='utf-8') as f:
                f.write("")
            return True
        except Exception:
            return False

# Асинхронные функции для скачивания, обработки, фильтрации и валидации профилей

async def download_ip2location_db(session: aiohttp.ClientSession, url: str = "https://download.ip2location.com/lite/IP2LOCATION-LITE-DB1.BIN.ZIP") -> Optional[str]:
    """
    Асинхронно скачивает ZIP-архив базы IP2Location, извлекает BIN-файл и сохраняет его во временный файл.
    """
    try:
        async with session.get(url) as response:
            if response.status == 200:
                content = await response.read()
                with zipfile.ZipFile(io.BytesIO(content)) as z:
                    for filename in z.namelist():
                        if filename.upper().endswith('.BIN'):
                            data = z.read(filename)
                            temp_path = "temp_ip2location.bin"
                            with open(temp_path, 'wb') as f:
                                f.write(data)
                            logger.info("IP2Location database downloaded and extracted.")
                            return temp_path
            else:
                logger.error("Failed to download IP2Location DB. Status code: %s", response.status)
    except Exception as e:
        logger.error(f"Exception during IP2Location DB download: {str(e)}")
    return None

async def process_channel(channel: ChannelConfig, ip_db, session: aiohttp.ClientSession, semaphore: asyncio.Semaphore, proxy_config: ProxyConfig) -> List[Dict]:
    """
    Асинхронно скачивает и обрабатывает профили из одного канала.
    Фильтрует по допустимым протоколам, выполняет валидацию и назначает скоринг.
    """
    proxies = []
    allowed_protocols = ALLOWED_PROTOCOLS
    async with semaphore:
        try:
            async with session.get(channel.url, timeout=channel.request_timeout) as response:
                text = await response.text()
                logger.info(f"Downloaded content from {channel.url}")
        except Exception as e:
            logger.error(f"Error downloading channel {channel.url}: {str(e)}")
            return proxies

    # Если источник с raw.githubusercontent.com – применяется оптимизированная обработка.
    is_fast_source = "raw.githubusercontent.com" in channel.url
    lines = text.splitlines()
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Фильтрация: оставляем только записи с допустимыми протоколами.
        if not any(line.startswith(proto) for proto in allowed_protocols):
            continue

        # Вычисление скоринга профиля.
        score = compute_profile_score(line)
        profile_name = "Unknown"
        
        # Попытка извлечь IP-адрес из строки (упрощённое предположение).
        ip_match = re.search(r'(\d{1,3}(?:\.\d{1,3}){3})', line)
        if ip_match and ip_db:
            ip_address = ip_match.group(1)
            try:
                rec = ip_db.get_all(ip_address)
                country_name = rec.country_long if hasattr(rec, 'country_long') else "Unknown"
                country_code = rec.country_short if hasattr(rec, 'country_short') else ""
                flag = country_code_to_emoji(country_code) if country_code else ""
                profile_name = f"{flag} | {country_name}"
                # Дополнительный бонус к скорингу при наличии корректной информации о стране.
                score += 10
            except Exception as e:
                logger.error(f"IP2Location lookup failed for IP {ip_address}: {str(e)}")
        else:
            # Если IP не найден, немного снижаем балл.
            score -= 5
        
        proxies.append({
            "config": line,
            "name": profile_name,
            "score": score
        })
    return proxies

async def process_all_channels(channels: List[ChannelConfig], ip_db, proxy_config: ProxyConfig) -> List[Dict]:
    """
    Асинхронно обрабатывает все каналы, используя 60 параллельных потоков.
    """
    semaphore = asyncio.Semaphore(60)
    proxies_all = []
    async with aiohttp.ClientSession(headers=proxy_config.HEADERS) as session:
        tasks = [process_channel(channel, ip_db, session, semaphore, proxy_config) for channel in channels]
        results = await asyncio.gather(*tasks)
        for result in results:
            proxies_all.extend(result)
    return proxies_all

def save_final_configs(proxies: List[Dict], output_file: str):
    """
    Сохраняет итоговые прокси-конфигурации, отсортированные по убыванию балла (от наиболее полного к менее заполненному).
    """
    proxies_sorted = sorted(proxies, key=lambda x: x['score'], reverse=True)
    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
    except Exception:
        pass
    with open(output_file, 'w', encoding='utf-8') as f:
        for proxy in proxies_sorted:
            # Формат записи: конфигурация - имя профиля (с флагом и названием страны)
            f.write(f"{proxy['config']} - {proxy['name']}\n")
    logger.info(f"Final configurations saved to {output_file}")

def main():
    proxy_config = ProxyConfig()
    channels = proxy_config.get_enabled_channels()
    
    async def runner():
        async with aiohttp.ClientSession(headers=proxy_config.HEADERS) as session:
            # Скачивание и инициализация базы IP2Location для временного использования.
            ip_db_path = await download_ip2location_db(session)
            ip_db = None
            if ip_db_path:
                try:
                    import IP2Location
                    ip_db = IP2Location.IP2Location(ip_db_path)
                except Exception as e:
                    logger.error(f"Error initializing IP2Location: {str(e)}")
            else:
                logger.warning("IP2Location database not available. Country info will be missing.")
            
            proxies = await process_all_channels(channels, ip_db, proxy_config)
            save_final_configs(proxies, proxy_config.OUTPUT_FILE)
            
            # Очистка временного файла базы IP2Location
            if ip_db_path and os.path.exists(ip_db_path):
                os.remove(ip_db_path)
                logger.info("Temporary IP2Location database file removed.")
    
    asyncio.run(runner())

if __name__ == "__main__":
    main()
