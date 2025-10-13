"""
Settings & Configuration Page
"""

import sys
from pathlib import Path

import streamlit as st

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from admin.utils.api_client import api

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")

st.title("⚙️ System Settings & Configuration")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(
    ["🎭 Flows & Pipelines", "👥 Managers", "ℹ️ System Info", "🔧 API Config"]
)

# Tab 1: Flows & Pipelines
with tab1:
    st.subheader("Pipeline Flows Configuration")

    try:
        flows = api.get_flows()

        st.info(f"📊 Total Flows: {len(flows)}")

        for flow in flows:
            with st.expander(
                f"🎭 {flow.get('flow_name', 'Unknown Flow')}", expanded=True
            ):
                pipelines = flow.get("pipelines", [])

                st.write(f"**Pipelines ({len(pipelines)}):**")

                if pipelines:
                    for pipeline in pipelines:
                        col1, col2, col3 = st.columns([3, 1, 1])

                        with col1:
                            enabled_emoji = "✅" if pipeline.get("enabled") else "❌"
                            st.write(
                                f"{enabled_emoji} **{pipeline.get('name', 'Unknown')}**"
                            )

                        with col2:
                            st.caption(f"ID: `{pipeline.get('id', 'N/A')}`")

                        with col3:
                            status = (
                                "🟢 Enabled"
                                if pipeline.get("enabled")
                                else "🔴 Disabled"
                            )
                            st.caption(status)

                        if pipeline.get("description"):
                            st.caption(f"_{pipeline.get('description')}_")

                        st.markdown("---")
                else:
                    st.warning("No pipelines configured for this flow")

                st.markdown("**Usage Example:**")
                st.code(
                    f"""
import requests

response = requests.post(
    "{api.base_url}{api.api_prefix}/flow/run",
    json={{
        "prompt": "Your text to analyze",
        "pipeline_flow": "{flow.get('flow_name')}"
    }}
)
                    """.strip(),
                    language="python",
                )

    except Exception as e:
        st.error(f"Failed to load flows: {str(e)}")

# Tab 2: Managers
with tab2:
    st.subheader("Manager Configuration")

    try:
        managers = api.get_managers()

        st.info(f"📊 Total Managers: {len(managers)}")

        for manager in managers:
            manager_enabled = manager.get("enabled", False)
            status_emoji = "🟢" if manager_enabled else "🔴"

            with st.expander(
                f"{status_emoji} {manager.get('name', 'Unknown Manager')}",
                expanded=manager_enabled,
            ):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.write("**Description:**")
                    st.caption(manager.get("description", "No description available"))

                    st.write("**Manager ID:**", f"`{manager.get('id', 'N/A')}`")
                    st.write(
                        "**Status:**",
                        "🟢 Enabled" if manager_enabled else "🔴 Disabled",
                    )

                with col2:
                    clients = manager.get("clients", [])
                    st.write(f"**Available Clients ({len(clients)}):**")

                    if clients:
                        for client in clients:
                            st.write(f"• {client.get('name', 'Unknown')}")
                            st.caption(f"  ID: `{client.get('id', 'N/A')}`")
                    else:
                        st.caption("_No clients available_")

                if not manager_enabled:
                    st.warning(
                        "⚠️ This manager is currently disabled. No clients are configured."
                    )

                st.markdown("---")
                st.markdown("**Switch Client Example:**")
                st.code(
                    f"""
import requests

response = requests.post(
    "{api.base_url}{api.api_prefix}/manager/switch_active_client",
    json={{
        "manager_id": "{manager.get('id')}",
        "client_id": "your_client_id"
    }}
)
                    """.strip(),
                    language="python",
                )

    except Exception as e:
        st.error(f"Failed to load managers: {str(e)}")

