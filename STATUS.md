# STATUS — 주간 부동산 입지분석 블로그 하니스

## 현재 상태
- 하니스 구축: 2026-08-13 (목요일) 완료
- 마지막 실행: 2026-08-13 (목요일) `/weekly-topics`
- 조사 글 수: 총 121건 수집 / 중복 10건 제외 고유 111개 (하한선 50개 충족)
- 주제 후보: `research/2026-08-13-topics.md`
  1. 임장 첫날, 부동산 문 안 열고도 할 수 있는 것 — 분위기 임장 완전 초보 가이드 [난이도 하]
  2. "충분한가?"에 답이 없어서 막막했다 — 초보를 위한 입지 판단 숫자 기준표 [난이도 중]
  3. 호갱노노·아실을 켜기만 하고 있다면 — 앱이 알려주지 않는 것들 [난이도 하~중]
- 사용자 선택 결과: **후보 3개 모두 이번 주 미채택.** 사용자가 직접 지정한 주제로 1편 집필 진행.
  - 2번·3번: 폐기
  - 1번: **다음 회차 주제로 킵** (아래 예약 항목 참조)

## 📌 예약된 다음 회차 주제

### ▶ 1순위 — 바로 다음 글 (2026-08-14 사용자 지정, 확정)
**제목: "직장인 시작 4년만에 순자산 10억 달성한 투자자의 이야기"**
- 제목은 **확정**이다. 그대로 쓴다.
- **상세 내용은 사용자가 다음 주에 전달할 예정이다.**
- ⛔ **내용을 전달받기 전에 임의로 집필을 시작하지 않는다.**
  인물 사례·수치·투자 이력을 지어내면 안 되는 글이므로,
  사용자가 준 내용만을 근거로 쓴다.
- 사용자가 내용을 주면 그 턴 안에서 조사 → 집필 → 검수까지 끝낸다.
- 실행 방법: `/weekly-write 직장인 시작 4년만에 순자산 10억 달성한 투자자의 이야기`
- 집필 시 주의: 실존 인물의 이야기라면 **notes와 사용자 제공 내용에 없는 수치를 지어내지 않는다.**
  확인되지 않은 금액·연도·수익률은 "미확인"으로 처리한다.

### ▶ 2순위 — 대기
**"임장 첫날, 부동산 문 안 열고도 할 수 있는 것 — 분위기 임장 완전 초보 가이드"**
- 출처: `research/2026-08-13-topics.md` 후보 1번
- 난이도: 하
- 2026-08-13 사용자가 "다음번 주제로 킵" 요청한 건이다.

### ▶ 3순위 — 대기 (2026-08-13 글에서 예고됨)
**"디딤돌 주택의 환금성" 편**
- 2026-08-13 글 마지막에서 "다음 글에서 이어서 다루겠다"고 독자에게 예고했다.
- 디딤돌 주택을 고를 때 환금성이 왜 중요한지, 무엇으로 판별하는지를 다룬다.
- ⚠️ 독자에게 예고한 글이므로 너무 미루지 않는다. 1순위 글 다음으로 배치를 검토한다.

---

## 자동 스케줄

### 등록된 내용
매주 **월요일 오전 9시**에 `/weekly-topics` 가 자동 실행된다.

감지된 OS: **Linux (Ubuntu 24.04)** → **cron** 사용

등록된 crontab 라인:
```
0 9 * * 1 cd /home/user/Realestate-basic-blog && claude -p "/weekly-topics" --dangerously-skip-permissions >> /home/user/Realestate-basic-blog/logs/weekly-topics.log 2>&1 # realestate-weekly-blog
```

실행 결과는 `research/YYYY-MM-DD-topics.md` 에 저장되고, 동시에
`scripts/notify.sh` 로 아래 알림이 발송된다.

```
[부동산 블로그] MM/DD 주제 후보 3개 준비 완료
번호를 골라줘.
```

번호를 답하면 `/weekly-write [번호]` 가 조사 → 집필 → 검수까지 끝까지 실행된다.

### 등록 명령어
```bash
bash scripts/setup-cron.sh
```
OS를 자동 감지해서 등록한다.
- macOS → cron + launchd(`~/Library/LaunchAgents/com.realestate.weeklyblog.plist`) 둘 다 등록
- Linux / WSL → cron
- Windows(Git Bash) → 작업 스케줄러(`schtasks`, 작업명 `RealestateWeeklyBlog`)

