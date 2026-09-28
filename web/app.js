const $ = (selector) => document.querySelector(selector);
const list = $("#evidence-list");
const layer = $("#bbox-layer");
let hotspots = [];

const statusNames = {
  observed: "공개 기록 있음",
  missing: "추가 확인 필요",
  context: "이해를 돕는 구성",
};

// hotspots.json keeps its original wording; show plainer words on the page.
function plain(text) {
  return String(text || "")
    .replace(/bbox는 수동 예시/g, "위치 상자는 사람이 직접 표시")
    .replace(/원본 P&ID 또는 모델 탐지 결과 아님/g, "실제 설비 도면이나 AI 탐지 결과 아님")
    .replace(/이 POC에/g, "이 예시 자료에")
    .replace(/팀 제작 계통도/g, "팀이 직접 그린 예시 도면")
    .replace(/팀 제작 예시 계통도/g, "팀이 직접 그린 예시 도면")
    .replace(/예시 계통$/g, "예시 구성")
    .replace(/공개 관측/g, "공개 기록 있음")
    .replace(/계측 필드/g, "계측 항목")
    .replace(/밸브 개도/g, "밸브 열림 정도");
}

function makeElement(tag, className, content) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (content) element.textContent = content;
  return element;
}

function selectHotspot(id) {
  const item = hotspots.find((candidate) => candidate.id === id);
  if (!item) return;

  document.querySelectorAll("[data-hotspot]").forEach((element) => {
    const selected = element.dataset.hotspot === id;
    element.classList.toggle("selected", selected);
    if (element.classList.contains("evidence-row")) {
      element.setAttribute("aria-pressed", String(selected));
    }
  });

  $("#detail-status").textContent = plain(item.status_label) || statusNames[item.status];
  $("#detail-status").className = `status-badge ${item.status}`;
  $("#detail-title").textContent = item.title;
  $("#detail-subtitle").textContent = item.subtitle;
  $("#detail-value").textContent = item.value;
  $("#detail-known").textContent = plain(item.known);
  $("#detail-unknown").textContent = plain(item.unknown);
  $("#detail-source").textContent = plain(item.source);
  $("#detail-provenance").textContent = plain(item.provenance);
}

function renderHotspots(items) {
  hotspots = items;
  for (const item of items) {
    const row = makeElement("button", `evidence-row ${item.status}`);
    row.type = "button";
    row.dataset.hotspot = item.id;
    row.setAttribute("aria-pressed", "false");
    const icon = makeElement("span", "evidence-icon", item.status === "observed" ? "◉" : item.status === "missing" ? "?" : "◇");
    icon.setAttribute("aria-hidden", "true");
    const copy = makeElement("span", "evidence-copy");
    copy.append(makeElement("strong", "", item.title), makeElement("small", "", item.subtitle));
    const arrow = makeElement("span", "evidence-arrow", "↗");
    arrow.setAttribute("aria-hidden", "true");
    row.append(icon, copy, arrow);
    row.addEventListener("click", () => selectHotspot(item.id));
    list.append(row);

    const box = makeElement("button", `bbox ${item.status}`);
    box.type = "button";
    box.dataset.hotspot = item.id;
    box.setAttribute("aria-label", `도면 위치: ${item.title}, ${plain(item.status_label) || statusNames[item.status]}`);
    const [x, y, width, height] = item.bbox;
    box.style.left = `${x * 100}%`;
    box.style.top = `${y * 100}%`;
    box.style.width = `${width * 100}%`;
    box.style.height = `${height * 100}%`;
    box.append(makeElement("span", "bbox-label", item.subtitle.split(" · ")[0]));
    box.addEventListener("click", () => selectHotspot(item.id));
    layer.append(box);
  }
  selectHotspot("supply");
}

function svgElement(tag, attributes = {}) {
  const element = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [key, value] of Object.entries(attributes)) element.setAttribute(key, String(value));
  return element;
}

function renderTrend(rows) {
  const width = 760;
  const height = 126;
  const left = 32;
  const right = 10;
  const top = 12;
  const bottom = 24;
  const yMin = 50;
  const yMax = 75;
  const plotWidth = width - left - right;
  const plotHeight = height - top - bottom;
  const svg = svgElement("svg", { viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": "실측 공급온도와 설정값의 24시간 추세" });
  const y = (value) => top + ((yMax - value) / (yMax - yMin)) * plotHeight;
  const x = (index) => left + (index / Math.max(rows.length - 1, 1)) * plotWidth;

  for (const value of [55, 60, 65, 70]) {
    svg.append(svgElement("line", { x1: left, y1: y(value), x2: width - right, y2: y(value), class: "grid-line" }));
    const label = svgElement("text", { x: 2, y: y(value) + 4, class: "axis-label" });
    label.textContent = String(value);
    svg.append(label);
  }

  const points = (field) => rows
    .map((row, index) => row[field] == null ? null : `${x(index).toFixed(2)},${y(row[field]).toFixed(2)}`)
    .filter(Boolean)
    .join(" ");
  svg.append(svgElement("polyline", { points: points("s_hc1_supply_temperature_setpoint"), class: "trend-line setpoint" }));
  svg.append(svgElement("polyline", { points: points("s_hc1_supply_temperature"), class: "trend-line actual" }));

  const start = svgElement("text", { x: left, y: height - 5, class: "time-label" });
  start.textContent = "12/11 16:00";
  const end = svgElement("text", { x: width - right, y: height - 5, class: "time-label end" });
  end.textContent = "12/12 15:50";
  svg.append(start, end);
  $("#trend-plot").replaceChildren(svg);
}

async function main() {
  try {
    const [hotspotsResponse, replayResponse] = await Promise.all([
      fetch("./hotspots.json"),
      fetch("../data/replay-52.json"),
    ]);
    if (!hotspotsResponse.ok || !replayResponse.ok) throw new Error("공개 자료를 불러오지 못했습니다.");
    const [items, replay] = await Promise.all([hotspotsResponse.json(), replayResponse.json()]);
    renderHotspots(items);
    renderTrend(replay.measurement_window.rows);
  } catch (error) {
    $("#trend-plot").textContent = `${error.message} 웹 서버를 통해 이 페이지를 열어 주세요.`;
  }
}

$("#outcome-toggle").addEventListener("click", () => {
  const panel = $("#outcome-panel");
  panel.hidden = !panel.hidden;
  $("#outcome-toggle").textContent = panel.hidden ? "나중에 밝혀진 결과 보기" : "나중에 밝혀진 결과 닫기";
});

main();
