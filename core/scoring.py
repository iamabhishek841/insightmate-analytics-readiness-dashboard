from __future__ import annotations

from typing import Any, Dict, List


def _severity_from_score(score: float) -> str:
    if score >= 70:
        return "High"
    if score >= 40:
        return "Medium"
    return "Low"


def calculate_quality_score(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate a rule-based overall data quality score out of 100."""
    column_profiles = profile.get("column_profiles", [])
    if not column_profiles:
        return {"score": 0, "status": "No Data", "penalties": {}}

    avg_missing = sum(c["missing_pct"] for c in column_profiles) / len(column_profiles)
    avg_outliers = sum(c["outlier_pct"] for c in column_profiles) / len(column_profiles)
    constant_cols = sum(1 for c in column_profiles if c["is_constant"])
    high_card_cols = sum(1 for c in column_profiles if c["is_high_cardinality"])

    penalties = {
        "missing_values": min(30, avg_missing * 0.8),
        "duplicate_rows": min(15, profile.get("duplicate_pct", 0) * 1.2),
        "outliers": min(20, avg_outliers * 1.5),
        "constant_columns": min(15, constant_cols * 5),
        "high_cardinality": min(10, high_card_cols * 2),
    }

    total_penalty = sum(penalties.values())
    score = max(0, round(100 - total_penalty, 1))

    if score >= 85:
        status = "Ready for analysis"
    elif score >= 70:
        status = "Mostly ready, minor cleaning needed"
    elif score >= 50:
        status = "Needs cleaning before modelling"
    else:
        status = "High risk, review before analysis"

    return {
        "score": score,
        "status": status,
        "penalties": {k: round(v, 1) for k, v in penalties.items()},
    }


def rank_column_risks(profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Rank columns by a simple data-quality risk score."""
    risks = []

    for col in profile.get("column_profiles", []):
        risk = 0.0
        reasons = []

        if col["missing_pct"] > 0:
            missing_penalty = min(45, col["missing_pct"] * 1.2)
            risk += missing_penalty
            reasons.append(f"{col['missing_pct']}% missing")

        if col["outlier_pct"] > 0:
            outlier_penalty = min(25, col["outlier_pct"] * 2.0)
            risk += outlier_penalty
            reasons.append(f"{col['outlier_pct']}% outliers")

        if col["is_constant"]:
            risk += 35
            reasons.append("constant column")

        elif col["is_near_constant"]:
            risk += 20
            reasons.append("near-constant column")

        if col["is_high_cardinality"]:
            risk += 20
            reasons.append("high cardinality or ID-like")

        risk = min(100, round(risk, 1))

        if not reasons:
            reasons.append("no major issue detected")

        risks.append(
            {
                "column": col["column"],
                "role": col["role"],
                "risk_score": risk,
                "severity": _severity_from_score(risk),
                "reason": "; ".join(reasons),
                "suggested_action": suggest_action(col, risk),
            }
        )

    return sorted(risks, key=lambda item: item["risk_score"], reverse=True)


def suggest_action(col: Dict[str, Any], risk: float) -> str:
    if col["is_constant"]:
        return "Consider removing this column before analysis."
    if col["is_high_cardinality"]:
        return "Check whether this is an ID field; exclude from modelling if not meaningful."
    if col["missing_pct"] >= 40:
        return "Investigate source or consider dropping/imputing carefully."
    if col["missing_pct"] >= 5:
        return "Consider imputation or missingness treatment."
    if col["outlier_pct"] >= 5:
        return "Review extreme values before modelling."
    if risk >= 40:
        return "Review this column before analysis."
    return "Keep; no major cleaning action required."
