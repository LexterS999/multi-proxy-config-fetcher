import os
import json
import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Set
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

from config import ProxyConfig, ChannelConfig
from config_validator import ConfigValidator, ALLOWED_PROTOCOLS

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('proxy_fetcher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ConfigFetcher:
    def __init__(self, config: ProxyConfig):
        self.config = config
        self.validator = ConfigValidator()
        # Учтём только разрешённые протоколы
        self.protocol_counts: Dict[str, int] = {p: 0 for p in self.config.SUPPORTED_PROTOCOLS if p in ALLOWED_PROTOCOLS}
        self.seen_configs: Set[str] = set()
        self.channel_protocol_counts: Dict[str, Dict[str, int]] = {}

    async def fetch_with_retry(self, url: str, session: aiohttp.ClientSession) -> Optional[aiohttp.ClientResponse]:
        backoff = 1
        for attempt in range(self.config.MAX_RETRIES):
            try:
                async with session.get(url, timeout=self.config.REQUEST_TIMEOUT) as response:
                    if response.status == 200:
                        return response
                    else:
                        logger.error(f"Non-200 status code {response.status} for URL: {url}")
            except Exception as e:
                if attempt == self.config.MAX_RETRIES - 1:
                    logger.error(f"Failed to fetch {url} after {self.config.MAX_RETRIES} attempts: {e}")
                    return None
                wait_time = min(self.config.RETRY_DELAY * backoff, 60)
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                await asyncio.sleep(wait_time)
                backoff *= 2
        return None

    async def fetch_ssconf_configs(self, url: str, session: aiohttp.ClientSession) -> List[str]:
        https_url = self.validator.convert_ssconf_to_https(url)
        configs = []
        response = await self.fetch_with_retry(https_url, session)
        if response:
            text = (await response.text()).strip()
            if text:
                if self.validator.is_base64(text):
                    decoded = self.validator.decode_base64_text(text)
                    if decoded:
                        text = decoded
                # Допускаем только если начинается с разрешённого протокола (например, ss:// не входит в ALLOWED_PROTOCOLS)
                if any(text.startswith(p) for p in ALLOWED_PROTOCOLS):
                    configs.append(text)
                else:
                    configs.extend(self.validator.split_configs(text))
        return configs

    def check_and_decode_base64(self, text: str) -> str:
        if self.validator.is_base64(text):
            decoded = self.validator.decode_base64_text(text)
            if decoded:
                return decoded
        return text

    async def fetch_configs_from_source(self, channel: ChannelConfig, session: aiohttp.ClientSession) -> List[str]:
        configs: List[str] = []
        # Сброс статистики канала
        channel.metrics.total_configs = 0
        channel.metrics.valid_configs = 0
        channel.metrics.unique_configs = 0
        channel.metrics.protocol_counts = {p: 0 for p in self.config.SUPPORTED_PROTOCOLS if p in ALLOWED_PROTOCOLS}

        start_time = datetime.now()

        if channel.url.startswith('ssconf://'):
            ssconf_configs = await self.fetch_ssconf_configs(channel.url, session)
            configs.extend(ssconf_configs)
            if configs:
                response_time = (datetime.now() - start_time).total_seconds()
                self.config.update_channel_stats(channel, True, response_time)
            return configs

        response = await self.fetch_with_retry(channel.url, session)
        if not response:
            self.config.update_channel_stats(channel, False)
            return configs

        response_text = await response.text()
        response_time = (datetime.now() - start_time).total_seconds()

        if channel.is_telegram:
            soup = BeautifulSoup(response_text, 'html.parser')
            messages = soup.find_all('div', class_='tgme_widget_message_text')
            sorted_messages = sorted(
                messages,
                key=lambda message: self.extract_date_from_message(message) or datetime.min.replace(tzinfo=timezone.utc),
                reverse=True
            )
            for message in sorted_messages:
                if not message or not message.text:
                    continue
                message_date = self.extract_date_from_message(message)
                if not self.is_config_valid(message.text, message_date):
                    continue
                text = message.text
                text_parts = text.split()
                for part in text_parts:
                    part = part.strip()
                    if not part:
                        continue
                    if part.startswith('ssconf://'):
                        ssconf_configs = await self.fetch_ssconf_configs(part, session)
                        configs.extend(ssconf_configs)
                        channel.metrics.total_configs += len(ssconf_configs)
                    else:
                        decoded_part = self.check_and_decode_base64(part)
                        if decoded_part != part:
                            found_configs = self.validator.split_configs(decoded_part)
                            channel.metrics.total_configs += len(found_configs)
                            configs.extend(found_configs)
                found_configs = self.validator.split_configs(text)
                channel.metrics.total_configs += len(found_configs)
                configs.extend(found_configs)
        else:
            text_parts = response_text.split()
            for part in text_parts:
                part = part.strip()
                if not part:
                    continue
                decoded_part = self.check_and_decode_base64(part)
                if decoded_part != part:
                    found_configs = self.validator.split_configs(decoded_part)
                    channel.metrics.total_configs += len(found_configs)
                    configs.extend(found_configs)
            found_configs = self.validator.split_configs(response_text)
            channel.metrics.total_configs += len(found_configs)
            configs.extend(found_configs)

        configs = list(set(configs))
        for conf in configs[:]:
            # Обработка только разрешённых протоколов
            for protocol in [p for p in self.config.SUPPORTED_PROTOCOLS if p in ALLOWED_PROTOCOLS]:
                if conf.startswith(protocol):
                    processed_configs = self.process_config(conf, channel)
                    if not processed_configs:
                        configs.remove(conf)
                    break

        if len(configs) >= self.config.MIN_CONFIGS_PER_CHANNEL:
            self.config.update_channel_stats(channel, True, response_time)
            self.config.adjust_protocol_limits(channel)
        else:
            self.config.update_channel_stats(channel, False)
            logger.warning(f"Not enough configs found in {channel.url}: {len(configs)} configs")
        return configs

    def process_config(self, config: str, channel: ChannelConfig) -> List[str]:
        processed_configs = []
        if config.startswith('hy2://') or config.startswith('hysteria2://'):
            config = self.validator.normalize_hysteria2_protocol(config)
        for protocol in [p for p in self.config.SUPPORTED_PROTOCOLS if p in ALLOWED_PROTOCOLS]:
            aliases = self.config.SUPPORTED_PROTOCOLS[protocol].get('aliases', [])
            protocol_match = False
            if config.startswith(protocol):
                protocol_match = True
            else:
                for alias in aliases:
                    if config.startswith(alias):
                        protocol_match = True
                        config = config.replace(alias, protocol, 1)
                        break
            if protocol_match:
                if protocol == "vless://" or protocol == "trojan://" or protocol == "tuic://" or protocol == "hy2://":
                    clean_config = self.validator.clean_config(config)
                    if self.validator.validate_protocol_config(clean_config, protocol):
                        channel.metrics.valid_configs += 1
                        channel.metrics.protocol_counts[protocol] = channel.metrics.protocol_counts.get(protocol, 0) + 1
                        if clean_config not in self.seen_configs:
                            channel.metrics.unique_configs += 1
                            self.seen_configs.add(clean_config)
                            processed_configs.append(clean_config)
                            self.protocol_counts[protocol] += 1
                break
        return processed_configs

    def extract_date_from_message(self, message) -> Optional[datetime]:
        try:
            time_element = message.find_parent('div', class_='tgme_widget_message').find('time')
            if time_element and 'datetime' in time_element.attrs:
                return datetime.fromisoformat(time_element['datetime'].replace('Z', '+00:00'))
        except Exception as e:
            logger.error(f"Error extracting date: {e}")
        return None

    def is_config_valid(self, config_text: str, date: Optional[datetime]) -> bool:
        if not date:
            return True
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.config.MAX_CONFIG_AGE_DAYS)
        return date >= cutoff_date

    def balance_protocols(self, configs: List[str]) -> List[str]:
        protocol_configs: Dict[str, List[str]] = {p: [] for p in self.config.SUPPORTED_PROTOCOLS if p in ALLOWED_PROTOCOLS}
        for conf in configs:
            if conf.startswith('hy2://') or conf.startswith('hysteria2://'):
                conf = self.validator.normalize_hysteria2_protocol(conf)
            for protocol in [p for p in self.config.SUPPORTED_PROTOCOLS if p in ALLOWED_PROTOCOLS]:
                if conf.startswith(protocol):
                    protocol_configs[protocol].append(conf)
                    break
        total_configs = sum(len(lst) for lst in protocol_configs.values())
        if total_configs == 0:
            return []
        balanced_configs: List[str] = []
        sorted_protocols = sorted(
            protocol_configs.items(),
            key=lambda x: (self.config.SUPPORTED_PROTOCOLS[x[0]]["priority"], len(x[1])),
            reverse=True
        )
        for protocol, protocol_list in sorted_protocols:
            protocol_info = self.config.SUPPORTED_PROTOCOLS[protocol]
            if len(protocol_list) >= protocol_info["min_configs"]:
                max_configs = min(protocol_info["max_configs"], len(protocol_list))
                balanced_configs.extend(protocol_list[:max_configs])
            elif protocol_info.get("flexible_max") and len(protocol_list) > 0:
                balanced_configs.extend(protocol_list)
        return balanced_configs

    async def fetch_all_configs(self, session: aiohttp.ClientSession) -> List[str]:
        all_configs: List[str] = []
        enabled_channels = self.config.get_enabled_channels()
        total_channels = len(enabled_channels)
        for idx, channel in enumerate(enabled_channels, 1):
            logger.info(f"Fetching configs from {channel.url} ({idx}/{total_channels})")
            channel_configs = await self.fetch_configs_from_source(channel, session)
            all_configs.extend(channel_configs)
            if idx < total_channels:
                await asyncio.sleep(2)
        if all_configs:
            all_configs = self.balance_protocols(sorted(set(all_configs)))
            return all_configs
        return []


