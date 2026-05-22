from __future__ import annotations

from typing import Any, Dict, List


def build_action_plan(profile: Dict[str, Any], risks: List[Dict[str, Any]], readiness: Dict[str, Any]) -> List[Dict[str, str]]:
    """Build a priority-based cleaning and modelling action plan."""
    actions: List[Dict[str, str]] = []

    if profile.get("duplicate_rows", 0) > 0:
        actions.append(
            {
                "priority": "High",
                "area": "Duplicate Records",
                "action": f"Review and remove {profile['duplicate_rows']} duplicate rows before analysis.",
            }
        )

    for risk in risks[:5]:
        if risk["severity"] in {"High", "Medium"}:
            actions.append(
                {
                    "priority": risk["severity"],
                    "area": risk["column"],
                    "action": risk["suggested_action"],
                }
            )

    if readiness.get("available"):
        for warning in readiness.get("warnings", [])[:4]:
            actions.append(
                {
                    "priority": "Medium",
                    "area": "Modelling Readiness",
                    "action": warning,
                }
            )

        for rec in readiness.get("recommendations", [])[:3]:
            actions.append(
                {
                    "priority": "Medium",
                    "area": "Recommended Modelling Step",
                    "action": rec,
                }
            )

    if not actions:
        actions.append(
            {
                "priority": "Low",
                "area": "Dataset",
                "action": "No major issues detected. Proceed with exploratory analysis and document assumptions.",
            }
        )

    return actions[:12]
