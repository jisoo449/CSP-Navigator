// CSP Navigator — F2013 프론트엔드 (바닐라 JS). 모든 데이터는 /api/* 에서 받는다.
"use strict";

const state = { sector: "public", meta: null, products: [], chats: {}, selected: null, status: null };
const $ = (sel, el = document) => el.querySelector(sel);
const $$ = (sel, el = document) => [...el.querySelectorAll(sel)];

// ── 공통 ───────────────────────────────────────────────
function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function won(v) { return v === null || v === undefined ? "계산 불가" : Math.round(v).toLocaleString("ko-KR") + "원"; }
function supportText(v) { return v === true ? "지원" : v === false ? "미지원" : String(v); }
function supportBadge(v) {
  const cls = v === true ? "ok" : v === false ? "bad" : "warn";
  return `<span class="badge ${cls}">${esc(supportText(v))}</span>`;
}
function freshBadge(dateStr, stale) {
  return `확인일 ${esc(dateStr)}` + (stale ? ` <span class="badge warn">재확인 권장</span>` : "");
}
function link(src) {
  return /^https?:\/\//.test(src) ? `<a href="${esc(src)}" target="_blank" rel="noopener">${esc(src)}</a>` : esc(src);
}
// 마크다운 일부(굵게·목록·줄바꿈)와 [근거 n] 표시만 처리한다. HTML은 먼저 이스케이프한다.
function md(text) {
  const lines = esc(text).split("\n");
  let html = "", inList = false;
  for (const raw of lines) {
    let line = raw.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
                  .replace(/\[근거\s*([\d,\s]+)\]/g, (_, n) => `<span class="cite">근거 ${n.trim()}</span>`);
    const m = line.match(/^\s*[-*]\s+(.*)$/);
    if (m) { if (!inList) { html += "<ul>"; inList = true; } html += `<li>${m[1]}</li>`; continue; }
    if (inList) { html += "</ul>"; inList = false; }
    html += line.trim() ? `<p>${line}</p>` : "";
  }
  return html + (inList ? "</ul>" : "");
}
async function api(path, opts = {}) {
  const res = await fetch(path, { headers: { "Content-Type": "application/json" }, ...opts });
  let body = null;
  try { body = await res.json(); } catch { /* 본문 없음 */ }
  if (!res.ok) throw new Error((body && body.detail) || "처리 중 문제가 생겼습니다. 잠시 후 다시 시도해 주세요.");
  return body;
}
function errorBox(msg) { return `<div class="error" role="alert">${esc(msg)}</div>`; }
function loading(msg) { return `<div class="card muted"><span class="spinner"></span>${esc(msg)}</div>`; }

// 근거: 실제로 인용된 것만 서버가 보내 준다 (F2008)
function evidenceHtml(evidences) {
  if (!evidences.length) {
    return `<div class="notice">이 답변에 인용된 근거가 없습니다. 색인된 문서에서 확인된 내용이 없다는 뜻입니다.</div>`;
  }
  const items = evidences.map((e) => `
    <div class="ev"><strong>[근거 ${e.number}]</strong> <span class="badge src">${esc(e.source_label)}</span> ${esc(e.title)}
      <div>출처: ${link(e.source)} · ${freshBadge(e.checked_at, e.stale)}</div>
      ${e.snippet ? `<div class="snip">${esc(e.snippet)}</div>` : ""}</div>`).join("");
  return `<details class="evid" open><summary>근거 ${evidences.length}건</summary>${items}</details>`;
}
function answerHtml(a) {
  const notices = (a.notices || []).map((n) => `<div class="notice">${esc(n)}</div>`).join("");
  return `<div class="answer">${md(a.text)}</div>${notices}${evidenceHtml(a.evidences)}
          <div class="foot-disclaimer">※ ${esc(a.disclaimer)}</div>`;
}

