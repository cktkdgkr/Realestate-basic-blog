#!/usr/bin/env python3
"""글자수 카운트 + 문체·구조 위반 검출.

사용법:
    python3 scripts/count.py posts/2026-08-13-example.md
    python3 scripts/count.py posts/2026-08-13-example.md --json
    python3 scripts/count.py posts/2026-08-13-example.md --intro   # 소설 도입부만 검사

판정 기준 (절대 규칙):
    -  5번 공백 포함 2000자 이상 (프론트매터/코드블록 제외)
    -  4번 "~이다"체 위반 문장 0개
    - 10번 고정 맺음 문구가 맨 마지막 줄
    - 11번 소설 도입부가 있고 공백 포함 500자 이내
    - 12번 본문 통계 수치 과다 금지 (퍼센트·%p·기관명 등)
    - 13번 체크리스트·"확인할 것" 절 0개
    - STYLE 6번 `##` 머리글 0개 (절 구분은 구분선으로)
종료 코드:
    0 = 통과, 1 = 미달/위반, 2 = 파일 오류
"""

import json
import re
import sys
from pathlib import Path

MIN_CHARS = 2000
MAX_INTRO_CHARS = 500
CLOSING_LINE = "오늘도 내집 마련을 꿈꾸는 모든 이들의 성공적인 내집 마련과 평안을 기원한다."
DIVIDER = "--------------------"

# 절대 규칙 13번 — 체크리스트/점검표 절
CHECKLIST_HEADINGS = [
    "확인하면 좋을", "확인해야 할", "확인할 것", "체크리스트", "체크포인트",
    "점검", "정리해 보았다", "정리해보았다",
]

# 절대 규칙 12번 — 본문에 들어오면 안 되는 통계 표지
STAT_MARKERS = [
    (r"\d+(?:\.\d+)?\s*%p", "퍼센트포인트"),
    (r"\d+(?:\.\d+)?\s*%", "퍼센트"),
    (r"마이너스\s*0\.\d+", "상관계수"),
    (r"-0\.\d{2,}", "상관계수"),
    (r"국토연구원|한국교통연구원|한국부동산원|자본시장연구원|국토교통부|한국은행|통계청|국가데이터처", "기관명"),
    (r"보고서|논문|연구팀|선임연구위원|박사학위", "보고서·논문 표기"),
    (r"\d+\.\d+분", "소수점 분 단위"),
    (r"\d+\.\d+자|\d+\.\d+건|\d+\.\d+명", "소수점 수치"),
]

# 금지 종결어미: 존댓말(합쇼체/해요체) 및 구어체
BANNED_ENDINGS = [
    (r"습니다", "합쇼체 '~습니다'"),
    (r"읍니다", "합쇼체 '~읍니다'"),
    (r"입니다", "합쇼체 '~입니다'"),
    (r"됩니다", "합쇼체 '~됩니다'"),
    (r"ㅂ니다", "합쇼체 '~ㅂ니다'"),
    (r"니까\?", "합쇼체 의문형 '~니까?'"),
    (r"세요", "해요체 '~세요'"),
    (r"에요", "해요체 '~에요'"),
    (r"예요", "해요체 '~예요'"),
    (r"해요", "해요체 '~해요'"),
    (r"어요", "해요체 '~어요'"),
    (r"아요", "해요체 '~아요'"),
    (r"네요", "해요체 '~네요'"),
    (r"지요", "해요체 '~지요'"),
    (r"죠", "구어체 '~죠'"),
    (r"군요", "해요체 '~군요'"),
    (r"거든요", "해요체 '~거든요'"),
    (r"는데요", "해요체 '~는데요'"),
]

# 과장·단정 표현 (경고용, 실패 처리는 아님)
HYPE_WORDS = [
    "무조건", "100% ", "100%다", "절대 오른다", "반드시 오른다",
    "확실하다", "틀림없다", "무조건적으로", "폭등", "떡상", "대박",
]


