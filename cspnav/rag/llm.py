"""LLM·임베딩 연결. 키·주소·모델명은 .env에서만 읽는다. (NF2003)

SSAFY GMS는 OpenAI와 같은 형식의 API라 langchain-openai를 그대로 쓰고 base_url만 바꾼다.
CSPNAV_FAKE=1 이면 가짜 모델(fake_llm.py)을 쓴다 — 키 없이 전 흐름을 점검하는 용도.
"""

from __future__ import annotations

import json
import logging
import re
from functools import lru_cache
from typing import Any

from cspnav import settings
from cspnav.errors import ServiceError

logger = logging.getLogger("cspnav.llm")


@lru_cache(maxsize=1)
def get_chat():
    """채팅 모델 1개를 만들어 재사용한다. (F2003, F2004, F2007)"""
    if settings.fake_mode():
        from cspnav.rag.fake_llm import RuleBasedFakeChat
        return RuleBasedFakeChat()
    from langchain_openai import ChatOpenAI

    env = settings.load_env()
    if not env.ready:
        raise ServiceError("LLM 연결 설정(.env)이 비어 있어 답변을 만들 수 없습니다. 관리자에게 .env 설정을 요청하세요.")
    kwargs: dict[str, Any] = {
        "model": env.llm_model,
        "api_key": env.api_key,
        "base_url": env.base_url,
        "timeout": settings.get("llm.timeout_sec", 60),
        "max_retries": settings.get("llm.max_retries", 2),
    }
    temperature = settings.get("llm.temperature")
    if temperature is not None:   # 일부 추론형 모델은 temperature를 받지 않아 기본은 넘기지 않는다
        kwargs["temperature"] = temperature
    return ChatOpenAI(**kwargs)


@lru_cache(maxsize=1)
def get_embeddings():
    """임베딩 모델. (F2002, F2005)"""
    if settings.fake_mode():
        from langchain_core.embeddings import DeterministicFakeEmbedding
        return DeterministicFakeEmbedding(size=384)
    from langchain_openai import OpenAIEmbeddings

    env = settings.load_env()
    if not env.ready:
        raise ServiceError("임베딩 연결 설정(.env)이 비어 있어 검색할 수 없습니다. 관리자에게 .env 설정을 요청하세요.")
    # check_embedding_ctx_length=False: 토큰 길이 검사용 tiktoken 사전 내려받기를 하지 않는다.
    # 청크가 1,000자 안팎이라 길이 초과 위험이 없다.
    return OpenAIEmbeddings(model=env.embedding_model, api_key=env.api_key, base_url=env.base_url,
                            check_embedding_ctx_length=False)


def message_text(msg: Any) -> str:
    """AIMessage → 문자열. 본문이 블록 목록이어도 텍스트만 모은다."""
    text = getattr(msg, "text", None)   # langchain-core 1.x: 문자열 속성
    if isinstance(text, str) and text:
        return str(text)
    content = getattr(msg, "content", "")
    if isinstance(content, list):
        return "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in content)
    return str(content)


def invoke_text(messages: list) -> str:
    """메시지 목록으로 LLM을 1회 호출한다. 연결 오류는 사용자용 문구로 바꾼다. (NF2004)"""
    try:
        return message_text(get_chat().invoke(messages)).strip()
    except ServiceError:
        raise
    except Exception as exc:  # noqa: BLE001 — 키·주소가 섞인 원문 오류는 화면에 내보내지 않는다
        logger.exception("LLM 호출 실패")
        raise ServiceError("LLM 호출에 실패했습니다. 잠시 후 다시 시도하거나 .env의 키·주소·모델명을 확인하세요.") from exc


def parse_json(text: str, kind: str) -> Any:
    """응답에서 JSON 배열(kind='array') 또는 객체(kind='object')를 꺼낸다. 실패하면 None."""
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    open_ch, close_ch = ("[", "]") if kind == "array" else ("{", "}")
    start, end = text.find(open_ch), text.rfind(close_ch)
    if start < 0 or end <= start:
        return None
    try:
        value = json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None
    if kind == "array" and not isinstance(value, list):
        return None
    if kind == "object" and not isinstance(value, dict):
        return None
    return value


def invoke_json(messages: list, kind: str) -> Any:
    """JSON만 출력하라는 프롬프트를 호출하고 파싱한다. 형식이 틀리면 한 번 더 요청한다. (F2003, F2004)"""
    from langchain_core.messages import HumanMessage

    text = invoke_text(messages)
    value = parse_json(text, kind)
    if value is None:
        reminder = "JSON 배열만" if kind == "array" else "JSON 객체만"
        text = invoke_text([*messages, HumanMessage(content=f"형식이 틀렸습니다. 설명 없이 {reminder} 다시 출력하세요.")])
        value = parse_json(text, kind)
    return value
