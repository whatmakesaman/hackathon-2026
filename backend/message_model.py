"""문자 2~4-gram 나이브 베이즈 학습·로딩과 API 분석 연결.

학습: python backend/message_model.py --train
모델 점수는 사기 확률이 아니며, CSV는 서버 시작이나 요청 처리 때 읽지 않는다.
"""
import argparse
import csv
import gzip
import hashlib
import inspect
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

from analyzer import (
    DEFAULT_ADVICE, IF_CLICKED, OTHER_CATEGORY, SAFE_CATEGORY,
    SEPARATOR_CHARS, TEXT_ALIASES, analyze_message, normalize,
)

ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = Path(__file__).with_name("message_model.json.gz")


def normalization_hash():
    configuration = inspect.getsource(normalize) + json.dumps(
        [sorted(SEPARATOR_CHARS), TEXT_ALIASES], sort_keys=True, ensure_ascii=False,
    )
    return hashlib.sha256(configuration.encode("utf-8")).hexdigest()


def canonical_text(text):
    return re.sub(r"\d+", "#", re.sub(r"\s+", "", normalize(text)[0].casefold()))


def extract_counts(text):
    text = canonical_text(text)
    return Counter(text[i:i + n] for n in (2, 3, 4) for i in range(len(text) - n + 1))


def fit_model(messages):
    counts = [Counter(), Counter()]
    documents = Counter()
    for text, label in messages:
        counts[label].update(extract_counts(text))
        documents[label] += 1
    vocabulary = set(counts[0]) | set(counts[1])
    if not vocabulary or not documents[0] or not documents[1]:
        raise ValueError("학습에는 일반 문자와 스미싱 문자가 모두 필요합니다.")
    denominators = [sum(count.values()) + len(vocabulary) for count in counts]
    return {
        "version": 1,
        "normalization_hash": normalization_hash(),
        "prior": math.log(documents[1] / documents[0]),
        "unknown_weight": math.log(denominators[0] / denominators[1]),
        "weights": {
            token: math.log((counts[1][token] + 1) / denominators[1])
            - math.log((counts[0][token] + 1) / denominators[0])
            for token in vocabulary
        },
    }


def raw_score(text, model):
    return model["prior"] + sum(
        count * model["weights"].get(token, model["unknown_weight"])
        for token, count in extract_counts(text).items()
    )


def calibrate_model(model, messages):
    negatives = sorted((raw_score(text, model) for text, label in messages if label == 0), reverse=True)
    if not negatives:
        raise ValueError("경고 기준 설정에는 일반 문자 검증 자료가 필요합니다.")
    # 시험용 정답은 사용하지 않고 검증용 일반 문자의 상위 점수로 경계를 정한다.
    model["caution_threshold"] = max(0.0, negatives[int(len(negatives) * 0.01)] + 1e-8)
    model["danger_threshold"] = max(
        negatives[int(len(negatives) * 0.001)] + 1e-8,
        model["caution_threshold"] + 1.0,
    )


def predict_score(text, model, levels):
    caution, danger = levels["caution"], levels["danger"]
    if not 0 < caution < danger < 100:
        raise ValueError("점수 기준은 0 < 주의 < 위험 < 100이어야 합니다.")
    margin = raw_score(text, model)
    low, high = model["caution_threshold"], model["danger_threshold"]
    scale = (high - low) / (danger - caution)
    if margin >= high:
        return min(100, danger + int((margin - high) / scale)), "danger"
    if margin >= low:
        return min(danger - 1, caution + int((margin - low) / scale)), "caution"
    return max(0, caution - 1 - int((low - margin) / scale)), "safe"


def load_model(path=MODEL_PATH):
    try:
        with gzip.open(path, "rt", encoding="utf-8") as source:
            model = json.load(source)
    except (OSError, ValueError) as error:
        raise RuntimeError("학습 모델을 읽을 수 없습니다. python backend/message_model.py --train 으로 생성하세요.") from error
    if model.get("version") != 1 or model.get("normalization_hash") != normalization_hash():
        raise ValueError("모델 버전 또는 문자 정규화가 달라졌습니다. 모델을 다시 학습하세요.")
    numbers = [model[key] for key in ("prior", "unknown_weight", "caution_threshold", "danger_threshold")]
    weights = model["weights"]
    if not weights or not all(math.isfinite(value) for value in [*numbers, *weights.values()]):
        raise ValueError("모델 가중치가 올바르지 않습니다.")
    if model["danger_threshold"] <= model["caution_threshold"]:
        raise ValueError("모델의 주의·위험 경계값이 올바르지 않습니다.")
    return model


