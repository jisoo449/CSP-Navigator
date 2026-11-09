"""설정 로드. 조정값은 settings.json, 키·주소·모델명은 .env에서 읽는다. (NF2003, NF2005)

이 모듈의 settings.json 읽기는 표준 라이브러리만 쓴다. 데이터 변환 스크립트를
LangChain 설치 전에도 돌릴 수 있게 하려는 것이다. .env 읽기(python-dotenv)는 load_env()
안에서만 가져온다.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

# csp_navigator/ 폴더
ROOT = Path(__file__).resolve().parent.parent


@lru_cache(maxsize=1)
def load_settings() -> dict:
    """settings.json 전체. CSPNAV_SETTINGS 환경변수로 다른 파일을 지정할 수 있다(테스트용). (NF2005)"""
    path = Path(os.environ.get("CSPNAV_SETTINGS") or ROOT / "settings.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get(path: str, default: Any = None) -> Any:
    """'retrieval.top_k' 같은 점 경로로 설정값을 읽는다."""
    node: Any = load_settings()
    for key in path.split("."):
        if not isinstance(node, dict) or key not in node:
            return default
        node = node[key]
    return node


def resolve_path(key: str) -> Path:
    """paths.<key> 값을 절대 경로로 바꾼다. CSPNAV_<KEY> 환경변수가 있으면 그것을 쓴다(테스트용)."""
    override = os.environ.get(f"CSPNAV_{key.upper()}")
    raw = override or get(f"paths.{key}")
    if raw is None:
        raise KeyError(f"settings.json에 paths.{key}가 없습니다.")
    path = Path(raw)
    return path if path.is_absolute() else (ROOT / path).resolve()


def fake_mode() -> bool:
    """CSPNAV_FAKE=1 이면 가짜 LLM·임베딩으로 동작한다. 오프라인 점검(scripts/smoke_test.py) 전용."""
    return os.environ.get("CSPNAV_FAKE") == "1"


def offline_mode() -> bool:
    """CSPNAV_OFFLINE=1 이면 외부 문서를 네트워크로 수집하지 않는다(점검용)."""
    return os.environ.get("CSPNAV_OFFLINE") == "1"


REQUIRED_ENV = ("GMS_KEY", "GMS_BASE_URL", "LLM_MODEL", "EMBEDDING_MODEL")


@dataclass(frozen=True)
class EnvConfig:
    """.env 값. 키 값은 화면·로그에 내보내지 않는다. (NF2003, NF2004)"""

    api_key: str = field(repr=False, default="")
    base_url: str = ""
    llm_model: str = ""
    embedding_model: str = ""
    contact: str = ""

    def missing(self) -> list[str]:
        """비어 있는 필수 항목 이름(값이 아니라 이름만). (F2012)"""
        if fake_mode():
            return []
        values = {
            "GMS_KEY": self.api_key,
            "GMS_BASE_URL": self.base_url,
            "LLM_MODEL": self.llm_model,
            "EMBEDDING_MODEL": self.embedding_model,
        }
        return [name for name in REQUIRED_ENV if not values[name]]

    @property
    def ready(self) -> bool:
        return not self.missing()


def load_env() -> EnvConfig:
    """상위 폴더(실습용) .env를 먼저 읽고, csp_navigator/.env가 있으면 덮어쓴다. (NF2003)"""
    from dotenv import load_dotenv  # 지연 import: 변환 스크립트는 dotenv 없이도 돈다

    load_dotenv(ROOT.parent / ".env")
    load_dotenv(ROOT / ".env", override=True)
    env = os.environ
    return EnvConfig(
        api_key=env.get("GMS_KEY", "").strip(),
        base_url=env.get("GMS_BASE_URL", "").strip(),
        llm_model=env.get("LLM_MODEL", "").strip(),
        embedding_model=env.get("EMBEDDING_MODEL", "").strip(),
        contact=(env.get("CONTACT") or env.get("WIKI_CONTACT") or "").strip(),
    )
