"""스팸 문자 점수 분석기.

1) 학습 방식: 스팸/정상 문자 목록에서 단어별 스팸 가중치를 학습하고(train),
   새 문자의 단어 가중치를 합산해 0~100점의 스팸 점수를 낸다(analyze).
   학습 데이터는 호출하는 쪽에서 넘겨준다.
2) 규칙 방식(노션 기능 명세): rules.yaml 규칙으로 채점하고(analyze_message),
   결과 화면에 쓸 의심 유형·위험 신호·원문 위치·대응 안내를 함께 돌려준다.
   규칙 파일 검사: python analyzer.py --check [rules.yaml 경로]
"""
import math
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

import yaml

BIAS = -2.0  # 대부분의 문자는 정상이므로, 증거가 쌓여야 점수가 올라가게 하는 기준값
MAX_WEIGHT = 3.0  # 단어 하나가 점수를 혼자 좌우하지 않도록 제한
DANGER_SCORE = 70
CAUTION_SCORE = 40

URL_RE = re.compile(r"(https?://|www\.)\S+|\b\w+\.(com|net|top|xyz|cc|vip|shop|kr)\b", re.I)
WORD_RE = re.compile(r"[가-힣]+|[a-zA-Z]+|\d+")
WEB_TAG_RE = re.compile(r"\[\s*Web\s*발신\s*\]", re.I)  # 일반 문자에도 붙는 통신사 표시라 분석에서 뺀다
URL_FEATURE = "<URL>"
URL_LABEL = "링크 포함"


def extract_features(text):
    """문자에서 분석할 단어(특징)를 뽑는다. {특징: 사용자에게 보여줄 단어}를 반환한다.

    한글은 조사/어미가 붙으므로("무료로", "당첨되셨습니다") 앞 두 글자를 특징으로 쓰고,
    사용자에게는 문자에 실제로 적힌 단어를 보여준다.
    링크는 하나의 특징(<URL>)으로 본다.
    """
    features = {}
    text = WEB_TAG_RE.sub(" ", text)
    if URL_RE.search(text):
        features[URL_FEATURE] = URL_LABEL
    text = URL_RE.sub(" ", text)
    for word in WORD_RE.findall(text):
        if word.isdigit():
            continue
        if re.match(r"[가-힣]", word):
            if len(word) >= 2:
                features.setdefault(word[:2], word)
        else:
            features.setdefault(word.lower(), word)
    return features


def train(spam_messages, ham_messages):
    """단어별 스팸 가중치(log-odds)를 계산한다. 양수일수록 스팸에서 자주 나오는 단어."""
    spam_counts, ham_counts = Counter(), Counter()
    for msg in spam_messages:
        spam_counts.update(extract_features(msg).keys())
    for msg in ham_messages:
        ham_counts.update(extract_features(msg).keys())

    weights = {}
    for feature in set(spam_counts) | set(ham_counts):
        p_spam = (spam_counts[feature] + 1) / (len(spam_messages) + 2)
        p_ham = (ham_counts[feature] + 1) / (len(ham_messages) + 2)
        weight = math.log(p_spam / p_ham)
        weights[feature] = max(-MAX_WEIGHT, min(MAX_WEIGHT, weight))
    return weights


def analyze(text, weights):
    """새 문자를 분석한다.

    반환: {"score": 0~100 정수, "level": "안전"|"주의"|"위험", "reasons": [단어, ...]}
    reasons는 점수를 올린 단어를 영향이 큰 순서로 담고, 안전일 때는 빈 목록이다.
    """
    hits = {f: (weights[f], shown) for f, shown in extract_features(text).items() if f in weights}
    total = BIAS + sum(w for w, _ in hits.values())
    score = round(100 / (1 + math.exp(-total)))

    if score >= DANGER_SCORE:
        level = "위험"
    elif score >= CAUTION_SCORE:
        level = "주의"
    else:
        level = "안전"

    reasons = []
    if level != "안전":
        for w, shown in sorted(hits.values(), key=lambda x: x[0], reverse=True):
            if w > 0 and shown not in reasons:
                reasons.append(shown)
    return {"score": score, "level": level, "reasons": reasons}


# ── 규칙 방식 (rules.yaml) ─────────────────────────────────────

