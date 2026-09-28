const details = {
  input: ['STREAM / PREPROCESS', '방대한 신호를, 조사할 수 있는 단위로.', '제안 구조에서는 센서별 시간 구간을 집계해 변화율·편차·운전 상태를 특징으로 만듭니다. 5만 신호는 설명용 규모이며, 현재 POC는 저장된 공개 사건을 재생합니다.'],
  nano: ['SYSTEM 1 / NEMOTRON NANO', '조사할 사건을 선별합니다.', '현재 POC에서는 저장된 공개 신고와 집계 특징으로 선별을 실행했습니다. 상시 감시와 규칙·모델 결합 운영은 계획 단계입니다. 세 실제 신고 모두 단순 키워드 규칙도 선별해 Nano의 추가 가치는 아직 입증되지 않았습니다.'],
  ultra: ['SYSTEM 2 / NEMOTRON ULTRA', '관련 근거를 모아, 다음 판단을 돕습니다.', '현재 공개 사건 재생에서는 읽기 도구로 계측·이전 기록을 조회하고 다음 점검을 제안했습니다. 도면 검색과 사전 인덱스 연동은 제안 구조입니다. 출처 인용은 일부 누락되어 검토가 필요합니다.'],
  human: ['ENGINEER / REVIEW', '결론과 함께, 판단의 근거도 전달합니다.', '엔지니어가 원본 출처와 불확실성을 검토하고 현장을 확인합니다. 현재 제안 아키텍처에 설비 자동 제어는 포함하지 않습니다.'],
  docs: ['KNOWLEDGE / SOURCES', '흩어진 문서를, 설비의 맥락으로 연결합니다.', '도면·매뉴얼·정비 기록의 개정본과 출처를 보존합니다. 사내 운영에서는 원문과 파생 데이터의 접근 권한도 같은 경계에서 관리하도록 설계합니다.'],
  index: ['INDEX / NEMO RETRIEVER', '사건이 생기기 전에, 검색할 수 있는 근거를 준비합니다.', 'NeMo Retriever의 추출·임베딩·재정렬을 적용 후보로 검토합니다. 설비 태그 정규화와 P&ID 배관 관계는 별도 연결·검증이 필요합니다. 인덱싱 적용과 검색 속도 향상은 아직 검증 전입니다.']
};
document.querySelectorAll('[data-detail]').forEach(node => node.addEventListener('click', () => {
  document.querySelectorAll('[data-detail]').forEach(item => { item.classList.remove('selected'); item.setAttribute('aria-pressed', 'false'); });
  node.classList.add('selected'); node.setAttribute('aria-pressed', 'true');
  const [number, title, copy] = details[node.dataset.detail];
  document.querySelector('#detail-num').textContent = number;
  document.querySelector('#arch-detail-title').textContent = title;
  document.querySelector('#arch-detail-copy').textContent = copy;
}));

document.querySelectorAll("[data-detail]").forEach(node => node.setAttribute("aria-pressed", "false"));
const regions = {
  exchanger: ['증기가 열을 전달하는 위치', '열교환기는 증기의 열을 공정 유체에 전달합니다. 도면의 공급·배출 경로를 함께 확인할 수 있습니다.', '같은 페이지의 End Use 설명과, 열교환기 아래 스팀트랩·응축수 회수 경로를 연결합니다.', '문서 전체를 다시 훑지 않고, 확인할 설비와 연결된 계통부터 조사할 수 있습니다.'],
  trap: ['응축수 배출을 확인할 위치', '원문은 스팀트랩이 응축수를 회수 계통으로 보내는 역할을 설명합니다. 선택 영역은 열교환기 출구의 스팀트랩입니다.', '열교환기 설명과 도면의 Steam Trap 범례를 대조합니다. 이 자료에는 해당 설비의 실측 상태가 없습니다.', '어떤 부품을 확인하는지와 그 이유를 원문에 연결합니다. 위치를 찾았다는 사실을 고장 진단으로 오해하지 않습니다.'],
  return: ['회수 경로를 함께 확인', '응축수 회수 계통은 사용한 물을 보일러로 되돌립니다. 원문 Recovery 절에서 탱크·펌프·탈기기의 역할을 설명합니다.', 'Figure 1의 파란 배관과 같은 페이지의 Recovery 설명을 함께 봅니다.', '단일 부품뿐 아니라 연결된 경로를 보며 조사 범위를 정할 수 있습니다.']
};
document.querySelectorAll('[data-region]').forEach(button => button.addEventListener('click', () => {
  const key = button.dataset.region;
  document.querySelectorAll('[data-region]').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
  document.querySelector('#source-region').className = 'source-region ' + key;
  ['source-title', 'source-role', 'source-evidence', 'source-value'].forEach((id, i) => document.getElementById(id).textContent = regions[key][i]);
}));
