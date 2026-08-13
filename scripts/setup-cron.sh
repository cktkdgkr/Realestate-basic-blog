#!/usr/bin/env bash
# 매주 월요일 오전 9시에 /weekly-topics 를 자동 실행하도록 스케줄을 등록한다.
#
# 사용법:
#   bash scripts/setup-cron.sh            # 등록
#   bash scripts/setup-cron.sh --remove   # 해제
#   bash scripts/setup-cron.sh --show     # 현재 등록 상태 확인

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TAG="# realestate-weekly-blog"
LOG_DIR="$ROOT/logs"
mkdir -p "$LOG_DIR"

CMD="cd $ROOT && claude -p \"/weekly-topics\" --dangerously-skip-permissions >> $LOG_DIR/weekly-topics.log 2>&1"
CRON_LINE="0 9 * * 1 $CMD $TAG"

detect_os() {
  case "$(uname -s 2>/dev/null)" in
    Darwin) echo "macos" ;;
    Linux) if grep -qi microsoft /proc/version 2>/dev/null; then echo "wsl"; else echo "linux"; fi ;;
    MINGW*|MSYS*|CYGWIN*) echo "windows" ;;
    *) echo "unknown" ;;
  esac
}
OS="$(detect_os)"

show() {
  echo "== 현재 등록된 주간 블로그 스케줄 =="
  if command -v crontab >/dev/null 2>&1; then
    crontab -l 2>/dev/null | grep -F "$TAG" || echo "(crontab에 등록된 항목 없음)"
  else
    echo "(crontab 명령을 찾을 수 없음)"
  fi
  if [ "$OS" = "macos" ] && [ -f "$HOME/Library/LaunchAgents/com.realestate.weeklyblog.plist" ]; then
    echo "(launchd plist 존재: ~/Library/LaunchAgents/com.realestate.weeklyblog.plist)"
  fi
}

remove() {
  if command -v crontab >/dev/null 2>&1; then
    crontab -l 2>/dev/null | grep -vF "$TAG" | crontab - 2>/dev/null \
      && echo "✅ crontab 항목을 제거했다."
  fi
  if [ "$OS" = "macos" ]; then
    PLIST="$HOME/Library/LaunchAgents/com.realestate.weeklyblog.plist"
    if [ -f "$PLIST" ]; then
      launchctl unload "$PLIST" 2>/dev/null
      rm -f "$PLIST"
      echo "✅ launchd 등록을 해제했다."
    fi
  fi
  if [ "$OS" = "windows" ] && command -v schtasks >/dev/null 2>&1; then
    schtasks /Delete /TN "RealestateWeeklyBlog" /F 2>/dev/null && echo "✅ 작업 스케줄러 항목을 제거했다."
  fi
  echo "해제 완료."
}

install_cron() {
  if ! command -v crontab >/dev/null 2>&1; then
    echo "❌ crontab 명령이 없다. 아래 중 하나로 설치한 뒤 다시 실행한다."
    echo "   Ubuntu/Debian : sudo apt-get install -y cron && sudo service cron start"
    echo "   RHEL/Fedora   : sudo dnf install -y cronie && sudo systemctl enable --now crond"
    return 1
  fi
  # 기존 항목 제거 후 재등록 (중복 방지)
  ( crontab -l 2>/dev/null | grep -vF "$TAG"; echo "$CRON_LINE" ) | crontab -
  echo "✅ cron 등록 완료 — 매주 월요일 09:00"
  echo "   $CRON_LINE"
}

install_launchd() {
  PLIST="$HOME/Library/LaunchAgents/com.realestate.weeklyblog.plist"
  mkdir -p "$HOME/Library/LaunchAgents"
  cat > "$PLIST" <<PLISTEOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.realestate.weeklyblog</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>-lc</string>
    <string>$CMD</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Weekday</key><integer>1</integer>
    <key>Hour</key><integer>9</integer>
    <key>Minute</key><integer>0</integer>
  </dict>
  <key>StandardOutPath</key><string>$LOG_DIR/weekly-topics.log</string>
  <key>StandardErrorPath</key><string>$LOG_DIR/weekly-topics.err</string>
  <key>RunAtLoad</key><false/>
</dict>
</plist>
PLISTEOF
  launchctl unload "$PLIST" 2>/dev/null
  launchctl load "$PLIST" 2>/dev/null \
    && echo "✅ launchd 등록 완료 — 매주 월요일 09:00 ($PLIST)" \
    || echo "⚠️  launchd load 실패. 수동으로: launchctl load $PLIST"
}

install_schtasks() {
  schtasks /Create /SC WEEKLY /D MON /TN "RealestateWeeklyBlog" /ST 09:00 \
    /TR "cmd /c cd /d $ROOT && claude -p \"/weekly-topics\" --dangerously-skip-permissions >> logs\\weekly-topics.log 2>&1" /F \
    && echo "✅ 작업 스케줄러 등록 완료 — 매주 월요일 09:00"
}

case "${1:-install}" in
  --remove|remove) remove ;;
  --show|show)     show ;;
  *)
    echo "감지된 OS: $OS"
    case "$OS" in
      macos)   install_cron || true; install_launchd ;;
      linux|wsl) install_cron ;;
      windows) install_schtasks ;;
      *) echo "❌ OS를 판별하지 못했다. STATUS.md의 수동 등록 방법을 참고한다." ; exit 1 ;;
    esac
    echo ""
    show
    ;;
esac
