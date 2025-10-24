import streamlit as st
from db import insert_ticket, list_tickets_db, get_conn
import uuid


def create_ticket_in_teamwork(payload, assigned_consultant):
    # Build ticket details
    service = payload.get("service")
    conv_id = payload.get("conversation_id")
    title = f"({service}) ({payload.get('fields', {}).get('description', '')[:50]})"
    description = f"Conversation #{conv_id}\nFields: {payload.get('fields')}"
    # Create record
    service_id = str(uuid.uuid4())[:8]
    tid = insert_ticket(service_id, title, description, assigned_consultant)
    print(f"[Teamwork] Ticket #{tid} created, assigned to {assigned_consultant}")
    return tid


def list_tickets_ui():
    st.header("Teamwork — Tickets Management")
    rows = list_tickets_db()
    if not rows:
        st.info("No tickets created yet.")
        return

    for t in rows:
        st.subheader(f"Ticket #{t['id']} — {t['ticket_title']}")
        st.write(f"🧩 Assigned to: **{t['assigned_to']}**")
        st.write(f"📅 Created: {t['created_at']}")
        st.write(f"📄 Status: **{t['status']}**")

        with st.expander("View / Update Ticket"):
            st.text_area("Description", t["description"], height=100, disabled=True)

            # Editable ticket fields
            new_status = st.selectbox(
                "Update Status",
                ["New", "In Progress", "Closed"],
                index=["New", "In Progress", "Closed"].index(t["status"]),
                key=f"status_{t['id']}",
            )

            progress = st.slider("Progress (%)", 0, 100, 0, 10, key=f"prog_{t['id']}")

            if st.button(f"💾 Save Changes (Ticket {t['id']})"):
                update_ticket_status(t["id"], new_status)
                st.success(f"Ticket #{t['id']} updated to status '{new_status}'.")
                st.experimental_rerun()

            if new_status == "Closed":
                st.info("✅ This ticket is marked complete and closed.")


def update_ticket_status(ticket_id: int, status: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE tickets SET status=? WHERE id=?", (status, ticket_id))
    conn.commit()
    conn.close()
