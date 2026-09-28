import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const SKILL_DIR = process.env.SKILL_DIR;
const RUNTIME_PYTHON = process.env.RUNTIME_PYTHON;
const RUNTIME_NODE_MODULES = process.env.RUNTIME_NODE_MODULES;
if (!SKILL_DIR || !RUNTIME_PYTHON || !RUNTIME_NODE_MODULES) throw new Error('Set SKILL_DIR, RUNTIME_PYTHON and RUNTIME_NODE_MODULES from the bundled workspace dependencies.');
const { Presentation, PresentationFile } = await import(pathToFileURL(path.join(RUNTIME_NODE_MODULES, '@oai/artifact-tool/dist/artifact_tool.mjs')).href);
const TMP = path.join(ROOT, '.artifacts/slides');
const OUT = path.join(ROOT, 'submission/slides/Plant_Reliability_Agent_submission.pptx');
const { finalizePresentation } = await import(pathToFileURL(path.join(SKILL_DIR, 'container_tools/artifact_tool_utils.mjs')).href);
await fs.mkdir(TMP, { recursive: true });
await fs.mkdir(path.dirname(OUT), { recursive: true });

const W=1280,H=720;
const C={ink:'#172B27', green:'#244E41', pale:'#F4F1E9', paper:'#FBF9F4', line:'#BFC8BF', muted:'#62736A', orange:'#D06B3D', red:'#A84E3B', white:'#FFFFFF'};
const font='Apple SD Gothic Neo';
const deck=Presentation.create({slideSize:{width:W,height:H}});
function rect(s,x,y,w,h,fill,stroke='none',sw=0){return s.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:h},fill,line:{fill:stroke,width:sw}})}
function line(s,x,y,w,h,color=C.line,sw=1){return s.shapes.add({geometry:'line',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:color,width:sw}})}
function txt(s,t,x,y,w,h,size=24,color=C.ink,bold=false){const q=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});q.text=t;q.text.style={typeface:font,fontSize:size,color,bold,autoFit:'none'};return q}
function base(n,title,section='PLANT RELIABILITY AGENT'){const s=deck.slides.add();s.background.fill=C.paper;rect(s,0,0,12,H,C.green);txt(s,section,58,29,800,22,15,C.green,true);txt(s,String(n).padStart(2,'0'),1184,28,50,24,16,C.muted,true);line(s,58,66,1164,0,C.line,1);if(title)txt(s,title,58,88,1150,74,38,C.ink,true);return s}
function foot(s,t){line(s,58,670,1164,0,C.line,1);txt(s,t,58,680,1155,24,14,C.muted)}
function note(s,t){s.speakerNotes.textFrame.setText(t)}
async function img(s,p,x,y,w,h,fit='contain'){s.images.add({blob:new Uint8Array(await fs.readFile(path.join(ROOT,p))),contentType:'image/png',alt:path.basename(p),fit,position:{left:x,top:y,width:w,height:h}})}

