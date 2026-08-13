# STATUS — 주간 부동산 입지분석 블로그 하니스

## 현재 상태
- 하니스 구축: 2026-08-13 (목요일) 완료
- 마지막 실행: 2026-08-13 (목요일) `/weekly-topics`
- 주제 후보: `research/2026-08-13-topics.md`
- 대기 중: 사용자 번호 선택 (1 / 2 / 3)

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

<!-- 이 아래로 qc-reviewer가 완료 기록을 추가한다 -->
