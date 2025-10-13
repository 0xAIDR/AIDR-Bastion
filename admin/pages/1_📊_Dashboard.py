"""
Dashboard Page - Statistics and Analytics
"""

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from admin.utils.api_client import api

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

st.title("📊 Dashboard & Analytics")

# Refresh button
col1, col2, col3 = st.columns([6, 1, 1])
with col2:
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()
with col3:
    auto_refresh = st.checkbox("Auto", help="Auto-refresh every 30 seconds")

if auto_refresh:
    import time

    time.sleep(30)
    st.rerun()

try:
    # Get statistics
    stats = api.get_event_stats()
    recent_events = api.get_events(limit=100)

    st.markdown("---")

    # Key Metrics
    st.subheader("🎯 Key Metrics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "📊 Total Events",
            stats.get("total", 0),
            help="Total number of analyzed prompts",
        )

    with col2:
        blocked = stats.get("blocked", 0)
        total = stats.get("total", 1)
        block_rate = (blocked / total * 100) if total > 0 else 0
        st.metric(
            "🚫 Blocked",
            blocked,
            delta=f"{block_rate:.1f}%",
            delta_color="inverse",
            help="Prompts blocked by security rules",
        )

    with col3:
        notified = stats.get("notified", 0)
        notify_rate = (notified / total * 100) if total > 0 else 0
        st.metric(
            "⚠️ Notified",
            notified,
            delta=f"{notify_rate:.1f}%",
            delta_color="off",
            help="Prompts flagged for review",
        )

    with col4:
        allowed = stats.get("allowed", 0)
        allow_rate = (allowed / total * 100) if total > 0 else 0
        st.metric(
            "✅ Allowed",
            allowed,
            delta=f"{allow_rate:.1f}%",
            delta_color="normal",
            help="Safe prompts",
        )

    st.markdown("---")

    # Charts Row 1
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 Status Distribution")

        # Pie chart
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=["Blocked", "Notified", "Allowed"],
                    values=[
                        stats.get("blocked", 0),
                        stats.get("notified", 0),
                        stats.get("allowed", 0),
                    ],
                    hole=0.4,
                    marker_colors=["#ff4444", "#ffaa00", "#44ff44"],
                )
            ]
        )
        fig.update_layout(showlegend=True, height=400, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🎭 Events by Flow")

        # Get events and count by flow
        events = recent_events.get("events", [])
        if events:
            df = pd.DataFrame(events)
            flow_counts = df["flow_name"].value_counts()

            fig = px.bar(
                x=flow_counts.index,
                y=flow_counts.values,
                labels={"x": "Flow Name", "y": "Count"},
                color=flow_counts.values,
                color_continuous_scale="Blues",
            )
            fig.update_layout(
                showlegend=False,
                height=400,
                xaxis_title="",
                yaxis_title="Events",
                margin=dict(t=0, b=0, l=0, r=0),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No events data available")

    st.markdown("---")

    # Charts Row 2
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Status by Flow")

        if events:
            df = pd.DataFrame(events)
            flow_status = (
                df.groupby(["flow_name", "status"]).size().reset_index(name="count")
            )

            fig = px.bar(
                flow_status,
                x="flow_name",
                y="count",
                color="status",
                barmode="group",
                color_discrete_map={
                    "block": "#ff4444",
                    "notify": "#ffaa00",
                    "allow": "#44ff44",
                },
                labels={"flow_name": "Flow", "count": "Events", "status": "Status"},
            )
            fig.update_layout(
                height=400, xaxis_title="", margin=dict(t=0, b=0, l=0, r=0)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No events data available")

    with col2:
        st.subheader("⏰ Recent Activity Timeline")

        if events:
            df = pd.DataFrame(events)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df["hour"] = df["timestamp"].dt.floor("h")

            timeline = df.groupby(["hour", "status"]).size().reset_index(name="count")

            fig = px.line(
                timeline,
                x="hour",
                y="count",
                color="status",
                markers=True,
                color_discrete_map={
                    "block": "#ff4444",
                    "notify": "#ffaa00",
                    "allow": "#44ff44",
                },
                labels={"hour": "Time", "count": "Events", "status": "Status"},
            )
            fig.update_layout(
                height=400, xaxis_title="", margin=dict(t=0, b=0, l=0, r=0)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No events data available")

    st.markdown("---")

    # System Health
    st.subheader("🏥 System Health")

    col1, col2, col3 = st.columns(3)

    with col1:
        try:
            flows = api.get_flows()
            st.metric(
                "Active Flows", len(flows), help="Number of configured pipeline flows"
            )
        except Exception:
            st.metric("Active Flows", "N/A")

    with col2:
        try:
            managers = api.get_managers()
            active_managers = sum(1 for m in managers if m.get("enabled"))
            st.metric(
                "Active Managers",
                f"{active_managers}/{len(managers)}",
                help="Enabled managers",
            )
        except Exception:
            st.metric("Active Managers", "N/A")

    with col3:
        try:
            rules = api.get_rules()
            enabled_rules = sum(1 for r in rules.get("rules", []) if r.get("enabled"))
            st.metric(
                "Active Rules",
                f"{enabled_rules}/{rules.get('total', 0)}",
                help="Enabled detection rules",
            )
        except Exception:
            st.metric("Active Rules", "N/A")

    st.markdown("---")

    # Top Triggered Rules
    st.subheader("🔥 Top Blocked Patterns")

    blocked_events = [e for e in events if e.get("status") == "block"]
    if blocked_events:
        rule_counts = {}
        for event in blocked_events:
            pipelines = event.get("pipeline_results", {}).get("pipelines", [])
            for pipeline in pipelines:
                for rule in pipeline.get("triggered_rules", []):
                    rule_name = rule.get("name", "Unknown")
                    rule_counts[rule_name] = rule_counts.get(rule_name, 0) + 1

        if rule_counts:
            top_rules = sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)[
                :10
            ]

            fig = px.bar(
                x=[count for _, count in top_rules],
                y=[name for name, _ in top_rules],
                orientation="h",
                labels={"x": "Triggered Count", "y": "Rule Name"},
                color=[count for _, count in top_rules],
                color_continuous_scale="Reds",
            )
            fig.update_layout(
                showlegend=False,
                height=400,
                yaxis={"categoryorder": "total ascending"},
                margin=dict(t=0, b=0, l=0, r=0),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No blocked patterns found")
    else:
        st.info("No blocked events found")

except Exception as e:
    st.error(f"Failed to load dashboard data: {str(e)}")
    st.exception(e)
