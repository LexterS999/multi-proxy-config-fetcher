import re
import base64
import json
from typing import Optional, Tuple, List
from urllib.parse import unquote, urlparse

class ConfigValidator:
    @staticmethod
    def sanitize_ascii(text: str) -> str:
        """Удаляет все не-ASCII символы из строки"""
        return text.encode('ascii', 'ignore').decode('ascii').strip()

    @staticmethod
    def decode_base64_text(text: str) -> str:
        try:
            clean_text = ConfigValidator.sanitize_ascii(text)
            missing_padding = len(clean_text) % 4
            if missing_padding:
                clean_text += '=' * (4 - missing_padding)
            return base64.b64decode(clean_text).decode('utf-8')
        except Exception as e:
            print(f"Base64 decode error: {str(e)}")
            return ""

    @staticmethod
    def is_base64(s: str) -> bool:
        try:
            s = ConfigValidator.sanitize_ascii(s)
            return (len(s) % 4 == 0 and 
                    re.fullmatch(r'^[A-Za-z0-9+/]*={0,2}$', s) is not None)
        except:
            return False

    @staticmethod
    def decode_base64_url(s: str) -> Optional[bytes]:
        try:
            s = unquote(s)
            s = ConfigValidator.sanitize_ascii(s)
            s = s.replace('-', '+').replace('_', '/')
            pad = len(s) % 4
            if pad:
                s += '=' * (4 - pad)
            return base64.urlsafe_b64decode(s)
        except Exception as e:
            print(f"URL-safe decode error: {str(e)}")
            return None

    @staticmethod
    def clean_vmess_config(config: str) -> str:
        if config.startswith("vmess://"):
            base64_part = config[8:]
            clean_part = re.split(r'[^A-Za-z0-9+/=_-]', base64_part, 1)[0]
            return f"vmess://{clean_part}"
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
            decoded = ConfigValidator.decode_base64_url(base64_part)
            return bool(decoded and json.loads(decoded))
        except Exception as e:
            print(f"VMESS validation error: {str(e)}")
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
                decoded_url = unquote(base_part)
                if ConfigValidator.is_base64(decoded_url) or ConfigValidator.is_base64(base_part):
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
            next_pos = len(clean_text)
            found_protocol = None
            
            for proto in protocols:
                pos = clean_text.find(proto, current_pos)
                if pos != -1 and pos < next_pos:
                    next_pos = pos
                    found_protocol = proto
            
            if found_protocol:
                if current_pos < next_pos:
                    candidate = clean_text[current_pos:next_pos].strip()
                    if candidate:
                        configs.append(candidate)
                
                current_pos = next_pos
                end_pos = len(clean_text)
                
                for proto in protocols:
                    pos = clean_text.find(proto, current_pos + len(found_protocol))
                    if pos != -1 and pos < end_pos:
                        end_pos = pos
                
                config = clean_text[current_pos:end_pos].strip()
                if found_protocol == "vmess://":
                    config = ConfigValidator.clean_vmess_config(config)
                elif found_protocol == "hy2://":
                    config = ConfigValidator.normalize_hysteria2_protocol(config)
                
                if config:
                    configs.append(config)
                current_pos = end_pos
            else:
                break
                
        return [cfg for cfg in configs if ConfigValidator.is_valid_config(cfg)]

    @staticmethod
    def clean_config(config: str) -> str:
        config = re.sub(r'[^\x00-\x7F]+', '', config)
        config = re.sub(r'[\U0001F300-\U0001F9FF]', '', config)
        config = re.sub(r'[\x00-\x08\x0B-\x1F\x7F-\x9F]', '', config)
        return config.strip()

    @staticmethod
    def is_valid_config(config: str) -> bool:
        if not config:
            return False
        protocols = [
            'vmess://', 'vless://', 'ss://', 'trojan://',
            'hysteria2://', 'hy2://', 'wireguard://',
            'tuic://', 'ssconf://'
        ]
        return any(config.startswith(p) for p in protocols)

    @classmethod
    def validate_protocol_config(cls, config: str, protocol: str) -> bool:
        try:
            clean_config = cls.clean_config(config)
            if protocol in ['vmess://', 'vless://', 'ss://', 'tuic://']:
                if protocol == 'vmess://':
                    return cls.is_vmess_config(clean_config)
                if protocol == 'tuic://':
                    return cls.is_tuic_config(clean_config)
                base_part = clean_config[len(protocol):]
                decoded_url = unquote(base_part)
                return (cls.is_base64(decoded_url) or 
                        cls.is_base64(base_part) or 
                        bool(cls.decode_base64_url(base_part)))
            elif protocol in ['trojan://', 'hysteria2://', 'hy2://', 'wireguard://']:
                parsed = urlparse(clean_config)
                return bool(parsed.netloc and '@' in parsed.netloc)
            elif protocol == 'ssconf://':
                return True
            return False
        except Exception as e:
            print(f"Validation error: {str(e)}")
            return False
