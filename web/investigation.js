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

function yesNo(value) {
  if (value === true) return "예";
  if (value === false) return "아니오";
  return "—";
}

function statusKo(value) {
  if (!value) return "알 수 없음";
  return String(value).startsWith("valid") ? "통과" : String(value);
}

function finishKo(value) {
  return { complete: "완료", stop: "완료", "not run": "실행 안 됨" }[value] || String(value);
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
      kind: "도구 결과", nav: "계측값 조회", title: "신고 전 24시간 계측값 확인",
      summary: "건물로 보내는 물의 온도(공급온도)는 목표값(설정값)을 잘 따랐습니다. 하지만 이 온도만으로 고객의 방까지 열이 전달됐다고 말할 수는 없습니다.",
      facts: [
        fact("조회한 기간", `계측값 ${result.samples ?? "—"}개 · ${result.interval ?? ""}`, `마지막 계측 시각: ${result.last_sample_time ?? "—"}`),
        fact("공급온도와 설정값의 차이", `평균 ${gap.mean ?? "—"} °C`, `최대 ${gap.max ?? "—"} °C · ±2 °C 안에 든 계측값 ${gap.samples_within_2C ?? "—"}/${gap.sample_count ?? "—"}개`),
        fact("도시 배관(1차) 열량계", `${signals.primary_network_meter_heat_power_kw?.min ?? "—"}–${signals.primary_network_meter_heat_power_kw?.max ?? "—"} kW`, "도시 배관 쪽 열량계 값입니다. 어느 정도가 정상인지는 데이터에 없습니다.", "neutral"),
        fact("해석의 한계", "고객 쪽 열 전달은 확인 안 됨", "실내 온도, 건물 배관(2차) 유량, 밸브 열림 정도가 이 자료에 없습니다.", "warn"),
      ], source: result.source_id, raw: result, index,
    });
  } else if (tool === "get_prior_incidents") {
    const record = result.records?.[0] || {};
    steps.push({
      kind: "도구 결과", nav: "과거 신고", title: "6일 전 신고와 조치 확인",
      summary: "이번 신고 전에 “난방이 약하다”는 신고가 있었고, 난방 온도 곡선을 올렸습니다. 이것이 이번 신고의 원인이라는 증거는 없습니다.",
      facts: [
        fact("과거 신고 내용", record.problem || "—", record.report_date || "—"),
        fact("공개 보고서 설명", record.event_description || "—", "보고서 원문 그대로 (영어)"),
        fact("주의", "이번 신고와 관련 있는지 확인 안 됨", "과거 조치는 점검할 때 참고할 배경입니다.", "warn"),
      ], source: record.source_id, raw: result, index,
    });
  } else if (tool === "get_maintenance_timeline") {
    steps.push({
      kind: "도구 결과", nav: "정비 이력", title: "과거 기록의 날짜 확인",
      summary: "이력 도구는 기록이 생긴 시각과 종류만 알려 줍니다. 무슨 작업을 했는지, 해결됐는지는 포함하지 않습니다.",
      facts: (result.records || []).map((record) => fact(record.source_id, record.event_start, `종류: ${record.type}`, "neutral")),
      source: sourceText((result.records || []).map((record) => record.source_id)), raw: result, index,
    });
  } else {
    steps.push({ kind: "도구 결과", nav: tool, title: tool, summary: "저장된 도구 결과입니다.", facts: [], source: result.source_id, raw: result, index });
  }
}

function modelStep(event, index) {
  const calls = event.tool_calls || [];
  const isFinal = calls.length === 0;
  steps.push({
    kind: isFinal ? "모델 최종 답변" : "모델의 자료 요청",
    nav: isFinal ? "조사 결과" : `Ultra 판단 ${event.step || ""}`,
    title: isFinal ? "근거와 다음 확인 사항 정리" : `읽기 전용 도구 ${calls.length}개 요청`,
    summary: isFinal ? "모델이 확인된 근거, 빠진 자료, 다음에 확인할 것을 나눠 답했습니다. 아래 답변 원문과 ‘읽을 때 주의할 점’을 함께 보세요." : "Nemotron 3 Ultra가 신고 시점까지의 공개 자료만 읽을 수 있는 도구를 불렀습니다.",
    facts: [
      fact("모델 응답 시간", `${event.latency_seconds ?? "—"}초`, "이번 한 번의 모델 응답에 걸린 시간입니다. 현장에서 원인을 찾는 시간과는 다릅니다."),
      ...(calls.length ? calls.map((call) => fact("읽기 전용 도구 요청", call, "공개 사례 자료 조회", "neutral")) : [fact("종료 이유", event.finish_reason || "—", "이후 추가 자료 요청 없음", "neutral")]),
    ], source: "저장된 Ultra 실행 기록", raw: isFinal ? event.model_content : event, index,
  });
}

