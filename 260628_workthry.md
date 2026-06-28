# 260628 Work-through — NPS Dashboard Narrative Flow Reflection & 개선 구현 계획

## 결론

오늘 논의의 핵심은 차트를 더 붙이는 것이 아니라, 현재 구현된 NPS 운영 Dashboard를 **현장 사용자가 바로 이해하고 실행할 수 있는 narrative flow**로 재정렬하는 것이다.

현재 dashboard는 이미 `NPS 현황판`을 넘어 `현장 코칭 운영판`에 가까워졌다. 다만 화면 일부가 아직 분석가 관점의 기능명/차트명 중심으로 배치되어 있어, 사용자가 처음 볼 때 “그래서 오늘 어디부터 보고 무엇을 해야 하지?”를 한 번 더 해석해야 한다.

이번 개선 방향은 다음 한 문장으로 정리한다.

> **판세를 보고 → 비판매성 risk 우선순위를 좁히고 → 반복성을 확인하고 → Coaching Card/Drill-down/T크루/Action Sheet로 실행한 뒤 → Audit layer에서 검산한다.**

## 현재 상태 요약

- 실행 repo: `/home/brian/workplace/nps-ops-dashboard`
- 현재 로컬 대시보드: `http://localhost:8502`
- Streamlit 실행 명령:

```bash
cd /home/brian/workplace/nps-ops-dashboard
.venv/bin/python -m streamlit run app.py --server.headless true --server.port 8502 --server.address 127.0.0.1
```

- 기준 데이터: `2026-06-24 기준`, 화면상 최신 일자 `2026-06-23`
- 현재 확인된 주요 수치:
  - 오늘 종합 NPS: `92.3`
  - 오늘 판매성 NPS: `96.3`
  - 오늘 비판매성 NPS: `89.5`
  - 오늘 중립/비추천: `4건`
  - 월누적 위험매장: `33곳`
- 진단 유형 분포:
  - 우수 확산형 `32`
  - 즉시 개선형 `14`
  - 비판매성 취약형 `13`
  - 구조 개선형 `2`
  - 판매성 취약형 `1`
  - 관찰/유지형 `1`
  - 샘플 착시형 `1`

이 수치가 말하는 핵심은 “전체 평균은 목표권이지만, 비판매성 축에서는 매장별 action 대상이 분명히 존재한다”는 것이다.

## 논의된 사용자 관점 Narrative Flow

### 현재 dashboard가 전달해야 할 core message

현재 dashboard의 core message는 단순히 “NPS가 몇 점이다”가 아니다.

> 전북팀 전체 NPS는 목표권을 방어하고 있지만, 팀 평가에 직접 영향을 주는 **비판매성 NPS 축**에서 매장별 risk가 갈린다. 따라서 월누적/오늘/최근 7일의 신호를 묶어서 **어느 매장에 어떤 코칭을 먼저 넣을지** 결정해야 한다.

따라서 dashboard는 `reporting`이 아니라 `operating` 화면이어야 한다.

### 사용자 reading path

사용자가 자연스럽게 따라가야 할 흐름은 아래와 같다.

1. **오늘 상태 판단** — 전체 NPS가 목표권인지, 취약축이 무엇인지 본다.
2. **이번 주 판세 확인** — 월중 trend와 오늘 실행 포인트를 본다.
3. **매장 우선순위 발견** — Risk Map과 Care Priority Top bar로 먼저 볼 매장을 좁힌다.
4. **반복성 검증** — Hot Spot에서 단발 이슈인지 반복 이슈인지 확인한다.
5. **Coaching Card 확인** — 유형별 매장 카드에서 실제 코칭 문구와 다음 점검 지표를 본다.
6. **비판매성 Drill-down** — Action Card의 근거를 더 깊게 확인한다.
7. **T크루 후보 확인** — 매장 코칭을 사람 단위 후보까지 좁힌다.
8. **Action Sheet로 공유/실행** — 다운로드 가능한 표로 실행 관리한다.
9. **Audit Check** — 원천 차이, 소표본, VOC 원문 등으로 마지막 검산한다.

## 최종 확정한 Section 구조

Brian과 논의 후, 11개 후보 중 **11번 참고 분포 영역은 삭제**하기로 했다. 나머지는 narrative flow에 맞춰 개선한다.

### 1. 전북팀 NPS 운영 Dashboard — Top Summary

