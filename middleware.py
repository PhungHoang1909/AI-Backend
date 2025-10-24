import streamlit as st
from db import (
    list_ready_payloads,
    mark_payload_processed,
    get_and_increment_rr,
    insert_ticket,
    get_conn,
)
from consultant_portal import apply_assignment_rule
import json
from teamwork import create_ticket_in_teamwork


def process_ready_payloads_ui():
    st.header("Middleware — Process Ready Payloads")
    rows = list_ready_payloads()
    if not rows:
        st.info("No ready payloads in DB.")
        return
    for payload_row in rows:
        pid = payload_row["id"]
        payload = payload_row["payload"]
        st.subheader(f"Payload #{pid} — Conversation {payload.get('conversation_id')}")
        st.write(json.dumps(payload, indent=2))
        if st.button(f"Process payload #{pid}", key=f"proc{pid}"):
            service = payload.get("service", "General")
            chosen = apply_assignment_rule(service, payload)
            ticket_id = create_ticket_in_teamwork(payload, chosen)
            mark_payload_processed(pid)
            st.success(f"Created ticket #{ticket_id} and assigned to {chosen}")
            st.experimental_rerun()


def process_single_payload(payload):
    service = payload.get("service", "General")
    chosen = apply_assignment_rule(service, payload)
    tid = create_ticket_in_teamwork(payload, chosen)
    return tid
