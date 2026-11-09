"""답변 본문의 [근거 n] 표기 처리. (F2008)

LLM이 [근거 1, 3]뿐 아니라 [근거 1~3], [근거 1-3], [근거 1, 상품 메타데이터]처럼 쓰는 경우가 있어
(2026-10-23 실제 GMS 검증에서 확인), 숫자·범위를 모두 읽고 화면 표기는 [근거 1, 2, 3] 형태로 통일한다.
"""

from __future__ import annotations

import re

from cspnav.schemas import Evidence

# [근거 ...] 또는 (근거 ...) 괄호 전체를 찾고, 안쪽에서 숫자·범위를 읽는다.
# 소괄호 형태 "(근거 1, 상품 메타데이터)"도 실제 GMS 검증에서 나와 함께 받는다(2026-10-23).
CITE_PATTERN = re.compile(r"[\[(]근거\s*([^\[\]()]*?\d[^\[\]()]*?)[\])]")
_RANGE = re.compile(r"(\d+)\s*[~\-–]\s*(\d+)")
_NUM = re.compile(r"\d+")


def _numbers(inner: str) -> list[int]:
    """'1, 3', '1~3', '1-3, 5', '1, 상품 메타데이터' → [1, 3] / [1, 2, 3] / … (F2008)"""
    nums: list[int] = []
    rest = inner
    for a, b in _RANGE.findall(inner):
        lo, hi = int(a), int(b)
        if lo <= hi and hi - lo <= 20:
            nums.extend(range(lo, hi + 1))
    rest = _RANGE.sub(" ", inner)
    nums.extend(int(n) for n in _NUM.findall(rest))
    out: list[int] = []
    for n in nums:
        if n not in out:
            out.append(n)
    return out


def extract_cited(text: str, evidences: list[Evidence]) -> list[int]:
    """본문이 실제로 인용한 근거 번호만 처음 나온 순서대로 돌려준다. 없는 번호는 버린다. (F2008)"""
    valid = {e.number for e in evidences}
    cited: list[int] = []
    for match in CITE_PATTERN.finditer(text):
        for n in _numbers(match.group(1)):
            if n in valid and n not in cited:
                cited.append(n)
    return cited


def strip_invalid(text: str, evidences: list[Evidence]) -> str:
    """근거 표기를 [근거 1, 2] 형태로 통일하고, 존재하지 않는 번호는 지운다(LLM이 번호를 지어낸 경우). (F2008)"""
    valid = {e.number for e in evidences}

    def _fix(m: re.Match) -> str:
        nums = [str(n) for n in _numbers(m.group(1)) if n in valid]
        return f"[근거 {', '.join(nums)}]" if nums else ""

    return CITE_PATTERN.sub(_fix, text)


def drop_on_not_found(text: str, marker: str = "확인되지 않") -> str:
    """'문서에서 확인되지 않음' 문장(줄)에 붙은 근거 번호를 지운다. 근거가 없다는 문장에 근거를 다는 것은
    모순이라서다(2026-10-23 실제 검증에서 LLM이 이런 줄에 모든 근거 번호를 붙인 사례 확인). (F2007, F2008)"""
    lines = []
    for line in text.splitlines():
        if marker in line:
            line = CITE_PATTERN.sub("", line).rstrip()
        lines.append(line)
    return "\n".join(lines)
