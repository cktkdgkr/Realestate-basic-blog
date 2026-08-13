#!/usr/bin/env bash
# OS별 알림 발송 스크립트
#
# 사용법:
#   bash scripts/notify.sh "제목" "본문"
#   bash scripts/notify.sh "[부동산 블로그] 08/17 주제 후보 3개 준비 완료" "번호를 골라줘."
#
# 동작:
#   macOS   → osascript(알림센터) + afplay 사운드
#   Linux   → notify-send (없으면 wall / 로그 파일)
#   Windows → powershell 토스트 (Git Bash / WSL)
#   공통    → logs/notify.log 에 항상 기록 (알림 수단이 없어도 유실되지 않음)

set -uo pipefail

TITLE="${1:-[부동산 블로그] 알림}"
BODY="${2:-확인이 필요하다.}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$ROOT/logs"
LOG_FILE="$LOG_DIR/notify.log"
mkdir -p "$LOG_DIR"

STAMP="$(date '+%Y-%m-%d %H:%M:%S %A')"

# 1) 로그에 무조건 기록
{
  echo "-----------------------------------------"
  echo "[$STAMP]"
  echo "TITLE: $TITLE"
  echo "BODY : $BODY"
} >> "$LOG_FILE"

detect_os() {
  case "$(uname -s 2>/dev/null)" in
    Darwin) echo "macos" ;;
    Linux)
      if grep -qi microsoft /proc/version 2>/dev/null; then echo "wsl"; else echo "linux"; fi ;;
    MINGW*|MSYS*|CYGWIN*) echo "windows" ;;
    *) echo "unknown" ;;
  esac
}

OS="$(detect_os)"
SENT="none"

case "$OS" in
  macos)
    if command -v osascript >/dev/null 2>&1; then
      osascript -e "display notification \"${BODY//\"/\\\"}\" with title \"${TITLE//\"/\\\"}\" sound name \"Glass\"" >/dev/null 2>&1 \
        && SENT="osascript"
    fi
    if command -v terminal-notifier >/dev/null 2>&1 && [ "$SENT" = "none" ]; then
      terminal-notifier -title "$TITLE" -message "$BODY" >/dev/null 2>&1 && SENT="terminal-notifier"
    fi
    ;;

  linux|wsl)
    if command -v notify-send >/dev/null 2>&1; then
      notify-send -u critical "$TITLE" "$BODY" >/dev/null 2>&1 && SENT="notify-send"
    fi
    if [ "$SENT" = "none" ] && [ "$OS" = "wsl" ] && command -v powershell.exe >/dev/null 2>&1; then
      powershell.exe -NoProfile -Command \
        "[void][Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType=WindowsRuntime]; \
         \$t=[Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02); \
         \$x=\$t.GetElementsByTagName('text'); \$x[0].AppendChild(\$t.CreateTextNode('$TITLE'))>\$null; \
         \$x[1].AppendChild(\$t.CreateTextNode('$BODY'))>\$null; \
         [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Claude').Show([Windows.UI.Notifications.ToastNotification]::new(\$t))" \
        >/dev/null 2>&1 && SENT="powershell-toast"
    fi
    if [ "$SENT" = "none" ] && command -v wall >/dev/null 2>&1; then
      echo "$TITLE — $BODY" | wall >/dev/null 2>&1 && SENT="wall"
    fi
    ;;

  windows)
    if command -v powershell >/dev/null 2>&1; then
      powershell -NoProfile -Command \
        "Add-Type -AssemblyName System.Windows.Forms; \
         \$n=New-Object System.Windows.Forms.NotifyIcon; \
         \$n.Icon=[System.Drawing.SystemIcons]::Information; \
         \$n.BalloonTipTitle='$TITLE'; \$n.BalloonTipText='$BODY'; \
         \$n.Visible=\$true; \$n.ShowBalloonTip(10000); Start-Sleep -s 10" \
        >/dev/null 2>&1 && SENT="powershell-balloon"
    fi
    ;;
esac

# 2) 어떤 환경이든 터미널에 보이게 출력 (헤드리스/CI 대비)
echo ""
echo "🔔 ============================================================"
echo "🔔  $TITLE"
echo "🔔  $BODY"
echo "🔔  ($STAMP / os=$OS / channel=$SENT)"
echo "🔔 ============================================================"
echo ""

echo "CHANNEL: $SENT (os=$OS)" >> "$LOG_FILE"
exit 0