#### 역할

오늘 전북팀이 목표권인지, 어디가 취약축인지 한 번에 판단하는 입구.

#### 유지/개선

- Hero 유지
- KPI cards 유지
- 상단에 **오늘의 Operating Message** 추가

#### 예시 문구

> **오늘의 판단:** 종합 NPS는 목표권이나, 비판매성 기준 월누적 위험매장 33곳이 있어 Care Priority 상위 매장부터 VOC와 업무유형을 확인해야 합니다.

#### 구현 메모

- `overall`, `sales`, `non_sales`, `monthly_risk_store_count`, `nps_time_intelligence` 계산 이후 KPI 인근에 삽입한다.
- 문구는 하드코딩이 아니라 현재 데이터 기준으로 동적 생성한다.

---

### 2. 이번 주 NPS 판세 — 오늘 취약축 확인

#### 현재 제목

`6월 NPS Trend`

#### 변경 제목

`이번 주 NPS 판세 — 오늘 취약축 확인`

#### 역할

월중 흐름과 오늘의 실행 포인트를 확인한다.

#### 논의 내용

현재 Trend 영역은 `이번 주 판세 / 최근 변화 / 오늘 실행` 메시지가 이미 들어가 있어 narrative가 좋다. 다만 회귀/상관 설명은 field-facing 관점에서는 약간 technical하다.

#### 개선 방향

- 제목을 action message 중심으로 변경한다.
- 회귀/상관 caption은 “해석 먼저, 수치 나중” 구조로 다듬는다.

#### 대안 문구

기존:

> 월간 일별 회귀 기준, 판매+비판매 총응답 +10건당 0.2p 상승, 비판매성 응답 +10건당 0.5p 하락이며 업무량-비판매성 NPS 상관은 약합니다.

개선 방향:

> 업무량 증가가 NPS 하락을 강하게 설명하지는 않습니다. 오늘은 점수 자체보다 중립/비추천 4건의 업무유형 확인이 우선입니다.

---

### 3. 매장 NPS Risk Map — 비판매성 케어 우선순위

#### 현재 제목

`매장 NPS Risk Map — 6월 월누적 기준`

#### 변경 제목

`매장 NPS Risk Map — 비판매성 케어 우선순위`

#### 역할

어느 매장을 먼저 봐야 하는지 결정한다.

#### 현재 좋은 점

- X축 = 비판매성 응답 수
- Y축 = 비판매성 NPS
- Bubble = 전체 응답건수
- Color = Care 등급
- 중복 좌표 jitter
- 음수 NPS 압축
- 샘플 착시형/관찰형 제외
- Care Priority Top 20 bar chart 연동
- Hot Spot과 겹치는 매장명 강조

#### 개선 방향

현재 caption은 chart encoding 설명은 정확하지만, 사용자 action message가 약하다.

개선 caption 예시:

> 비판매성 응답이 쌓였는데 NPS가 낮은 매장을 우선 케어 후보로 봅니다. 우측 하단 또는 Care Priority 상위 매장이 이번 주 확인 대상입니다.

#### 연결 문장 추가

Risk Map/Care Priority bar 아래에 Action Card로 이어지는 연결 문장을 추가한다.

예시:

> 우측 하단/상위 bar에 있는 매장은 Action Card에서 VOC 근거와 이번 주 코칭 문구를 확인하세요. 굵은 기울임 매장은 반복 Hot Spot에도 잡힌 공통 action 후보입니다.

---

### 4. 반복 Risk 확인 — 며칠째 흔들리는 매장인가

#### 현재 제목

`NPS Hot Spot Mesh`

#### 변경 제목

`반복 Risk 확인 — 며칠째 흔들리는 매장인가`

#### 역할

우선순위 매장이 단발 이슈인지 반복 이슈인지 확인한다.

#### 논의 내용

Hot Spot은 더 많은 분석이 아니라, Risk Map에서 잡힌 우선순위의 **확증 장치**다. 현장에서는 한 건 때문에 과잉 코칭하는 것도 문제이고, 반복 risk를 놓치는 것도 문제다.

#### 개선 caption 예시

> 중립/비추천이 2일 이상 반복된 매장만 추려 단발 이슈와 반복 이슈를 분리합니다. 굵은 기울임 매장은 Care Priority Top 20에도 잡힌 공통 action 후보입니다.

---