def analyze_with_model(text, rules, model):
    reference = analyze_message(text, rules)
    score, level = predict_score(text, model, rules["levels"])
    if level == "safe":
        return {**reference, "score": score, "level": level, "category": SAFE_CATEGORY,
                "signals": [], "advice": [], "if_clicked": []}
    # 모델은 경고 여부만 결정한다. 등급은 규칙 근거로 나누고, 모델 단독 탐지도 주의로 남긴다.
    score = max(rules["levels"]["caution"], reference["score"])
    level = "danger" if score >= rules["levels"]["danger"] else "caution"
    category = reference["category"] if reference["category"] != SAFE_CATEGORY else OTHER_CATEGORY
    explanation = {
        "rule_id": "model_pattern", "type": "학습 패턴", "detail": "학습된 문자 패턴상 확인이 필요합니다.",
        "weight": 0, "explain": "모델이 의심 문자로 분류했습니다. 위험 신호 점수는 규칙 점수를 사용하며, 규칙 근거가 부족해도 최소 주의 점수로 경고합니다. 사기 확률은 아닙니다.",
        "start": None, "end": None,
    }
    signals = [explanation] + [
        {**signal, "explain": "규칙 근거: " + signal["explain"]}
        for signal in reference["signals"]
    ]
    specific_advice = [item for item in reference["advice"] if item not in DEFAULT_ADVICE[reference["level"]]]
    return {**reference, "score": score, "level": level, "category": category,
            "signals": signals, "advice": specific_advice + DEFAULT_ADVICE[level],
            "if_clicked": reference["if_clicked"] or IF_CLICKED}


def train_csv(csv_path, output_path=MODEL_PATH):
    groups = defaultdict(list)
    excluded = Counter()
    raw = Path(csv_path).read_bytes()
    with Path(csv_path).open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if not {"content", "class"} <= set(reader.fieldnames or []):
            raise ValueError("CSV에 content와 class 열이 필요합니다.")
        for row in reader:
            if row["class"] not in {"1", "2"}:
                excluded[row["class"]] += 1
                continue
            text = row["content"]
            if not text.strip() or len(text) > 2000:
                raise ValueError("CSV에 비어 있거나 2000자를 넘는 문자가 있습니다.")
            groups[canonical_text(text)].append((text, int(row["class"] == "2")))
    splits = {"train": [], "validation": [], "test": []}
    group_counts = Counter()
    for key, items in groups.items():
        bucket = int(hashlib.sha256(key.encode()).hexdigest()[:8], 16) % 10
        split = "train" if bucket < 7 else ("validation" if bucket == 7 else "test")
        group_counts[split] += 1
        if split == "train":
            # 같은 형태의 반복 문자가 학습 횟수만 부풀리지 않게 한다. 라벨은 바꾸지 않는다.
            unique = {label: text for text, label in items}
            splits[split].extend((text, label) for label, text in unique.items())
        else:
            splits[split].extend(items)
    held_out = {canonical_text(text) for name in ("validation", "test") for text, _ in splits[name]}
    training_labels = {canonical_text(text): label for text, label in splits["train"]}
    normal_sms = []
    normal_sms_path = ROOT / "data" / "ham.txt"
    for text in normal_sms_path.read_text(encoding="utf-8").splitlines():
        text = text.strip()
        if not text:
            continue
        key = canonical_text(text)
        if key in held_out:
            continue
        if training_labels.get(key) == 1:
            raise ValueError("정상 문자 보충 자료가 class=2 정답과 충돌합니다.")
        if key not in training_labels:
            normal_sms.append((text, 0))
            training_labels[key] = 0
    # CSV의 일반 자료는 댓글이 많아 SMS 예시를 가중 학습한다. 시험 자료에는 넣지 않는다.
    model = fit_model(splits["train"] + normal_sms * 5)
    calibrate_model(model, splits["validation"])
    counts = {"normal": Counter(), "spam": Counter()}
    for text, label in splits["test"]:
        _, level = predict_score(text, model, {"caution": 20, "danger": 60})
        counts["spam" if label else "normal"][level] += 1
    normal_total, spam_total = sum(counts["normal"].values()), sum(counts["spam"].values())
    if not normal_total or not spam_total:
        raise ValueError("시험 자료에 일반 문자와 스미싱 문자가 모두 필요합니다.")
    metrics = {
        "normal_total": normal_total, "spam_total": spam_total,
        "false_positives": normal_total - counts["normal"]["safe"],
        "missed_spam": counts["spam"]["safe"],
        "detection_percent": round(100 * (1 - counts["spam"]["safe"] / spam_total), 2),
        "false_positive_percent": round(100 * (1 - counts["normal"]["safe"] / normal_total), 2),
        "level_counts": counts,
    }
    model["training"] = {
        "source_sha256": hashlib.sha256(raw).hexdigest(), "group_counts": group_counts,
        "train_messages": len(splits["train"]), "excluded_labels": excluded,
        "normal_sms_training_samples": len(normal_sms), "normal_sms_weight": 5,
        "normal_sms_source_sha256": hashlib.sha256(normal_sms_path.read_bytes()).hexdigest(),
        "test_metrics": metrics,
    }
    output_path = Path(output_path)
    encoded = json.dumps(model, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    # 읽는 중인 서버가 반쪽짜리 모델을 보지 않도록 완성 후 교체한다.
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary.write_bytes(gzip.compress(encoded, mtime=0))
    temporary.replace(output_path)
    return model


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", action="store_true", help="CSV로 학습하고 모델 저장")
    parser.add_argument("--csv", type=Path, default=ROOT / "data" / "lgaidataset.csv")
    args = parser.parse_args()
    if not args.train:
        parser.error("학습하려면 --train을 지정하세요.")
    trained = train_csv(args.csv)
    print(json.dumps(trained["training"], ensure_ascii=False, indent=2))
    print(f"모델 저장 완료: {MODEL_PATH}")
