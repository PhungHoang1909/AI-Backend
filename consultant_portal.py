import streamlit as st
from db import (
    list_consultants,
    save_rule,
    get_rule_for_service,
    add_consultant,
    get_and_increment_rr,
    list_consultants,
    get_conn,
)
import random


def admin_rules_ui():
    st.header("Consultant Assignment Portal (Admin)")
    st.subheader("Consultant list (DB)")
    consultants = list_consultants()
    st.write(", ".join(consultants))
    with st.form("add_consultant"):
        newc = st.text_input("Add consultant username")
        if st.form_submit_button("Add consultant"):
            if newc:
                add_consultant(newc.strip())
                st.success(f"Added {newc}")
                st.experimental_rerun()
    st.markdown("---")
    st.subheader("Define assignment rule for a service")
    service = st.text_input("Service name", value="Finance")
    mode = st.selectbox("Mode", ["static", "random", "round_robin"])
    static = None
    if mode == "static":
        static = st.selectbox("Pick static consultant", consultants)
    if st.button("Save rule"):
        save_rule(service, mode, static)
        st.success("Rule saved")
        st.experimental_rerun()
    st.markdown("---")
    st.subheader("Existing Rules")
    # Display rules
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM rules")
    rows = cur.fetchall()
    for r in rows:
        st.write(dict(r))


def apply_assignment_rule(service, payload):
    # Get rule from DB
    from db import get_rule_for_service, list_consultants, get_and_increment_rr

    rule = get_rule_for_service(service)
    consultants = list_consultants()
    if not consultants:
        return "unassigned"
    if not rule:
        idx = get_and_increment_rr("default") % len(consultants)
        return consultants[idx]
    mode = rule["mode"]
    if mode == "static":
        return rule["static_consultant"] or consultants[0]
    if mode == "random":
        return random.choice(consultants)
    if mode == "round_robin":
        idx = get_and_increment_rr(service) % len(consultants)
        return consultants[idx]
    return consultants[0]