### 5. 매장별 Coaching Card — 이번 주 바로 전달할 액션

#### 현재 제목

`유형별 대응방안`

#### 변경 제목

`매장별 Coaching Card — 이번 주 바로 전달할 액션`

#### 역할

Risk Map과 Hot Spot에서 잡힌 매장을 실제 코칭 문장으로 전환한다.

#### 논의 내용

이 영역은 main flow의 landing point다. dashboard가 “분석했다”에서 끝나지 않고 “이번 주 어떤 말을 해야 하는가”까지 내려가는 핵심 영역이다.

#### 현재 카드 구조

- 매장명
- 대리점 / 담당
- Care Priority rank
- 진단 유형
- 종합 / 최근7일 비판매성 / 오늘 비판매성
- 비판매성 Gap
- 추천/중립/비추천
- 왜 문제
- 대표 VOC
- 이번 주 액션
- 목표
- 다음 점검

#### 개선 방향

카드 내부 label 일부를 field-facing하게 다듬는다.

- `왜 문제` → `우선 케어 이유`
- `다음 점검` → `다음 확인 지표`
- `이번 주 액션`은 유지 가능

#### 개선 caption 예시

> 유형별로 매장을 나누고, 각 카드에서 상태 → VOC 근거 → 이번 주 코칭 → 다음 점검 지표 순으로 봅니다.

---

### 6. 비판매성 Drill-down — Action Card 근거 확인

#### 현재 제목

`비판매성 NPS 전용 상세`

#### 변경 제목

`비판매성 Drill-down — Action Card 근거 확인`

#### 역할

Action Card의 근거를 더 깊게 확인한다.

#### 배치 결정

이 영역을 Risk Map 바로 아래로 올릴 수도 있었으나, 그러면 main flow가 다시 분석 중심으로 길어진다. 현 위치를 유지하되 제목을 바꿔 “Action Card 이후 근거 확인 layer”로 명확히 한다.

#### 유지할 탭

- 집중관리 매장
- 업무유형 Top
- 매장별 추이
- 판매성 양호·비판매성 취약

#### 개선 caption 예시

> Action Card의 근거를 더 확인하는 영역입니다. 비판매성 업무유형, 매장별 추이, 판매성은 양호하지만 비판매성만 낮은 매장을 분리해 봅니다.

---

### 7. T크루 Coaching 후보 — 매장 코칭을 사람 단위로 좁히기

#### 현재 제목

`T크루 코칭 후보`

#### 변경 제목

`T크루 Coaching 후보 — 매장 코칭을 사람 단위로 좁히기`

#### 역할

매장/업무유형 단위의 원인을 사람 단위 코칭 후보로 좁힌다.

#### 배치 결정

Brian 제안대로 **비판매성 Drill-down 다음, Action Sheet 이전**에 배치한다.

흐름상 자연스러운 이유:

1. 비판매성 Drill-down으로 매장/업무유형 원인을 확인한다.
2. T크루 후보에서 매장 안의 코칭 후보를 좁힌다.
3. Action Sheet로 공유/실행한다.

#### 개선 caption 예시

> 개인 평가가 아니라 코칭 후보 탐색입니다. n≥5 기준에서 중립/비추천 건수와 목표 Gap을 함께 보고, 매장 코칭 시 확인할 대상을 좁힙니다.

---

### 8. 매장별 Action Sheet — 다운로드/공유용 실행표

#### 현재 제목

`매장별 Action Sheet`

#### 변경 제목

`매장별 Action Sheet — 다운로드/공유용 실행표`

#### 역할

위에서 확인한 내용을 공유/다운로드 가능한 실행표로 정리한다.

#### 배치 결정

T크루 Coaching 후보 다음에 배치한다. Coaching Card는 읽고 판단하는 카드이고, Action Sheet는 다운로드/공유/실행 관리용 표다.

#### 개선 caption 예시

> 대리점 필터/다운로드와 TOP 10 별도 출력이 가능한 실행표입니다. 위 Coaching Card와 Drill-down에서 확인한 내용을 공유·점검용 표로 정리합니다.

---

### 9. Audit Check — 원천 차이와 소표본 확인

#### 현재 제목

`검산 / 샘플 경고`

#### 변경 제목

`Audit Check — 원천 차이와 소표본 확인`

#### 역할

운영 판단의 신뢰도를 마지막에 확인한다.

