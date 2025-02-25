import asyncio
import aiohttp
import re
import zipfile
import io
import os
from typing import Dict, List, Optional
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from dataclasses import dataclass
import logging
from math import inf

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# =============================================================================
# ГЛОБАЛЬНЫЕ КОНСТАНТЫ ДЛЯ НАСТРОЕК
# =============================================================================
# Настройки загрузки профилей по давности
PROFILE_MIN_AGE_DAYS = 1     # минимальный возраст профиля (дней)
PROFILE_MAX_AGE_DAYS = 30    # максимальный возраст профиля (дней)

# Настройки количества профилей из одного источника
PROFILE_MIN_COUNT = 10       # минимальное число профилей, которое требуется получить
PROFILE_MAX_COUNT = 1000     # максимальное число профилей, которое можно получить

# Настройки контроля качества источника
MAX_SOURCE_CHECKS = 30       # после 30 проверок источник с низким баллом будет отключён
MIN_ACCEPTABLE_SCORE = 50    # пороговое значение общего балла для источника

# Весовые коэффициенты для расчёта балла источника
RELIABILITY_WEIGHT = 35      # вес надёжности (на основе успехов/провалов)
QUANTITY_WEIGHT = 25         # вес количества полученных записей
DIVERSITY_WEIGHT = 25        # вес разнообразия протоколов
FREQUENCY_WEIGHT = 15        # вес частоты обновлений

# Дополнительные настройки нормировки
DESIRED_TOTAL_CONFIGS = PROFILE_MAX_COUNT    # нормировочное значение для количества записей
TOTAL_POSSIBLE_PROTOCOLS = 4                 # число разрешённых протоколов (vless, trojan, tuic, hy2)

# Допустимые протоколы для сохранения в конечный файл
ALLOWED_PROTOCOLS = ["vless://", "trojan://", "tuic://", "hy2://"]

# Файл для сохранения итоговых конфигураций
OUTPUT_CONFIG_FILE = "configs/proxy_configs.txt"

# =============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =============================================================================
def country_code_to_emoji(country_code: str) -> str:
    """
    Преобразует двухбуквенный код страны в эмодзи флага.
    """
    OFFSET = 127397
    return ''.join(chr(ord(c) + OFFSET) for c in country_code.upper())

