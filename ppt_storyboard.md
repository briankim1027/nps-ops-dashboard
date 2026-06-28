# 전북팀 NPS 운영 Dashboard 소개 PPT Storyboard

## 결론

이 PPT의 core message는 아래 한 문장이다.

> **이 Dashboard는 NPS를 ‘점수 확인’에서 끝내지 않고, 비판매성 Risk를 매장·업무·사람 단위 Coaching Action으로 전환하는 운영 도구다.**

구성원 comm.용 문서는 기술 설명보다 “왜 만들었고, 어떻게 보면 되고, 그래서 현장에서 무엇을 하면 되는지”가 한 번에 잡혀야 한다. 아래 storyboard는 Claude에게 PPT 제작을 맡길 때 그대로 전달할 수 있는 slide-by-slide outline이다.

---

# PPT Draft

## 전북팀 NPS 운영 Dashboard 소개
### — 점수 확인에서 현장 Coaching Action으로

---

## 1. Opening Message
### 이 Dashboard는 NPS 점수표가 아니라, 현장 Coaching 운영판입니다

**핵심 메시지**

전북팀 NPS Dashboard의 목적은 단순히 종합 NPS가 몇 점인지 확인하는 것이 아니다. 핵심은 **판매성 / 비판매성 NPS를 분리해 보고, 비판매성 Risk를 매장별 action으로 전환하는 것**이다.

**슬라이드에 들어갈 문장**

> 전체 평균이 목표권이어도, 매장별 비판매성 경험은 다르게 흔들릴 수 있습니다.  
> 이 Dashboard는 그 흔들림을 찾아내고, 이번 주 어떤 매장을 어떻게 코칭할지 정리하기 위해 만들었습니다.

**시각 요소**

- Dashboard 첫 화면 screenshot
- 상단 KPI 영역 강조
- 문구 callout: `점수 확인 → Risk 발견 → Coaching Action`

---

## 2. Why We Built This
### 평균 NPS만 보면 현장의 문제 지점이 보이지 않습니다

**핵심 메시지**

종합 NPS는 팀 전체 상태를 보는 데 유용하지만, 현장 개선에는 충분하지 않다. 실제 코칭은 “어느 매장, 어떤 업무, 어떤 VOC, 어떤 사람”까지 내려가야 실행된다.

**슬라이드 메시지**

> 평균 점수는 방향을 보여주지만, action list를 만들어주지는 않습니다.  
> 현장 개선은 평균이 아니라 **매장별 Risk와 VOC 근거**에서 시작됩니다.

**주요 포인트**

- 종합 NPS만 보면 좋은 평균 뒤에 숨어 있는 매장별 편차를 놓칠 수 있음
- 판매성은 양호해도 비판매성에서 팀 평가 Risk가 발생할 수 있음
- 중립/비추천은 단순 숫자가 아니라 현장 코칭의 출발점
- 그래서 dashboard는 비판매성 축을 중심으로 Risk를 재구성함

**시각 요소**

- Before / After 구조
  - Before: `종합 NPS 확인`
  - After: `비판매성 Risk → 매장 → VOC → Coaching`

---

## 3. Dashboard Reading Flow
### 화면은 “관찰 → 해석 → 액션 → 확인” 순서로 읽습니다

**핵심 메시지**

Dashboard는 많은 차트를 모아둔 화면이 아니라, 사용자가 따라가야 할 reading path를 가지고 있다.

**슬라이드 메시지**

> 위에서 아래로 읽으면, 오늘의 상태 판단에서 시작해 매장별 Coaching Action까지 자연스럽게 내려갑니다.

**최종 화면 흐름**