RULE_GROUPS = ("signals", "categories", "safe_signals")
DEFAULT_LEVELS = {"danger": 60, "caution": 30}
SAFE_CATEGORY = "정상"
OTHER_CATEGORY = "기타 의심"  # caution 이상인데 맞는 유형이 없을 때 (docs/API.md)
SEPARATOR_CHARS = set("-_.*·~/")  # '코-인-원'처럼 한글 사이에 끼워 필터를 피하는 문자
TEXT_ALIASES = {
    "캬톡": "카톡", "까톡": "카톡", "카똑": "카톡",
    "땔래": "텔레그램", "땔레": "텔레그램", "텔래": "텔레그램", "테레": "텔레그램",
    "사e트": "사이트",
}
ALIAS_RE = re.compile("|".join(map(re.escape, TEXT_ALIASES)), re.I)
DEFAULT_ADVICE = {
    "danger": ["문자 속 링크를 누르지 마세요", "발신 번호로 전화하거나 답장하지 마세요"],
    "caution": ["보낸 곳을 공식 앱이나 대표번호로 직접 확인하세요"],
    "safe": [],
}
IF_CLICKED = [
    "설치한 앱이 있다면 바로 삭제하고 비행기 모드로 바꾸세요",
    "입력한 비밀번호와 금융 인증서를 변경하세요",
    "송금했다면 즉시 은행 고객센터나 112에 지급정지를 요청하세요",
]


def load_rules(path):
    """rules.yaml을 읽어 정규식을 미리 컴파일한다. 서버 시작 때 한 번만 부른다.

    잘못된 규칙은 서버가 죽지 않도록 건너뛰고 경고 목록에 담는다.
    반환: (rules, warnings)
    """
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    rules = {"levels": {**DEFAULT_LEVELS, **(data.get("levels") or {})}}
    warnings = []
    for group in RULE_GROUPS:
        rules[group] = []
        for i, raw in enumerate(data.get(group) or []):
            try:
                rules[group].append(_compile_rule(raw))
            except (KeyError, TypeError, ValueError, re.error) as e:
                rule_id = raw.get("id", "?") if isinstance(raw, dict) else "?"
                warnings.append(f"{group}[{i}] {rule_id}: {e}")
    return rules, warnings


def _compile_rule(raw):
    if not isinstance(raw, dict):
        raise TypeError("규칙은 키: 값 형태여야 합니다")
    missing = [k for k in ("id", "name", "weight", "patterns") if k not in raw]
    if missing:
        raise KeyError(f"필수 필드 없음: {', '.join(missing)}")
    if not raw["patterns"]:
        raise ValueError("patterns가 비어 있습니다")
    return {
        **raw,
        "weight": int(raw["weight"]),
        "min_hits": int(raw.get("min_hits", 1)),
        "compiled": [re.compile(p, re.I) for p in raw["patterns"]],
    }


def _is_hangul(ch):
    return "가" <= ch <= "힣"


