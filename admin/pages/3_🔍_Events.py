"""
Events Viewer Page - Browse and analyze security events
"""

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from admin.utils.api_client import api

st.set_page_config(page_title="Events Viewer", page_icon="🔍", layout="wide")

st.title("🔍 Security Events Viewer")

# Filters
st.subheader("Filters")

col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1, 1])

with col1:
    status_filter = st.selectbox(
        "Status", ["All", "block", "notify", "allow"], help="Filter by event status"
    )

with col2:
    try:
        flows = api.get_flows()
        flow_names = ["All"] + [f.get("flow_name") for f in flows]
    except Exception:
        flow_names = ["All"]

    flow_filter = st.selectbox("Flow", flow_names, help="Filter by pipeline flow")

with col3:
    limit = st.selectbox(
        "Limit", [10, 25, 50, 100, 200], index=2, help="Number of events to show"
    )

with col4:
    st.write("")
    st.write("")
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

with col5:
    st.write("")
    st.write("")
    auto_refresh = st.checkbox("Auto", help="Auto-refresh")

if auto_refresh:
    import time

    time.sleep(30)
    st.rerun()

# Search
search_term = st.text_input(
    "🔍 Search in prompts",
    placeholder="Search for text in prompts...",
    help="Search events by prompt content",
)

st.markdown("---")

try:
    # Fetch events
    params = {"limit": limit}
    if status_filter != "All":
        params["status"] = status_filter
    if flow_filter != "All":
        params["flow_name"] = flow_filter

    result = api.get_events(**params)
    events = result.get("events", [])

    # Apply search filter
    if search_term and events:
        events = [
            e
            for e in events
            if e.get("prompt") and search_term.lower() in e.get("prompt", "").lower()
        ]

    # Statistics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Events", result.get("total", 0))

    with col2:
        st.metric("Showing", len(events))

    with col3:
        if events:
            avg_time = "N/A"
            st.metric(
                "Latest Event",
                events[0].get("timestamp", "N/A")[:16] if events else "N/A",
            )

    st.markdown("---")

    # Events list
    if events:
        st.subheader(f"📋 Events ({len(events)})")

        for event in events:
            status = event.get("status", "unknown")
            status_emoji = {"block": "🚫", "notify": "⚠️", "allow": "✅"}.get(
                status, "❓"
            )

            status_color = {"block": "red", "notify": "orange", "allow": "green"}.get(
                status, "gray"
            )

            timestamp = event.get("timestamp", "N/A")
            if timestamp != "N/A":
                timestamp = timestamp[:19].replace("T", " ")

            with st.expander(
                f"{status_emoji} **{status.upper()}** | {event.get('flow_name', 'Unknown')} | {timestamp}",
                expanded=False,
            ):
                # Event details
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"**Status:** :{status_color}[{status.upper()}]")
                    st.write("**Flow:**", event.get("flow_name", "N/A"))
                    st.write("**Event ID:**", event.get("id"))

                    if event.get("task_id"):
                        st.write("**Task ID:**", event.get("task_id"))

                    st.write("**Timestamp:**", timestamp)

                with col2:
                    # Quick actions
                    st.markdown("**Actions:**")

                    if st.button(
                        "📋 Copy ID",
                        key=f"copy_{event['id']}",
                        use_container_width=True,
                    ):
                        st.code(event["id"])

                    if st.button(
                        "🔗 View JSON",
                        key=f"json_{event['id']}",
                        use_container_width=True,
                    ):
                        st.session_state[f"show_json_{event['id']}"] = (
                            not st.session_state.get(f"show_json_{event['id']}", False)
                        )

                st.markdown("---")

                # Prompt
                if event.get("prompt"):
                    st.markdown("**📝 Analyzed Prompt:**")
                    prompt_text = event.get("prompt", "")
                    if len(prompt_text) > 500:
                        with st.expander(
                            f"Show full prompt ({len(prompt_text)} characters)"
                        ):
                            st.code(prompt_text, language="text")
                    else:
                        st.code(prompt_text, language="text")

                # Pipeline Results
                pipeline_results = event.get("pipeline_results", {})
                pipelines = pipeline_results.get("pipelines", [])

                if pipelines:
                    st.markdown("**🔧 Pipeline Results:**")

                    for idx, pipeline in enumerate(pipelines):
                        pipeline_status = pipeline.get("status", "unknown")
                        pipeline_name = pipeline.get("name", "Unknown Pipeline")

                        with st.expander(
                            f"{status_emoji} {pipeline_name} - {pipeline_status.upper()}"
                        ):
                            triggered_rules = pipeline.get("triggered_rules", [])

                            if triggered_rules:
                                st.write(
                                    f"**Triggered Rules ({len(triggered_rules)}):**"
                                )

                                for rule_idx, rule in enumerate(triggered_rules):
                                    st.markdown(
                                        f"**{rule_idx + 1}. {rule.get('name', 'Unnamed Rule')}**"
                                    )

                                    col_a, col_b = st.columns(2)

                                    with col_a:
                                        st.write(
                                            "**Action:**",
                                            f"`{rule.get('action', 'N/A')}`",
                                        )
                                        if rule.get("severity"):
                                            st.write(
                                                "**Severity:**", rule.get("severity")
                                            )

                                    with col_b:
                                        st.write("**Rule ID:**", rule.get("id", "N/A"))
                                        if rule.get("cwe_id"):
                                            st.write("**CWE:**", rule.get("cwe_id"))

                                    if rule.get("details"):
                                        st.caption(rule.get("details"))

                                    if rule.get("body"):
                                        with st.expander("Show pattern"):
                                            st.code(rule.get("body"), language="regex")

                                    if rule_idx < len(triggered_rules) - 1:
                                        st.markdown("---")
                            else:
                                st.info("No rules triggered in this pipeline")

                # Show full JSON if requested
                if st.session_state.get(f"show_json_{event['id']}", False):
                    st.markdown("---")
                    st.markdown("**📄 Full Event JSON:**")
                    st.json(event)

    else:
        st.info("No events found matching the filters.")

    # Pagination info
    if events:
        st.markdown("---")
        st.caption(f"Showing {len(events)} of {result.get('total', 0)} total events")

except Exception as e:
    st.error(f"Failed to load events: {str(e)}")
    st.exception(e)

# Export option
st.markdown("---")
st.subheader("📥 Export Options")

col1, col2, col3 = st.columns([1, 1, 4])

with col1:
    if st.button("📊 Export CSV", use_container_width=True):
        if events:
            df = pd.DataFrame(events)
            csv = df.to_csv(index=False)
            st.download_button(
                "Download CSV",
                csv,
                "events_export.csv",
                "text/csv",
                use_container_width=True,
            )
        else:
            st.warning("No events to export")

with col2:
    if st.button("📄 Export JSON", use_container_width=True):
        if events:
            json_str = json.dumps(events, indent=2)
            st.download_button(
                "Download JSON",
                json_str,
                "events_export.json",
                "application/json",
                use_container_width=True,
            )
        else:
            st.warning("No events to export")
