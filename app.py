from __future__ import annotations

import io
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from core.profiler import profile_dataset
from core.scoring import calculate_quality_score, rank_column_risks
from core.readiness import assess_modelling_readiness
from core.recommendations import build_action_plan
from core.reporting import build_markdown_report
from core.storage import save_review, load_history


st.set_page_config(
    page_title="InsightMate",
    page_icon="📊",
    layout="wide",
)

st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        color: #4b5563;
        margin-bottom: 1.4rem;
    }
    .metric-card {
        padding: 1rem;
        border-radius: 0.75rem;
        border: 1px solid #e5e7eb;
        background: #ffffff;
    }
    .status-good {
        color: #047857;
        font-weight: 700;
    }
    .status-warn {
        color: #b45309;
        font-weight: 700;
    }
    .status-bad {
        color: #b91c1c;
        font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-title">InsightMate</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Analytics Readiness & Data Quality Decision Dashboard for Business Analytics coursework datasets.</div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Upload Dataset")
    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

    use_sample = st.checkbox("Use sample customer dataset", value=uploaded_file is None)
    st.caption("Tip: Select a target column after uploading to run modelling readiness checks.")

    st.divider()
    st.header("Project Purpose")
    st.write(
        "This dashboard helps decide whether a dataset is ready for analysis, reporting, or modelling. "
        "It diagnoses quality risks, ranks risky columns, and recommends cleaning actions."
    )

@st.cache_data(show_spinner=False)
def load_sample_data() -> pd.DataFrame:
    return pd.read_csv("sample_data/sample_customer_data.csv")


def read_uploaded_csv(file) -> pd.DataFrame:
    return pd.read_csv(file)


df = None
dataset_name = None

try:
    if uploaded_file is not None:
        df = read_uploaded_csv(uploaded_file)
        dataset_name = uploaded_file.name
    elif use_sample:
        df = load_sample_data()
        dataset_name = "sample_customer_data.csv"
except Exception as exc:
    st.error(f"Could not read dataset: {exc}")
    st.stop()

if df is None:
    st.info("Upload a CSV file or use the sample dataset to begin.")
    st.stop()

# Basic cleanup for display safety
df.columns = [str(c).strip() for c in df.columns]

with st.sidebar:
    target_column = st.selectbox(
        "Target column for modelling readiness",
        options=["None"] + list(df.columns),
        index=0,
    )
    target_column = None if target_column == "None" else target_column

profile = profile_dataset(df)
quality = calculate_quality_score(profile)
risks = rank_column_risks(profile)
readiness = assess_modelling_readiness(df, profile, target_column)
actions = build_action_plan(profile, risks, readiness)
report = build_markdown_report(dataset_name, profile, quality, risks, readiness, actions)

# Save review once per dataset/target combination in session
session_key = f"{dataset_name}_{target_column}_{profile['rows']}_{profile['columns']}"
if st.session_state.get("last_saved_review") != session_key:
    save_review(
        dataset_name,
        {
            "profile": profile,
            "quality": quality,
            "risks": risks[:20],
            "readiness": readiness,
            "actions": actions,
        },
    )
    st.session_state["last_saved_review"] = session_key

tabs = st.tabs(
    [
        "Executive Overview",
        "Data Quality Risks",
        "Modelling Readiness",
        "Correlation Explorer",
        "Action Plan & Report",
        "Review History",
    ]
)

with tabs[0]:
    st.subheader("Executive Readiness Overview")

    score = quality["score"]
    status_class = "status-good" if score >= 85 else "status-warn" if score >= 60 else "status-bad"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Data Quality Score", f"{score}/100")
    c2.metric("Rows", f"{profile['rows']:,}")
    c3.metric("Columns", f"{profile['columns']:,}")
    c4.metric("Duplicate Rows", f"{profile['duplicate_rows']:,}", f"{profile['duplicate_pct']}%")

    st.markdown(f"### Dataset Status: <span class='{status_class}'>{quality['status']}</span>", unsafe_allow_html=True)

    penalty_df = pd.DataFrame(
        [{"Issue": k.replace("_", " ").title(), "Penalty": v} for k, v in quality["penalties"].items()]
    )
    col_a, col_b = st.columns([1.2, 1])

    with col_a:
        st.write("#### Quality Penalty Breakdown")
        st.dataframe(penalty_df, use_container_width=True, hide_index=True)

    with col_b:
        if not penalty_df.empty:
            fig = px.bar(penalty_df, x="Issue", y="Penalty", title="Penalty Contribution")
            fig.update_layout(xaxis_title="", yaxis_title="Penalty Points")
            st.plotly_chart(fig, use_container_width=True)

    st.write("#### Dataset Preview")
    st.dataframe(df.head(20), use_container_width=True)

