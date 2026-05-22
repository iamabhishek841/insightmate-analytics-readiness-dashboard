from __future__ import annotations

import io
from typing import Optional

import pandas as pd
from fastapi import FastAPI, File, UploadFile, Form

from core.profiler import profile_dataset
from core.scoring import calculate_quality_score, rank_column_risks
from core.readiness import assess_modelling_readiness
from core.recommendations import build_action_plan
from core.reporting import build_markdown_report


app = FastAPI(title="InsightMate API", version="1.0.0")


@app.get("/")
def health_check():
    return {"status": "ok", "service": "InsightMate API"}


@app.post("/analyze")
async def analyze_dataset(
    file: UploadFile = File(...),
    target_column: Optional[str] = Form(None),
):
    content = await file.read()
    df = pd.read_csv(io.BytesIO(content))

    profile = profile_dataset(df)
    quality = calculate_quality_score(profile)
    risks = rank_column_risks(profile)
    readiness = assess_modelling_readiness(df, profile, target_column)
    actions = build_action_plan(profile, risks, readiness)
    report = build_markdown_report(file.filename, profile, quality, risks, readiness, actions)

    return {
        "dataset_name": file.filename,
        "profile": profile,
        "quality": quality,
        "risks": risks,
        "readiness": readiness,
        "actions": actions,
        "report": report,
    }
