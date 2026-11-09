"""(점검용) 규칙 기반 가짜 채팅 모델. CSPNAV_FAKE=1 일 때만 쓴다.

키 없이 수집→색인→검색→생성 전 흐름이 끊기지 않는지 확인하려는 것이다.
응답 내용은 프롬프트의 '# 작업:' 표시를 보고 고정 규칙으로 만든 (더미) 문장이며, 품질 평가에 쓰지 않는다.
"""

from __future__ import annotations

import json
import re
from typing import Any, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult


class RuleBasedFakeChat(BaseChatModel):
    """작업 종류별로 형식에 맞는 (더미) 응답을 돌려준다."""

    @property
    def _llm_type(self) -> str:
        return "cspnav-fake"

    def _generate(self, messages: list[BaseMessage], stop: Optional[list[str]] = None,
                  run_manager: Any = None, **kwargs: Any) -> ChatResult:
        system = str(messages[0].content) if messages else ""
        human = str(messages[-1].content) if messages else ""
        full = "\n".join(str(m.content) for m in messages)
        if "# 작업: 검색어 추출" in system:
            name = re.search(r"상품명:\s*(.+)", full)
            base = name.group(1).strip() if name else "클라우드 상품"
            text = json.dumps([f"{base} 요금", "클라우드 컴퓨팅"], ensure_ascii=False)
        elif "# 작업: 후보 문서 선별" in system:
            picked, seen = [], set()
            for cid, stype in re.findall(r"id:\s*(c\d+)\s*\|\s*출처:\s*(\w+)", full):
                if stype not in seen:      # 출처 종류마다 첫 후보 하나씩
                    picked.append(cid)
                    seen.add(stype)
            text = json.dumps(picked[:3])
        elif "# 작업: 조건 탐색" in system:
            ids = re.findall(r"item_id:\s*([A-Z]+-[A-Z]+-\d+)", full)
            money = re.search(r"(\d+(?:\.\d+)?)\s*만\s*원", human)
            text = json.dumps({
                "conditions": ["(더미) 키워드 해석"],
                "max_monthly_krw": float(money.group(1)) * 10000 if money else None,
                "matches": [{"item_id": i, "reason": "(더미) 후보 상위 항목"} for i in ids[:4]],
            }, ensure_ascii=False)
        elif "# 작업: 답변 생성" in system:
            nums = re.findall(r"\[근거 (\d+)\]", full)
            if not nums:
                text = "문서에서 확인되지 않음. (더미 응답) 근거가 없습니다."
            else:
                first = nums[0]
                rest = nums[1] if len(nums) > 1 else first
                text = (f"(더미 응답) 상품 메타데이터의 사양과 요금을 확인했습니다 [근거 {first}].\n"
                        f"- 관련 문서 내용을 함께 참고했습니다 [근거 {rest}].\n"
                        f"- 그 밖의 내용은 문서에서 확인되지 않음.")
        else:
            text = "(더미 응답)"
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=text))])
