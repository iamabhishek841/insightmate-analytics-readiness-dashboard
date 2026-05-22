from __future__ import annotations

from typing import Any, Dict, List


def build_markdown_report(
    dataset_name: str,
    profile: Dict[str, Any],
    quality: Dict[str, Any],
    risks: List[Dict[str, Any]],
    readiness: Dict[str, Any],
    actions: List[Dict[str, str]],
) -> str:
    """Build a markdown readiness report."""
    lines = []
    lines.append(f"# InsightMate Readiness Report: {dataset_name}")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append(f"- Rows: {profile.get('rows')}")
    lines.append(f"- Columns: {profile.get('columns')}")
    lines.append(f"- Duplicate rows: {profile.get('duplicate_rows')} ({profile.get('duplicate_pct')}%)")
    lines.append(f"- Data quality score: {quality.get('score')}/100")
    lines.append(f"- Status: {quality.get('status')}")
    lines.append("")

    lines.append("## Top Column Risks")
    for risk in risks[:10]:
        lines.append(f"- **{risk['column']}** — {risk['severity']} risk ({risk['risk_score']}/100): {risk['reason']}. Action: {risk['suggested_action']}")
    lines.append("")

    lines.append("## Correlation Findings")
    corr_pairs = profile.get("correlation_pairs", [])
    if corr_pairs:
        for pair in corr_pairs[:10]:
            lines.append(f"- {pair['source']} ↔ {pair['target']}: {pair['correlation']}")
    else:
        lines.append("- No strong numerical correlations above 0.70 detected.")
    lines.append("")

    lines.append("## Modelling Readiness")
    if readiness.get("available"):
        lines.append(f"- Target column: {readiness.get('target_column')}")
        lines.append(f"- Suggested task type: {readiness.get('task_type')}")
        lines.append(f"- Readiness score: {readiness.get('readiness_score')}/100")
        lines.append(f"- Status: {readiness.get('status')}")
        if readiness.get("warnings"):
            lines.append("")
            lines.append("### Warnings")
            for warning in readiness["warnings"]:
                lines.append(f"- {warning}")
        if readiness.get("recommendations"):
            lines.append("")
            lines.append("### Recommendations")
            for rec in readiness["recommendations"]:
                lines.append(f"- {rec}")
    else:
        lines.append("- No target column selected.")
    lines.append("")

    lines.append("## Cleaning Action Plan")
    for action in actions:
        lines.append(f"- **{action['priority']}** | {action['area']}: {action['action']}")
    lines.append("")

    return "\n".join(lines)