1. **Top Summary / Operating Message** — 오늘 전북팀 상태와 취약축을 한 문장으로 판단
2. **이번 주 NPS 판세** — 월중 흐름과 오늘 실행 포인트 확인
3. **Risk Map / Care Priority** — 비판매성 기준으로 먼저 볼 매장 확인
4. **반복 Risk 확인** — 단발 이슈인지, 며칠째 반복되는 이슈인지 확인
5. **Coaching Card** — 매장별 코칭 메시지와 다음 확인 지표 확인
6. **비판매성 Drill-down** — Action Card의 근거를 상세 확인
7. **T크루 Coaching 후보** — 매장 코칭을 사람 단위 후보까지 좁힘
8. **Action Sheet** — 다운로드/공유 가능한 실행표로 정리
9. **Audit / VOC Evidence** — 원천 차이, 소표본, VOC 원문으로 마지막 검산

**시각 요소**

- 9-step horizontal flow diagram
- 각 단계에 작은 dashboard screenshot crop

---

## 4. Top Summary
### 첫 화면에서 오늘의 판단을 먼저 봅니다

**핵심 메시지**

Dashboard의 입구는 KPI가 아니라 **오늘의 Operating Message**다. KPI를 해석하지 않아도 오늘 무엇을 봐야 하는지 바로 알 수 있게 했다.

**슬라이드 메시지**

> 첫 화면의 목적은 “오늘 괜찮은가?”가 아니라, “오늘 어디를 먼저 봐야 하는가?”를 판단하는 것입니다.

**주요 구성**

- 종합 NPS
- 판매성 NPS
- 비판매성 NPS
- 총응답자
- 중립/비추천
- 월누적 위험매장
- 오늘의 Operating Message

**예시 문구**

> 종합 NPS는 목표권 흐름을 유지하고 있지만, 비판매성 축 기준 월누적 위험매장이 있어 Care Priority 상위 매장부터 VOC와 업무유형을 확인해야 합니다.

**시각 요소**

- Top KPI screenshot
- Operating Message box 확대

---

## 5. Weekly NPS Flow
### 이번 주 판세는 “오늘 취약축”을 찾기 위한 화면입니다

**핵심 메시지**

Trend chart는 점수 변화를 보는 용도에 그치지 않는다. 오늘 취약축이 판매성인지 비판매성인지, 그리고 오늘 확인해야 할 Risk가 있는지를 알려준다.

**슬라이드 메시지**

> Trend는 과거 흐름을 보는 차트가 아니라, 오늘의 대응 우선순위를 정하는 입구입니다.

**현재 화면에서 읽을 것**

- 이번 주 종합 NPS가 목표권인지
- 오늘 취약축이 판매성인지 비판매성인지
- 오늘 중립/비추천이 몇 건인지
- 오늘 실행 메시지가 무엇인지

**주요 문구**

- `이번 주 판세`
- `최근 변화`
- `오늘 실행`

**시각 요소**

- Trend chart screenshot
- `오늘 실행` 영역 callout

---

## 6. Risk Map
### 비판매성 케어 우선순위는 Risk Map에서 찾습니다

**핵심 메시지**

Risk Map은 dashboard의 핵심 발견 화면이다. 비판매성 응답이 쌓였고 NPS가 낮은 매장을 먼저 보도록 설계했다.

**슬라이드 메시지**

> 전체 평균이 아니라, “비판매성 응답이 쌓였는데 NPS가 낮은 매장”이 이번 주 우선 케어 대상입니다.

**차트 읽는 법**

- X축: 비판매성 응답 수
- Y축: 비판매성 NPS
- Bubble: 전체 응답건수
- Color: Care 유형
- 우측 하단 / Care Priority 상위 매장 = 먼저 확인할 후보

**Care 유형 예시**

- 즉시 개선형
- 비판매성 취약형
- 구조 개선형
- 판매성 취약형
- 우수 확산형

**시각 요소**

- Risk Map screenshot
- 우측 하단 영역 highlight
- Care Priority Top bar screenshot

---

## 7. Care Priority
### 단순 Risk 건수가 아니라, 실행 우선순위를 봅니다

**핵심 메시지**

단순히 중립/비추천 건수가 많은 매장을 보는 것이 아니라, 목표 Gap, 필요추천수, 표본 신뢰도까지 반영한 Care Priority를 본다.

**슬라이드 메시지**

> Care Priority는 “문제가 큰 매장”을 찾는 점수가 아니라, “이번 주 먼저 코칭해야 할 매장”을 찾는 운영 점수입니다.

