#!/usr/bin/env python3
"""글자수 카운트 + 문체(~이다체) 위반 문장 검출.

사용법:
    python3 scripts/count.py posts/2026-08-13-example.md
    python3 scripts/count.py posts/2026-08-13-example.md --json

판정 기준:
    - 공백 포함 2000자 이상 (본문 기준, 프론트매터/코드블록 제외)
    - "~이다"체 위반 문장 0개
종료 코드:
    0 = 통과, 1 = 미달/위반, 2 = 파일 오류
"""

import json
import re
import sys
from pathlib import Path

MIN_CHARS = 2000

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


def analyze(path: Path):
    raw = path.read_text(encoding="utf-8")
    plain = to_plain(raw)

    with_space = len(plain.replace("\n", ""))
    without_space = len(re.sub(r"\s", "", plain))

    violations = check_style(plain)
    hype = check_hype(plain)

    return {
        "file": str(path),
        "chars_with_space": with_space,
        "chars_without_space": without_space,
        "min_required": MIN_CHARS,
        "length_pass": with_space >= MIN_CHARS,
        "style_violations": violations,
        "style_pass": len(violations) == 0,
        "hype_warnings": hype,
        "pass": with_space >= MIN_CHARS and len(violations) == 0,
    }


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    as_json = "--json" in sys.argv

    if not args:
        print("사용법: python3 scripts/count.py <파일경로> [--json]", file=sys.stderr)
        return 2

    path = Path(args[0])
    if not path.is_file():
        print(f"파일을 찾을 수 없다: {path}", file=sys.stderr)
        return 2

    r = analyze(path)

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

    print("=" * 60)
    print(f"최종 : {'PASS' if r['pass'] else 'FAIL'}")
    print("=" * 60)
    return 0 if r["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
