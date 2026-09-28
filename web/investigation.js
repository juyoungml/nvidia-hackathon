const $ = (selector) => document.querySelector(selector);
const TRACE_PATHS = [
  "../poc/trace-52-pipeline.json",
  "../poc/trace-52-nvidia-nemotron-3-ultra-550b-a55b.json",
];

let steps = [];
let selected = 0;
let timer = null;

function element(tag, className, content) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (content !== undefined) node.textContent = String(content);
  return node;
}

function fact(label, value, note, kind = "") {
  return { label, value, note, kind };
}

function sourceText(sourceIds) {
  return (sourceIds || []).filter(Boolean).join(" · ");
}

function addToolStep(event, index) {
  const result = event.result || {};
  const tool = event.tool || "Unknown tool";
  if (tool === "get_recent_measurements") {
    const gap = result.secondary_heating_supply_vs_setpoint_absolute_gap_celsius || {};
    const signals = result.signals || {};
    steps.push({
      kind: "TOOL RESULT", nav: "계측 조회", title: "24시간 계측을 확인",
      summary: "2차측 난방 공급온도는 설정값을 따랐습니다. 이 위치의 온도만으로 고객 실내에 열이 도달했다고 말할 수는 없습니다.",
      facts: [
        fact("MEASUREMENT WINDOW", `${result.samples ?? "—"}개 · ${result.interval ?? ""}`, `마지막 샘플: ${result.last_sample_time ?? "—"}`),
        fact("SECONDARY SUPPLY VS SETPOINT", `평균 절대 차이 ${gap.mean ?? "—"} °C`, `최대 ${gap.max ?? "—"} °C · ±2 °C 내 ${gap.samples_within_2C ?? "—"}/${gap.sample_count ?? "—"}`),
        fact("PRIMARY NETWORK METER", `${signals.primary_network_meter_heat_power_kw?.min ?? "—"}–${signals.primary_network_meter_heat_power_kw?.max ?? "—"} kW`, "1차측 열량계 값입니다. 정상 범위는 제공되지 않았습니다.", "neutral"),
        fact("INTERPRETATION LIMIT", "고객 측 열 전달은 미확인", "실내 온도, 2차측 유량, 밸브 위치가 이 replay에 없습니다.", "warn"),
      ], source: result.source_id, raw: result, index,
    });
  } else if (tool === "get_prior_incidents") {
    const record = result.records?.[0] || {};
    steps.push({
      kind: "TOOL RESULT", nav: "이전 장애", title: "6일 전 신고와 조치를 확인",
      summary: "현재 신고 이전에 난방 부족이 기록됐고 난방곡선을 상향했습니다. 현재 사건의 원인으로 연결할 증거는 없습니다.",
      facts: [
        fact("PRIOR REPORT", record.problem || "—", record.report_date || "—"),
        fact("PUBLISHED DESCRIPTION", record.event_description || "—", "보고서의 원문 표현"),
        fact("CAUSAL LIMIT", "현재 사건과의 인과관계 미확인", "이전 조치 이력은 점검 맥락입니다.", "warn"),
      ], source: record.source_id, raw: result, index,
    });
  } else if (tool === "get_maintenance_timeline") {
    steps.push({
      kind: "TOOL RESULT", nav: "이력 조회", title: "과거 이벤트 시간 확인",
      summary: "이력 도구는 발생 시각과 유형을 반환했습니다. 세부 작업 내용이나 해결 여부는 포함하지 않습니다.",
      facts: (result.records || []).map((record) => fact(record.source_id, record.event_start, `유형: ${record.type}`, "neutral")),
      source: sourceText((result.records || []).map((record) => record.source_id)), raw: result, index,
    });
  } else {
    steps.push({ kind: "TOOL RESULT", nav: tool, title: tool, summary: "저장된 도구 결과입니다.", facts: [], source: result.source_id, raw: result, index });
  }
}

function modelStep(event, index) {
  const calls = event.tool_calls || [];
  const isFinal = calls.length === 0;
  steps.push({
    kind: isFinal ? "NEMOTRON OUTPUT" : "NEMOTRON TOOL CALL",
    nav: isFinal ? "조사 결과" : `Ultra 요청 ${event.step || ""}`,
    title: isFinal ? "근거와 다음 확인을 정리" : `${calls.length}개 읽기 도구 요청`,
    summary: isFinal ? "모델이 근거, 결측, 다음 확인을 구분해 답했습니다. 아래 원문과 검토 경계를 함께 읽어야 합니다." : "Nemotron 3 Ultra가 공개 replay에 범위가 제한된 도구를 호출했습니다.",
    facts: [
      fact("MODEL API REQUEST", `${event.latency_seconds ?? "—"}초`, "이 한 번의 모델 요청 시간. 현장 식별 시간과 다릅니다."),
      ...(calls.length ? calls.map((call) => fact("READ-ONLY TOOL REQUEST", call, "공개 사례에 대한 조회", "neutral")) : [fact("FINISH REASON", event.finish_reason || "—", "이후 도구 호출 없음", "neutral")]),
    ], source: "Saved Ultra trace", raw: isFinal ? event.model_content : event, index,
  });
}