def normalize(text):
    """변형 표기를 편다. 전각→반각, 원문자→일반 문자(NFKC), 한글 사이 구분자 제거.

    반환: (정리한 문장, 정리한 문장의 각 글자가 원문 몇 번째 글자인지 담은 목록)
    예: "코-인-원" → "코인원"
    """
    chars, index = [], []
    for i, ch in enumerate(text):
        if ch in SEPARATOR_CHARS and 0 < i < len(text) - 1 and _is_hangul(text[i - 1]) and _is_hangul(text[i + 1]):
            continue
        for out in unicodedata.normalize("NFKC", ch):
            chars.append("." if out in "。｡" else out)
            index.append(i)
    normalized = "".join(chars)
    # 주소 구분자 주변 공백만 제거해 뒤의 일반 문장과 붙지 않게 한다.
    for pattern in (
        r"\bhttps?\s*:\s*/\s*/\s*(?=[a-z0-9])",
        r"\b(?:https?://|www\.)[a-z0-9-]+(?:\s*\.\s*[a-z0-9-]+)+",
    ):
        gaps = {i for match in re.finditer(pattern, normalized, re.I)
                for i in range(match.start(), match.end()) if normalized[i].isspace()}
        if gaps:
            index = [pos for i, pos in enumerate(index) if i not in gaps]
            normalized = "".join(ch for i, ch in enumerate(normalized) if i not in gaps)
    # 길이가 달라지는 별칭도 원문 위치를 보존해 하이라이트가 어긋나지 않게 한다.
    for match in reversed(list(ALIAS_RE.finditer(normalized))):
        replacement = TEXT_ALIASES[match.group().casefold()]
        positions = index[match.start():match.end()]
        index[match.start():match.end()] = [
            positions[j * len(positions) // len(replacement)] for j in range(len(replacement))
        ]
        normalized = normalized[:match.start()] + replacement + normalized[match.end():]
    return normalized, index


def _find(pattern, text, normalized, index):
    """원문에서 먼저 찾고, 없으면 정리한 문장에서 찾아 원문 위치로 바꾼다. 반환: (start, end) 또는 None"""
    m = pattern.search(text)
    if m and m.end() > m.start():
        return m.start(), m.end()
    m = pattern.search(normalized)
    if m and m.end() > m.start():
        return index[m.start()], index[m.end() - 1] + 1
    return None


def _level(score, levels):
    if score >= levels["danger"]:
        return "danger"
    if score >= levels["caution"]:
        return "caution"
    return "safe"


def analyze_message(text, rules):
    """rules.yaml 규칙으로 문자를 채점한다.

    - 규칙 하나는 패턴이 여러 개 맞아도 weight를 한 번만 더한다. 점수는 0~100.
    - categories는 서로 다른 패턴이 min_hits개 이상 맞아야 해당 유형이 된다.
    - 의심 유형은 규칙의 category 값별로 weight를 합해 가장 큰 것을 고른다.
    - safe_signals는 점수만 깎고 위험 신호 목록에는 넣지 않는다.
    - signals는 공통 신호(링크 등)를 먼저, 유형 신호를 뒤에 둔다. 알림 문구가 "유형 · 첫 신호"라서
      첫 신호가 유형과 겹치지 않게 하려는 것이다.
    - start/end는 원문 글자(코드포인트) 기준이라 프론트의 Array.from 위치와 맞는다.
    반환: {"text", "score", "level", "category", "signals", "advice", "if_clicked"} (docs/API.md의 Result)
    """
    normalized, index = normalize(text)
    total, matched, signals_by_group = 0, [], {"signals": [], "categories": []}
    for group in RULE_GROUPS:
        for rule in rules[group]:
            spans = [s for s in (_find(p, text, normalized, index) for p in rule["compiled"]) if s]
            need = rule["min_hits"] if group == "categories" else 1
            if len(spans) < need:
                continue
            total += rule["weight"]
            matched.append(rule)
            if group != "safe_signals":
                start, end = spans[0]
                signals_by_group[group].append({
                    "rule_id": rule["id"],
                    "type": rule["name"],
                    "detail": text[start:end],
                    "weight": rule["weight"],
                    "explain": rule.get("description", ""),
                    "start": start,
                    "end": end,
                })

    score = max(0, min(100, total))
    level = _level(score, rules["levels"])
    category = _pick_category(matched, level)
    advice_rules = [r for r in matched if r.get("category") == category and r.get("advice")]
    top = max(advice_rules, key=lambda r: r["weight"]) if advice_rules and level != "safe" else None
    advice = ([top["advice"]] if top else []) + DEFAULT_ADVICE[level]
    if_clicked = [] if level == "safe" else (top or {}).get("if_clicked") or IF_CLICKED
    signals = [s for group in ("signals", "categories")
               for s in sorted(signals_by_group[group], key=lambda s: s["weight"], reverse=True)]
    return {
        "text": text,
        "score": score,
        "level": level,
        "category": category,
        "signals": signals,
        "advice": advice,
        "if_clicked": if_clicked,
    }


def _pick_category(matched, level):
    if level == "safe":
        return SAFE_CATEGORY
    weights = Counter()
    for rule in matched:
        if rule.get("category"):
            weights[rule["category"]] += rule["weight"]
    return weights.most_common(1)[0][0] if weights else OTHER_CATEGORY


def check_rules(path):
    """rules.yaml 오류를 출력한다. 규칙 담당자가 push 전에 실행한다. 오류가 있으면 1을 돌려준다."""
    rules, warnings = load_rules(path)
    for w in warnings:
        print(f"[오류] {w}")
    count = sum(len(rules[g]) for g in RULE_GROUPS)
    print(f"정상 규칙 {count}개, 오류 {len(warnings)}개 (위험 {rules['levels']['danger']}점~, 주의 {rules['levels']['caution']}점~)")
    return 1 if warnings else 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--check"]
    if "--check" not in sys.argv:
        print("사용법: python analyzer.py --check [rules.yaml 경로]")
        sys.exit(2)
    sys.exit(check_rules(args[0] if args else Path(__file__).resolve().parent.parent / "rules.yaml"))
