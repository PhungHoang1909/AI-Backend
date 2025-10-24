import streamlit as st
from db import insert_conversation, list_conversations_db, update_conversation_status
from ai_bot import analyze_conversation


def receive_message_ui():
    st.header("Input Collector (Simulate Qiscus / Email / WhatsApp)")

    st.markdown("### 🧾 Quick Message Templates")

    if st.button("💬 Missing Info Example"):
        st.session_state["msg_template"] = "I need help!"
    if st.button("✅ Complete Ticket Example"):
        st.session_state["msg_template"] = (
            "Please create a finance report for Q3. "
            "Customer ID: 98765. Start Date: 2025-10-01. End Date: 2025-10-10."
        )

    st.markdown("---")

    # Message sending form
    with st.form("send_msg_form", clear_on_submit=True):
        col1, col2 = st.columns([2, 1])
        with col1:
            sender = st.text_input("Sender (email or phone)", value="user@example.com")
            channel = st.selectbox("Channel", ["email", "whatsapp"])
            subject = st.text_input(
                "Subject (for email)", value="Support: Cannot access service"
            )
            message_default = st.session_state.get("msg_template", "")
            message = st.text_area("Message body", height=150, value=message_default)
        submitted = st.form_submit_button("📨 Send message")

    if submitted:
        normalized = {
            "sender": sender,
            "channel": channel,
            "subject": subject,
            "message_preview": message[:500],
        }
        cid = insert_conversation(sender, channel, subject, message, normalized)
        st.success(f"✅ Message received and stored as conversation #{cid}")

        # Immediately simulate AI Bot processing
        payload = analyze_conversation(cid)
        if payload:
            if payload["complete"]:
                st.info("🤖 AI Bot marked this request as *ready for ticket creation*.")
            else:
                st.warning(
                    "🤖 AI Bot needs clarification: " + ", ".join(payload["missing"])
                )
        st.session_state.pop("msg_template", None)  # reset template

    st.markdown("---")
    st.subheader("🗂️ Recent Conversations")
    for conv in list_conversations_db()[:10]:
        st.write(
            f"**#{conv['id']}** | {conv['channel']} | {conv['sender']} | "
            f"Status: `{conv['status']}` | {conv['created_at']}"
        )
        with st.expander("Show details"):
            st.text(f"Subject: {conv['subject']}")
            st.text(conv["raw_message"])


def list_conversations():
    st.header("All Conversations (Database View)")
    rows = list_conversations_db()
    if not rows:
        st.info("No conversations yet.")
        return
    for r in rows:
        st.write(
            f"**#{r['id']}** — {r['sender']} ({r['channel']}) — status: {r['status']} — created: {r['created_at']}"
        )
        with st.expander("Details"):
            st.text(r["subject"])
            st.text(r["raw_message"])
            st.text("Normalized: " + r["normalized_json"])
            if st.button(f"Mark waiting for info ({r['id']})", key=f"mark{r['id']}"):
                update_conversation_status(r["id"], "waiting_for_info")
                st.experimental_rerun()