// ── 상태·부문 (F2012, F2017) ────────────────────────────
async function loadStatus() {
  try {
    const s = await api("/api/status");
    state.status = s;
    const chips = [
      `<span class="badge">csp_product_meta ${s.meta_count.toLocaleString()}건</span>`,
      `<span class="badge">csp_external_docs ${s.doc_chunk_count.toLocaleString()}청크</span>`,
    ];
    if (!s.api_key_ready) chips.push(`<span class="badge bad">LLM·임베딩 설정 누락: ${esc(s.missing_env.join(", "))}</span>`);
    if (!s.index_ready) chips.push(`<span class="badge bad">색인 없음 — 데이터 준비·색인 절차를 먼저 실행하세요</span>`);
    if (s.fake_mode) chips.push(`<span class="badge warn">점검 모드(가짜 LLM)</span>`);
    $("#status").innerHTML = chips.join("");
    $("#disclaimer").textContent = s.disclaimer;
  } catch (e) {
    $("#status").innerHTML = errorBox(e.message);
  }
}
function ready() { return state.status && state.status.api_key_ready && state.status.index_ready; }
function blockedMessage() {
  if (!state.status) return "서버 상태를 확인하지 못했습니다.";
  if (!state.status.api_key_ready) return "LLM·임베딩 API 키가 설정되지 않았습니다. 관리자에게 .env 설정을 요청하세요.";
  return "색인된 상품 데이터가 없습니다. 데이터 준비·색인 절차를 먼저 실행하세요.";
}
function setSector(code) {
  state.sector = code;
  $$(".sector button").forEach((b) => { const on = b.dataset.sector === code; b.classList.toggle("on", on); b.setAttribute("aria-checked", on); });
  $("#sectorHelp").textContent = `현재 부문: ${state.meta.sectors[code]} — ${state.meta.sector_help[code]}`;
  $("#gradeWrap").style.display = code === "public" ? "" : "none";
}

