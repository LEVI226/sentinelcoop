"""Reproducible synthetic experiment. NumPy required for training only."""
import csv
import hashlib
import json
import random
import time
from pathlib import Path

import numpy as np

from .engine import FEATURES, features

OUT = Path(__file__).parent / "artifacts"


def build_dataset():
    rng = random.Random(42)
    syllables = ["bala", "dori", "fena", "galo", "kemi", "loma", "nari", "palo", "sena", "tovi", "wena", "zari"]
    identities = [{"id": f"SYN-{i:04d}",
                   "name": " ".join(rng.choice(syllables).title() + rng.choice(syllables) for _ in range(2)),
                   "birth_date": f"{rng.randint(1960,2000)}-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}"}
                  for i in range(600)]
    rng.shuffle(identities)
    groups = {"train": identities[:360], "validation": identities[360:480], "test": identities[480:]}
    rows = []
    for split, people in groups.items():
        for person in people:
            for positive in (True, False):
                right = person if positive else rng.choice([p for p in people if p["id"] != person["id"]])
                left = dict(person)
                if positive:
                    mode = rng.randrange(4)
                    if mode == 0: left["name"] = " ".join(reversed(left["name"].split()))
                    if mode == 1: left["name"] = left["name"][:-1]
                    if mode == 2: left["name"] = left["name"].replace("a", "e", 1)
                elif rng.random() < 0.6:
                    left["name"] = right["name"]  # distinct identities: difficult homonym
                if not positive and rng.random() < 0.25:
                    left["birth_date"] = right["birth_date"]
                if rng.random() < 0.35:
                    left["birth_date"] = None
                if positive and rng.random() < 0.08:
                    left["birth_date"] = "1971-01-01"  # imperfect source data
                rows.append({"split": split, "left_id": person["id"], "right_id": right["id"],
                             "left_name": left["name"], "right_name": right["name"],
                             "left_dob": left["birth_date"], "right_dob": right["birth_date"],
                             "label": int(positive), "x": features(left, right)})
    return rows


def metrics(y, scores, threshold):
    pred = scores >= threshold
    tp = int(((y == 1) & pred).sum()); fp = int(((y == 0) & pred).sum())
    fn = int(((y == 1) & ~pred).sum()); tn = int(((y == 0) & ~pred).sum())
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precision": tp / max(tp + fp, 1), "recall": tp / max(tp + fn, 1),
            "false_positive_rate": fp / max(fp + tn, 1)}


def main():
    start = time.perf_counter()
    OUT.mkdir(exist_ok=True)
    rows = build_dataset()
    ids = {s: {r[k] for r in rows if r["split"] == s for k in ("left_id", "right_id")}
           for s in ("train", "validation", "test")}
    assert not ids["train"] & (ids["validation"] | ids["test"])
    assert not ids["validation"] & ids["test"]
    data = {}
    for split in ids:
        selected = [r for r in rows if r["split"] == split]
        data[split] = np.array([r["x"] for r in selected]), np.array([r["label"] for r in selected])
    x, y = data["train"]
    w = np.zeros(len(FEATURES)); bias = 0.0
    for _ in range(2500):
        p = 1 / (1 + np.exp(-np.clip(x @ w + bias, -40, 40)))
        w -= 0.15 * (x.T @ (p - y) / len(y) + 0.002 * w)
        bias -= 0.15 * float((p - y).mean())
    vx, vy = data["validation"]
    vs = 1 / (1 + np.exp(-np.clip(vx @ w + bias, -40, 40)))
    # Fixed validation recall target; no threshold selection from test.
    threshold = float(np.quantile(vs[vy == 1], 0.05, method="lower"))
    baseline_threshold = float(np.quantile(vx[vy == 1, 0], 0.05, method="lower"))
    tx, ty = data["test"]
    scores = 1 / (1 + np.exp(-np.clip(tx @ w + bias, -40, 40)))
    ml = metrics(ty, scores, threshold); baseline = metrics(ty, tx[:, 0], baseline_threshold)
    result = {"dataset": "synthetic-42-v1", "rows": {s: len(data[s][1]) for s in data},
              "identity_splits_disjoint": True, "validation_recall_target": 0.95,
              "test_model": ml, "test_baseline_wape": baseline,
              "model_threshold": threshold, "baseline_threshold": baseline_threshold,
              "promotion_observed": ml["recall"] >= baseline["recall"] and ml["fp"] < baseline["fp"],
              "limitations": ["Synthetic syllabic names, not representative of West African population",
                              "Balanced pair sample, not operational prevalence",
                              "Pair classification only; full retrieval recall not benchmarked",
                              "Not calibrated; not independently validated; no legal decisions"],
              "training_seconds": round(time.perf_counter() - start, 3)}
    model = {"version": "synthetic-logistic-42-v1", "feature_names": FEATURES,
             "weights": w.tolist(), "bias": bias, "threshold": threshold,
             "status": "EXPERIMENTAL_SYNTHETIC_ONLY", "training": {"seed": 42, "iterations": 2500,
             "learning_rate": 0.15, "l2": 0.002, "numpy": np.__version__}}
    (OUT / "model.json").write_text(json.dumps(model, indent=2), encoding="utf-8")
    (OUT / "metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    with (OUT / "pairs.csv").open("w", encoding="utf-8", newline="") as f:
        fields = [k for k in rows[0] if k != "x"]
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader()
        writer.writerows({k: r[k] for k in fields} for r in rows)
    manifest = {"seed": 42, "synthetic": True, "sha256": {
        name: hashlib.sha256((OUT / name).read_bytes()).hexdigest() for name in ("pairs.csv", "model.json")}}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
