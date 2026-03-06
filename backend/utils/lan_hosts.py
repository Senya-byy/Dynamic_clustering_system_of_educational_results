# backend/utils/lan_hosts.py
"""Определение IPv4 в локальной сети (ноутбук в Wi‑Fi) для CORS и ссылок в QR."""
import os
import socket
import subprocess
import sys
from typing import List, Optional
from urllib.parse import urlparse


def _docker_bridge_ipv4(ip: str) -> bool:
    """172.16.0.0–172.31.255.255 — типичная сеть Docker; с телефона туда не достучаться."""
    parts = ip.split('.')
    if len(parts) != 4:
        return False
    try:
        a, b = int(parts[0]), int(parts[1])
    except ValueError:
        return False
    return a == 172 and 16 <= b <= 31


def collect_lan_ipv4() -> List[str]:
    ips: set = set()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.2)
        s.connect(('10.254.254.254', 1))
        ip = s.getsockname()[0]
        s.close()
        if ip and not ip.startswith('127.'):
            ips.add(ip)
    except OSError:
        pass
    if sys.platform == 'darwin':
        for name in ('en0', 'en1'):
            try:
                out = subprocess.run(
                    ['ipconfig', 'getifaddr', name],
                    capture_output=True,
                    text=True,
                    timeout=1,
                    check=False,
                )
                line = (out.stdout or '').strip()
                if line and not line.startswith('127.'):
                    ips.add(line)
            except (OSError, subprocess.TimeoutExpired):
                pass
    return sorted(ips)


def collect_lan_ipv4_for_qr() -> List[str]:
    """IP для ссылок в QR: сначала «живые» LAN, без адресов моста Docker."""
    ips = collect_lan_ipv4()
    physical = [ip for ip in ips if not _docker_bridge_ipv4(ip)]
    return physical if physical else ips


def configured_qr_frontend_origin() -> Optional[str]:
    raw = (os.environ.get('QR_FRONTEND_ORIGIN') or '').strip().rstrip('/')
    return raw or None


def vite_lan_cors_origins(ports=(5173, 5174)) -> List[str]:
    return [f'http://{ip}:{p}' for ip in collect_lan_ipv4() for p in ports]


def suggested_frontend_origin(port: int = 5173) -> Optional[str]:
    """Первая подходящая ссылка http://<LAN>:port для QR и телефона."""
    cfg = configured_qr_frontend_origin()
    if cfg:
        return cfg
    ips = collect_lan_ipv4_for_qr()
    if not ips:
        return None
    return f'http://{ips[0]}:{port}'


def _origin_netloc_loopback(origin: str) -> bool:
    if not origin:
        return True
    u = origin if '://' in origin else f'http://{origin}'
    try:
        p = urlparse(u)
        h = (p.hostname or '').lower()
        return h in ('localhost', '127.0.0.1', '::1') or h == ''
    except ValueError:
        return True


def _port_from_origin(origin: str, default: int) -> int:
    if not origin:
        return default
    u = origin if '://' in origin else f'http://{origin}'
    try:
        p = urlparse(u)
        return p.port or default
    except ValueError:
        return default


def resolve_public_frontend_base(
    x_frontend_origin: Optional[str],
    referer: Optional[str],
    default_port: int = 5173,
) -> str:
    """
    Базовый URL фронта для ссылок в QR.
    Учитывает QR_FRONTEND_ORIGIN, заменяет localhost из заголовка и (если нужно) Referer.
    """
    env_o = configured_qr_frontend_origin()
    header = (x_frontend_origin or '').strip().rstrip('/')

    if header and not _origin_netloc_loopback(header):
        return header

    if env_o:
        return env_o

    if header and _origin_netloc_loopback(header):
        port = _port_from_origin(header, default_port)
        sug = suggested_frontend_origin(port)
        if sug:
            return sug.rstrip('/')

    ref = (referer or '').strip()
    if ref:
        try:
            p = urlparse(ref)
            if p.scheme and p.netloc:
                cand = f'{p.scheme}://{p.netloc}'.rstrip('/')
                if not _origin_netloc_loopback(cand):
                    return cand
        except ValueError:
            pass

    if header:
        return header

    sug = suggested_frontend_origin(default_port)
    if sug:
        return sug.rstrip('/')

    return ''