**간단 산식 설명**

```text
Care Priority = Base Risk Score × Sample Confidence
```

**Base Risk Score에 반영되는 것**

- 비추천 건수
- 중립 건수
- 목표까지 필요한 추천 수
- 응답 수
- 목표 미달 Gap

**Sample Confidence**

- 소표본 매장이 과도하게 상위에 올라오는 착시를 완화
- n이 작으면 확인은 하되, 과잉 일반화하지 않음

**시각 요소**

- Care Priority bar chart
- formula note crop

---

## 8. Repeated Risk
### Hot Spot은 “한 번 튄 건지, 반복되는 건지”를 확인합니다

**핵심 메시지**

한 번 나온 VOC와 며칠 반복되는 Risk는 다르게 봐야 한다. Hot Spot은 중립/비추천이 2일 이상 반복된 매장을 추려, 반복성 있는 이슈를 확인하는 화면이다.

**슬라이드 메시지**

> Hot Spot은 더 많은 차트가 아니라, Risk Map에서 찾은 매장이 반복적으로 흔들리는지 확인하는 검증 장치입니다.

**읽는 법**

- 날짜 × 매장 heatmap
- 중립/비추천 2일 이상 반복 매장만 표시
- 매장명 옆 `(N일)` = risk 발생일 수
- 굵은 기울임 매장 = Care Priority Top 20과도 겹치는 공통 action 후보

**시각 요소**

- Hot Spot heatmap screenshot
- 굵은 기울임 매장 label callout

---

## 9. Coaching Card
### Dashboard의 landing point는 매장별 Coaching Card입니다

**핵심 메시지**

Dashboard는 분석에서 끝나지 않는다. 매장별 Coaching Card에서 “왜 문제인지, 이번 주 무엇을 말해야 하는지, 다음에 무엇을 확인할지”까지 내려간다.

**슬라이드 메시지**

> Coaching Card는 dashboard의 최종 실행 단위입니다.  
> 매장별 상태 → VOC 근거 → 이번 주 액션 → 다음 확인 지표 순서로 읽습니다.

**카드 구성**

1. **식별**
   - 매장명
   - 대리점
   - 담당
   - 진단 유형
   - Care Priority rank
2. **상태**
   - 종합 NPS
   - 최근 7일 비판매성 NPS
   - 오늘 비판매성 NPS
   - 응답 / 추천 / 중립 / 비추천
3. **우선 케어 이유**
   - 주요 Risk 업무
   - 대표 VOC
4. **이번 주 액션**
   - 코칭 checklist
   - 정량 목표
   - 다음 확인 지표

**시각 요소**

- Action Card screenshot
- 카드 4-zone annotation

---

## 10. Drill-down & T크루
### 매장 문제를 업무유형과 사람 단위 코칭 후보로 좁힙니다

**핵심 메시지**

Coaching Card에서 방향을 잡고, Drill-down과 T크루 후보에서 근거를 더 확인한다. 이 영역은 “왜 이 매장을 봐야 하는가”와 “매장 안에서 누구를 확인할 것인가”를 연결한다.

**슬라이드 메시지**

> Drill-down은 Action Card의 근거 확인이고, T크루 후보는 매장 코칭을 사람 단위로 좁히는 화면입니다.

**비판매성 Drill-down**

- 집중관리 매장
- 업무유형 Top
- 매장별 추이
- 판매성 양호·비판매성 취약 매장

**T크루 Coaching 후보**

- 개인 평가가 아니라 코칭 후보 탐색
- n≥5 기준
- 중립/비추천 건수와 목표 Gap 함께 확인
- 매장 코칭 시 확인할 대상을 좁히는 용도

**주의 메시지**

> T크루 화면은 줄세우기가 아니라 코칭 후보를 찾기 위한 보조 화면입니다.

**시각 요소**

- Drill-down tab screenshot
- T크루 table screenshot
- `개인 평가 아님 / Coaching 후보 탐색` callout

---

## 11. Action Sheet
### 공유와 실행 관리는 Action Sheet로 합니다

