"""스팸 문자 점수 분석기.

기존 스팸/정상 문자 데이터에서 단어별 스팸 가중치를 학습하고,
새 문자의 단어 가중치를 합산해 0~100점의 스팸 점수를 낸다.

사용법:
    python3 spam_checker.py "검사할 문자 내용"
"""
import math
import re
import sys
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
BIAS = -2.0  # 대부분의 문자는 정상이므로, 증거가 쌓여야 점수가 올라가게 하는 기준값
MAX_WEIGHT = 3.0  # 단어 하나가 점수를 혼자 좌우하지 않도록 제한
DANGER_SCORE = 70
CAUTION_SCORE = 40

URL_RE = re.compile(r"(https?://|www\.)\S+|\b\w+\.(com|net|top|xyz|cc|vip|shop|kr)\b", re.I)
WORD_RE = re.compile(r"[가-힣]+|[a-zA-Z]+|\d+")
URL_FEATURE = "<URL>"


def extract_features(text):
    """문자에서 분석할 단어(특징)를 뽑는다.

    한글은 조사/어미가 붙으므로("무료로", "당첨되셨습니다") 앞 두 글자만 쓴다.
    링크는 하나의 특징(<URL>)으로 본다.
    """
    features = set()
    if URL_RE.search(text):
        features.add(URL_FEATURE)
    text = URL_RE.sub(" ", text)
    for word in WORD_RE.findall(text):
        if word.isdigit():
            continue
        if re.match(r"[가-힣]", word):
            if len(word) >= 2:
                features.add(word[:2])
        else:
            features.add(word.lower())
    return features


def load_messages(path):
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip()]


def train(spam_messages, ham_messages):
    """단어별 스팸 가중치(log-odds)를 계산한다. 양수일수록 스팸에서 자주 나오는 단어."""
    spam_counts, ham_counts = Counter(), Counter()
    for msg in spam_messages:
        spam_counts.update(extract_features(msg))
    for msg in ham_messages:
        ham_counts.update(extract_features(msg))

    weights = {}
    for feature in set(spam_counts) | set(ham_counts):
        p_spam = (spam_counts[feature] + 1) / (len(spam_messages) + 2)
        p_ham = (ham_counts[feature] + 1) / (len(ham_messages) + 2)
        weight = math.log(p_spam / p_ham)
        weights[feature] = max(-MAX_WEIGHT, min(MAX_WEIGHT, weight))
    return weights


def analyze(text, weights):
    """새 문자를 분석해 점수, 등급, 판단 근거 단어를 반환한다."""
    hits = {f: weights[f] for f in extract_features(text) if f in weights}
    total = BIAS + sum(hits.values())
    score = round(100 / (1 + math.exp(-total)))
    if score >= DANGER_SCORE:
        level = "위험"
    elif score >= CAUTION_SCORE:
        level = "주의"
    else:
        level = "안전"
    reasons = sorted(
        ((f, w) for f, w in hits.items() if w > 0), key=lambda x: x[1], reverse=True
    )
    return {"score": score, "level": level, "reasons": reasons}


def load_default_weights():
    return train(load_messages(DATA_DIR / "spam.txt"), load_messages(DATA_DIR / "ham.txt"))


def main():
    if len(sys.argv) < 2:
        print('사용법: python3 spam_checker.py "검사할 문자 내용"')
        sys.exit(1)
    result = analyze(" ".join(sys.argv[1:]), load_default_weights())
    print(f"스팸 점수: {result['score']}점 ({result['level']})")
    if result["level"] != "안전" and result["reasons"]:
        words = ", ".join(f"'{w}'" for w, _ in result["reasons"][:5])
        print(f"의심 단어: {words}")


if __name__ == "__main__":
    main()
