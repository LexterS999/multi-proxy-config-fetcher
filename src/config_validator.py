import re
import base64
import json
from typing import Optional, Tuple, List
from urllib.parse import unquote, urlparse
import logging

logger = logging.getLogger(__name__)

# Разрешённые протоколы согласно основному коду
ALLOWED_PROTOCOLS = ["vless://", "trojan://", "tuic://", "hy2://"]

class ConfigValidator:
    @staticmethod
    def is_base64(s: str) -> bool:
        try:
            s = s.rstrip('=')
            return bool(re.match(r'^[A-Za-z0-9+/\-_]*$', s))
        except Exception as e:
            logger.error(f"Error in is_base64: {e}")
            return False

    @staticmethod
    def decode_base64_url(s: str) -> Optional[bytes]:
        try:
            s = s.replace('-', '+').replace('_', '/')
            padding = 4 - (len(s) % 4)
            if padding != 4:
                s += '=' * padding
            return base64.b64decode(s)
        except Exception as e:
            logger.error(f"Error decoding base64 URL: {e}")
            return None

    @staticmethod
    def decode_base64_text(text: str) -> Optional[str]:
        try:
            if ConfigValidator.is_base64(text):
                decoded = ConfigValidator.decode_base64_url(text)
                if decoded:
                    return decoded.decode('utf-8')
            return None
        except Exception as e:
            logger.error(f"Error decoding base64 text: {e}")
            return None

    @staticmethod
    def normalize_hysteria2_protocol(config: str) -> str:
        """
        Приводит протокол с префиксом "hysteria2://" к требуемому виду "hy2://".
        """
        if config.startswith('hysteria2://'):
            return config.replace('hysteria2://', 'hy2://', 1)
        return config

    @staticmethod
    def is_base64_config(config: str) -> Tuple[bool, str]:
        for protocol in ALLOWED_PROTOCOLS:
            if config.startswith(protocol):
                base64_part = config[len(protocol):]
                decoded_url = unquote(base64_part)
                if (ConfigValidator.is_base64(decoded_url) or 
                    ConfigValidator.is_base64(base64_part)):
                    return True, protocol[:-3]
        return False, ''

    @staticmethod
    def check_base64_content(text: str) -> Optional[str]:
        try:
            decoded_text = ConfigValidator.decode_base64_text(text)
            if decoded_text:
                for protocol in ALLOWED_PROTOCOLS:
                    if protocol in decoded_text:
                        return decoded_text
            return None
        except Exception as e:
            logger.error(f"Error checking base64 content: {e}")
            return None

    @staticmethod
    def split_configs(text: str) -> List[str]:
        """
        Разбивает входной текст на отдельные конфигурационные строки,
        учитывая только разрешённые протоколы.
        """
        configs = []
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Если строка выглядит как Base64-код, пытаемся декодировать
            if ConfigValidator.is_base64(line):
                decoded_content = ConfigValidator.check_base64_content(line)
                if decoded_content:
                    text = decoded_content

            protocols = ALLOWED_PROTOCOLS
            current_pos = 0
            text_length = len(text)
            while current_pos < text_length:
                next_config_start = text_length
                matching_protocol = None
                for protocol in protocols:
                    protocol_pos = text.find(protocol, current_pos)
                    if protocol_pos != -1 and protocol_pos < next_config_start:
                        next_config_start = protocol_pos
                        matching_protocol = protocol
                if matching_protocol:
                    if current_pos < next_config_start and configs:
                        current_config = text[current_pos:next_config_start].strip()
                        if ConfigValidator.is_valid_config(current_config):
                            configs.append(current_config)
                    current_pos = next_config_start
                    next_protocol_pos = text_length
                    for protocol in protocols:
                        pos = text.find(protocol, next_config_start + len(matching_protocol))
                        if pos != -1 and pos < next_protocol_pos:
                            next_protocol_pos = pos
                    current_config = text[next_config_start:next_protocol_pos].strip()
                    if matching_protocol == "hy2://":
                        current_config = ConfigValidator.normalize_hysteria2_protocol(current_config)
                    if ConfigValidator.is_valid_config(current_config):
                        configs.append(current_config)
                    current_pos = next_protocol_pos
                else:
                    break
        return configs

    @staticmethod
    def clean_config(config: str) -> str:
        config = re.sub(r'[\U0001F300-\U0001F9FF]', '', config)
        config = re.sub(r'[\x00-\x08\x0B-\x1F\x7F-\x9F]', '', config)
        config = re.sub(r'[^\S\r\n]+', ' ', config)
        return config.strip()

    @staticmethod
    def is_valid_config(config: str) -> bool:
        """
        Допускает конфигурацию только если она начинается с одного из разрешённых протоколов.
        """
        if not config:
            return False
        return any(config.startswith(p) for p in ALLOWED_PROTOCOLS)

    @classmethod
    def validate_protocol_config(cls, config: str, protocol: str) -> bool:
        """
        Выполняет базовую проверку конфигурации для разрешённых протоколов.
        """
        try:
            if protocol not in ALLOWED_PROTOCOLS:
                return False
            if protocol in ["vless://", "trojan://"]:
                parsed = urlparse(config)
                return bool(parsed.netloc)
            elif protocol == "tuic://":
                parsed = urlparse(config)
                return bool(parsed.netloc and ':' in parsed.netloc)
            elif protocol == "hy2://":
                config = cls.normalize_hysteria2_protocol(config)
                parsed = urlparse(config)
                return bool(parsed.netloc)
            return False
        except Exception as e:
            logger.error(f"Error validating protocol config: {e}")
            return False