// ── 추천 (F2010, F2017, F2018) ──────────────────────────
function recommendHtml(r, budget) {
  const best = r.candidates.find((c) => c.csp === r.recommended_csp);
  let html = "";
  if (best) {
    html += `<div class="metrics">
      <div class="metric"><div class="k">추천 CSP</div><div class="v">${esc(best.csp)}</div></div>
      <div class="metric"><div class="k">예상 월 비용</div><div class="v">${won(best.monthly_total)}</div></div>
      <div class="metric"><div class="k">예산 잔액</div><div class="v">${won(budget - best.monthly_total)}</div></div></div>`;
    if (!best.within_budget) html += `<div class="notice">예산 안에 드는 후보가 없어 가장 저렴한 후보를 보여 줍니다.</div>`;
  }
  html += `<div class="card">${md(r.answer.text)}${(r.answer.notices || []).map((n) => `<div class="notice">${esc(n)}</div>`).join("")}`;
  html += `<div class="subtabs"><button class="on" data-sub="design">설계안·비용 계산</button>
           <button data-sub="compare">CSP 후보 비교</button><button data-sub="evid">근거</button></div>`;
  // 설계안
  html += `<div class="subpanel on" data-subpanel="design">`;
  if (best) {
    html += `<div class="table-wrap"><table><thead><tr><th>구성</th><th>계산식</th><th>월 비용</th><th>부문 조건</th><th>단가 출처</th></tr></thead><tbody>` +
      best.lines.map((l) => `<tr><td>${esc(l.product_name)}${l.note ? `<div class="muted">${esc(l.note)}</div>` : ""}</td>
        <td class="formula">${esc(l.formula)}</td><td class="num">${won(l.subtotal)}</td>
        <td>${l.sector_status === "unknown" ? '<span class="badge warn">확인 필요</span>' : '<span class="badge ok">충족</span>'}</td>
        <td>${link(l.source_url)}<div class="muted">${freshBadge(l.checked_at, l.stale)}</div></td></tr>`).join("") +
      `</tbody></table></div><p><strong>합계 ${won(best.monthly_total)}</strong> / 월 예산 ${won(budget)}</p>
       <p class="muted">비용은 단가 × 수량 × 사용 시간으로 서버 코드에서 계산했습니다(LLM 계산 아님). VAT 별도, 트래픽·약정 할인 제외.</p>`;
    if (best.notes.length) html += `<ul class="muted">${best.notes.map((n) => `<li>${esc(n)}</li>`).join("")}</ul>`;
  } else {
    html += `<p class="muted">표시할 설계안이 없습니다.</p>`;
  }
  html += `</div>`;
  // 후보 비교
  const rows = [...r.candidates].sort((a, b) => (a.eligible === b.eligible ? a.monthly_total - b.monthly_total : a.eligible ? -1 : 1));
  html += `<div class="subpanel" data-subpanel="compare"><div class="table-wrap"><table><thead><tr><th>CSP</th><th>조건</th><th>예상 월 비용</th><th>예산 이내</th><th>확인 필요</th><th>제외 사유</th></tr></thead><tbody>` +
    rows.map((c) => `<tr><td>${c.csp === r.recommended_csp ? "★ " : ""}${esc(c.csp)}</td>
      <td>${c.eligible ? '<span class="badge ok">충족</span>' : '<span class="badge bad">제외</span>'}</td>
      <td class="num">${c.eligible ? won(c.monthly_total) : "-"}</td><td>${c.eligible ? (c.within_budget ? "예" : "아니오") : "-"}</td>
      <td class="muted">${esc(c.unknown_items.join(", ") || "-")}</td><td class="muted">${esc(c.excluded_reasons.join("; ") || "-")}</td></tr>`).join("") +
    `</tbody></table></div><p class="muted">조건을 만족하지 않는 상품은 추천 근거에서 뺐고, 값이 ‘확인 필요’인 상품은 빼지 않고 표시했습니다.</p></div>`;
  html += `<div class="subpanel" data-subpanel="evid">${evidenceHtml(r.answer.evidences)}</div>`;
  html += `<div class="foot-disclaimer">※ ${esc(r.answer.disclaimer)}</div></div>`;
  return html;
}
async function onRecommend(ev) {
  ev.preventDefault();
  const out = $("#recResult");
  if (!ready()) { out.innerHTML = errorBox(blockedMessage()); return; }
  const f = new FormData(ev.target);
  const requirement = {
    workload: f.get("workload"), instances: +f.get("instances"), vcpu: +f.get("vcpu"), memory_gb: +f.get("memory_gb"),
    need_db: f.get("need_db") === "on", storage_gb: +f.get("storage_gb"), hours: +f.get("hours"), budget: +f.get("budget"),
    security: f.getAll("security"), note: f.get("note") || "", data_grade: f.get("data_grade") || "모름",
  };
  $("#recBtn").disabled = true;
  out.innerHTML = loading("CSP별 후보를 비교하고 근거를 찾아 추천안을 만들고 있습니다… (최대 1분)");
  try {
    const r = await api("/api/recommend", { method: "POST", body: JSON.stringify({ requirement, sector: state.sector }) });
    out.innerHTML = recommendHtml(r, requirement.budget);
    $$(".subtabs button", out).forEach((b) => b.addEventListener("click", () => {
      $$(".subtabs button", out).forEach((x) => x.classList.toggle("on", x === b));
      $$(".subpanel", out).forEach((p) => p.classList.toggle("on", p.dataset.subpanel === b.dataset.sub));
    }));
  } catch (e) { out.innerHTML = errorBox(e.message); }
  finally { $("#recBtn").disabled = false; }
}

