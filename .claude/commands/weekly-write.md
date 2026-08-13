---
description: 선택한 주제로 심층조사 → 집필 → 검수를 연속 실행해 블로그 글을 완성한다
argument-hint: "[번호 또는 주제명]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebSearch, WebFetch, Task
---

# /weekly-write $ARGUMENTS — 글 작성 (조사 → 집필 → 검수)

## ⛔ 이 커맨드는 한 턴 안에서 끝까지 실행한다.
## ⛔ 단계 사이에서 멈추지 않는다. "다음 단계로 진행할까요?" 라고 묻지 않는다.
## ⛔ 이 커맨드 실행 중 사용자에게 질문하는 것은 금지다.

---

### STEP 1. 날짜 확인 (필수)

```bash
date "+%Y-%m-%d %A"
```

응답 **첫 줄**에 `오늘은 YYYY년 MM월 DD일 O요일이다` 를 출력한다.

---

### STEP 2. 주제 확정

`$ARGUMENTS` 를 해석한다.
- **숫자(1/2/3)** → 가장 최근 `research/*-topics.md` 파일에서 해당 번호의 주제를 찾는다
- **주제명 문자열** → 그 주제로 진행한다
- **비어 있음** → 가장 최근 topics 파일의 1번 주제로 진행한다. 되묻지 않는다

확정한 주제명과 예상 소제목을 화면에 출력하고 **즉시 다음 단계로 넘어간다.**

---

### STEP 3. research-analyst 실행 (즉시)

`research-analyst` 서브에이전트를 실행한다.
(세션에 미등록이면 general-purpose 에이전트에 `.claude/agents/research-analyst.md`
 전문 + 확정 주제를 프롬프트로 넣어 실행한다.)

**요구사항**
- 관련 글 **20개 이상** 수집·정독 (하한선)
- 5개 분석 항목 전부 작성
- 출처 URL 기록, 미확인 수치는 `[미확인]` 표기
- `research/YYYY-MM-DD-notes.md` 저장

---

### STEP 4. writer 실행 (즉시 연속)

`writer` 서브에이전트를 실행한다. notes 파일 경로를 넘긴다.

**요구사항**
- notes 파일만 근거
- 6단 구조 (도입 / 핵심 개념 / 실전 단계 / 디테일 한~두 스푼 / 체크리스트 / 마무리)
- `~이다` 체, 공백 포함 2000자 이상
- `posts/YYYY-MM-DD-{슬러그}.md` 저장

---

### STEP 5. qc-reviewer 실행 (즉시 연속)

`qc-reviewer` 서브에이전트를 실행한다.

- `python3 scripts/count.py posts/...md` 를 **실제로 실행**
- 7개 항목 검수
- 미달 시 구체적 수정 지시와 함께 writer 재실행 (**최대 3회**)
- 통과 시 `STATUS.md` 에 완료 기록

---

### STEP 6. 결과 출력

1. **완성 글 전문을 채팅창에 그대로 출력한다.** 요약하지 않는다. 자르지 않는다.
2. 그 아래에 정보 블록을 붙인다.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 완료
파일    : posts/YYYY-MM-DD-{슬러그}.md
조사    : research/YYYY-MM-DD-notes.md (글 N개 분석)
분량    : 공백 포함 N자 / 공백 제외 N자
문체    : ~이다 체 위반 0건
검수    : PASS (반복 N회)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### STEP 7. 알림 발송

```bash
bash scripts/notify.sh "[부동산 블로그] {주제명} 글 완성" "공백 포함 N자. posts/YYYY-MM-DD-{슬러그}.md 에 저장했다."
```