with tabs[1]:
    st.subheader("Data Quality Risk Dashboard")

    risk_df = pd.DataFrame(risks)
    st.write("Columns are ranked by risk score based on missingness, outliers, cardinality, and constant-value checks.")
    st.dataframe(risk_df, use_container_width=True, hide_index=True)

    top_risks = risk_df.head(10)
    if not top_risks.empty:
        fig = px.bar(
            top_risks.sort_values("risk_score"),
            x="risk_score",
            y="column",
            orientation="h",
            color="severity",
            title="Top Column Risk Scores",
        )
        fig.update_layout(xaxis_title="Risk Score", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    profile_df = pd.DataFrame(profile["column_profiles"])
    st.write("#### Column Profiling Details")
    st.dataframe(profile_df, use_container_width=True, hide_index=True)

with tabs[2]:
    st.subheader("Modelling Readiness Check")

    if not readiness.get("available"):
        st.info(readiness["message"])
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Target", readiness["target_column"])
        c2.metric("Suggested Task", readiness["task_type"])
        c3.metric("Readiness Score", f"{readiness['readiness_score']}/100")
        c4.metric("Target Missing", f"{readiness['target_missing_pct']}%")

        st.markdown(f"### Modelling Status: **{readiness['status']}**")

        if readiness.get("target_imbalance_majority_pct") is not None:
            st.warning(f"Majority class share: {readiness['target_imbalance_majority_pct']}%")

        col_a, col_b = st.columns(2)
        with col_a:
            st.write("#### Warnings")
            if readiness["warnings"]:
                for warning in readiness["warnings"]:
                    st.warning(warning)
            else:
                st.success("No major modelling warnings detected.")

        with col_b:
            st.write("#### Recommendations")
            if readiness["recommendations"]:
                for rec in readiness["recommendations"]:
                    st.info(rec)
            else:
                st.info("Select a target column to get recommendations.")

        if readiness.get("leakage_signals"):
            st.write("#### Potential Leakage Signals")
            st.dataframe(pd.DataFrame(readiness["leakage_signals"]), use_container_width=True, hide_index=True)

with tabs[3]:
    st.subheader("Correlation & Relationship Explorer")

    corr_pairs = profile.get("correlation_pairs", [])
    if corr_pairs:
        corr_df = pd.DataFrame(corr_pairs)
        st.write("Strong numerical relationships detected with absolute correlation >= 0.70.")
        st.dataframe(corr_df, use_container_width=True, hide_index=True)

        fig = px.scatter(
            corr_df,
            x="source",
            y="target",
            size="correlation",
            color="correlation",
            title="Strong Correlation Relationship Map",
        )
        st.plotly_chart(fig, use_container_width=True)

        adjacency = {}
        for pair in corr_pairs:
            adjacency.setdefault(pair["source"], []).append(pair["target"])
            adjacency.setdefault(pair["target"], []).append(pair["source"])

        st.write("#### Graph-style Relationship Mapping")
        adjacency_rows = [{"Variable": k, "Strongly Related Variables": ", ".join(v)} for k, v in adjacency.items()]
        st.dataframe(pd.DataFrame(adjacency_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No strong numerical correlations above 0.70 were detected.")

with tabs[4]:
    st.subheader("Cleaning Action Plan & Report")

    action_df = pd.DataFrame(actions)
    st.write("Recommended next steps are prioritised from detected dataset risks and modelling-readiness warnings.")
    st.dataframe(action_df, use_container_width=True, hide_index=True)

    st.write("#### Download Readiness Report")
    st.download_button(
        label="Download Markdown Report",
        data=report,
        file_name=f"insightmate_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        mime="text/markdown",
    )

    with st.expander("Preview Report"):
        st.markdown(report)

with tabs[5]:
    st.subheader("Review History")
    history = load_history()
    if history:
        st.dataframe(pd.DataFrame(history), use_container_width=True, hide_index=True)
    else:
        st.info("No review history yet.")
