from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import pandas as pd


def _task_type_for_target(series: pd.Series) -> str:
    if pd.api.types.is_numeric_dtype(series):
        unique = series.nunique(dropna=True)
        if unique <= 10:
            return "Classification"
        return "Regression"
    return "Classification"


def assess_modelling_readiness(
    df: pd.DataFrame,
    profile: Dict[str, Any],
    target_column: str | None,
) -> Dict[str, Any]:
    """Assess target-based modelling readiness."""
    if not target_column or target_column not in df.columns:
        return {
            "available": False,
            "message": "Select a target column to assess modelling readiness.",
        }

    target = df[target_column]
    task_type = _task_type_for_target(target)
    target_missing_pct = round((target.isna().sum() / max(len(target), 1)) * 100, 2)

    warnings: List[str] = []
    recommendations: List[str] = []

    if target_missing_pct > 0:
        warnings.append(f"Target column has {target_missing_pct}% missing values.")
        recommendations.append("Handle or remove missing target rows before modelling.")

    imbalance = None
    if task_type == "Classification":
        distribution = target.value_counts(normalize=True, dropna=True)
        if not distribution.empty:
            majority_pct = round(float(distribution.iloc[0] * 100), 2)
            imbalance = majority_pct
            if majority_pct >= 75:
                warnings.append(f"Target imbalance detected: majority class is {majority_pct}%.")
                recommendations.append("Use stratified train-test split and metrics such as F1-score, precision, and recall.")
            else:
                recommendations.append("Use stratified train-test split to preserve class distribution.")
    else:
        recommendations.append("Use regression metrics such as MAE, RMSE, and R-squared.")

    # Feature quality warnings
    profile_by_col = {c["column"]: c for c in profile.get("column_profiles", [])}
    risky_features = [
        c for c in profile.get("column_profiles", [])
        if c["column"] != target_column and (c["missing_pct"] >= 20 or c["outlier_pct"] >= 10 or c["is_constant"])
    ]

    for c in risky_features[:5]:
        warnings.append(f"Feature '{c['column']}' may need review: missing={c['missing_pct']}%, outliers={c['outlier_pct']}%.")

    # Leakage heuristic through high correlation with numeric target
    leakage_signals = []
    if pd.api.types.is_numeric_dtype(target):
        numeric_df = df.select_dtypes(include=[np.number])
        if target_column in numeric_df.columns:
            corr = numeric_df.corr(numeric_only=True)[target_column].drop(labels=[target_column], errors="ignore").abs()
            for feature, value in corr.sort_values(ascending=False).head(5).items():
                if pd.notna(value) and value >= 0.85:
                    leakage_signals.append({"feature": str(feature), "correlation": round(float(value), 3)})
                    warnings.append(f"Potential leakage or redundancy: '{feature}' is highly correlated with the target.")

    readiness_score = 100
    readiness_score -= min(30, target_missing_pct * 1.5)
    readiness_score -= min(25, len(risky_features) * 5)
    readiness_score -= min(20, len(leakage_signals) * 7)
    if imbalance and imbalance >= 75:
        readiness_score -= 10

    readiness_score = max(0, round(readiness_score, 1))

    if readiness_score >= 80:
        status = "Ready for baseline modelling"
    elif readiness_score >= 60:
        status = "Usable after cleaning"
    else:
        status = "Not ready for modelling"

    return {
        "available": True,
        "target_column": target_column,
        "task_type": task_type,
        "target_missing_pct": target_missing_pct,
        "target_imbalance_majority_pct": imbalance,
        "readiness_score": readiness_score,
        "status": status,
        "warnings": warnings,
        "recommendations": recommendations,
        "leakage_signals": leakage_signals,
    }
