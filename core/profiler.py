from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

import numpy as np
import pandas as pd


def infer_column_role(series: pd.Series) -> str:
    """Infer a simple analytical role for a column."""
    non_null = series.dropna()
    unique_ratio = series.nunique(dropna=True) / max(len(series), 1)

    if pd.api.types.is_numeric_dtype(series):
        if unique_ratio > 0.90 and series.nunique(dropna=True) > 20:
            return "numeric_id_like"
        return "numeric"

    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"

    if unique_ratio > 0.90 and series.nunique(dropna=True) > 20:
        return "categorical_high_cardinality"

    return "categorical"


def iqr_outlier_count(series: pd.Series) -> int:
    """Count outliers using the IQR rule for numeric columns."""
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty:
        return 0

    q1 = numeric.quantile(0.25)
    q3 = numeric.quantile(0.75)
    iqr = q3 - q1

    if iqr == 0 or pd.isna(iqr):
        return 0

    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    return int(((numeric < lower) | (numeric > upper)).sum())


def profile_dataset(df: pd.DataFrame) -> Dict[str, Any]:
    """Create a data-quality profile for an uploaded dataset."""
    rows, columns = df.shape
    duplicate_rows = int(df.duplicated().sum())
    duplicate_pct = round((duplicate_rows / max(rows, 1)) * 100, 2)

    column_profiles: List[Dict[str, Any]] = []

    for col in df.columns:
        series = df[col]
        missing_count = int(series.isna().sum())
        missing_pct = round((missing_count / max(rows, 1)) * 100, 2)
        unique_count = int(series.nunique(dropna=True))
        unique_ratio = round(unique_count / max(rows, 1), 4)

        role = infer_column_role(series)
        outlier_count = iqr_outlier_count(series) if pd.api.types.is_numeric_dtype(series) else 0
        outlier_pct = round((outlier_count / max(series.dropna().shape[0], 1)) * 100, 2)

        is_constant = unique_count <= 1
        is_near_constant = unique_ratio < 0.02 and unique_count <= max(2, int(rows * 0.02))
        is_high_cardinality = role in {"categorical_high_cardinality", "numeric_id_like"}

        column_profiles.append(
            {
                "column": str(col),
                "dtype": str(series.dtype),
                "role": role,
                "missing_count": missing_count,
                "missing_pct": missing_pct,
                "unique_count": unique_count,
                "unique_ratio": unique_ratio,
                "outlier_count": outlier_count,
                "outlier_pct": outlier_pct,
                "is_constant": bool(is_constant),
                "is_near_constant": bool(is_near_constant),
                "is_high_cardinality": bool(is_high_cardinality),
            }
        )

    numeric_df = df.select_dtypes(include=[np.number])
    corr_pairs = []
    if numeric_df.shape[1] >= 2:
        corr = numeric_df.corr(numeric_only=True).abs()
        for i, col_a in enumerate(corr.columns):
            for col_b in corr.columns[i + 1 :]:
                value = corr.loc[col_a, col_b]
                if pd.notna(value) and value >= 0.70:
                    corr_pairs.append(
                        {
                            "source": str(col_a),
                            "target": str(col_b),
                            "correlation": round(float(value), 3),
                        }
                    )

    return {
        "rows": rows,
        "columns": columns,
        "duplicate_rows": duplicate_rows,
        "duplicate_pct": duplicate_pct,
        "column_profiles": column_profiles,
        "correlation_pairs": corr_pairs,
    }
