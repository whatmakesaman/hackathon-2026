"""스팸 문자 점수 분석기.

스팸/정상 문자 목록에서 단어별 스팸 가중치를 학습하고(train),
새 문자의 단어 가중치를 합산해 0~100점의 스팸 점수를 낸다(analyze).
파일이나 DB는 직접 읽지 않는다. 학습 데이터는 호출하는 쪽에서 넘겨준다.
"""
import math
import re
from collections import Counter

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