#### 논의 내용

Audit layer는 action flow에 끼어들면 흐름을 끊지만, 마지막에 있으면 신뢰도 확인 역할을 한다.

#### 유지할 탭

- 원천 vs 재계산 차이 Top
- 샘플소수 경고

#### 현재 caption 유지 가능

> 운영 판단은 재계산 NPS로 고정하되, 원천 Excel NPS와 차이가 큰 매장과 표본이 작은 축은 별도로 확인합니다.

---

### 10. VOC 근거 확인 — 중립·비추천 원문과 업무유형

#### 현재 제목

`VOC / 중립·비추천`

#### 변경 제목

`VOC 근거 확인 — 중립·비추천 원문과 업무유형`

#### 역할

대표 VOC 외의 원문과 업무유형 근거를 확인한다.

#### 논의 내용

대표 VOC는 Action Card 안에 있어야 현장 코칭의 생생함이 살아난다. 반면 원문 전체 Table은 위로 올리면 dashboard가 무거워진다.

따라서:

- 대표 VOC / 주요 업무유형은 Action Card와 Drill-down에 유지
- 전체 VOC 원문 Table은 Evidence/Audit 성격으로 하단에 유지

---

### 11. 참고 분포 — 삭제 확정

#### 대상

- `진단 유형 분포`
- `비추천/중립 Risk Top`

#### 최종 결정

삭제한다.

#### 삭제 이유

1. **진단 유형 분포는 Risk Map legend/count와 유형별 Coaching Card에서 이미 반복된다.**
2. **비추천/중립 Risk Top은 Care Priority Top bar와 Action Sheet가 더 나은 버전으로 대체한다.**
   - 단순 risk 건수 Top은 “건수 많은 곳”만 보여준다.
   - 현재 dashboard의 core logic은 `risk 건수 + 목표 gap + 필요추천수 + sample confidence`를 반영한 Care Priority다.
   - 따라서 단순 Risk Top은 priority 기준을 헷갈리게 할 수 있다.
3. **하단 layer가 길어져 main story가 흐려진다.**

#### 구현 메모

`app.py` 하단의 아래 블록을 삭제한다.

- `left, right = st.columns(2)`로 시작하는 `진단 유형 분포` / `비추천/중립 Risk Top` 2-column block
- 현재 위치는 `검산 / 샘플 경고` 이후, `VOC / 중립·비추천` 이전

삭제 후 `VOC 근거 확인` section이 바로 이어지도록 한다.

## 구현 순서

작업은 사용자가 최종 OK한 뒤 아래 순서로 진행한다.

### Step 1. Section title/caption rename

먼저 기능 변경 없이 제목과 caption만 바꾼다.

대상:

- `6월 NPS Trend` → `이번 주 NPS 판세 — 오늘 취약축 확인`
- `매장 NPS Risk Map — 6월 월누적 기준` → `매장 NPS Risk Map — 비판매성 케어 우선순위`
- `NPS Hot Spot Mesh` → `반복 Risk 확인 — 며칠째 흔들리는 매장인가`
- `유형별 대응방안` → `매장별 Coaching Card — 이번 주 바로 전달할 액션`
- `비판매성 NPS 전용 상세` → `비판매성 Drill-down — Action Card 근거 확인`
- `T크루 코칭 후보` → `T크루 Coaching 후보 — 매장 코칭을 사람 단위로 좁히기`
- `매장별 Action Sheet` → `매장별 Action Sheet — 다운로드/공유용 실행표`
- `검산 / 샘플 경고` → `Audit Check — 원천 차이와 소표본 확인`
- `VOC / 중립·비추천` → `VOC 근거 확인 — 중립·비추천 원문과 업무유형`

### Step 2. 오늘의 Operating Message 추가

Top KPI 인근에 동적 summary box를 추가한다.

예시 구조:

```text
오늘의 판단: 종합 NPS는 목표권이나, 비판매성 기준 월누적 위험매장 N곳이 있어 Care Priority 상위 매장부터 VOC와 업무유형을 확인해야 합니다.
```

가능하면 오늘의 취약축(`weak_axis`), 오늘 중립/비추천 건수(`today_risk_count`), 월누적 위험매장 수(`monthly_risk_store_count`)를 함께 쓴다.

### Step 3. Risk Map → Coaching Card 연결 문장 추가

