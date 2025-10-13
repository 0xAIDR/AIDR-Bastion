"""
Rules Management Page - CRUD Operations
"""

import sys
import uuid
from pathlib import Path

import pandas as pd
import streamlit as st

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from admin.utils.api_client import api

st.set_page_config(page_title="Rules Management", page_icon="📋", layout="wide")

st.title("📋 Detection Rules Management")

# Tabs
tab1, tab2, tab3 = st.tabs(["📝 All Rules", "➕ Create Rule", "📊 Statistics"])

# Tab 1: All Rules
with tab1:
    st.subheader("Detection Rules")

    # Filters
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

    with col1:
        category_filter = st.selectbox(
            "Category",
            [
                "All",
                "injection",
                "obfuscation",
                "override",
                "leakage",
                "pii",
                "semantic",
                "dos",
            ],
            help="Filter by rule category",
        )

    with col2:
        status_filter = st.selectbox(
            "Status", ["All", "Enabled", "Disabled"], help="Filter by enabled status"
        )

    with col3:
        search_term = st.text_input(
            "🔍 Search", placeholder="Search by name or pattern...", help="Search rules"
        )

    with col4:
        st.write("")  # Spacing
        st.write("")  # Spacing
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    try:
        # Fetch rules
        params = {}
        if category_filter != "All":
            params["category"] = category_filter
        if status_filter != "All":
            params["enabled"] = status_filter == "Enabled"

        result = api.get_rules(**params)
        rules = result.get("rules", [])

        # Apply search filter
        if search_term:
            rules = [
                r
                for r in rules
                if search_term.lower() in r.get("name", "").lower()
                or search_term.lower() in r.get("pattern", "").lower()
            ]

        st.info(
            f"📊 Total: {result.get('total', 0)} rules | Showing: {len(rules)} rules"
        )

        if rules:
            for rule in rules:
                with st.expander(
                    f"{'✅' if rule.get('enabled') else '❌'} {rule.get('name', 'Unnamed Rule')} "
                    f"[{rule.get('category', 'N/A').upper()}]"
                ):
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.write("**Details:**", rule.get("details", "No description"))
                        st.code(rule.get("pattern", ""), language="regex")

                        st.write("**Action:**", f"`{rule.get('action', 'N/A')}`")
                        if rule.get("severity"):
                            st.write("**Severity:**", rule.get("severity"))
                        if rule.get("cwe_id"):
                            st.write("**CWE:**", rule.get("cwe_id"))

                    with col2:
                        st.write("**ID:**", rule.get("id"))
                        st.write("**UUID:**", f"`{rule.get('uuid', 'N/A')[:8]}...`")
                        st.write("**Language:**", rule.get("language", "N/A"))

                        st.markdown("---")

                        # Actions
                        col_a, col_b = st.columns(2)

                        with col_a:
                            if st.button(
                                "🔄 Toggle",
                                key=f"toggle_{rule['id']}",
                                use_container_width=True,
                            ):
                                try:
                                    api.toggle_rule(rule["id"])
                                    st.success("Toggled!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")

                        with col_b:
                            if st.button(
                                "🗑️ Delete",
                                key=f"delete_{rule['id']}",
                                use_container_width=True,
                                type="secondary",
                            ):
                                if st.session_state.get(f"confirm_delete_{rule['id']}"):
                                    try:
                                        api.delete_rule(rule["id"])
                                        st.success("Deleted!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
                                else:
                                    st.session_state[f"confirm_delete_{rule['id']}"] = (
                                        True
                                    )
                                    st.warning("Click again to confirm")

                        # Edit button
                        if st.button(
                            "✏️ Edit", key=f"edit_{rule['id']}", use_container_width=True
                        ):
                            st.session_state.editing_rule = rule
                            st.session_state.active_tab = 2  # Switch to create tab
                            st.rerun()

        else:
            st.info("No rules found matching the filters.")

    except Exception as e:
        st.error(f"Failed to load rules: {str(e)}")

# Tab 2: Create/Edit Rule
with tab2:
    st.subheader(
        "Create New Detection Rule"
        if not st.session_state.get("editing_rule")
        else "Edit Detection Rule"
    )

    # Load editing rule if exists
    editing_rule = st.session_state.get("editing_rule")

    with st.form("rule_form"):
        col1, col2 = st.columns(2)

        with col1:
            rule_uuid = st.text_input(
                "UUID *",
                value=editing_rule.get("uuid") if editing_rule else str(uuid.uuid4()),
                help="Unique identifier for the rule",
                disabled=bool(editing_rule),
            )

            rule_name = st.text_input(
                "Rule Name *",
                value=editing_rule.get("name", "") if editing_rule else "",
                placeholder="e.g., SQL Injection Detection",
                help="Human-readable name for the rule",
            )

            rule_details = st.text_area(
                "Description *",
                value=editing_rule.get("details", "") if editing_rule else "",
                placeholder="Detailed description of what this rule detects...",
                help="Explain what threats this rule catches",
                height=100,
            )

            rule_pattern = st.text_area(
                "Detection Pattern *",
                value=editing_rule.get("pattern", "") if editing_rule else "",
                placeholder="(?i)\\b(SELECT|INSERT)\\b.*\\bFROM\\b",
                help="Regex pattern for detection",
                height=150,
            )

        with col2:
            rule_language = st.selectbox(
                "Pattern Language *",
                ["llm-regex-pattern", "semgrep", "yara"],
                index=(
                    ["llm-regex-pattern", "semgrep", "yara"].index(
                        editing_rule.get("language", "llm-regex-pattern")
                    )
                    if editing_rule
                    else 0
                ),
                help="Type of pattern language",
            )

            rule_action = st.selectbox(
                "Action *",
                ["block", "notify", "allow"],
                index=(
                    ["block", "notify", "allow"].index(
                        editing_rule.get("action", "notify")
                    )
                    if editing_rule
                    else 1
                ),
                help="Action to take when rule matches",
            )

            rule_category = st.selectbox(
                "Category",
                [
                    "",
                    "injection",
                    "obfuscation",
                    "override",
                    "leakage",
                    "pii",
                    "semantic",
                    "dos",
                ],
                index=(
                    [
                        "",
                        "injection",
                        "obfuscation",
                        "override",
                        "leakage",
                        "pii",
                        "semantic",
                        "dos",
                    ].index(editing_rule.get("category", ""))
                    if editing_rule
                    else 0
                ),
                help="Rule category",
            )

            rule_severity = st.selectbox(
                "Severity",
                ["", "critical", "high", "medium", "low"],
                index=(
                    ["", "critical", "high", "medium", "low"].index(
                        editing_rule.get("severity", "")
                    )
                    if editing_rule
                    else 0
                ),
                help="Severity level",
            )

            rule_cwe = st.text_input(
                "CWE ID",
                value=editing_rule.get("cwe_id", "") if editing_rule else "",
                placeholder="e.g., CWE-89",
                help="Common Weakness Enumeration ID",
            )

            rule_enabled = st.checkbox(
                "Enabled",
                value=editing_rule.get("enabled", True) if editing_rule else True,
                help="Whether this rule is active",
            )

        st.markdown("---")

        col1, col2, col3 = st.columns([1, 1, 4])

        with col1:
            submit = st.form_submit_button(
                "💾 Update Rule" if editing_rule else "✨ Create Rule",
                use_container_width=True,
                type="primary",
            )

        with col2:
            if editing_rule and st.form_submit_button(
                "❌ Cancel", use_container_width=True
            ):
                st.session_state.editing_rule = None
                st.rerun()

        if submit:
            # Validate required fields
            if not all(
                [
                    rule_uuid,
                    rule_name,
                    rule_details,
                    rule_pattern,
                    rule_language,
                    rule_action,
                ]
            ):
                st.error("Please fill in all required fields (*)")
            else:
                try:
                    rule_data = {
                        "uuid": rule_uuid,
                        "name": rule_name,
                        "details": rule_details,
                        "language": rule_language,
                        "pattern": rule_pattern,
                        "action": rule_action,
                        "enabled": rule_enabled,
                    }

                    # Optional fields
                    if rule_category:
                        rule_data["category"] = rule_category
                    if rule_severity:
                        rule_data["severity"] = rule_severity
                    if rule_cwe:
                        rule_data["cwe_id"] = rule_cwe

                    if editing_rule:
                        # Update existing rule
                        api.update_rule(editing_rule["id"], rule_data)
                        st.success("✅ Rule updated successfully!")
                        st.session_state.editing_rule = None
                    else:
                        # Create new rule
                        api.create_rule(rule_data)
                        st.success("✅ Rule created successfully!")

                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Failed to save rule: {str(e)}")

# Tab 3: Statistics
with tab3:
    st.subheader("📊 Rules Statistics")

    try:
        result = api.get_rules(limit=1000)
        rules = result.get("rules", [])

        if rules:
            df = pd.DataFrame(rules)

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Total Rules", len(rules))
                enabled_count = len(df[df["enabled"]])
                st.metric(
                    "Enabled Rules",
                    enabled_count,
                    delta=f"{enabled_count/len(rules)*100:.1f}%",
                )

            with col2:
                # By category
                st.write("**By Category:**")
                category_counts = df["category"].value_counts()
                for cat, count in category_counts.items():
                    st.write(f"• {cat}: {count}")

            with col3:
                # By action
                st.write("**By Action:**")
                action_counts = df["action"].value_counts()
                for action, count in action_counts.items():
                    st.write(f"• {action}: {count}")

            st.markdown("---")

            # Charts
            col1, col2 = st.columns(2)

            with col1:
                st.write("**Rules by Category**")
                st.bar_chart(df["category"].value_counts())

            with col2:
                st.write("**Rules by Severity**")
                st.bar_chart(df["severity"].value_counts())

        else:
            st.info("No rules found.")

    except Exception as e:
        st.error(f"Failed to load statistics: {str(e)}")