// 1. Cover
{
 const s=deck.slides.add();s.background.fill=C.ink;
 rect(s,0,0,13,H,C.orange);txt(s,'PLANT RELIABILITY AGENT',70,58,700,30,19,'#BED1C3',true);
 txt(s,'설비 조사에 필요한\n근거와 다음 점검을 연결하다',70,172,1070,160,52,C.white,true);
 line(s,70,388,1120,0,'#658176',2);
 txt(s,'공개 지역난방 사건을 시점에 맞춰 재생한 System 2 조사 실험',70,421,1040,74,27,'#DAE6DA');
 txt(s,'NVIDIA 해커톤 제출 발표  ·  2026.09',70,633,1040,30,17,'#BED1C3');
 note(s,'약 20초. 엔지니어가 알람 이후 도면, 계측, 과거 조치를 맞춰 보는 시간을 줄이려는 시도입니다. 이 발표는 공개 PreDist 지역난방 사건을 대상으로 한 조사 실험이며 발전소 현장 검증을 주장하지 않습니다.');
}
// 2. Problem and independent schematic
{
 const s=base(2,'신고 뒤의 질문은 “무엇을 확인할까”');
 txt(s,'고객 신고',60,188,280,37,25,C.green,true);line(s,60,238,295,0,C.green,2);
 txt(s,'“난방이 되지 않는다”',60,262,440,54,33,C.ink,true);
 txt(s,'엔지니어는 온도 추세와 과거 변경 이력을 맞춰 보고,\n측정되지 않은 상태를 구분해 다음 점검을 정한다.',60,344,520,124,24,C.ink);
 txt(s,'도면 탐색 예시',682,180,450,35,21,C.green,true);
 await img(s,'web/assets/doe-steam-figure-1.png',682,222,520,330,'contain');
 txt(s,'DOE 공개 증기 계통도. PreDist 사건 설비의 도면은 아님.',682,570,535,45,17,C.muted);
 foot(s,'자료: PreDist v2 사건 52 · DOE Improving Steam System Performance, Figure 1');
 note(s,'약 25초. 신고 이후의 실제 문제는 단순히 이상 수치를 찾는 일이 아니라, 공급측 계측과 고객 열 전달 사이의 빈칸을 파악하는 것입니다. 오른쪽 그림은 도면 탐색 방향을 설명하는 DOE의 독립된 공개 증기 계통도입니다. PreDist 서브스테이션 21의 도면이 아니고 자동 연결한 결과도 아닙니다. 출처: data/replay-52.json; https://www.energy.gov/sites/prod/files/2014/05/f15/steamsourcebook.pdf, p.3 Figure 1; web/assets/SOURCES.md.');
}
// 3. Actual evidence
{
 const s=base(3,'공급온도는 설정값을 따랐지만, 고객은 “no heat”라고 신고했다');
 txt(s,'PreDist  /  Substation 21  /  2016.12.12 15:55',60,174,780,32,18,C.muted,true);
 await img(s,'web/assets/predist-trend.png',58,215,875,420,'contain');
 line(s,963,206,0,412,C.line,1);
 txt(s,'144',992,238,225,72,58,C.green,true);txt(s,'신고 전 24시간 계측',992,314,225,38,20,C.ink);
 txt(s,'0.31°C',992,386,225,65,45,C.green,true);txt(s,'공급온도와 설정값의\n평균 절대 편차',992,458,235,67,20,C.ink);
 txt(s,'측정 위치: 2차측 난방 공급\n실내 열 도달은 확인 불가',992,560,235,65,18,C.red,true);
 foot(s,'원자료: PreDist v2, CC BY 4.0 · 재도표: web/assets/predist-trend.png');
 note(s,'약 40초. 실제 신고 52는 2016년 12월 12일 15시 55분의 no heat입니다. 당시까지의 24시간 144개 계측에서 2차측 난방 공급온도와 설정값의 평균 절대 편차는 0.31도이고 144개 모두 2도 이내였습니다. 2도는 설명용 편차 기준이지 고장 판정 기준이 아닙니다. 이 센서는 실내 온도나 고객 측 방열기 유량을 보여주지 않으므로, 온도가 설정값을 따른다는 사실만으로 고객에게 열이 도달했다고 말할 수 없습니다. 그림은 공개 원자료를 재도표한 것으로 원 출판사 UI가 아닙니다. 출처: data/replay-52.json; submission/CASE_STORY.md; https://zenodo.org/records/19496480.');
}
// 4. Developer run
{
 const s=base(4,'사례 52의 실제 조사: 읽은 근거에서 세 가지 확인으로');
 txt(s,'개발 실행  ·  bounded_finalize_v2',60,174,690,28,18,C.muted,true);
 const xs=[60,430,800], heads=['01  읽기 도구','02  사실 연결','03  다음 점검'];
 const bodies=[
  'Ultra가 공개 계측·이력과\n시간 자료를 6회 조회',
  '선택한 사실 ID를 묶어\n관측 12개를 구성',
  '실내 온도와 방열 상태\n2차 회로 유량\n제어기 설정·알람 이력'
 ];
 xs.forEach((x,i)=>{txt(s,heads[i],x,230,320,36,22,C.green,true);line(s,x,283,300,0,C.green,2);txt(s,bodies[i],x,312,320,180,i===2?24:25,C.ink)});
 line(s,60,555,1130,0,C.line,1);
 txt(s,'27.811초',60,575,350,56,38,C.green,true);txt(s,'저장된 개발 실행의 벽시계 시간',60,633,445,27,16,C.muted);
 txt(s,'조회 한도 도달 후 종료 단계로 넘김',560,579,620,40,25,C.red,true);
 txt(s,'investigation_budget_exhausted = true  ·  원래 고정 비교 2/4에는 합산하지 않음',560,627,645,32,16,C.muted);
 foot(s,'근거: evaluation/cycle4/development/handoff-v2-case52.json');
 note(s,'약 40초. 이 슬라이드는 고정 비교 이후의 개발 실행 한 건입니다. Ultra는 공개 읽기 도구를 여섯 번 호출했고, 프로그램이 점검에 연결된 사실 ID의 합집합으로 관측 12개를 구성했습니다. 세 점검은 실내 영향, 2차 회로 유량, 제어기 설정과 알람 이력입니다. 여섯 조회 후에는 종료 호출을 위한 예산이 부족해 정책이 최종 단계로 넘겼으며 investigation_budget_exhausted를 명시했습니다. 27.811초는 이 개발 실행의 벽시계 시간이지 엔지니어의 현장 식별 시간이 아닙니다. 참조 검사 통과가 진단 정확도를 뜻하지 않습니다. 출처: evaluation/cycle4/development/handoff-v2-case52.json; evaluation/cycle4/RESULTS.md.');
}
// 5. Editable architecture
{
 const s=base(5,'현재 System 2 조사 경로');
 txt(s,'현재 실행  /  계획 요청 최대 6회',60,175,480,28,18,C.green,true);
 // Editable native PowerPoint shapes: evidence loop, plan, review.
 const boxes=[
  [60,240,185,170,'사건 + 결정시점','신고만 입력\n사후 진단 제외',false],
  [320,240,235,170,'Nemotron Ultra','도구 선택\n추가 조회 판단',true],
  [645,240,285,170,'읽기 전용 도구','계측·시간 구간\n이전 이력',false],
  [320,495,235,125,'최종 점검안','근거 ID·다음 점검',false],
  [645,495,285,125,'출처 연결·검사','선택 사실 ID의 합집합\n불일치 시 보류',false],
  [1010,495,195,125,'엔지니어','원문과 함께 검토',false]
 ];
 boxes.forEach(([x,y,w,h,head,sub,dark])=>{rect(s,x,y,w,h,dark?C.green:C.pale,C.line,1);txt(s,head,x+15,y+16,w-30,35,21,dark?C.white:C.ink,true);line(s,x+15,y+56,w-30,0,dark?'#9CBBAA':C.line,1);txt(s,sub,x+15,y+68,w-30,h-74,18,dark?C.white:C.ink)});
 line(s,248,321,68,0,C.orange,3);txt(s,'입력',254,288,60,28,16,C.orange,true);
 line(s,558,285,84,0,C.orange,3);txt(s,'조회 →',571,251,80,27,16,C.orange,true);
 line(s,558,366,84,0,C.orange,3);txt(s,'← 관측 반환',544,375,130,27,16,C.orange,true);
 txt(s,'추가 조회 판단',460,432,240,29,18,C.green,true);
 line(s,440,413,0,78,C.orange,3);txt(s,'최종 생성',455,454,105,25,16,C.orange,true);
 line(s,558,550,83,0,C.orange,3);line(s,932,550,75,0,C.orange,3);
 txt(s,'점검 이유를 사실 ID로 추적',59,633,580,32,20,C.ink,true);
 txt(s,'후속 후보: Nano 재정렬 · NeMo Retriever · 지속 감시',586,633,620,32,17,C.muted);
 foot(s,'현재 경로: evaluation/run_live_cycle.py, evaluation/cycle4/PROTOCOL.md');
 note(s,'약 45초. 네이티브 PowerPoint 도형과 글자로 편집 가능한 시스템 구조입니다. 알려진 사건과 결정 시점을 넣고 Nemotron Ultra가 도메인 읽기 도구를 선택합니다. 공개 계측, 시점별 자료와 이전 이력의 결과가 Ultra로 돌아오면 추가 조회 여부를 판단합니다. 계획 요청은 최대 여섯 번이며 한 요청에서 여러 도구를 호출할 수 있습니다. 이후 Ultra가 최종 점검안을 생성합니다. 프로그램은 선택된 사실 ID를 점검에 연결하고 출력 계약과 참조를 검사하며, 엔지니어는 원문과 함께 검토합니다. Nano의 새 재정렬 역할, NeMo Retriever, 지속 감시는 후속 후보입니다. 출처: evaluation/cycle4/PROTOCOL.md; evaluation/run_live_cycle.py; submission/REPORT.md.');
}
// 6. Original contribution
{
 const s=base(6,'설비 의미와 시간 경계를 도구 계약에 담았다');
 const rows=[
 ['측정 위치','1차망 계측과 2차측 공급을 분리','공급온도가 맞아도 실내 열 도달은 미확인'],
 ['시점','신고 시각 이전 자료만 조회','사후 원인·조치 정보가 조사 입력에 섞이지 않음'],
 ['시간 주장','같은 시각의 실제값·설정값을 쌍으로 조회','극값과 구간 첫·마지막 값을 구분해 제공'],
 ['근거 ID','점검 이유가 선택한 원본 사실을 참조','ID 존재 검사는 의미적 지지까지 보장하지 않음']
 ];
 let y=195;rows.forEach((r,i)=>{line(s,60,y,1150,0,C.line,1);txt(s,r[0],60,y+20,190,45,25,C.green,true);txt(s,r[1],274,y+17,475,63,23,C.ink,true);txt(s,r[2],779,y+17,425,65,21,C.muted);y+=105});line(s,60,y,1150,0,C.line,1);
 txt(s,'알람 조사 자체는 선행 연구가 있다. 이 구현의 초점은 공개 사건의 원본 필드와 검증 경계다.',60,630,1155,34,18,C.muted);
 foot(s,'NVIDIA 산업 알람 분석 에이전트 선행 글 · evaluation/cycle4/PROTOCOL.md');
 note(s,'약 35초. 산업 알람 조사 에이전트라는 일반 구조는 NVIDIA의 선행 기술 글에도 있습니다. 이 작업의 구체적인 기여는 공개 사건을 설비와 결정 시점에 묶고, 원본 필드와 측정 위치를 보존하며, 시점별 관측과 점검별 사실 ID를 연결한 데 있습니다. 다만 ID가 존재하는지만 확인하는 검사는 문장 의미가 지지되는지 보증하지 않습니다. 실제 사례 3에서도 시간 인용의 일부가 선택 근거에 없다는 검수 경고가 나왔습니다. 출처: evaluation/cycle4/RESULTS.md; evaluation/cycle4/PROTOCOL.md; https://developer.nvidia.com/blog/building-an-analysis-ai-agent-for-industrial-alarm-management-with-nvidia-nemotron/.');
}
// 7. Comparison
{
 const s=base(7,'고정 비교: 출력 계약과 참조 검사는 Ultra 2/4, Sonnet 5 4/4');
 txt(s,'최초 정책 고정 비교  /  개발 52·3  /  별도 설비 신규 29·47  /  각 경로 1회',60,175,1130,31,19,C.muted);
 txt(s,'2 / 4',64,240,480,138,92,C.green,true);txt(s,'Nemotron Ultra + 도메인 도구',65,390,480,44,26,C.ink,true);
 txt(s,'4 / 4',680,240,480,138,92,C.ink,true);txt(s,'제한된 Claude Code + Sonnet 5',680,390,510,44,26,C.ink,true);
 line(s,60,467,1140,0,C.line,1);
 txt(s,'두 Ultra 실패: 6회 유효 조회 뒤 최종 생성으로 넘어가지 못함',60,492,1100,50,25,C.red,true);
 txt(s,'두 경로는 모델과 실행 하네스가 함께 다르다. 이 비율은 형식·참조 통과율이며 진단 정확도나 품질 우위가 아니다.',60,555,1135,57,20,C.ink);
 txt(s,'추가 AI 근거 검수에서 양쪽 점검 이유의 인용 결함이 발견됐다. 현장 전문가 평가는 아직 없다.',60,618,1120,29,17,C.muted);
 foot(s,'근거: evaluation/cycle4/RESULTS.md · results.json');
 note(s,'약 45초. 추론 전에 사례와 프로토콜을 고정했습니다. 개발 사건 두 건과 처음 평가하는 별도 설비 사건 두 건, 총 네 건을 각 경로에서 한 번씩 실행했습니다. 공통 출력 계약과 ID 참조 검사 통과는 Ultra 2/4, 제한된 Claude Code와 Sonnet 5 경로 4/4입니다. Ultra의 두 실패는 실제 도구 조회 6회 후 최종 생성 전환에 실패한 제어 문제입니다. 모델과 하네스가 동시에 다르므로 하네스 효과나 모델 우열을 분리할 수 없습니다. 후속 AI 근거 검수는 두 경로 점검 이유의 인용 결함을 발견했습니다. 독립 현장 전문가의 내용 평가는 아직 없습니다. 진단 정확도나 현장 유용성을 평가한 수치가 아닙니다. 출처: evaluation/cycle4/RESULTS.md; evaluation/cycle4/results.json; evaluation/readiness/content-review/CONTENT_RESULTS.md.');
}
// 8. Boundaries
{
 const s=base(8,'지금 검증한 것과 아직 남은 것');
 txt(s,'실행 기록',60,196,350,40,26,C.green,true);txt(s,'남은 검증',655,196,430,40,26,C.red,true);
 line(s,60,248,540,0,C.green,2);line(s,655,248,540,0,C.red,2);
 txt(s,'Nemotron Ultra의 실제 도구 선택과 조회\n시점별 공개 계측·이력 읽기\n점검별 사실 ID와 참조 검사\nNAT 1.8.0 경유 사례 52의 6개 도구 조회\nOpenShell의 별도 공개 fixture 정책 시험',60,278,550,269,23,C.ink);
 txt(s,'점검 이유의 의미적 근거 지지\n독립 전문가의 맹검 평가\n현장 원인 식별·작업 시간 절감\nNAT 안의 전체 모델 루프\nOpenShell로 보호된 실제 조사 경로',655,278,550,269,23,C.ink);
 line(s,60,570,1140,0,C.line,1);
 txt(s,'공개 자료에 한정한 읽기 경로를 확인했다. 운영 환경 통합은 별도 검증이 필요하다.',60,595,1125,65,22,C.muted,true);
 foot(s,'근거: integrations/README.md · integrations/openshell-README.md · evaluation/cycle4/RESULTS.md');
 note(s,'약 30초. Nemotron Ultra의 실제 도구 선택과 결과는 trace로 확인됩니다. NAT 1.8.0의 여섯 공개 읽기 도구는 직접 경로와 결과 및 사실 구성이 같은지 무키 로컬 시험을 통과했습니다. 별도 사례 52 개발 smoke에서 hosted Ultra가 고른 여섯 조회가 NAT를 거쳐 실행되고 점검안이 참조 검사에 통과했습니다. 이는 최초 Cycle 4 비교와 다른 실행입니다. 모델 계획 루프는 기존 NVIDIA chat API client가 맡고 NAT는 선택된 읽기 도구를 실행합니다. OpenShell은 별도 공개 fixture에서 허용·차단 정책을 시험했으며 실제 조사 루프 보호가 아닙니다. 출처: integrations/NAT_LIVE.md; integrations/nat-live-smoke.json; integrations/nat-live-case52.json; integrations/openshell-README.md; evaluation/cycle4/RESULTS.md.');
}
// 9. Next step
{
 const s=base(9,'다음 검증: 더 쓸 만한 점검안인가');
 txt(s,'제품 가치의 검증 단위는 “근거를 확인할 수 있는 다음 점검”',60,183,1110,66,30,C.green,true);
 const ys=[292,380,468], ns=['01','02','03'], hs=['같은 정보로 내용 평가','변경 정책의 새 사건 재검증','현장 시간·결과 측정'], bs=['방법을 가리고 점검 타당성과 문장별 근거를 전문가가 검토','이미 본 29·47은 개발 자료로 돌리고 새 사건에서 실패 포함 비교','엔지니어 식별 시간과 실제 점검 결과를 별도 기록'];
 ys.forEach((y,i)=>{line(s,60,y-12,1140,0,C.line,1);txt(s,ns[i],60,y,83,41,27,C.orange,true);txt(s,hs[i],154,y,380,50,25,C.ink,true);txt(s,bs[i],550,y,640,58,20,C.muted)});
 line(s,60,563,1140,0,C.line,1);
 txt(s,'8시간에서 30분은 경제성 가정과 목표다. 이번 실험에서 측정한 성과는 아니다.',60,599,1125,65,23,C.red,true);
 foot(s,'다음 단계: evaluation/cycle4/RESULTS.md · evaluation/readiness/RUBRIC.md');
 note(s,'약 35초. 다음에는 동일한 허용 정보에서 방법 이름을 가리고 점검의 타당성과 문장별 근거를 독립 전문가가 검토해야 합니다. 제어 handoff 수정은 기존 사례 52에서만 확인했으므로, 이미 본 29와 47을 새 holdout으로 부르지 않고 미사용 사건에서 재검증합니다. 그리고 현장에서 엔지니어가 원인을 식별하는 시간과 실제 점검 결과를 측정하겠습니다. 8시간에서 30분은 경제성 가정이자 목표이지 이번 실험의 측정 성과가 아닙니다. 출처: evaluation/cycle4/RESULTS.md; evaluation/readiness/RUBRIC.md; submission/REPORT.md.');
}

const candidate=path.join(TMP,'candidate-final-v2.pptx');
await (await PresentationFile.exportPptx(deck)).save(candidate);
for(let i=0;i<deck.slides.items.length;i++){
 const b=await deck.export({slide:deck.slides.items[i],format:'png',scale:1});
 await fs.writeFile(path.join(TMP,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await b.arrayBuffer()));
}
const result=await finalizePresentation({
 workspaceDir:ROOT,candidatePath:candidate,finalPath:OUT,
 pythonExecutable:RUNTIME_PYTHON,
 integrityValidatorPath:path.join(SKILL_DIR,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(SKILL_DIR,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit'],
 explicitTotalSlideCount:9,requiredNativeTableOwnerSlides:[],requiredNativeChartOwnerSlides:[],
 fontPolicy:{basis:'design',families:[font]},verifyArtifactToolImport:true,
 receiptPath:path.join(TMP,'validation-final-v2.json')
});
console.log(JSON.stringify({out:OUT,result},null,2));