Care Priority bar/formula note 아래에 “이 다음 어디를 보면 되는지”를 명확히 적는다.

예시:

```text
우측 하단/상위 bar에 있는 매장은 Action Card에서 VOC 근거와 이번 주 코칭 문구를 확인하세요. 굵은 기울임 매장은 반복 Hot Spot에도 잡힌 공통 action 후보입니다.
```

### Step 4. Section order 조정

Brian이 제안한 최종 구조로 재배치한다.

현재 일부 순서를 아래로 이동한다.

최종 순서:

1. Top Summary
2. Trend
3. Risk Map
4. Hot Spot
5. Coaching Card
6. 비판매성 Drill-down
7. T크루 Coaching 후보
8. Action Sheet
9. Audit Check
10. VOC 근거 확인
11. 참고 분포 삭제

중요한 구조 변경:

- `T크루 Coaching 후보`를 `비판매성 Drill-down` 뒤, `Action Sheet` 앞으로 이동한다.
- `Audit Check`는 Action Sheet 뒤로 둔다.
- `VOC 근거 확인`은 Audit 이후 하단 Evidence layer로 둔다.
- `진단 유형 분포` / `비추천·중립 Risk Top`은 삭제한다.

### Step 5. Action Card 내부 label 정리

카드 내부 field-facing label을 다듬는다.

- `왜 문제` → `우선 케어 이유`
- `다음 점검` → `다음 확인 지표`

### Step 6. 중복 그래프 삭제

최종 확정된 11번 항목 삭제.

- `진단 유형 분포`
- `비추천/중립 Risk Top`

### Step 7. 검증

최소 검증:

```bash
cd /home/brian/workplace/nps-ops-dashboard
.venv/bin/python -m py_compile app.py
curl -I --max-time 10 http://127.0.0.1:8502/
```

권장 검증:

```bash
.venv/bin/python -m pytest -q
```

Browser check:

- `http://127.0.0.1:8502/` 접속
- section 순서 확인
- 삭제 대상 그래프가 사라졌는지 확인
- 주요 section title이 변경되었는지 확인
- 화면 렌더링 오류/Streamlit exception 없음 확인

## 구현 시 주의사항

1. **기능보다 흐름을 먼저 바꾼다.**
   - 이번 작업의 핵심은 새 분석을 추가하는 것이 아니라, 사용자 해석 비용을 줄이는 것이다.
2. **Caption은 사용법 설명보다 insight/action 문장으로 쓴다.**
   - 예: “X축은 무엇”보다 “어느 매장을 먼저 볼지”를 먼저 말한다.
3. **Audit layer는 마지막에 둔다.**
   - 검산은 중요하지만 main operating flow를 끊지 않게 한다.
4. **T크루 영역은 개인 평가가 아니라 코칭 후보 탐색으로 표현한다.**
   - `n≥5`, `코칭 후보`, `확인 대상` 같은 완충 표현을 유지한다.
5. **삭제 대상은 네가 최종 OK한 항목만 삭제한다.**
   - 이번에는 `진단 유형 분포`, `비추천/중립 Risk Top` 삭제 확정.
6. **이미 실행 중인 Streamlit 서버는 code change를 반영할 수 있지만, 오류 판단 전에는 필요 시 재시작한다.**
   - 기존 skill reminder: stale Streamlit process가 오래된 module state를 잡을 수 있다.

## 현재 대화상 결정사항 기록

- Brian은 narrative flow 개선 방향에 동의했다.
- `비판매성 NPS 전용 상세`는 현 위치를 유지하되 `비판매성 Drill-down — Action Card 근거 확인`으로 바꾼다.
- `T크루 Coaching 후보`는 `비판매성 Drill-down` 다음에 배치한다.
- `매장별 Action Sheet`는 T크루 후보 다음에 배치한다.
- `Audit Check`는 그 뒤에서 마무리 layer 역할을 한다.
- `진단 유형 분포`와 `비추천/중립 Risk Top`은 중복적이므로 최종 삭제한다.
- 구현은 이 문서 저장 후 순서대로 진행한다.

## 재개 명령어

```bash
cd /home/brian/workplace/nps-ops-dashboard
.venv/bin/python -m streamlit run app.py --server.headless true --server.port 8502 --server.address 127.0.0.1
.venv/bin/python -m py_compile app.py
.venv/bin/python -m pytest -q
```