# Tab 3: System Info
with tab3:
    st.subheader("System Information")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🛡️ AIDR Bastion")

        st.write("**Admin Panel Version:**", "1.0.0")
        st.write("**Admin Framework:**", "Streamlit")

        try:
            stats = api.get_event_stats()
            st.write("**Total Events:**", stats.get("total", 0))
        except Exception:
            st.write("**Total Events:**", "N/A")

        try:
            rules = api.get_rules()
            st.write("**Total Rules:**", rules.get("total", 0))
        except Exception:
            st.write("**Total Rules:**", "N/A")

        try:
            flows = api.get_flows()
            st.write("**Configured Flows:**", len(flows))
        except Exception:
            st.write("**Configured Flows:**", "N/A")

    with col2:
        st.markdown("### 🔗 API Connection")

        st.write("**Base URL:**", api.base_url)
        st.write("**API Prefix:**", api.api_prefix)
        st.write("**Full API URL:**", f"{api.base_url}{api.api_prefix}")

        # Test connection
        if st.button("🔍 Test Connection", use_container_width=True):
            try:
                stats = api.get_event_stats()
                st.success("✅ API connection successful!")
                st.json(stats)
            except Exception as e:
                st.error(f"❌ API connection failed: {str(e)}")

    st.markdown("---")

    st.subheader("📚 Documentation Links")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Project:**")
        st.markdown("- [GitHub Repository](https://github.com/0xAIDR/AIDR-Bastion)")
        st.markdown(
            "- [README Documentation](https://github.com/0xAIDR/AIDR-Bastion/blob/main/README.md)"
        )

    with col2:
        st.markdown("**API Documentation:**")
        st.markdown(f"- [FastAPI Docs]({api.base_url}/docs)")
        st.markdown(f"- [ReDoc]({api.base_url}/redoc)")

    with col3:
        st.markdown("**Technologies:**")
        st.markdown("- [Streamlit](https://streamlit.io/)")
        st.markdown("- [FastAPI](https://fastapi.tiangolo.com/)")
        st.markdown("- [SQLAlchemy](https://www.sqlalchemy.org/)")

# Tab 4: API Configuration
with tab4:
    st.subheader("API Configuration")

    st.write("Configure the connection to AIDR Bastion API.")

    with st.form("api_config"):
        base_url = st.text_input(
            "Base URL", value=api.base_url, help="Base URL of the AIDR Bastion API"
        )

        api_prefix = st.text_input(
            "API Prefix",
            value=api.api_prefix,
            help="API version prefix (usually /api/v1)",
        )

        timeout = st.number_input(
            "Request Timeout (seconds)",
            value=30,
            min_value=5,
            max_value=300,
            help="HTTP request timeout",
        )

        col1, col2 = st.columns(2)

        with col1:
            save = st.form_submit_button(
                "💾 Save Configuration", use_container_width=True, type="primary"
            )

        with col2:
            test = st.form_submit_button("🔍 Test Connection", use_container_width=True)

        if save:
            api.base_url = base_url
            api.api_prefix = api_prefix
            st.success("✅ Configuration saved!")
            st.rerun()

        if test:
            try:
                # Create temporary client with new settings
                from admin.utils.api_client import APIClient

                test_api = APIClient(base_url)
                test_api.api_prefix = api_prefix
                stats = test_api.get_event_stats()
                st.success("✅ Connection successful!")
                st.json(stats)
            except Exception as e:
                st.error(f"❌ Connection failed: {str(e)}")

    st.markdown("---")

    st.subheader("🔧 Advanced Settings")

    with st.expander("Admin Panel Environment Variables"):
        st.write("**Current Configuration:**")

        import os

        env_vars = {
            "ADMIN_API_BASE_URL": os.getenv(
                "ADMIN_API_BASE_URL", "http://localhost:8000 (default)"
            ),
            "ADMIN_API_PREFIX": os.getenv("ADMIN_API_PREFIX", "/api/v1 (default)"),
            "ADMIN_API_TIMEOUT": os.getenv("ADMIN_API_TIMEOUT", "30 (default)"),
        }

        col1, col2 = st.columns([1, 2])

        with col1:
            for key in env_vars.keys():
                st.write(f"**{key}:**")

        with col2:
            for value in env_vars.values():
                st.code(value)

        st.markdown("---")
        st.write("**To configure, create `admin/.env` file:**")
        st.code(
            """
# admin/.env
ADMIN_API_BASE_URL=http://localhost:8000
ADMIN_API_PREFIX=/api/v1
ADMIN_API_TIMEOUT=30
            """,
            language="bash",
        )

    with st.expander("Admin Panel Configuration"):
        st.write("**Streamlit Configuration:**")
        st.code(
            """
# .streamlit/config.toml

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"

[server]
port = 8501
enableCORS = false
            """,
            language="toml",
        )

st.markdown("---")

# Footer
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 2rem;'>
        <p>⚙️ AIDR Bastion Settings & Configuration</p>
    </div>
    """,
    unsafe_allow_html=True,
)