function buildSteps(trace) {
  steps = [{
    kind: "사건 입력", nav: "신고 접수", title: "“no heat” 신고 시점으로 돌아가기",
    summary: "2016-12-12 15:55에 접수된 공개 사건입니다. 나중에 작성된 원인과 조치 기록은 모델이 읽지 않았습니다.",
    facts: [
      fact("설비", "지역난방 서브스테이션 21", "PreDist v2 공개 데이터 · 제조사 1"),
      fact("신고", "no heat (난방 안 됨)", "공개 데이터의 신고 분류"),
      fact("모델에게 준 자료", "신고 전 자료만 제공", "나중에 밝혀진 원인·조치 기록은 채점용으로 따로 보관", "warn"),
    ], source: "PreDist 사례 52 신고 기록", raw: null, index: 0,
  }];
  if (trace.triage) {
    const triage = trace.triage;
    const decision = triage.decision || {};
    const effective = triage.effective_decision || decision;
    steps.push({
      kind: "1단계 · 선별 (Nano)", nav: "신고 선별", title: effective.escalate ? "조사가 필요한 신고로 분류" : "선별 판단 검토",
      summary: "작은 모델(Nemotron Nano)이 이 신고를 더 조사할지 정한 결과입니다. 신고 내용과 센서 값이 어긋나 다음 조사 단계로 넘겼습니다. 이 단계는 원인 진단이 아닙니다.",
      facts: [
        fact("모델 판단: 조사 필요?", yesNo(decision.escalate), `우선순위: ${decision.priority ?? "—"}`),
        fact("모델이 쓴 이유 (영어 원문)", decision.reason || "—", "모델이 출력한 선별 근거"),
        fact("최종 처리: 조사로 넘김?", yesNo(effective.escalate), effective.reason || "—", "neutral"),
        fact("출력 형식 검사", statusKo(triage.validation_status), `Nano 응답 시간 ${triage.latency_seconds ?? "—"}초 · 모델 ${triage.model ?? "—"}`, "neutral"),
      ], source: sourceText(effective.source_ids || decision.source_ids), raw: triage, index: 1,
    });
    if (trace.rules_baseline) {
      const rule = trace.rules_baseline;
      steps.push({
        kind: "1단계 · 비교용 단순 규칙", nav: "단순 규칙 비교", title: "같은 신고에 단순 규칙을 적용한 결과",
        summary: "같은 입력에 미리 정한 단순 규칙을 적용한 결과입니다. 사례 1건만으로는 Nano가 단순 규칙보다 낫다고 말할 수 없습니다.",
        facts: [
          fact("규칙 판단: 조사 필요?", yesNo(rule.escalate), `우선순위: ${rule.priority ?? "—"}`),
          fact("규칙이 쓴 이유 (영어 원문)", rule.reason || "—", "규칙 결과"),
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
    details.append(element("summary", "", "저장된 원본 데이터 보기 (영어·JSON)"));
    const pre = element("pre", "", typeof step.raw === "string" ? step.raw : JSON.stringify(step.raw, null, 2));
    details.append(pre);
    body.append(details);
  }
  $("#event-source").textContent = step.source ? `출처 · ${step.source}` : "출처 · 저장된 실행 기록";
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
  throw new Error("저장된 실행 기록을 읽지 못했습니다. 웹 서버를 통해 이 페이지를 열어 주세요.");
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
      ? `1단계 선별: ${statusKo(trace.triage.validation_status)} · 2단계 조사: ${finishKo(finish)}`
      : `조사: ${finishKo(finish)}`;
    if (!trace.final || (trace.triage && !String(trace.triage.validation_status).startsWith("valid"))) status.classList.add("error");
    const toolsUsed = (trace.events || []).filter((event) => event.tool).map((event) => event.tool);
    $("#tool-count").textContent = `읽기 전용 도구 ${toolsUsed.length}회`;
    const toolNames = { get_recent_measurements: "계측값", get_prior_incidents: "과거 신고", get_maintenance_timeline: "정비 이력" };
    $("#tool-list").textContent = toolsUsed.length ? toolsUsed.map((tool) => toolNames[tool] || tool).join(" · ") : "Ultra 도구 사용 없음";
    const undefinedTags = trace.undefined_signal_names || [];
    $("#tag-check-title").textContent = undefinedTags.length ? "데이터에 없는 센서 이름 주의" : "센서 이름 확인";
    $("#tag-check").textContent = undefinedTags.length
      ? `${undefinedTags.join(", ")}는 공개 데이터의 센서 목록에 없는 이름입니다. 이미 있는 측정값이 아니라, 앞으로 새로 재야 할 값으로 읽어야 합니다.`
      : "답변에 데이터에 없는 센서 이름은 없었습니다. 다만 이것이 제안이 맞다거나 현장에서 바로 확인할 수 있다는 뜻은 아닙니다.";
    const download = document.querySelector('a[download]');
    download.href = path;
    download.download = path.split("/").at(-1);
    if (trace.triage) {
      document.querySelector(".case-strip>div:last-child strong").textContent = "Nano 선별 → Ultra 조사";
      document.querySelector(".case-strip>div:last-child small").textContent = `저장된 2단계 실행 · 읽기 전용 도구 ${toolsUsed.length}회 사용`;
    }
  } catch (error) {
    $("#event-title").textContent = "실행 기록 로드 실패";
    $("#event-summary").textContent = error.message;
    $("#final-output").textContent = error.message;
    $("#run-status").textContent = `불러오기 실패 · ${error.message}`;
    $("#run-status").classList.add("error");
  }
}

$("#play-button").addEventListener("click", startPlayback);
$("#next-button").addEventListener("click", () => { stopPlayback(); renderStep(Math.min(selected + 1, steps.length - 1)); });
$("#outcome-button").addEventListener("click", () => {
  const text = $("#outcome-text");
  text.hidden = !text.hidden;
  $("#outcome-button").setAttribute("aria-expanded", String(!text.hidden));
  $("#outcome-button").textContent = text.hidden ? "나중에 밝혀진 결과 보기 ↗" : "나중에 밝혀진 결과 닫기 ↑";
});
$("#print-button").addEventListener("click", () => window.print());
init();
