"""1일차 수집 결과(md) → 적재용 JSON 변환. (F2001, F2016, F2017, NF2007)

입력: ../data/sources/수집결과_상품메타_공공PDF.md (원본은 수정하지 않는다)
출력: data/processed/
  - products.json      상품 메타데이터 108건 (요금 원문 + 구조화한 요금)
  - csap.json          CSP별 CSAP IaaS 인증 현황 (부문 필터용)
  - public_docs.json   공공 요건 PDF·원문 자료 목록(P1~P8)
  - common_docs.json   특정 상품에 묶이지 않는 공통 문서(수집 결과 요약) — 항목ID 'COMMON'으로 색인
  - web_catalog.json   웹 문서 후보 목록(공식 요금 페이지, 법령 원문 등) — F2004 후보 수집에 쓴다

표준 라이브러리만 쓴다.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from cspnav.data_prep import domain

_LINK = re.compile(r"\[([^\]]*)\]\((https?://[^)\s]+)\)")


def _cells(line: str) -> list[str]:
    """마크다운 표 1행을 칸 목록으로 나눈다."""
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _first_url(cell: str) -> str:
    m = _LINK.search(cell)
    if m:
        return m.group(2)
    m = re.search(r"https?://\S+", cell)
    return m.group(0).rstrip(")") if m else ""


def _plain(text: str) -> str:
    """마크다운 강조·링크를 평문으로 바꾼다."""
    text = _LINK.sub(lambda m: f"{m.group(1)}({m.group(2)})", text)
    text = text.replace("**", "").replace("`", "")
    return re.sub(r"\s+", " ", text).strip()


def _doc_id(prefix: str, key: str) -> str:
    return f"{prefix}-{hashlib.sha1(key.encode('utf-8')).hexdigest()[:10]}"


def _section(lines: list[str], start_pat: str, stop_pat: str = r"^#{1,3} ") -> list[str]:
    """start_pat 제목 다음 줄부터 다음 제목 전까지."""
    out, inside = [], False
    for line in lines:
        if re.match(start_pat, line):
            inside = True
            continue
        if inside and re.match(stop_pat, line):
            break
        if inside:
            out.append(line)
    return out


def parse_products(lines: list[str], checked_at: str) -> list[dict]:
    """① 섹션의 CSP별 표에서 상품 행을 읽는다. (F2001)"""
    products: list[dict] = []
    in_section = False
    current_csp = None
    for line in lines:
        if line.startswith("## ①"):
            in_section = True
            continue
        if in_section and line.startswith("## ") and not line.startswith("## ①"):
            break
        if not in_section:
            continue
        if line.startswith("### "):
            current_csp = domain.csp_name(line[4:].strip())
            continue
        if not line.startswith("| "):
            continue
        cells = _cells(line)
        if len(cells) < 12 or not re.match(r"^[A-Z]+-[A-Z]+-\d{2}$", cells[0]):
            continue
        item_id, cat_ko, name, spec, price_text, monthly_ref, region, public_raw, closed_raw, free_raw, note, src = cells[:12]
        category = domain.CATEGORY_FROM_KO.get(cat_ko, item_id.split("-")[1])
        csp = current_csp or domain.csp_name(item_id)
        vcpu, mem = domain.parse_vcpu_mem(spec, name)
        role = domain.classify_role(category, name, spec, closed_raw, note)
        price = domain.parse_price(price_text)
        official_monthly = domain.official_monthly_from_note(note) if category == "CMP" else None
        products.append({
            "item_id": item_id,
            "csp": csp,
            "category": category,
            "role": role,
            "name": name,
            "spec": spec,
            "vcpu": vcpu,
            "memory_gb": mem,
            "price_text": price_text,
            "price": price,
            "official_monthly": official_monthly,
            "monthly_ref": monthly_ref,
            "region": region,
            "public_raw": public_raw,
            "closed_raw": closed_raw,
            "free_raw": free_raw,
            "note": note,
            "source_url": _first_url(src),
            "checked_at": checked_at,
        })
    return products


def parse_csap(lines: list[str]) -> tuple[list[dict], str, list[str]]:
    """②-1 CSAP 인증 현황 표 → 행 목록, 출처 URL, 표 아래 주의 문장. (F2017)"""
    body = _section(lines, r"^### ②-1")
    source_url = ""
    rows, bullets = [], []
    for line in body:
        if line.startswith("출처:"):
            source_url = _first_url(line)
        if line.startswith("- "):
            bullets.append(_plain(line[2:]))
        if not line.startswith("| ") or line.startswith("| CSP ") or line.startswith("|---"):
            continue
        cells = _cells(line)
        if len(cells) < 5:
            continue
        csp = domain.csp_name(cells[0])
        if not csp:
            continue
        period = re.findall(r"\d{4}-\d{2}-\d{2}", _plain(cells[3]))
        rows.append({
            "csp": csp,
            "cert_no": _plain(cells[1]),
            "scope": _plain(cells[2]),
            "valid_from": period[0] if period else "",
            "valid_to": period[1] if len(period) > 1 else "",
            "status": _plain(cells[4]),
            "low_grade_only": "하등급" in cells[2],
        })
    return rows, source_url, bullets


def parse_public_docs(lines: list[str]) -> list[dict]:
    """②-2 공공 요건 PDF·원문 자료 목록. (F2016, NF2007)"""
    docs = []
    for line in _section(lines, r"^### ②-2"):
        if not re.match(r"^\| P\d+ ", line):
            continue
        c = _cells(line)
        if len(c) < 8:
            continue
        docs.append({
            "id": c[0], "title": _plain(c[1]), "publisher": _plain(c[2]), "date": _plain(c[3]),
            "form": _plain(c[4]), "url": _first_url(c[5]), "url_text": _plain(c[5]),
            "license": _plain(c[6]), "purpose": _plain(c[7]),
        })
    return docs


def parse_csp_common(lines: list[str]) -> list[dict]:
    """'CSP별 공통 정보' 표 (기준 리전·통화·계정 단위 무료 혜택)."""
    rows = []
    for line in _section(lines, r"^### CSP별 공통 정보"):
        if not line.startswith("| ") or line.startswith("| CSP ") or line.startswith("|---"):
            continue
        c = _cells(line)
        csp = domain.csp_name(c[0]) if c else None
        if csp and len(c) >= 4:
            rows.append({"csp": csp, "region": _plain(c[1]), "currency": _plain(c[2]), "free": _plain(c[3])})
    return rows


def build_common_docs(lines: list[str], csap_rows: list[dict], csap_url: str, csap_bullets: list[str],
                      csp_common: list[dict], checked_at: str, md_name: str) -> list[dict]:
    """상품에 묶이지 않는 공통 문서(수집 결과 요약)를 만든다. 항목ID는 'COMMON'. (F2016, F2017)"""
    docs = []

    # 1) CSAP 인증 현황 요약
    parts = [f"KISA ISMS-P 누리집 CSAP 인증서 발급현황(인증범위 IaaS)을 {checked_at}에 조회한 결과 요약이다."]
    for r in csap_rows:
        parts.append(
            f"{r['csp']}: 인증번호 {r['cert_no']}, 인증범위 '{r['scope']}', "
            f"유효기간 {r['valid_from']} ~ {r['valid_to']}, 목록상 상태 '{r['status']}'."
        )
    parts.extend(csap_bullets)
    docs.append({
        "doc_id": _doc_id("sum", "csap"),
        "title": f"CSAP(클라우드 보안인증) IaaS 인증 현황 — KISA 발급현황 조회 요약({checked_at})",
        "source": csap_url, "source_type": "summary", "csp": "", "sectors": ["public"],
        "license": "공개 조회 페이지의 사실 정보 요약(원문 복제 아님)", "collected_at": checked_at,
        "body": "\n".join(parts),
    })

    # 2) 제도 변경(국정원 단일 검증) 요약
    change = [_plain(l[2:]) for l in lines if l.startswith("- **제도 변경")]
    ref = next((l for l in lines if l.startswith("**참고(PDF 아님")), "")
    if change or ref:
        docs.append({
            "doc_id": _doc_id("sum", "policy-change"),
            "title": "공공 클라우드 보안 검증 제도 변경(2026-04-20 발표) 요약",
            "source": _first_url(ref) or md_name, "source_type": "summary", "csp": "", "sectors": ["public"],
            "license": "언론 보도 내용의 요약(원문 복제 아님). 공식 보도자료 원문은 확인 필요", "collected_at": checked_at,
            "body": "\n".join([*change, _plain(ref)]),
        })

    # 3) 계정 단위 무료 티어·크레딧
    if csp_common:
        body = ["CSP별 기준 리전·통화·계정 단위 무료 티어·크레딧(1일차 수집 결과)."]
        for r in csp_common:
            body.append(f"{r['csp']}: 기준 리전 {r['region']}, 통화 {r['currency']}, 무료 티어·크레딧 {r['free']}.")
        docs.append({
            "doc_id": _doc_id("sum", "free-tier"),
            "title": "CSP별 계정 단위 무료 티어·크레딧 요약",
            "source": f"{md_name} · CSP별 공통 정보", "source_type": "summary", "csp": "",
            "sectors": ["learning", "public", "private"],
            "license": "팀 수집 결과(각 CSP 공식 페이지 확인값)", "collected_at": checked_at,
            "body": "\n".join(body),
        })

    # 4) 로그인이 필요하거나 공개 단가가 없는 정보
    login = _section(lines, r"^## ③")
    rows = [_cells(l) for l in login if l.startswith("| ") and not l.startswith("| CSP") and not l.startswith("|---")]
    bullets = [_plain(l[2:]) for l in login if l.startswith("- ")]
    if rows or bullets:
        body = ["회원가입·로그인이 필요해 수집하지 않은 정보와 공개 단가가 없는 항목(영업 문의·협정가)."]
        for c in rows:
            if len(c) >= 4:
                body.append(f"{_plain(c[0])} — {_plain(c[1])}: {_plain(c[2])}. 대안: {_plain(c[3])}.")
        body.extend(bullets)
        docs.append({
            "doc_id": _doc_id("sum", "login-required"),
            "title": "로그인 필요·공개 단가 없음 항목 정리",
            "source": f"{md_name} · ③", "source_type": "summary", "csp": "",
            "sectors": ["public", "private", "learning"],
            "license": "팀 수집 결과", "collected_at": checked_at,
            "body": "\n".join(body),
        })
    return docs


def build_web_catalog(products: list[dict], public_docs: list[dict]) -> list[dict]:
    """웹 문서 후보 목록: 공식 요금 페이지(상품 출처 URL)와 공공 요건 원문 페이지. (F2004)"""
    by_url: dict[str, list[dict]] = defaultdict(list)
    for p in products:
        if p["source_url"]:
            by_url[p["source_url"]].append(p)
    catalog = []
    for url, items in by_url.items():
        csp = items[0]["csp"]
        names = ", ".join(i["name"] for i in items[:5])
        cats = ", ".join(sorted({domain.CATEGORIES[i["category"]] for i in items}))
        catalog.append({
            "id": _doc_id("web", url), "url": url, "csp": csp, "source_type": "web",
            "title": f"{csp} 공식 상품·요금 페이지 ({cats})",
            "summary": f"{csp}의 {cats} 상품 요금·과금 안내. 관련 상품: {names}",
            "sectors": ["public", "private", "learning"], "item_ids": [i["item_id"] for i in items],
            "license": "CSP 이용약관·robots.txt 확인 필요(미결 #3)",
        })
    for d in public_docs:
        if not d["url"] or d["url"].lower().endswith(".pdf"):
            continue
        catalog.append({
            "id": _doc_id("web", d["url"] + d["id"]), "url": d["url"], "csp": "", "source_type": "web",
            "title": d["title"], "summary": f"{d['publisher']} · {d['date']} · 용도: {d['purpose']}",
            "sectors": ["public"], "item_ids": [], "license": d["license"],
        })
    return catalog


def convert(md_path: Path, out_dir: Path) -> dict:
    """md 1개를 읽어 processed JSON 파일들을 쓴다. 건수 요약을 돌려준다. (F2001)"""
    text = md_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    m = re.search(r"수집일\(checked_at\):\s*(\d{4}-\d{2}-\d{2})", text)
    checked_at = m.group(1) if m else ""
    if not checked_at:
        raise ValueError("md 머리말에서 수집일(checked_at)을 찾지 못했습니다.")

    products = parse_products(lines, checked_at)
    csap_rows, csap_url, csap_bullets = parse_csap(lines)
    public_docs = parse_public_docs(lines)
    csp_common = parse_csp_common(lines)
    common_docs = build_common_docs(lines, csap_rows, csap_url, csap_bullets, csp_common, checked_at, md_path.name)
    catalog = build_web_catalog(products, public_docs)

    out_dir.mkdir(parents=True, exist_ok=True)
    meta = {"source_md": md_path.name, "checked_at": checked_at, "csap_source_url": csap_url}
    files = {
        "products.json": {"meta": meta, "items": products},
        "csap.json": {"meta": meta, "items": csap_rows},
        "public_docs.json": {"meta": meta, "items": public_docs},
        "common_docs.json": {"meta": meta, "items": common_docs},
        "web_catalog.json": {"meta": meta, "items": catalog},
        "csp_common.json": {"meta": meta, "items": csp_common},
    }
    for name, payload in files.items():
        (out_dir / name).write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

    by_csp = Counter(p["csp"] for p in products)
    by_cat = Counter(p["category"] for p in products)
    unparsed = [p["item_id"] for p in products if p["price"]["status"] != "ok"]
    return {
        "products": len(products), "by_csp": dict(by_csp), "by_category": dict(by_cat),
        "price_unparsed": unparsed, "csap": len(csap_rows), "public_docs": len(public_docs),
        "common_docs": len(common_docs), "web_catalog": len(catalog), "checked_at": checked_at,
    }
