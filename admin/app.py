"""
AIDR Bastion Admin Panel

Main entry point for the Streamlit admin interface.
"""

import sys
from pathlib import Path

import streamlit as st

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from admin.utils.api_client import api

# Page configuration
st.set_page_config(
    page_title="AIDR Bastion Admin",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .stButton>button {
        width: 100%;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Sidebar
with st.sidebar:
    st.markdown("# 🛡️ AIDR Bastion")
    st.markdown("### Admin Panel")
    st.markdown("---")

    # API Status
    try:
        stats = api.get_event_stats()
        st.success("🟢 API Connected")
        st.metric("Total Events", stats.get("total", 0))
    except Exception as e:
        st.error("🔴 API Disconnected")
        st.caption(f"Error: {str(e)[:50]}...")

    st.markdown("---")
    st.markdown("### Navigation")
    st.info(
        """
        📊 **Dashboard** - Statistics & Analytics
        📋 **Rules** - Manage Detection Rules
        🔍 **Events** - View Analysis Events
        ⚙️ **Settings** - Configuration
        """
    )

    st.markdown("---")
    st.markdown("### Quick Actions")

    if st.button("🔄 Refresh Data"):
        st.rerun()

    if st.button("📥 Export Data"):
        st.info("Export functionality coming soon!")

# Main content
st.markdown(
    '<h1 class="main-header">🛡️ AIDR Bastion Admin Panel</h1>', unsafe_allow_html=True
)

st.markdown(
    """
    Welcome to the AIDR Bastion Administration Panel. Use the navigation on the left to:

    - 📊 View real-time statistics and analytics
    - 📋 Manage detection rules (create, edit, delete)
    - 🔍 Browse analysis events and results
    - ⚙️ Configure system settings
    """
)

st.markdown("---")

# Quick Overview
st.subheader("📊 Quick Overview")

try:
    stats = api.get_event_stats()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Events",
            stats.get("total", 0),
            help="Total number of prompt analysis events",
        )

    with col2:
        st.metric(
            "🚫 Blocked",
            stats.get("blocked", 0),
            delta=f"-{stats.get('blocked', 0)}",
            delta_color="inverse",
            help="Prompts blocked due to security rules",
        )

    with col3:
        st.metric(
            "⚠️ Notified", stats.get("notified", 0), help="Prompts flagged for review"
        )

    with col4:
        st.metric(
            "✅ Allowed",
            stats.get("allowed", 0),
            delta=f"+{stats.get('allowed', 0)}",
            delta_color="normal",
            help="Prompts passed all security checks",
        )

    # Block rate
    if stats.get("total", 0) > 0:
        block_rate = (stats.get("blocked", 0) / stats.get("total", 1)) * 100
        st.progress(block_rate / 100, text=f"Block Rate: {block_rate:.1f}%")

except Exception as e:
    st.error(f"Failed to load statistics: {str(e)}")

st.markdown("---")

# Recent Activity
st.subheader("🕐 Recent Activity")

try:
    recent = api.get_recent_events(limit=5)
    events = recent.get("events", [])

    if events:
        for event in events:
            status_emoji = {"block": "🚫", "notify": "⚠️", "allow": "✅"}.get(
                event.get("status", ""), "❓"
            )

            with st.expander(
                f"{status_emoji} {event.get('flow_name', 'Unknown')} - {event.get('timestamp', 'N/A')}"
            ):
                col1, col2 = st.columns([1, 3])

                with col1:
                    st.write("**Status:**", event.get("status", "N/A").upper())
                    st.write("**Flow:**", event.get("flow_name", "N/A"))
                    if event.get("task_id"):
                        st.write("**Task ID:**", event.get("task_id"))

                with col2:
                    if event.get("prompt"):
                        st.write("**Prompt:**")
                        st.code(
                            (
                                event.get("prompt", "")[:200] + "..."
                                if len(event.get("prompt", "")) > 200
                                else event.get("prompt", "")
                            ),
                            language="text",
                        )
    else:
        st.info("No recent events found.")

except Exception as e:
    st.error(f"Failed to load recent events: {str(e)}")

st.markdown("---")

# Footer
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 2rem;'>
        <p>AIDR Bastion Admin Panel v1.0.0</p>
    </div>
    """,
    unsafe_allow_html=True,
)
