"""외부 출처 예절을 지키는 HTTP 클라이언트. (NF2006)

- 연락처가 들어간 User-Agent를 보낸다 (.env의 CONTACT 또는 WIKI_CONTACT).
- 같은 호스트에는 설정한 간격(collection.request_interval_sec) 이상 두고 호출한다.
- 429·5xx·연결 오류는 지수 백오프로 재시도하고, Retry-After가 있으면 따른다.
- 웹 페이지는 robots.txt를 확인한 뒤에만 가져온다(API 호출은 각 API 정책을 따른다).
"""

from __future__ import annotations

import logging
import time
import urllib.robotparser
from typing import Optional
from urllib.parse import urlparse

import requests

from cspnav import settings

logger = logging.getLogger("cspnav.http")


class PoliteClient:
    """호출 간격·재시도·robots.txt를 지키는 requests 래퍼. (NF2006)"""

    def __init__(self, contact: str = ""):
        version = requests.__version__
        contact_part = f" ({contact})" if contact else ""
        # User-Agent는 latin-1만 허용되므로 한글 연락처는 넣지 않는다.
        try:
            contact_part.encode("latin-1")
        except UnicodeEncodeError:
            contact_part = ""
        self.user_agent = f"CSPNavigator/0.1{contact_part} python-requests/{version}"
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent, "Accept-Language": "ko,en;q=0.8"})
        self.interval = float(settings.get("collection.request_interval_sec", 1.0))
        self.max_retries = int(settings.get("collection.max_retries", 4))
        self.backoff = float(settings.get("collection.backoff_base_sec", 1.5))
        self.timeout = float(settings.get("collection.timeout_sec", 20))
        self._last_call: dict[str, float] = {}
        self._robots: dict[str, Optional[urllib.robotparser.RobotFileParser]] = {}

    def _wait_turn(self, host: str) -> None:
        last = self._last_call.get(host)
        if last is not None:
            gap = time.monotonic() - last
            if gap < self.interval:
                time.sleep(self.interval - gap)
        self._last_call[host] = time.monotonic()

    def get(self, url: str, params: Optional[dict] = None) -> requests.Response:
        """재시도·간격을 지키는 GET. 끝까지 실패하면 마지막 예외를 그대로 올린다. (NF2006)"""
        host = urlparse(url).netloc
        last_exc: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            self._wait_turn(host)
            try:
                resp = self.session.get(url, params=params, timeout=self.timeout)
            except requests.RequestException as exc:
                last_exc = exc
            else:
                if resp.status_code == 429 or resp.status_code >= 500:
                    last_exc = requests.HTTPError(f"HTTP {resp.status_code}", response=resp)
                    retry_after = resp.headers.get("Retry-After", "")
                    if retry_after.isdigit():
                        time.sleep(min(float(retry_after), 60))
                        continue
                else:
                    resp.raise_for_status()
                    return resp
            if attempt < self.max_retries:
                time.sleep(self.backoff * (2 ** attempt))
        assert last_exc is not None
        raise last_exc

    def allowed(self, url: str) -> bool:
        """robots.txt가 이 URL 수집을 허용하는가. robots.txt가 없으면(4xx) 허용, 읽기 실패(5xx·네트워크)는 불허. (NF2006)"""
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        if base not in self._robots:
            rp = urllib.robotparser.RobotFileParser()
            try:
                self._wait_turn(parsed.netloc)
                resp = self.session.get(base + "/robots.txt", timeout=self.timeout)
                if resp.status_code >= 500:
                    self._robots[base] = None
                elif resp.status_code >= 400:
                    rp.parse([])
                    self._robots[base] = rp
                else:
                    rp.parse(resp.text.splitlines())
                    self._robots[base] = rp
            except requests.RequestException:
                self._robots[base] = None
        rp = self._robots[base]
        if rp is None:
            logger.info("robots.txt를 읽지 못해 수집하지 않음: %s", base)
            return False
        return rp.can_fetch(self.user_agent, url)
