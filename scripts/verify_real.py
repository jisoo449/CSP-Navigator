"""실제 GMS 연결 검증 스크립트 — 명세서 4장 확인 항목을 실행하고 결과를 문서로 남긴다. (4.1~4.7, F2001~F2019, NF2001~NF2002)

실행 (csp_navigator 폴더에서, prepare_data.py · build_index.py 다음에):
    python scripts/verify_real.py              # 4.2~4.5 검증 + 설정값 비교(Top-k, similarity/MMR)
    python scripts/verify_real.py chunk        # (내부용) 청크 크기 실험 1회분. 상위 스크립트가 환경변수로 호출
출력: docs/evidence/verify_real.md, docs/evidence/verify_real.json
성공 기준: 마지막 줄 "검증 완료" 출력. 각 항목의 판정(통과/실패/미확인)은 md 파일 표에 기록된다.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from cspnav import settings  # noqa: E402
from cspnav.data_prep import domain  # noqa: E402
from cspnav.data_prep.products import index_text  # noqa: E402
from cspnav.errors import ServiceError  # noqa: E402
from cspnav.rag import prompts  # noqa: E402
from cspnav.rag.graph import generate_answer, retrieve_evidences  # noqa: E402
from cspnav.schemas import Requirement  # noqa: E402
from cspnav.services import get_service  # noqa: E402

OUT = ROOT / "docs" / "evidence"
EXP = ROOT / "data" / "experiments"

# 설정값 비교에 쓰는 같은 질문 3개 (03_검증결과 5장)
EXP_QUESTIONS = [
    ("E1", "NCP-CMP-01", "이 상품을 월 730시간 쓰면 비용이 얼마인가요?", "learning"),
    ("E2", "KT-NET-02", "사내 폐쇄망에서 이 상품을 쓰려면 무엇이 더 필요한가요?", "private"),
    ("E3", "NHN-CMP-02", "공공기관이 이 상품을 써도 되나요?", "public"),
]


def ev_rows(evidences, cited=None):
    cited = set(cited or [])
    return [{"n": e.number, "type": e.source_type, "title": e.title, "source": e.source,
             "checked_at": e.checked_at.isoformat(), "chunk_id": e.chunk_id, "item_id": e.item_id,
             "cited": e.number in cited} for e in evidences]


def instrument(svc, log: dict):
    """검색어(프롬프트1)·후보·선별(프롬프트2)·수집 보고를 기록하도록 서비스에 감시를 붙인다. (4.2)"""
    import cspnav.services.navigator as nav
    orig_invoke = nav.invoke_json

    def invoke_json(messages, kind):
        out = orig_invoke(messages, kind)
        sys_text = str(getattr(messages[0], "content", ""))
        if "검색어" in sys_text and "keywords" not in log:
            log["keywords"] = out
        return out
    nav.invoke_json = invoke_json

    collector = svc._get_collector()
    orig_collect = collector.collect

    def collect(product, keywords, select_fn, on_progress=None):
        def select(cands):
            picked = select_fn(cands)
            log["candidates"] = [{"cid": c.cid, "type": c.source_type, "title": c.title, "ref": c.ref,
                                  "selected": c.cid in picked} for c in cands]
            return picked
        log["keywords_used"] = list(keywords)
        rep = orig_collect(product, keywords, select, on_progress)
        log["report"] = {"official": rep.official, "new_keywords": rep.new_keywords,
                         "cached_keywords": rep.cached_keywords, "candidates": rep.candidates,
                         "selected": rep.selected, "indexed_docs": rep.indexed_docs, "skipped": rep.skipped}
        return rep
    collector.collect = collect
    return lambda: (setattr(nav, "invoke_json", orig_invoke), setattr(collector, "collect", orig_collect))


def timed_ask(svc, item_id, question, sector):
    log: dict = {"progress": []}
    restore = instrument(svc, log)
    t0 = time.time()
    try:
        ans = svc.ask(item_id, question, sector, on_progress=log["progress"].append)
        log.update(ok=True, answer=ans.text, cited=ans.cited, notices=ans.notices,
                   evidences=ev_rows(ans.evidences, ans.cited))
    except ServiceError as err:
        log.update(ok=False, error=err.user_message)
    finally:
        restore()
    log["seconds"] = round(time.time() - t0, 1)
    log.update(item_id=item_id, question=question, sector=sector)
    return log


def run_chunk_mode() -> int:
    """청크 실험 1회분: (환경변수로 지정된) 별도 settings·chroma·cache에서 색인 후 E1 질문. (4.2 청크 변경)"""
    sys.path.insert(0, str(ROOT / "scripts"))
    from build_index import build
    meta, docs_common = build(reset=True, verbose=False)
    svc = get_service()
    log = timed_ask(svc, *EXP_QUESTIONS[0][1:])
    _, docs_after = svc.store.counts()
    print(json.dumps({"meta": meta, "docs_common": docs_common, "docs_after_e1": docs_after,
                      "chunk": settings.get("chunking.web"), "e1": log}, ensure_ascii=False))
    return 0


def chunk_experiment(size: int, overlap: int) -> dict:
    """청크 크기·중복 길이만 바꾼 settings로 하위 프로세스를 띄운다. 원래 색인은 건드리지 않는다."""
    tag = f"chunk_{size}_{overlap}"
    base = EXP / tag
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True)
    conf = json.loads((ROOT / "settings.json").read_text(encoding="utf-8"))
    for k in conf["chunking"]:
        if isinstance(conf["chunking"][k], dict):
            conf["chunking"][k] = {"chunk_size": size, "chunk_overlap": overlap}
    (base / "settings.json").write_text(json.dumps(conf, ensure_ascii=False, indent=2), encoding="utf-8")
    # 수집 캐시는 원래 것을 복사해 같은 문서 본문을 쓰게 한다(네트워크 차이 제거). 검색어 기록은 비워 다시 색인되게 한다.
    src_cache = settings.resolve_path("cache_dir")
    if (src_cache / "docs").exists():
        shutil.copytree(src_cache / "docs", base / "cache" / "docs")
    env = dict(os.environ, CSPNAV_SETTINGS=str(base / "settings.json"), CSPNAV_CHROMA_DIR=str(base / "chroma"),
               CSPNAV_CACHE_DIR=str(base / "cache"))
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "verify_real.py"), "chunk"], env=env, cwd=str(ROOT),
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    line = next((l for l in reversed(r.stdout.splitlines()) if l.startswith("{")), None)
    if not line:
        return {"tag": tag, "error": (r.stdout + r.stderr)[-1500:]}
    data = json.loads(line)
    data["tag"] = tag
    return data


def main() -> int:
    env = settings.load_env()
    if env.missing():
        print("[실패] .env에 비어 있는 항목이 있습니다: " + ", ".join(env.missing()))
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    R: dict = {"run_at": datetime.now().strftime("%Y-%m-%d %H:%M"), "llm": env.llm_model,
               "embedding": env.embedding_model, "settings": settings.get("retrieval"),
               "chunking": settings.get("chunking.web")}
    svc = get_service()

    # 4.1 데이터·색인
    st = svc.get_status()
    p = svc.get_product("NCP-CMP-01")
    R["4.1"] = {"products": st.product_count, "meta_count": st.meta_count, "doc_chunks": st.doc_chunk_count,
                "index_text_NCP-CMP-01": index_text(p)}
    print("4.1", R["4.1"]["products"], R["4.1"]["meta_count"])

    # 4.3 그래프 구조
    g = svc._get_graph().get_graph()
    R["graph"] = {"nodes": [n for n in g.nodes], "edges": [(e.source, e.target) for e in g.edges],
                  "mermaid": g.draw_mermaid()}

    # 4.2 수집 — 첫 질문, 같은 질문 재질문
    # 첫 질문은 공식 문서를 수집할 수 있는 AWS 상품으로 한다(NCP·KT는 robots.txt 불허, NHN·SCP는 스크립트 렌더링)
    q = ("Q0", "AWS-CMP-01", "이 상품을 월 730시간 쓰면 비용이 얼마인가요?", "learning")
    print("4.2 첫 질문")
    R["ask_first"] = timed_ask(svc, *q[1:])
    print("4.2 재질문")
    R["ask_again"] = timed_ask(svc, *q[1:])
    cache_file = settings.resolve_path("cache_dir") / "collect_cache.json"
    R["cache_keys"] = list(json.loads(cache_file.read_text(encoding="utf-8")).get("keywords", {}).keys()) if cache_file.exists() else []

    # 나머지 설정 실험용 질문도 한 번씩 물어 문서를 수집해 둔다
    R["ask_exp"] = {}
    for qid, item, question, sector in EXP_QUESTIONS[1:]:
        print("수집", qid)
        R["ask_exp"][qid] = timed_ask(svc, item, question, sector)

    # 4.3 문서에 없는 질문 / 무관한 질문
    print("4.3 없는 질문")
    R["not_in_docs"] = timed_ask(svc, "NCP-CMP-01", "이 상품의 SLA 장애 보상 비율은 몇 퍼센트인가요?", "learning")
    R["unrelated"] = timed_ask(svc, "NCP-CMP-01", "다음 주 서울 날씨는 어떤가요?", "learning")

    # 4.3 / 4.5 설정 비교: Top-k, similarity vs MMR — 검색만 다시 하고 같은 질문으로 답을 만든다
    conf = settings.load_settings()["retrieval"]
    R["exp_topk"], R["exp_search"] = {}, {}
    for qid, item, question, sector in EXP_QUESTIONS:
        for k in (3, 5, 8):
            conf["max_evidences"] = max(8, k + 3)
            evs = retrieve_evidences(svc.store, question, sector, item_id=item, top_k=k)
            text, cited = generate_answer(question, sector, evs)
            R["exp_topk"][f"{qid}_k{k}"] = {"evidences": ev_rows(evs, cited), "cited": cited, "answer": text}
            print("top_k", qid, k, len(evs))
        conf["max_evidences"] = 8
        for stype in ("similarity", "mmr"):
            conf["search_type"] = stype
            evs = retrieve_evidences(svc.store, question, sector, item_id=item)
            text, cited = generate_answer(question, sector, evs)
            R["exp_search"][f"{qid}_{stype}"] = {"evidences": ev_rows(evs, cited), "cited": cited, "answer": text}
            print("search", qid, stype, len(evs))
        conf["search_type"] = "similarity"

    # 4.4 조건 탐색 — 조건과 맞지 않는 상품이 섞이지 않는지
    print("4.4 탐색")
    R["explore"] = {}
    for sector, query in (("private", "서울 리전, 폐쇄망 지원, 월 3만 원 이하 MySQL"),
                          ("learning", "월 2만 원 이하 2vCPU 서버"),
                          ("public", "공공기관용 오브젝트 스토리지")):
        t0 = time.time()
        try:
            res = svc.explore(query, sector)
            R["explore"][sector] = {"query": query, "conditions": res.conditions, "seconds": round(time.time() - t0, 1),
                                    "hits": [{"item_id": h.product.item_id, "name": h.product.name, "csp": h.product.csp,
                                              "category": h.product.category, "monthly": h.monthly_estimate,
                                              "closed": str(h.product.closed_network_support),
                                              "public": str(h.product.public_support),
                                              "status": h.sector_status, "reason": h.reason} for h in res.hits]}
        except ServiceError as err:
            R["explore"][sector] = {"query": query, "error": err.user_message}

    # 4.4 특화 기능(F2010) — 부문 3개 추천, 근거 포함 여부
    print("4.4 추천")
    R["recommend"] = {}
    reqs = {
        "learning": Requirement("학습·실습", 1, 1, 1, True, 0, 730, 50_000, [], "학습용 웹 서버 + DB"),
        "public": Requirement("민원·대국민 서비스", 2, 2, 8, True, 100, 730, 2_000_000,
                              ["공공 요건", "웹 방화벽(WAF)"], "지자체 민원 시스템", "중"),
        "private": Requirement("사내 업무 시스템(ERP 등)", 1, 2, 8, True, 100, 730, 1_000_000,
                               ["폐쇄망(사설 연결)"], "사내망에서만 접근하는 ERP"),
    }
    for sector, req in reqs.items():
        t0 = time.time()
        try:
            rec = svc.recommend(req, sector)
            R["recommend"][sector] = {
                "requirement": req.__dict__, "best": rec.recommended_csp, "seconds": round(time.time() - t0, 1),
                "candidates": [{"csp": c.csp, "eligible": c.eligible, "monthly": c.monthly_total,
                                "excluded": c.excluded_reasons} for c in rec.candidates],
                "answer": rec.answer.text, "cited": rec.answer.cited, "notices": rec.answer.notices,
                "evidences": ev_rows(rec.answer.evidences, rec.answer.cited)}
        except ServiceError as err:
            R["recommend"][sector] = {"error": err.user_message}

    # F2013 API (실제 서비스로 TestClient 요청)
    print("F2013 API")
    try:
        from fastapi.testclient import TestClient
        from api.main import app
        c = TestClient(app)
        R["api"] = {
            "status": c.get("/api/status").status_code,
            "products": c.get("/api/products", params={"csp": "NCP"}).status_code,
            "bad_product": [c.get("/api/products/NOPE").status_code, c.get("/api/products/NOPE").json()],
            "ask": None,
        }
        r = c.post("/api/ask", json={"item_id": "AWS-CMP-01", "question": q[2], "sector": "learning"})
        body = r.json()
        R["api"]["ask"] = {"code": r.status_code, "keys": sorted(body.keys()),
                           "evidence_count": len(body.get("evidences", [])) if isinstance(body, dict) else None}
    except Exception as exc:  # noqa: BLE001
        R["api"] = {"error": f"{type(exc).__name__}: {exc}"}

    # 4.2 청크 크기 변경 실험 (별도 색인 폴더)
    print("4.2 청크 실험")
    R["exp_chunk"] = [chunk_experiment(s, o) for s, o in ((500, 100), (1000, 200), (1500, 300))]

    R["final_counts"] = dict(zip(("meta", "docs"), svc.store.counts()))
    (OUT / "verify_real.json").write_text(json.dumps(R, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print("검증 완료 → docs/evidence/verify_real.json")
    return 0


def run_recheck() -> int:
    """수정 후 재확인: 같은 질문 두 번(NF2002), 근거 없는 질문 2개(F2007·F2008). 결과는 verify_recheck.json. """
    svc = get_service()
    R = {"run_at": datetime.now().strftime("%Y-%m-%d %H:%M")}
    q = ("GCP-CMP-01", "이 상품을 월 730시간 쓰면 비용이 얼마인가요?", "learning")
    R["first"] = timed_ask(svc, *q)
    R["again"] = timed_ask(svc, *q)
    R["not_in_docs"] = timed_ask(svc, "GCP-CMP-01", "이 상품의 SLA 장애 보상 비율은 몇 퍼센트인가요?", "learning")
    R["unrelated"] = timed_ask(svc, "GCP-CMP-01", "다음 주 서울 날씨는 어떤가요?", "learning")
    # 조건 탐색 사양 조건(코드 비교) 재확인
    res = svc.explore("월 2만 원 이하 2vCPU 서버", "learning")
    R["explore_learning"] = {"conditions": res.conditions,
                             "hits": [{"item_id": h.product.item_id, "vcpu": h.product.vcpu, "monthly": h.monthly_estimate,
                                       "reason": h.reason} for h in res.hits]}
    (OUT / "verify_recheck.json").write_text(json.dumps(R, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print("재확인 완료")
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "recheck":
        raise SystemExit(run_recheck())
    if len(sys.argv) > 1 and sys.argv[1] == "chunk":
        raise SystemExit(run_chunk_mode())
    raise SystemExit(main())