def strip_noise(text: str) -> str:
    """프론트매터, 코드블록, 이미지/링크 URL을 본문 판정에서 제거."""
    # YAML 프론트매터
    text = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)
    # 펜스 코드블록
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    return text


def to_plain(text: str) -> str:
    """마크다운 기호를 제거한 순수 본문."""
    t = strip_noise(text)
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", t)          # 이미지
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)      # 링크 → 텍스트만
    t = re.sub(r"^#{1,6}\s*", "", t, flags=re.M)        # 헤딩 기호
    t = re.sub(r"^\s*[-*+]\s+", "", t, flags=re.M)      # 리스트 기호
    t = re.sub(r"^\s*>\s?", "", t, flags=re.M)          # 인용 기호
    t = re.sub(r"[*_`~]", "", t)                        # 강조 기호
    t = re.sub(r"^\s*\|.*\|\s*$", "", t, flags=re.M)    # 표
    return t


def split_sentences(text: str):
    """줄 단위로 나눈 뒤 문장 종결부호로 재분할."""
    out = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        for s in re.split(r"(?<=[.!?。])\s+", line):
            s = s.strip()
            if s:
                out.append(s)
    return out


def check_style(text: str):
    """문체 위반 문장 목록을 반환."""
    violations = []
    for sent in split_sentences(text):
        # URL만 있는 줄은 건너뜀
        if sent.startswith("http"):
            continue
        for pattern, label in BANNED_ENDINGS:
            if re.search(pattern, sent):
                violations.append({"sentence": sent, "reason": label})
                break
    return violations


def check_hype(text: str):
    found = []
    for sent in split_sentences(text):
        for w in HYPE_WORDS:
            if w in sent:
                found.append({"sentence": sent, "word": w.strip()})
                break
    return found


def extract_intro(raw: str):
    """제목(# ...) 다음부터 첫 구분선까지가 소설 도입부다."""
    body = re.sub(r"\A---\n.*?\n---\n", "", raw, flags=re.S)
    m = re.search(r"^#\s+.*$", body, flags=re.M)
    if not m:
        return None
    after = body[m.end():]
    cut = after.find(DIVIDER)
    if cut == -1:
        return None
    return after[:cut].strip()


def check_intro(raw: str):
    """절대 규칙 11번 — 소설 도입부 존재와 500자 이내."""
    intro = extract_intro(raw)
    if intro is None:
        return {"ok": False, "chars": 0, "reason": "소설 도입부가 없다 (제목 다음 구분선까지가 도입부다)"}
    plain = to_plain(intro)
    n = len(plain.replace("\n", ""))
    if n == 0:
        return {"ok": False, "chars": 0, "reason": "소설 도입부가 비어 있다"}
    if n > MAX_INTRO_CHARS:
        return {"ok": False, "chars": n, "reason": f"{n - MAX_INTRO_CHARS}자 초과 — {MAX_INTRO_CHARS}자 이내로 줄일 것"}
    return {"ok": True, "chars": n, "reason": ""}


def check_checklist(raw: str):
    """절대 규칙 13번 — 체크리스트/점검표 절."""
    found = []
    for i, line in enumerate(raw.splitlines(), 1):
        s = line.strip()
        if re.match(r"^-\s*\[[ xX]\]", s):
            found.append({"line": i, "text": s[:70], "why": "체크박스 목록"})
            continue
        for kw in CHECKLIST_HEADINGS:
            if kw in s and len(s) <= 60:
                found.append({"line": i, "text": s[:70], "why": f"점검표 표현 '{kw}'"})
                break
    return found


def check_headings(raw: str):
    """STYLE 6번 — ## 머리글 금지 (글 제목 #는 허용)."""
    found = []
    body = re.sub(r"```.*?```", "", raw, flags=re.S)
    for i, line in enumerate(body.splitlines(), 1):
        if re.match(r"^#{2,6}\s+", line.strip()):
            found.append({"line": i, "text": line.strip()[:70]})
    return found