// ── 조건 탐색 (F2011) ──────────────────────────────────
async function onExplore(ev) {
  ev && ev.preventDefault();
  const q = $("#exploreQ").value.trim();
  const out = $("#exploreResult");
  if (!q) return;
  if (!ready()) { out.innerHTML = errorBox(blockedMessage()); return; }
  out.innerHTML = loading("조건에 맞는 상품을 찾고 있습니다…");
  try {
    const r = await api("/api/explore", { method: "POST", body: JSON.stringify({ query: q, sector: state.sector }) });
    let html = `<p>해석한 조건 ${r.conditions.map((c) => `<span class="badge">${esc(c)}</span>`).join(" ")}</p>`;
    if (!r.hits.length) {
      html += `<div class="notice">조건에 맞는 상품이 문서에서 확인되지 않음. 조건을 줄여 다시 찾아보세요.</div>`;
    } else {
      html += `<p class="muted">${r.hits.length}건 · 예상 월 비용이 낮은 순</p><div class="grid3">` + r.hits.map((h) => {
        const p = h.product;
        return `<div class="pcard"><strong>${esc(p.name)}</strong>
          <div class="muted">${esc(p.csp)} · ${esc(state.meta.categories[p.category])} · ${esc(p.region)}</div>
          <div>${esc(p.spec)}</div><div class="muted">요금 ${esc(p.price_text)}</div>
          <div class="price">예상 월 ${won(h.monthly_estimate)}</div><div class="muted">(${esc(h.estimate_basis)})</div>
          <div>공공 ${supportBadge(p.public_support)} 폐쇄망 ${supportBadge(p.closed_network_support)} 무료 ${supportBadge(p.free_tier)}</div>
          ${h.sector_status === "unknown" ? '<div><span class="badge warn">부문 조건 확인 필요</span></div>' : ""}
          <div class="muted">${freshBadge(p.checked_at, p.stale)}</div>
          <div class="muted">${esc(h.reason)}</div>
          <button class="ghost" data-ask="${esc(p.item_id)}">이 상품으로 질문하기</button></div>`;
      }).join("") + `</div>`;
    }
    out.innerHTML = html + `<div class="foot-disclaimer">※ ${esc(state.meta.disclaimer)}</div>`;
    $$("[data-ask]", out).forEach((b) => b.addEventListener("click", () => openChat(b.dataset.ask)));
  } catch (e) { out.innerHTML = errorBox(e.message); }
}

// ── 상품 선택·질의응답 (F2009) ──────────────────────────
function fillProductSelect() {
  const csp = $("#fCsp").value, cat = $("#fCat").value;
  const list = state.products.filter((p) => (!csp || p.csp === csp) && (!cat || p.category === cat));
  $("#fProduct").innerHTML = list.map((p) => `<option value="${esc(p.item_id)}">${esc(p.csp)} · ${esc(p.name)}</option>`).join("");
  if (list.some((p) => p.item_id === state.selected)) $("#fProduct").value = state.selected;
  selectProduct($("#fProduct").value || null);
}
function selectProduct(id) {
  state.selected = id;
  const p = state.products.find((x) => x.item_id === id);
  $("#productBox").innerHTML = p ? `<div class="card"><h2>${esc(p.name)}</h2>
    <div class="muted">${esc(p.csp)} · ${esc(state.meta.categories[p.category])} · ${esc(p.region)} · ID <code>${esc(p.item_id)}</code></div>
    <p><strong>사양</strong> ${esc(p.spec)}<br><strong>요금</strong> ${esc(p.price_text)}
    ${p.unit_price !== null ? `(원화 환산 ${p.unit_price.toLocaleString("ko-KR", { maximumFractionDigits: 2 })}원)` : ""}
    ${p.price_note ? `<br><span class="muted">${esc(p.price_note)}</span>` : ""}</p>
    <p>공공 ${supportBadge(p.public_support)} <span class="muted">${esc(p.public_note)}</span><br>
       폐쇄망 ${supportBadge(p.closed_network_support)} <span class="muted">${esc(p.closed_note)}</span><br>
       무료 티어 ${supportBadge(p.free_tier)} <span class="muted">${esc(p.free_note)}</span></p>
    <div class="muted">${freshBadge(p.checked_at, p.stale)} · 출처 ${link(p.source_url)}</div></div>` : `<p class="muted">상품을 고르세요.</p>`;
  renderChat();
}
function renderChat() {
  const log = state.chats[state.selected] || [];
  $("#chatLog").innerHTML = log.map((m) => m.role === "user"
    ? `<div class="msg user">${esc(m.text)}</div>`
    : m.loading ? loading("검색어 추출 → 문서 수집·선별 → 근거 검색 → 답변 생성 중입니다… (첫 수집은 최대 1분)")
    : m.error ? errorBox(m.error) : `<div class="msg">${answerHtml(m.answer)}</div>`).join("");
  $("#chatExamples").style.display = log.length ? "none" : "";
}
async function onAsk(ev, preset) {
  ev && ev.preventDefault();
  const q = (preset || $("#chatQ").value).trim();
  if (!q || !state.selected) return;
  const id = state.selected;
  const log = (state.chats[id] = state.chats[id] || []);
  if (!ready()) { log.push({ role: "user", text: q }, { role: "assistant", error: blockedMessage() }); renderChat(); return; }
  $("#chatQ").value = "";
  log.push({ role: "user", text: q });
  const slot = { role: "assistant", loading: true };
  log.push(slot);
  renderChat();
  try {
    slot.answer = await api("/api/ask", { method: "POST", body: JSON.stringify({ item_id: id, question: q, sector: state.sector }) });
  } catch (e) { slot.error = e.message; }
  slot.loading = false;
  if (state.selected === id) renderChat();
}
function openChat(itemId) {
  const p = state.products.find((x) => x.item_id === itemId);
  if (!p) return;
  $("#fCsp").value = p.csp; $("#fCat").value = p.category; state.selected = itemId;
  fillProductSelect();
  switchTab("chat");
}