수동으로 등록하려면:
```bash
# Linux / macOS
( crontab -l 2>/dev/null; echo '0 9 * * 1 cd /home/user/Realestate-basic-blog && claude -p "/weekly-topics" --dangerously-skip-permissions >> /home/user/Realestate-basic-blog/logs/weekly-topics.log 2>&1 # realestate-weekly-blog' ) | crontab -

# Windows (관리자 권한 명령 프롬프트)
schtasks /Create /SC WEEKLY /D MON /TN "RealestateWeeklyBlog" /ST 09:00 ^
  /TR "cmd /c cd /d C:\path\to\Realestate-basic-blog && claude -p \"/weekly-topics\" --dangerously-skip-permissions" /F
```

### 해제 방법
```bash
bash scripts/setup-cron.sh --remove
```

수동으로 해제하려면:
```bash
# Linux / macOS — crontab에서 해당 줄만 제거
crontab -l | grep -v 'realestate-weekly-blog' | crontab -

# macOS — launchd 해제
launchctl unload ~/Library/LaunchAgents/com.realestate.weeklyblog.plist
rm ~/Library/LaunchAgents/com.realestate.weeklyblog.plist

# Windows — 작업 스케줄러 해제
schtasks /Delete /TN "RealestateWeeklyBlog" /F
```

### 등록 상태 확인
```bash
bash scripts/setup-cron.sh --show
```

### ⚠️ 중요 — 실제 사용 환경에 대해
이번 구축은 **원격 임시 컨테이너**에서 이뤄졌다. 위 cron은 이 컨테이너 안에는
정상 등록됐지만, 컨테이너가 회수되면 함께 사라진다.
**매주 자동 실행이 실제로 동작하려면, 이 저장소를 본인 PC로 clone한 뒤
그 PC에서 `bash scripts/setup-cron.sh` 를 한 번 실행해야 한다.**
`claude` CLI가 PATH에 있어야 하고, PC가 월요일 오전 9시에 켜져 있어야 한다.
(macOS는 절전 상태에서도 실행되도록 cron보다 launchd 쪽이 안정적이며,
 setup-cron.sh 가 macOS에서는 둘 다 등록한다.)

---

## 실행 이력

### 2026-08-13 (목요일) — 하니스 구축 + 1회차 주제 조사
- 구축 파일: CLAUDE.md / 서브에이전트 4종 / 슬래시 커맨드 2종 / scripts 3종
- `scripts/count.py` 동작 검증 완료 (문체 위반 검출 정상)
- `scripts/notify.sh` 동작 검증 완료 (channel=wall, 로그 기록 정상)
- cron 등록 완료 (매주 월요일 09:00)
- `/weekly-topics` 1회차 실행 → 주제 후보 3개 산출

### 2026-08-13 (목요일) — 완료
- 주제: 서울 아파트 사고 싶은데 돈이 없는 당신 무엇부터 해야할까? (사용자 지정)
- 파일: `posts/2026-08-13-seoul-apartment-first-step.md`
- 분량: 공백 포함 5,260자 / 공백 제외 4,053자 (기준 2,000자 충족)
- 문체 위반: 0건 / 과장·단정 표현 경고: 0건
- 조사: topics 121건 수집(고유 111개) / notes 42개 글 분석
- 검수 반복: 1회 (초회 PASS)
- 디테일 팁 4개:
  1) 주식·채권 매각대금으로 집 산 금액이 전년 대비 531.59% 증가 (국토부 자금조달계획서)
  2) 규제는 지역이 아니라 계약일로 갈린다 — 2025.10.19 계약분과 10.20 계약분의 규칙이 다름
  3) 갭투자를 막은 건 규제지역 지정이 아니라 '소유권 이전 조건부 전세대출 금지' 한 줄
  4) 규제 이후 경기 18개 연접지역 주택 매입액 6조2690억 → 15조5882억 (+158.65%)
- 집필 시 지킨 사실관계 원칙:
  - 규제 현황에 "2026년 2월 기준 확인 자료" 시점을 병기하고 최신 고시 직접 확인을 권고
  - '수도권 외곽'을 **경기·인천 비규제지역**으로 명시. 서울 외곽 자치구와 구분
    (2025년 서울 중랑 0.79%·도봉 0.89%·강북 0.99%로 데이터가 반대 방향이므로)
  - notes에서 [미확인]으로 표기된 수치(구리·동탄·기흥 아파트값 상승률 등)는 본문에 쓰지 않음
  - "앞으로도 오른다"는 단정을 하지 않고 양극화 지속 전망도 함께 명시

<!-- 이 아래로 qc-reviewer가 완료 기록을 추가한다 -->