def save_configs(configs: List[str], config: ProxyConfig):
    try:
        os.makedirs(os.path.dirname(config.OUTPUT_FILE), exist_ok=True)
        with open(config.OUTPUT_FILE, 'w', encoding='utf-8') as f:
            header = """//profile-title: base64:8J+RvUFub255bW91cy3wnZWP
//profile-update-interval: 1
//subscription-userinfo: upload=0; download=0; total=10737418240000000; expire=2546249531
//support-url: https://t.me/BXAMbot
//profile-web-page-url: https://github.com/4n0nymou3

"""
            f.write(header)
            # Формат записи: <config URL>#<flag emoji> | <Protocol> | <Protocol Type>
            for conf in configs:
                parsed = urlparse(conf)
                proto = parsed.scheme if parsed.scheme else "Unknown"
                qs = parse_qs(parsed.query)
                proto_type = qs.get("type", ["Unknown"])[0]
                flag = "Unknown"  # Флаг будет определён основным скриптом с IP2Location
                final_line = f"{conf}#{flag} | {proto} | {proto_type}\n\n"
                f.write(final_line)
        logger.info(f"Successfully saved {len(configs)} configs to {config.OUTPUT_FILE}")
    except Exception as e:
        logger.error(f"Error saving configs: {e}")


def save_channel_stats(config: ProxyConfig):
    try:
        stats = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'channels': []
        }
        for channel in config.SOURCE_URLS:
            channel_stats = {
                'url': channel.url,
                'enabled': channel.enabled,
                'metrics': {
                    'total_configs': channel.metrics.total_configs,
                    'valid_configs': channel.metrics.valid_configs,
                    'unique_configs': channel.metrics.unique_configs,
                    'avg_response_time': round(channel.metrics.avg_response_time, 2),
                    'success_count': channel.metrics.success_count,
                    'fail_count': channel.metrics.fail_count,
                    'overall_score': round(channel.metrics.overall_score, 2),
                    'last_success': channel.metrics.last_success_time.replace(tzinfo=timezone.utc).isoformat() if channel.metrics.last_success_time else None,
                    'protocol_counts': channel.metrics.protocol_counts
                }
            }
            stats['channels'].append(channel_stats)
        os.makedirs(os.path.dirname(config.STATS_FILE), exist_ok=True)
        with open(config.STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
        logger.info(f"Channel statistics saved to {config.STATS_FILE}")
    except Exception as e:
        logger.error(f"Error saving channel statistics: {e}")


async def main():
    config = ProxyConfig()
    fetcher = ConfigFetcher(config)
    async with aiohttp.ClientSession(headers=config.HEADERS) as session:
        configs = await fetcher.fetch_all_configs(session)
    if configs:
        save_configs(configs, config)
        logger.info(f"Successfully processed {len(configs)} configs at {datetime.now(timezone.utc)}")
        for protocol, count in fetcher.protocol_counts.items():
            logger.info(f"{protocol}: {count} configs")
    else:
        logger.error("No valid configs found!")
    save_channel_stats(config)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