function buildSteps(trace) {
  steps = [{
    kind: "CASE INPUT", nav: "사건 입력", title: "“no heat” 신고 시점으로 돌아가기",
    summary: "2016-12-12 15:55의 공개 사건입니다. 이후 작성된 원인과 조치 문장은 모델이 읽지 않았습니다.",
    facts: [
      fact("ASSET", "District-heating substation 21", "PreDist v2 · manufacturer 1"),
      fact("REPORT", "no heat", "현재 사건 신고 분류"),
      fact("DATA BOUNDARY", "신고 전 자료만 제공", "사후 원인·조치 기록은 평가용으로 분리", "warn"),
    ], source: "PreDist-M1-fault-52 · data/replay-52.json", raw: null, index: 0,
  }];
  if (trace.triage) {
    const triage = trace.triage;
    const decision = triage.decision || {};
    const effective = triage.effective_decision || decision;
    steps.push({
      kind: "STAGE 1 / TRIAGE", nav: "사건 선별", title: effective.escalate ? "조사가 필요한 사건으로 선별" : "선별 판단 검토",
      summary: "저장된 Stage 1 실행의 결정입니다. 신고와 센서의 간극을 다음 조사 단계로 넘깁니다. 이 단계는 원인 진단이 아닙니다.",
      facts: [
        fact("MODEL DECISION", String(decision.escalate ?? "—"), `우선순위: ${decision.priority ?? "—"}`),
        fact("MODEL REASON", decision.reason || "—", "모델이 출력한 선별 근거"),
        fact("EFFECTIVE ROUTING", String(effective.escalate ?? "—"), effective.reason || "—", "neutral"),
        fact("VALIDATION", triage.validation_status || "—", `Nano API 요청 ${triage.latency_seconds ?? "—"}초 · 모델 ${triage.model ?? "—"}`, "neutral"),
      ], source: sourceText(effective.source_ids || decision.source_ids), raw: triage, index: 1,
    });
    if (trace.rules_baseline) {
      const rule = trace.rules_baseline;
      steps.push({
        kind: "STAGE 1 / RULE BASELINE", nav: "규칙 기준선", title: "같은 신고의 규칙 기준선",
        summary: "동일 입력에 대한 단순 규칙 결과입니다. 이 사례 하나만으로 Nano가 기준선보다 낫다고 판단할 수 없습니다.",
        facts: [
          fact("RULE DECISION", String(rule.escalate ?? "—"), `우선순위: ${rule.priority ?? "—"}`),
          fact("RULE REASON", rule.reason || "—", "규칙 결과"),
        ], source: sourceText(rule.source_ids), raw: rule, index: 2,
      });
    }
  }
  for (const [index, event] of (trace.events || []).entries()) {
    if (event.tool) addToolStep(event, index + 1);
    else modelStep(event, index + 1);
  }
}

function renderStep(index) {
  if (!steps[index]) return;
  selected = index;
  document.querySelectorAll(".step").forEach((node, stepIndex) => {
    const active = stepIndex === index;
    node.classList.toggle("active", active);
    node.setAttribute("aria-current", active ? "step" : "false");
  });
  const step = steps[index];
  $("#event-index").textContent = `${String(index + 1).padStart(2, "0")} / ${String(steps.length).padStart(2, "0")}`;
  $("#event-kind").textContent = step.kind;
  $("#event-title").textContent = step.title;
  $("#event-summary").textContent = step.summary;
  const body = $("#event-body");
  body.replaceChildren();
  for (const item of step.facts) {
    const card = element("div", `fact ${item.kind || ""}`);
    card.append(element("span", "", item.label), element("strong", "", item.value));
    if (item.note) card.append(element("p", "", item.note));
    body.append(card);
  }
  if (step.raw != null) {
    const details = element("details", "raw-details");
    details.append(element("summary", "", "저장된 원본 출력 보기"));
    const pre = element("pre", "", typeof step.raw === "string" ? step.raw : JSON.stringify(step.raw, null, 2));
    details.append(pre);
    body.append(details);
  }
  $("#event-source").textContent = step.source ? `SOURCE ID / ${step.source}` : "SOURCE ID / 저장된 trace";
}