**핵심 메시지**

Coaching Card가 판단용이라면, Action Sheet는 공유와 실행 관리용이다. 대리점 필터와 CSV 다운로드를 통해 현장 점검 list로 활용할 수 있다.

**슬라이드 메시지**

> Action Sheet는 dashboard에서 나온 판단을 현장 공유용 action list로 바꾸는 화면입니다.

**활용 방식**

- 대리점별 필터
- Top 10만 보기
- CSV 다운로드
- 매장별 주요 Risk 업무 / 대표 VOC / 이번 주 액션 확인
- 회의 전 공유 자료로 활용 가능

**시각 요소**

- Action Sheet screenshot
- CSV download button highlight

---

## 12. Audit Layer
### Audit은 판단 기준이 아니라, 데이터 신뢰도 검산입니다

**핵심 메시지**

Audit 영역은 우선순위를 다시 정하는 화면이 아니다. 운영 판단은 count 기반 재계산 NPS로 하고, Audit은 원천 Excel NPS와 차이가 큰 매장이나 소표본을 확인하는 역할이다.

**슬라이드 메시지**

> Audit은 “누구를 코칭할까”를 정하는 화면이 아니라, “이 판단이 데이터상 설명 가능한가”를 확인하는 화면입니다.

**Audit에서 보는 것**

- 원천 Excel NPS vs count 기반 재계산 NPS 차이
- 소표본 경고
- VOC 원문과 업무유형 근거

**순창 / 전북경원 사례로 설명 가능**

- 원천 축별 NPS와 count 기반 재계산 NPS가 다르게 나오는 사례가 있음
- 운영 판단은 설명 가능한 count 기반 NPS를 기준으로 함
- 원천 차이는 Audit에서 별도 확인

**시각 요소**

- Audit Check table screenshot
- `Source NPS` vs `Recalc NPS` 비교 diagram

---

## 13. How to Use in Weekly Operation
### 매주 운영은 5분 review → 15분 coaching 준비로 충분합니다

**핵심 메시지**

Dashboard는 한 번 보고 끝나는 리포트가 아니라, 주간 운영 루틴에 들어가야 한다.

**추천 운영 루틴**

### Step 1. 5분 — 오늘 상태 확인

- Operating Message 확인
- 오늘 취약축 확인
- 오늘 중립/비추천 건수 확인

### Step 2. 5분 — 우선 매장 확인

- Risk Map
- Care Priority Top bar
- 반복 Hot Spot 겹치는 매장 확인

### Step 3. 10분 — Coaching Card 확인

- 상위 매장 Action Card 확인
- 대표 VOC 확인
- 이번 주 액션 문구 확인

### Step 4. 5분 — 공유/점검

- Action Sheet 다운로드
- 대리점별 코칭 대상 공유
- 다음 확인 지표 설정

**슬라이드 메시지**

> Dashboard를 오래 보는 것이 목적이 아닙니다.  
> 짧게 보고, 정확히 코칭하고, 다음 지표로 확인하는 것이 목적입니다.

---

## 14. What Changes for the Team
### 팀 운영은 감이 아니라 evidence-based coaching으로 바뀝니다

**핵심 메시지**

이 dashboard가 바꾸는 것은 차트가 아니라 운영 방식이다.

**Before**

- 종합 NPS 중심 확인
- 문제가 생긴 뒤 사후 확인
- 매장 방문/코칭 대상이 경험과 감에 의존
- VOC 원문과 action이 분리됨

**After**

- 판매성/비판매성 분리 확인
- 비판매성 Risk 조기 발견
- Care Priority 기반 코칭 대상 선정
- VOC 근거와 action이 한 화면에서 연결
- Action Sheet로 공유/점검 가능

**슬라이드 메시지**

> 이제 NPS는 결과 점수가 아니라, 현장 코칭을 설계하는 입력값이 됩니다.

---

## 15. Closing Message
### 이 Dashboard의 목적은 점수를 설명하는 것이 아니라, 다음 행동을 정하는 것입니다

**핵심 메시지**