def compute_profile_score(config: str) -> float:
    """
    Базовая функция скоринга для отдельного профиля.
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

# =============================================================================
# КЛАССЫ ДЛЯ МЕТРИК И КОНФИГУРАЦИИ
# =============================================================================
@dataclass
class ChannelMetrics:
    total_configs: int = 0        # общее число строк (попыток)
    valid_configs: int = 0        # число валидных записей (соответствующих фильтру)
    unique_configs: int = 0       # число уникальных протоколов (разнообразие)
    avg_response_time: float = 0.0
    last_success_time: Optional[datetime] = None
    fail_count: int = 0
    success_count: int = 0
    overall_score: float = 0.0    # итоговый балл источника
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
        self.request_timeout = 60
        # Счётчик проверок для контроля качества источника
        self.check_count = 0

    def _validate_url(self, url: str) -> str:
        if not url or not isinstance(url, str):
            raise ValueError("Invalid URL")
        url = url.strip()
        if not url.startswith(('http://', 'https://', 'ssconf://')):
            raise ValueError("Invalid URL protocol")
        return url

    def calculate_overall_score(self):
        """
        Вычисляет общий балл источника с учётом:
         - Надёжности (успешных/неудачных попыток)
         - Количества полученных записей
         - Разнообразия протоколов (сравнивая число уникальных протоколов с максимально возможным)
         - Частоты обновлений (на основе времени последнего успешного обновления)
        Итоговый балл лежит в диапазоне 0-100.
        """
        try:
            total_attempts = max(1, self.metrics.success_count + self.metrics.fail_count)
            reliability_score = (self.metrics.success_count / total_attempts) * RELIABILITY_WEIGHT

            # Балл за количество: нормируем по DESIRED_TOTAL_CONFIGS
            quantity_score = min(QUANTITY_WEIGHT, (self.metrics.total_configs / DESIRED_TOTAL_CONFIGS) * QUANTITY_WEIGHT)

            # Балл за разнообразие протоколов
            diversity_score = (self.metrics.unique_configs / TOTAL_POSSIBLE_PROTOCOLS) * DIVERSITY_WEIGHT

            # Балл за частоту обновлений: чем быстрее обновление, тем выше балл.
            if self.metrics.last_success_time:
                delta = (datetime.now() - self.metrics.last_success_time).total_seconds()
                frequency_score = max(0, FREQUENCY_WEIGHT * (3600 / (delta + 3600)))
            else:
                frequency_score = 0

            self.metrics.overall_score = round(reliability_score + quantity_score + diversity_score + frequency_score, 2)
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
            ChannelConfig("https://raw.githubusercontent.com/MrMohebi/xray-proxy-grabber-telegram/master/collected-proxies/row-url/all.txt)",
            ChannelConfig("https://raw.githubusercontent.com/ALIILAPRO/v2rayNG-Config/refs/heads/main/server.txt)",
            ChannelConfig("https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/All_Configs_Sub.txt)",
            ChannelConfig("https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/All_Configs_Sub.txt)",
            ChannelConfig("https://raw.githubusercontent.com/lagzian/SS-Collector/refs/heads/main/VLESS/VL100.txt)",
            ChannelConfig("https://raw.githubusercontent.com/lagzian/new-configs-collector/main/protocols/hysteria)",
            ChannelConfig("https://raw.githubusercontent.com/lagzian/SS-Collector/main/reality.txt)",
            ChannelConfig("https://raw.githubusercontent.com/sevcator/5ubscrpt10n/refs/heads/main/protocols/vl.txt)",
            ChannelConfig("https://raw.githubusercontent.com/sevcator/5ubscrpt10n/refs/heads/main/protocols/tr.txt)",
            ChannelConfig("https://raw.githubusercontent.com/MhdiTaheri/V2rayCollector/refs/heads/main/sub/hysteria)",
            ChannelConfig("https://raw.githubusercontent.com/MhdiTaheri/V2rayCollector/refs/heads/main/sub/trojan)",
            ChannelConfig("https://raw.githubusercontent.com/MhdiTaheri/V2rayCollector/refs/heads/main/sub/tuic)",
            ChannelConfig("https://raw.githubusercontent.com/MhdiTaheri/V2rayCollector/refs/heads/main/sub/vless)",
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

        # Используем глобальную константу для OUTPUT_CONFIG_FILE
        self.OUTPUT_FILE = OUTPUT_CONFIG_FILE
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
        # Если канал получает низкий балл после 30 проверок, отключаем его
        if channel.check_count >= MAX_SOURCE_CHECKS and channel.metrics.overall_score < MIN_ACCEPTABLE_SCORE:
            channel.enabled = False
            logger.info(f"Channel {channel.url} disabled after {channel.check_count} checks (score: {channel.metrics.overall_score}).")
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
        """
        Сохраняет пустой файл в OUTPUT_CONFIG_FILE.
        Используем глобальную константу, чтобы избежать ошибки, если self оказался строкой.
        """
        try:
            os.makedirs(os.path.dirname(OUTPUT_CONFIG_FILE), exist_ok=True)
            with open(OUTPUT_CONFIG_FILE, 'w', encoding='utf-8') as f:
                f.write("")
            return True
        except Exception as e:
            logger.error(f"Error saving empty configs: {str(e)}")
            return False

# =============================================================================
# АСИНХРОННЫЕ ФУНКЦИИ ДЛЯ СКАЧИВАНИЯ И ОБРАБОТКИ ПРОФИЛЕЙ
# =============================================================================
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
    Фильтрация производится по допустимым протоколам, обновляются метрики канала и вычисляется скоринг.
    """
    proxies = []
    async with semaphore:
        try:
            async with session.get(channel.url, timeout=channel.request_timeout) as response:
                text = await response.text()
                logger.info(f"Downloaded content from {channel.url}")
        except Exception as e:
            logger.error(f"Error downloading channel {channel.url}: {str(e)}")
            channel.check_count += 1
            channel.metrics.fail_count += 1
            channel.calculate_overall_score()
            return proxies

    lines = text.splitlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue

        channel.metrics.total_configs += 1

        # Фильтрация: оставляем только записи, начинающиеся с разрешённых протоколов
        if not any(line.startswith(proto) for proto in ALLOWED_PROTOCOLS):
            continue

        channel.metrics.valid_configs += 1
        for proto in ALLOWED_PROTOCOLS:
            if line.startswith(proto):
                channel.metrics.protocol_counts[proto] = channel.metrics.protocol_counts.get(proto, 0) + 1
                break
        channel.metrics.unique_configs = len(channel.metrics.protocol_counts)

        score = compute_profile_score(line)
        flag = "Unknown"

        ip_match = re.search(r'(\d{1,3}(?:\.\d{1,3}){3})', line)
        if ip_match and ip_db:
            ip_address = ip_match.group(1)
            try:
                rec = ip_db.get_all(ip_address)
                country_name = rec.country_long if hasattr(rec, 'country_long') else "Unknown"
                country_code = rec.country_short if hasattr(rec, 'country_short') else ""
                if country_code:
                    flag = country_code_to_emoji(country_code)
                # Дополнительный бонус за наличие корректной информации о стране
                score += 10
            except Exception as e:
                logger.error(f"IP2Location lookup failed for IP {ip_address}: {str(e)}")
        else:
            score -= 5

        # В словаре сохраняем исходную строку, а также вычисленный балл и флаг
        proxies.append({
            "config": line,
            "flag": flag,
            "score": score
        })

    channel.check_count += 1
    if proxies:
        channel.metrics.success_count += 1
        channel.metrics.last_success_time = datetime.now()
    else:
        channel.metrics.fail_count += 1

    channel.calculate_overall_score()

    if channel.check_count >= MAX_SOURCE_CHECKS and channel.metrics.overall_score < MIN_ACCEPTABLE_SCORE:
        channel.enabled = False
        logger.info(f"Channel {channel.url} disabled after {channel.check_count} checks (score: {channel.metrics.overall_score}).")

    multiplier = 1 + (channel.metrics.overall_score / 100)
    for p in proxies:
        p['score'] *= multiplier

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
    Сохраняет итоговые прокси-конфигурации.
    Формат записи:
    <config URL>#<flag emoji> | <Protocol> | <Protocol Type>
    Все записи сохраняются в OUTPUT_CONFIG_FILE.
    """
    proxies_sorted = sorted(proxies, key=lambda x: x['score'], reverse=True)
    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
    except Exception:
        pass
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for proxy in proxies_sorted:
                config = proxy['config']
                # Извлекаем флаг из сохранённого значения (либо "Unknown")
                flag = proxy.get("flag", "Unknown")
                # Извлекаем протокол (до "://")
                parsed = urlparse(config)
                proto = parsed.scheme if parsed.scheme else "Unknown"
                # Извлекаем тип протокола из параметра "type" (если есть)
                qs = parse_qs(parsed.query)
                proto_type = qs.get("type", ["Unknown"])[0]
                final_line = f"{config}#{flag} | {proto} | {proto_type}\n"
                f.write(final_line)
        logger.info(f"Final configurations saved to {output_file}")
    except Exception as e:
        logger.error(f"Error saving configs: {str(e)}")

def main():
    proxy_config = ProxyConfig()
    channels = proxy_config.get_enabled_channels()
    
    async def runner():
        async with aiohttp.ClientSession(headers=proxy_config.HEADERS) as session:
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
            
            if ip_db_path and os.path.exists(ip_db_path):
                os.remove(ip_db_path)
                logger.info("Temporary IP2Location database file removed.")
    
    asyncio.run(runner())

if __name__ == "__main__":
    main()
