import re
import base64
import json
from typing import Optional, Tuple, List
from urllib.parse import unquote, urlparse

class ConfigValidator:
    @staticmethod
    def sanitize_ascii(text: str) -> str:
        """Полная очистка текста от нестандартных символов и пробелов"""
        # Удаление эмодзи и специфических Unicode символов
        text = re.sub(r'[\U0001F300-\U0001F9FF]', '', text)
        # Удаление управляющих символов
        text = re.sub(r'[\x00-\x08\x0B-\x1F\x7F-\x9F]', '', text)
        # Удаление не-ASCII символов и лишних пробелов
        text = text.encode('ascii', 'ignore').decode('ascii')
        text = re.sub(r'\s+', '', text)
        return text.strip()

    @staticmethod
    def decode_base64_text(text: str) -> str:
        try:
            clean_text = ConfigValidator.sanitize_ascii(text)
            missing_padding = (4 - (len(clean_text) % 4)) % 4
            clean_text += '=' * missing_padding
            return base64.b64decode(clean_text).decode('utf-8')
        except Exception as e:
            return ""

    @staticmethod
    def is_base64(s: str) -> bool:
        try:
            s = ConfigValidator.sanitize_ascii(s)
            s = s.replace('-', '+').replace('_', '/')
            return len(s) % 4 == 0 and re.fullmatch(r'^[A-Za-z0-9+/]*={0,2}$', s) is not None
        except:
            return False

    @staticmethod
    def decode_base64_url(s: str) -> Optional[bytes]:
        try:
            s = unquote(s)
            s = ConfigValidator.sanitize_ascii(s)
            s = s.replace('-', '+').replace('_', '/')
            pad_len = (4 - (len(s) % 4)) % 4
            s += '=' * pad_len
            return base64.urlsafe_b64decode(s)
        except Exception as e:
            return None

    @staticmethod
    def clean_vmess_config(config: str) -> str:
        if config.startswith("vmess://"):
            base64_part = config[8:]
            base64_clean = re.split(r'[^A-Za-z0-9+/=_-]', base64_part, 1)[0]
            return f"vmess://{base64_clean.rstrip('=')}"
        return config

    @staticmethod
    def normalize_hysteria2_protocol(config: str) -> str:
        return config.replace('hy2://', 'hysteria2://', 1) if config.startswith('hy2://') else config

    @staticmethod
    def is_vmess_config(config: str) -> bool:
        try:
            if not config.startswith('vmess://'):
                return False
            cleaned = ConfigValidator.clean_vmess_config(config)
            base64_part = cleaned[8:]
            decoded_bytes = ConfigValidator.decode_base64_url(base64_part)
            if not decoded_bytes:
                return False
            json.loads(decoded_bytes.decode('utf-8', 'ignore'))
            return True
        except:
            return False

    @staticmethod
    def is_tuic_config(config: str) -> bool:
        try:
            if config.startswith('tuic://'):
                parsed = urlparse(config)
                return bool(parsed.netloc and ':' in parsed.netloc)
            return False
        except:
            return False

    @staticmethod
    def convert_ssconf_to_https(url: str) -> str:
        return url.replace('ssconf://', 'https://', 1) if url.startswith('ssconf://') else url

    @staticmethod
    def is_base64_config(config: str) -> Tuple[bool, str]:
        protocols = ['vmess://', 'vless://', 'ss://', 'tuic://']
        for protocol in protocols:
            if config.startswith(protocol):
                base_part = config[len(protocol):]
                if ConfigValidator.is_base64(base_part):
                    return True, protocol[:-3]
        return False, ''

    @staticmethod
    def split_configs(text: str) -> List[str]:
        protocols = [
            'vmess://', 'vless://', 'ss://', 'trojan://',
            'hysteria2://', 'hy2://', 'wireguard://', 
            'tuic://', 'ssconf://'
        ]
        clean_text = ConfigValidator.sanitize_ascii(text)
        configs = []
        current_pos = 0
        
        while current_pos < len(clean_text):
            next_proto_pos = len(clean_text)
            found_proto = None
            
            for proto in protocols:
                pos = clean_text.find(proto, current_pos)
                if 0 <= pos < next_proto_pos:
                    next_proto_pos = pos
                    found_proto = proto
            
            if found_proto:
                if current_pos < next_proto_pos:
                    candidate = clean_text[current_pos:next_proto_pos]
                    if any(candidate.startswith(p) for p in protocols):
                        configs.append(candidate.strip())
                
                end_pos = len(clean_text)
                for proto in protocols:
                    pos = clean_text.find(proto, next_proto_pos + len(found_proto))
                    if 0 <= pos < end_pos:
                        end_pos = pos
                
                config = clean_text[next_proto_pos:end_pos].strip()
                if found_proto == "vmess://":
                    config = ConfigValidator.clean_vmess_config(config)
                elif found_proto == "hy2://":
                    config = ConfigValidator.normalize_hysteria2_protocol(config)
                
                configs.append(config)
                current_pos = end_pos
            else:
                break
                
        return [cfg for cfg in configs if ConfigValidator.is_valid_config(cfg)]

    @staticmethod
    def is_valid_config(config: str) -> bool:
        protocols = [
            'vmess://', 'vless://', 'ss://', 'trojan://',
            'hysteria2://', 'hy2://', 'wireguard://',
            'tuic://', 'ssconf://'
        ]
        return any(config.startswith(p) for p in protocols)

    @classmethod
    def validate_protocol_config(cls, config: str, protocol: str) -> bool:
        try:
            clean_config = cls.sanitize_ascii(config)
            if protocol == 'vmess://':
                return cls.is_vmess_config(clean_config)
            if protocol == 'tuic://':
                return cls.is_tuic_config(clean_config)
            if protocol in ['vless://', 'ss://']:
                base_part = clean_config[len(protocol):]
                return cls.is_base64(base_part)
            if protocol in ['trojan://', 'hysteria2://', 'hy2://', 'wireguard://']:
                parsed = urlparse(clean_config)
                return bool(parsed.netloc and '@' in parsed.netloc)
            return protocol == 'ssconf://'
        except:
            return False