마지막 슬라이드는 감성적으로 끝내기보다 운영 원칙을 분명히 남긴다.

**마무리 문장 후보**

> 이 Dashboard는 좋은 점수를 보여주기 위한 화면이 아닙니다.  
> 어디에서 고객 경험이 흔들리는지 찾고, 이번 주 어떤 코칭을 할지 결정하기 위한 운영 도구입니다.

더 압축한 버전:

> NPS를 보는 목적은 점수 해석이 아니라 다음 action 결정입니다.  
> 이 Dashboard는 그 판단을 더 빠르고, 더 설명 가능하게 만들기 위한 전북팀 운영판입니다.

---

# Claude에게 넘길 수 있는 PPT 제작 지시문

```markdown
전북팀 NPS 운영 Dashboard 소개 PPT를 만들어줘.

대상은 전북팀 구성원/대리점 관리자가 dashboard를 이해하고 실제 주간 운영에 활용하도록 돕는 내부 comm. 자료야.  
톤은 과장 없이 factual하고, conclusion-first / Pyramid Structure로 작성해줘.  
핵심은 “NPS 점수표가 아니라 현장 Coaching 운영판”이라는 메시지야.

## PPT 핵심 메시지

이 Dashboard는 NPS를 단순 점수 확인에서 끝내지 않고, 판매성/비판매성 NPS를 분리해 비판매성 Risk를 매장·업무·사람 단위 coaching action으로 전환하는 운영 도구다.

## 반드시 담을 흐름

1. Opening — 이 Dashboard는 NPS 점수표가 아니라 현장 Coaching 운영판
2. Why — 평균 NPS만 보면 현장의 문제 지점이 보이지 않음
3. Reading Flow — 관찰 → 해석 → 액션 → 확인
4. Top Summary — 오늘의 Operating Message
5. 이번 주 NPS 판세 — 오늘 취약축 확인
6. Risk Map — 비판매성 케어 우선순위
7. Care Priority — 단순 Risk 건수가 아니라 실행 우선순위
8. Hot Spot — 단발 이슈인지 반복 Risk인지 확인
9. Coaching Card — 매장별 실행 단위
10. Drill-down & T크루 — 업무유형과 사람 단위 코칭 후보 확인
11. Action Sheet — 다운로드/공유용 실행표
12. Audit Layer — 원천 차이와 소표본 검산
13. Weekly Operation — 5분 review → coaching 준비 루틴
14. What Changes — 감이 아니라 evidence-based coaching
15. Closing — 목적은 점수 설명이 아니라 다음 action 결정

## 표현 원칙

- 제목은 목차형이 아니라 메시지형으로 써줘.
- 각 슬라이드는 “핵심 메시지 1개 + supporting bullets 3~4개” 구조로 해줘.
- 과도한 buzzword나 감성적 표현은 피하고, 현장 운영자가 바로 이해하는 문장으로 써줘.
- 영어 jargon은 필요한 경우 그대로 써도 됨: Dashboard, Risk Map, Care Priority, Coaching Card, Action Sheet, Audit Layer 등.
- PPT에는 실제 dashboard screenshot을 넣을 수 있도록 각 슬라이드별 추천 screenshot 영역도 표시해줘.
- 최종 산출물은 PowerPoint 제작용 상세 slide-by-slide outline으로 만들어줘.
```

---

# PPT에서 특히 강조해야 할 5개 문장

1. **“이 Dashboard는 NPS 점수표가 아니라 현장 Coaching 운영판입니다.”**
2. **“평균 점수는 방향을 보여주지만, action list를 만들어주지는 않습니다.”**
3. **“Care Priority는 문제가 큰 매장이 아니라, 이번 주 먼저 코칭해야 할 매장을 찾는 운영 점수입니다.”**
4. **“Hot Spot은 한 번 튄 이슈와 반복되는 Risk를 구분하기 위한 검증 장치입니다.”**
5. **“NPS를 보는 목적은 점수 해석이 아니라 다음 action 결정입니다.”**

이 5개가 PPT 전체의 spine이다.