function renderNavigation() {
  const nav = $("#steps");
  nav.replaceChildren();
  for (const [index, step] of steps.entries()) {
    const button = element("button", "step");
    button.type = "button";
    button.append(element("small", "", `${String(index + 1).padStart(2, "0")} / ${step.kind}`), element("b", "", step.nav));
    button.addEventListener("click", () => { stopPlayback(); renderStep(index); });
    nav.append(button);
  }
  renderStep(0);
}

function stopPlayback() {
  if (timer) window.clearInterval(timer);
  timer = null;
  $("#play-button").textContent = "▶ 단계 재생";
}

function startPlayback() {
  if (timer) { stopPlayback(); return; }
  if (selected >= steps.length - 1) renderStep(0);
  $("#play-button").textContent = "Ⅱ 일시 정지";
  timer = window.setInterval(() => {
    if (selected >= steps.length - 1) { stopPlayback(); return; }
    renderStep(selected + 1);
  }, 1900);
}

async function loadTrace() {
  for (const path of TRACE_PATHS) {
    try {
      const response = await fetch(path, { cache: "no-store" });
      if (response.ok) return { trace: await response.json(), path };
    } catch { /* Try the checked-in Ultra trace. */ }
  }
  throw new Error("저장된 실행 기록을 읽지 못했습니다. 저장소 루트에서 HTTP 서버를 실행해 주세요.");
}

async function init() {
  try {
    const { trace, path } = await loadTrace();
    buildSteps(trace);
    renderNavigation();
    $("#final-output").textContent = trace.final || "최종 응답 없음";
    const modelTime = (trace.events || []).reduce((sum, event) => sum + (Number(event.latency_seconds) || 0), 0);
    $("#api-time").textContent = `${modelTime.toFixed(2)}초`;
    const status = $("#run-status");
    const lastModelEvent = [...(trace.events || [])].reverse().find((event) => !event.tool);
    const finish = trace.finish_reason || lastModelEvent?.finish_reason || (trace.final ? "complete" : "not run");
    status.textContent = trace.triage
      ? `STAGE 1 ${trace.triage.validation_status || "UNKNOWN"} · STAGE 2 ${finish}`
      : `STAGE 2 ${finish} · ULTRA TRACE`;
    if (!trace.final || (trace.triage && !String(trace.triage.validation_status).startsWith("valid"))) status.classList.add("error");
    const toolsUsed = (trace.events || []).filter((event) => event.tool).map((event) => event.tool);
    $("#tool-count").textContent = `읽기 전용 도구 ${toolsUsed.length}회`;
    const toolNames = { get_recent_measurements: "계측", get_prior_incidents: "이전 장애", get_maintenance_timeline: "이력 타임라인" };
    $("#tool-list").textContent = toolsUsed.length ? toolsUsed.map((tool) => toolNames[tool] || tool).join(" · ") : "Ultra 도구 호출 없음";
    const undefinedTags = trace.undefined_signal_names || [];
    $("#tag-check-title").textContent = undefinedTags.length ? "미정의 신호 이름 경고" : "미정의 신호 이름 검사";
    $("#tag-check").textContent = undefinedTags.length
      ? `${undefinedTags.join(", ")}는 공개 feature 목록에 없는 이름입니다. 기존 신호가 아닌 추가로 확보할 측정값으로 읽어야 합니다.`
      : "저장된 출력 검사에서 미정의 신호 이름은 발견되지 않았습니다. 이는 제안의 정확성이나 현장 가용성을 보증하지 않습니다.";
    const download = document.querySelector('a[download]');
    download.href = path;
    download.download = path.split("/").at(-1);
    if (trace.triage) {
      document.querySelector(".case-strip>div:last-child strong").textContent = "Stage 1 선별 → Ultra 조사";
      document.querySelector(".case-strip>div:last-child small").textContent = `저장된 2단계 실행 · 읽기 전용 도구 ${toolsUsed.length}회`;
    }
  } catch (error) {
    $("#event-title").textContent = "실행 기록 로드 실패";
    $("#event-summary").textContent = error.message;
    $("#final-output").textContent = error.message;
    $("#run-status").textContent = `LOAD ERROR · ${error.message}`;
    $("#run-status").classList.add("error");
  }
}

$("#play-button").addEventListener("click", startPlayback);
$("#next-button").addEventListener("click", () => { stopPlayback(); renderStep(Math.min(selected + 1, steps.length - 1)); });
$("#outcome-button").addEventListener("click", () => {
  const text = $("#outcome-text");
  text.hidden = !text.hidden;
  $("#outcome-button").setAttribute("aria-expanded", String(!text.hidden));
  $("#outcome-button").textContent = text.hidden ? "사후 기록 보기 ↗" : "사후 기록 닫기 ↑";
});
$("#print-button").addEventListener("click", () => window.print());
init();