def check_stats(raw: str):
    """절대 규칙 12번 — 본문 통계 표지."""
    body = re.sub(r"\A---\n.*?\n---\n", "", raw, flags=re.S)
    body = re.sub(r"```.*?```", "", body, flags=re.S)
    found = []
    for line in body.splitlines():
        s = line.strip()
        if not s or s.startswith("http") or s.startswith(DIVIDER[:10]):
            continue
        for pattern, label in STAT_MARKERS:
            m = re.search(pattern, s)
            if m:
                found.append({"text": s[:70], "marker": m.group(0)[:24], "kind": label})
                break
    return found


def analyze(path: Path):
    raw = path.read_text(encoding="utf-8")
    plain = to_plain(raw)

    with_space = len(plain.replace("\n", ""))
    without_space = len(re.sub(r"\s", "", plain))

    violations = check_style(plain)
    hype = check_hype(plain)
    intro = check_intro(raw)
    checklist = check_checklist(raw)
    headings = check_headings(raw)
    stats = check_stats(raw)

    return {
        "file": str(path),
        "chars_with_space": with_space,
        "chars_without_space": without_space,
        "min_required": MIN_CHARS,
        "length_pass": with_space >= MIN_CHARS,
        "style_violations": violations,
        "style_pass": len(violations) == 0,
        "hype_warnings": hype,
        "intro": intro,
        "checklist_hits": checklist,
        "heading_hits": headings,
        "stat_hits": stats,
        "pass": (
            with_space >= MIN_CHARS
            and len(violations) == 0
            and intro["ok"]
            and len(checklist) == 0
            and len(headings) == 0
            and len(stats) == 0
        ),
    }


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    as_json = "--json" in sys.argv
    intro_only = "--intro" in sys.argv

    if not args:
        print("사용법: python3 scripts/count.py <파일경로> [--json] [--intro]", file=sys.stderr)
        return 2

    path = Path(args[0])
    if not path.is_file():
        print(f"파일을 찾을 수 없다: {path}", file=sys.stderr)
        return 2

    # --intro : novelist 전용. 소설 도입부만 재서 바로 끝낸다.
    if intro_only:
        raw = path.read_text(encoding="utf-8")
        ic = check_intro(raw)
        if as_json:
            print(json.dumps(ic, ensure_ascii=False, indent=2))
            return 0 if ic["ok"] else 1
        print("=" * 60)
        print(f"소설 도입부 검사 : {path}")
        print("=" * 60)
        print(f"공백 포함 글자수 : {ic['chars']:,}자   (상한 {MAX_INTRO_CHARS:,}자)")
        if ic["ok"]:
            print("판정             : 통과")
        else:
            print(f"판정             : ⛔ {ic['reason']}")
        intro_txt = extract_intro(raw)
        if intro_txt:
            iv = check_style(to_plain(intro_txt))
            print("-" * 60)
            if iv:
                print(f"문체 위반 : {len(iv)}건")
                for i, v in enumerate(iv, 1):
                    print(f"  {i:>2}. [{v['reason']}] {v['sentence'][:80]}")
            else:
                print("문체 판정        : 통과 (위반 0건)")
        print("=" * 60)
        print(f"최종 : {'PASS' if ic['ok'] else 'FAIL'}")
        print("=" * 60)
        return 0 if ic["ok"] else 1

    r = analyze(path)

    # 절대 규칙 10번 — 고정 맺음 문구
    raw_lines = [l.rstrip() for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    r["closing_line_ok"] = bool(raw_lines) and raw_lines[-1].strip() == CLOSING_LINE
    r["closing_line_found"] = raw_lines[-1].strip() if raw_lines else ""
    if not r["closing_line_ok"]:
        r["pass"] = False

    if as_json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if r["pass"] else 1

    print("=" * 60)
    print(f"파일: {r['file']}")
    print("=" * 60)
    print(f"공백 포함 글자수 : {r['chars_with_space']:,}자   (기준 {MIN_CHARS:,}자)")
    print(f"공백 제외 글자수 : {r['chars_without_space']:,}자")
    print(f"분량 판정        : {'통과' if r['length_pass'] else '미달 ' + str(MIN_CHARS - r['chars_with_space']) + '자 부족'}")
    print("-" * 60)

    if r["style_violations"]:
        print(f"문체 위반 : {len(r['style_violations'])}건 — 아래 문장을 '~이다'체로 고칠 것")
        for i, v in enumerate(r["style_violations"], 1):
            s = v["sentence"]
            s = s if len(s) <= 90 else s[:90] + "…"
            print(f"  {i:>2}. [{v['reason']}] {s}")
    else:
        print("문체 판정        : 통과 (위반 0건)")

    if r["hype_warnings"]:
        print("-" * 60)
        print(f"과장/단정 표현 경고 : {len(r['hype_warnings'])}건 (검토 권장)")
        for i, h in enumerate(r["hype_warnings"], 1):
            s = h["sentence"]
            s = s if len(s) <= 90 else s[:90] + "…"
            print(f"  {i:>2}. [{h['word']}] {s}")

    print("-" * 60)
    ic = r["intro"]
    if ic["ok"]:
        print(f"소설 도입부      : 통과 ({ic['chars']:,}자 / 상한 {MAX_INTRO_CHARS:,}자)")
    else:
        print(f"소설 도입부      : ⛔ {ic['reason']} — 절대 규칙 11번 위반")

    print("-" * 60)
    if r["checklist_hits"]:
        print(f"체크리스트 절    : ⛔ {len(r['checklist_hits'])}건 — 절대 규칙 13번 위반 (전부 지울 것)")
        for i, c in enumerate(r["checklist_hits"][:8], 1):
            print(f"  {i:>2}. {c['line']}행 [{c['why']}] {c['text']}")
        if len(r["checklist_hits"]) > 8:
            print(f"      ... 그 외 {len(r['checklist_hits']) - 8}건")
    else:
        print("체크리스트 절    : 통과 (0건)")

    print("-" * 60)
    if r["stat_hits"]:
        print(f"본문 통계 수치   : ⛔ {len(r['stat_hits'])}건 — 절대 규칙 12번 위반")
        print("   말로 바꾸거나 가상 예시로 대체할 것. 조사 수치는 notes에 남겨 둔다.")
        for i, s in enumerate(r["stat_hits"][:8], 1):
            print(f"  {i:>2}. [{s['kind']}: {s['marker']}] {s['text']}")
        if len(r["stat_hits"]) > 8:
            print(f"      ... 그 외 {len(r['stat_hits']) - 8}건")
    else:
        print("본문 통계 수치   : 통과 (0건)")

    print("-" * 60)
    if r["heading_hits"]:
        print(f"## 머리글        : ⛔ {len(r['heading_hits'])}건 — 구분선으로 바꿀 것 (STYLE 6번)")
        for i, h in enumerate(r["heading_hits"][:8], 1):
            print(f"  {i:>2}. {h['line']}행 {h['text']}")
        if len(r["heading_hits"]) > 8:
            print(f"      ... 그 외 {len(r['heading_hits']) - 8}건")
    else:
        print("## 머리글        : 통과 (0건)")

    print("-" * 60)
    if r["closing_line_ok"]:
        print("맺음 문구        : 통과")
    else:
        print("맺음 문구        : ⛔ 누락/변형 — 절대 규칙 10번 위반")
        print(f"   있어야 할 줄 : {CLOSING_LINE}")
        print(f"   실제 마지막 줄 : {r['closing_line_found'][:70]}")

    print("=" * 60)
    print(f"최종 : {'PASS' if r['pass'] else 'FAIL'}")
    print("=" * 60)
    return 0 if r["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
