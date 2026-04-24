from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


RANDOM_SEED = 42
DATA_PATH = Path("data/credit_scoring_dataset.csv")
ARTIFACT_DIR = Path("artifacts")

BASE_FEATURES = [
    "age",
    "monthly_income",
    "employment_years",
    "loan_amount",
    "loan_term_months",
    "interest_rate",
    "past_due_30d",
    "inquiries_6m",
]


def add_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Create optional engineered features.

    The final selected model may still use only BASE_FEATURES if validation
    quality is better. The UI uses the feature list stored in scoring_model.json.
    """
    x = frame[BASE_FEATURES].copy()
    income = x["monthly_income"].clip(lower=1)
    term = x["loan_term_months"].clip(lower=1)

    x["loan_to_annual_income"] = x["loan_amount"] / (income * 12)
    x["monthly_payment_to_income"] = (x["loan_amount"] / term) / income
    x["risk_events"] = x["past_due_30d"] + x["inquiries_6m"]
    x["employment_to_age"] = x["employment_years"] / (x["age"].clip(lower=19) - 18)
    x["income_per_loan_amount"] = income / x["loan_amount"].clip(lower=1)

    return x


def stratified_split(y: np.ndarray, test_size: float = 0.2, seed: int = 42) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    train_idx: list[int] = []
    test_idx: list[int] = []

    for cls in np.unique(y):
        idx = np.where(y == cls)[0]
        rng.shuffle(idx)
        n_test = int(round(len(idx) * test_size))
        test_idx.extend(idx[:n_test].tolist())
        train_idx.extend(idx[n_test:].tolist())

    rng.shuffle(train_idx)
    rng.shuffle(test_idx)
    return np.asarray(train_idx), np.asarray(test_idx)


def sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))


def fit_standardizer(x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mu = x.mean(axis=0)
    sd = x.std(axis=0)
    sd = np.where(sd < 1e-12, 1.0, sd)
    return mu, sd


def transform(x: np.ndarray, mu: np.ndarray, sd: np.ndarray) -> np.ndarray:
    return (x - mu) / sd


def fit_logreg_newton(
    x: np.ndarray,
    y: np.ndarray,
    *,
    l2: float = 0.001,
    pos_weight: float = 1.0,
    max_iter: int = 80,
    tol: float = 1e-8,
) -> np.ndarray:
    """L2-regularized logistic regression trained with Newton updates.

    No scikit-learn dependency is required, so the whole project is lightweight.
    Intercept is not regularized.
    """
    n, d = x.shape
    xb = np.column_stack([np.ones(n), x])
    w = np.zeros(d + 1)
    sample_weight = np.where(y == 1, pos_weight, 1.0).astype(float)

    reg = np.eye(d + 1)
    reg[0, 0] = 0.0

    for _ in range(max_iter):
        p = sigmoid(xb @ w)
        grad = (xb.T @ (sample_weight * (p - y))) / n + l2 * (reg @ w)
        r = sample_weight * p * (1.0 - p)
        hessian = (xb.T @ (xb * r[:, None])) / n + l2 * reg + np.eye(d + 1) * 1e-9

        try:
            step = np.linalg.solve(hessian, grad)
        except np.linalg.LinAlgError:
            step = np.linalg.pinv(hessian) @ grad

        w_next = w - step
        if np.linalg.norm(w_next - w) < tol:
            w = w_next
            break
        w = w_next

    return w


def predict_proba(x_scaled: np.ndarray, w: np.ndarray) -> np.ndarray:
    xb = np.column_stack([np.ones(len(x_scaled)), x_scaled])
    return sigmoid(xb @ w)


def roc_auc(y_true: np.ndarray, score: np.ndarray) -> float:
    y_true = np.asarray(y_true).astype(int)
    score = np.asarray(score)

    order = np.argsort(score)
    ranks = np.empty_like(order, dtype=float)
    ranks[order] = np.arange(1, len(score) + 1)

    # Average ranks for ties.
    _, inv, counts = np.unique(score, return_inverse=True, return_counts=True)
    if np.any(counts > 1):
        rank_sums = np.bincount(inv, weights=ranks)
        ranks = (rank_sums / counts)[inv]

    n_pos = int(y_true.sum())
    n_neg = int(len(y_true) - n_pos)
    if n_pos == 0 or n_neg == 0:
        return float("nan")

    return float((ranks[y_true == 1].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))


def pr_auc(y_true: np.ndarray, score: np.ndarray) -> float:
    """Average precision / area under precision-recall curve."""
    y_true = np.asarray(y_true).astype(int)
    order = np.argsort(-np.asarray(score))
    yt = y_true[order]

    tp = np.cumsum(yt)
    fp = np.cumsum(1 - yt)
    precision = tp / np.maximum(tp + fp, 1)

    return float((precision * yt).sum() / max(int(yt.sum()), 1))


def threshold_metrics(y_true: np.ndarray, p_default: np.ndarray, threshold: float) -> dict:
    y_true = np.asarray(y_true).astype(int)
    pred_default = (p_default >= threshold).astype(int)

    tn = int(((pred_default == 0) & (y_true == 0)).sum())
    fp = int(((pred_default == 1) & (y_true == 0)).sum())
    fn = int(((pred_default == 0) & (y_true == 1)).sum())
    tp = int(((pred_default == 1) & (y_true == 1)).sum())

    approved = pred_default == 0
    approval_rate = float(approved.mean())
    default_rate_approved = float(y_true[approved].mean()) if approved.any() else None

    return {
        "threshold": float(threshold),
        "accuracy": float((pred_default == y_true).mean()),
        "approval_rate": approval_rate,
        "decline_rate": float(1.0 - approval_rate),
        "default_rate_approved": default_rate_approved,
        "recall_default": float(tp / max(tp + fn, 1)),
        "precision_default": float(tp / max(tp + fp, 1)),
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "tp": tp,
    }


def model_matrix(frame: pd.DataFrame, feature_set_name: str, selected_columns: list[str]) -> np.ndarray:
    if feature_set_name.startswith("engineered"):
        source = add_features(frame)
    else:
        source = frame[BASE_FEATURES].copy()
    return source[selected_columns].to_numpy(dtype=float)


def main() -> None:
    ARTIFACT_DIR.mkdir(exist_ok=True)

    df = pd.read_csv(DATA_PATH)
    y_all = df["target"].to_numpy(dtype=int)

    train_idx, test_idx = stratified_split(y_all, test_size=0.20, seed=RANDOM_SEED)
    train_df = df.iloc[train_idx].reset_index(drop=True)
    test_df = df.iloc[test_idx].reset_index(drop=True)

    sub_idx, val_idx = stratified_split(train_df["target"].to_numpy(dtype=int), test_size=0.25, seed=RANDOM_SEED + 1)
    subtrain_df = train_df.iloc[sub_idx].reset_index(drop=True)
    val_df = train_df.iloc[val_idx].reset_index(drop=True)

    feature_sets = {
        "baseline_8_features": BASE_FEATURES,
        "engineered_13_features": list(add_features(df).columns),
    }
    l2_values = [0.001, 0.01, 0.05, 0.1, 0.3, 1.0]
    bad = int(subtrain_df["target"].sum())
    good = int(len(subtrain_df) - bad)
    balanced_pos_weight = good / max(bad, 1)
    pos_weights = [1.0, 1.5, 2.0, balanced_pos_weight]

    search_rows: list[dict] = []
    candidate_cache: dict[tuple[str, float, float], dict] = {}

    for fs_name, columns in feature_sets.items():
        x_sub = model_matrix(subtrain_df, fs_name, columns)
        x_val = model_matrix(val_df, fs_name, columns)
        y_sub = subtrain_df["target"].to_numpy(dtype=int)
        y_val = val_df["target"].to_numpy(dtype=int)

        mu, sd = fit_standardizer(x_sub)
        x_sub_scaled = transform(x_sub, mu, sd)
        x_val_scaled = transform(x_val, mu, sd)

        for l2 in l2_values:
            for pos_weight in pos_weights:
                w = fit_logreg_newton(x_sub_scaled, y_sub, l2=l2, pos_weight=float(pos_weight))
                p_val = predict_proba(x_val_scaled, w)
                row = {
                    "feature_set": fs_name,
                    "l2": float(l2),
                    "pos_weight": float(pos_weight),
                    "roc_auc": roc_auc(y_val, p_val),
                    "pr_auc": pr_auc(y_val, p_val),
                }
                search_rows.append(row)
                candidate_cache[(fs_name, float(l2), float(pos_weight))] = {
                    "columns": columns,
                    "mu": mu,
                    "sd": sd,
                    "w": w,
                    "p_val": p_val,
                }

    search_df = pd.DataFrame(search_rows).sort_values(["roc_auc", "pr_auc"], ascending=False)
    search_df.to_csv(ARTIFACT_DIR / "model_search_results.csv", index=False)
    best = search_df.iloc[0].to_dict()

    best_fs = str(best["feature_set"])
    best_l2 = float(best["l2"])
    best_pos_weight = float(best["pos_weight"])
    selected_columns = feature_sets[best_fs]

    # Select threshold on validation data.
    best_candidate = candidate_cache[(best_fs, best_l2, best_pos_weight)]
    y_val = val_df["target"].to_numpy(dtype=int)
    p_val = best_candidate["p_val"]

    threshold_grid = np.round(np.arange(0.05, 0.951, 0.01), 2)
    val_threshold_df = pd.DataFrame([threshold_metrics(y_val, p_val, t) for t in threshold_grid])

    # Business rule: keep actual bad-rate among approved around 10-11% on validation,
    # while maximizing approval rate. The cap is intentionally strict; a 500-row
    # dataset makes exact 10.0% unstable, so 11% is used.
    risk_cap = 0.11
    eligible = val_threshold_df[
        (val_threshold_df["approval_rate"] > 0)
        & (val_threshold_df["default_rate_approved"].fillna(1.0) <= risk_cap)
    ]

    if len(eligible):
        chosen = eligible.sort_values(["approval_rate", "threshold"], ascending=[False, False]).iloc[0]
        selected_threshold = float(chosen["threshold"])
        threshold_rule = (
            "validation: максимальная доля одобрений при bad-rate среди одобренных "
            f"<= {risk_cap:.0%}"
        )
    else:
        val_threshold_df["specificity"] = val_threshold_df["tn"] / (val_threshold_df["tn"] + val_threshold_df["fp"]).replace(0, np.nan)
        val_threshold_df["balanced_score"] = val_threshold_df["recall_default"] + val_threshold_df["specificity"]
        chosen = val_threshold_df.sort_values("balanced_score", ascending=False).iloc[0]
        selected_threshold = float(chosen["threshold"])
        threshold_rule = "validation: максимум recall(default) + specificity"

    val_threshold_df.to_csv(ARTIFACT_DIR / "validation_threshold_table.csv", index=False)

    # Refit final model on full train, then evaluate once on holdout test.
    x_train = model_matrix(train_df, best_fs, selected_columns)
    y_train = train_df["target"].to_numpy(dtype=int)
    x_test = model_matrix(test_df, best_fs, selected_columns)
    y_test = test_df["target"].to_numpy(dtype=int)

    mu, sd = fit_standardizer(x_train)
    x_train_scaled = transform(x_train, mu, sd)
    x_test_scaled = transform(x_test, mu, sd)
    w = fit_logreg_newton(x_train_scaled, y_train, l2=best_l2, pos_weight=best_pos_weight)

    p_test = predict_proba(x_test_scaled, w)
    p_train = predict_proba(x_train_scaled, w)

    holdout_threshold_df = pd.DataFrame([threshold_metrics(y_test, p_test, t) for t in threshold_grid])
    holdout_threshold_df.to_csv(ARTIFACT_DIR / "threshold_table.csv", index=False)

    selected_metrics = threshold_metrics(y_test, p_test, selected_threshold)
    at_050_metrics = threshold_metrics(y_test, p_test, 0.50)

    metrics = {
        "model": {
            "name": "L2 Logistic Regression",
            "implementation": "NumPy Newton solver",
            "feature_set": best_fs,
            "feature_columns": selected_columns,
            "l2": best_l2,
            "pos_weight": best_pos_weight,
        },
        "split": {
            "random_seed": RANDOM_SEED,
            "train_size": int(len(train_df)),
            "holdout_size": int(len(test_df)),
            "target_rate_train": float(y_train.mean()),
            "target_rate_holdout": float(y_test.mean()),
        },
        "quality_holdout": {
            "roc_auc": roc_auc(y_test, p_test),
            "pr_auc": pr_auc(y_test, p_test),
            "accuracy_at_selected_threshold": selected_metrics["accuracy"],
            "accuracy_at_0_50": at_050_metrics["accuracy"],
        },
        "threshold": {
            "selected_threshold": selected_threshold,
            "selection_rule": threshold_rule,
            "selected_threshold_metrics_holdout": selected_metrics,
            "threshold_0_50_metrics_holdout": at_050_metrics,
        },
        "notes": [
            "Решение использует P(default). Клиент считается default, если P(default) >= threshold.",
            "Более низкий threshold уменьшает риск среди одобренных, но снижает долю одобрений.",
            "Метрики рассчитаны на holdout-выборке 20%; из-за 500 строк значения могут быть нестабильны.",
        ],
    }
    with open(ARTIFACT_DIR / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    defaults = df[BASE_FEATURES].median(numeric_only=True).to_dict()
    mins = df[BASE_FEATURES].min(numeric_only=True).to_dict()
    maxs = df[BASE_FEATURES].max(numeric_only=True).to_dict()

    model_artifact = {
        "model_type": "l2_logistic_regression_numpy",
        "target": {"positive_class": 1, "positive_class_name": "default"},
        "base_feature_columns": BASE_FEATURES,
        "feature_set": best_fs,
        "feature_columns": selected_columns,
        "coefficients": {
            "intercept": float(w[0]),
            "features": {col: float(coef) for col, coef in zip(selected_columns, w[1:])},
        },
        "standardization": {
            "mean": {col: float(v) for col, v in zip(selected_columns, mu)},
            "std": {col: float(v) for col, v in zip(selected_columns, sd)},
        },
        "threshold": selected_threshold,
        "training_params": {
            "l2": best_l2,
            "pos_weight": best_pos_weight,
            "random_seed": RANDOM_SEED,
        },
        "input_defaults": {k: float(v) for k, v in defaults.items()},
        "input_min": {k: float(v) for k, v in mins.items()},
        "input_max": {k: float(v) for k, v in maxs.items()},
    }
    with open(ARTIFACT_DIR / "scoring_model.json", "w", encoding="utf-8") as f:
        json.dump(model_artifact, f, ensure_ascii=False, indent=2)

    print("Training complete.")
    print(f"Selected model: {metrics['model']['name']} / {best_fs}")
    print(f"Selected threshold: {selected_threshold:.2f}")
    print(f"ROC-AUC holdout: {metrics['quality_holdout']['roc_auc']:.4f}")
    print(f"PR-AUC holdout: {metrics['quality_holdout']['pr_auc']:.4f}")
    print(f"Accuracy holdout @threshold: {metrics['quality_holdout']['accuracy_at_selected_threshold']:.4f}")
    print(f"Approval rate @threshold: {selected_metrics['approval_rate']:.4f}")
    print(f"Default rate among approved @threshold: {selected_metrics['default_rate_approved']:.4f}")


if __name__ == "__main__":
    main()