// ── 탭 ─────────────────────────────────────────────────
function switchTab(name) {
  $$(".tabs button").forEach((b) => b.classList.toggle("on", b.dataset.tab === name));
  $$(".panel").forEach((p) => p.classList.toggle("on", p.id === `tab-${name}`));
}

// ── 시작 ───────────────────────────────────────────────
async function init() {
  try {
    state.meta = await api("/api/meta");
  } catch (e) { document.querySelector("main").innerHTML = errorBox(e.message); return; }
  const m = state.meta;
  $("#disclaimer").textContent = m.disclaimer;
  $("#workload").innerHTML = m.workloads.map((w) => `<option>${esc(w)}</option>`).join("");
  $("#dataGrade").innerHTML = m.data_grades.map((g) => `<option>${esc(g)}</option>`).join("");
  $("#securityBoxes").innerHTML = m.security_options.map((s) => `<label><input type="checkbox" name="security" value="${esc(s)}"> ${esc(s)}</label>`).join("");
  $("#fCsp").innerHTML = `<option value="">전체</option>` + m.csps.map((c) => `<option>${esc(c)}</option>`).join("");
  $("#fCat").innerHTML = `<option value="">전체</option>` + Object.entries(m.categories).map(([k, v]) => `<option value="${k}">${esc(v)} (${k})</option>`).join("");
  const exploreEx = ["서울 리전, 폐쇄망 지원, 월 3만 원 이하 MySQL", "공공 요건을 만족하는 웹 방화벽", "무료 티어가 있는 소형 서버"];
  $("#exploreExamples").innerHTML = exploreEx.map((x) => `<button type="button">${esc(x)}</button>`).join("");
  $$("#exploreExamples button").forEach((b) => b.addEventListener("click", () => { $("#exploreQ").value = b.textContent; onExplore(); }));
  const chatEx = ["이 상품을 월 730시간 쓰면 비용이 얼마인가요?", "공공기관이 이 상품을 써도 되나요?", "사내 폐쇄망에서 이 상품을 쓰려면 무엇이 더 필요한가요?"];
  $("#chatExamples").innerHTML = chatEx.map((x) => `<button type="button">${esc(x)}</button>`).join("");
  $$("#chatExamples button").forEach((b) => b.addEventListener("click", () => onAsk(null, b.textContent)));

  $$(".sector button").forEach((b) => b.addEventListener("click", () => setSector(b.dataset.sector)));
  $$(".tabs button").forEach((b) => b.addEventListener("click", () => switchTab(b.dataset.tab)));
  $("#recForm").addEventListener("submit", onRecommend);
  $("#exploreForm").addEventListener("submit", onExplore);
  $("#chatForm").addEventListener("submit", onAsk);
  $("#fCsp").addEventListener("change", fillProductSelect);
  $("#fCat").addEventListener("change", fillProductSelect);
  $("#fProduct").addEventListener("change", (e) => selectProduct(e.target.value));
  $("#clearChat").addEventListener("click", () => { delete state.chats[state.selected]; renderChat(); });

  setSector("public");
  await loadStatus();
  try {
    state.products = (await api("/api/products")).items;
  } catch (e) { $("#productBox").innerHTML = errorBox(e.message); }
  fillProductSelect();
}
init();
