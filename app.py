import streamlit as st
from auth import login_user, logout_user, require_login, init_auth
from input_collector import receive_message_ui, list_conversations
from consultant_portal import admin_rules_ui
from middleware import process_ready_payloads_ui
from teamwork import list_tickets_ui
from db import init_db

st.set_page_config(layout="wide", page_title="AI Backend Demo")

init_db()
init_auth()

PAGES = {
    "Chat / Input Collector": receive_message_ui,
    "Conversations": list_conversations,
    "Process (Middleware)": process_ready_payloads_ui,
    "Tickets (Teamwork)": list_tickets_ui,
    "Consultant Assignment Portal (Admin)": admin_rules_ui,
}

st.title("AI Backend — Demo (Modular Streamlit App)")

# Sidebar auth & navigation
if "auth" not in st.session_state:
    st.session_state.auth = {"logged_in": False, "user": None}

if not st.session_state.auth["logged_in"]:
    st.sidebar.header("Login")
    email = st.sidebar.text_input("Email")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        ok, msg = login_user(email.strip(), password.strip())
        if ok:
            st.session_state.auth["logged_in"] = True
            st.session_state.auth["user"] = email
            st.experimental_rerun()
        else:
            st.sidebar.error(msg)
else:
    st.sidebar.write(f"Signed in as **{st.session_state.auth['user']}**")
    if st.sidebar.button("Logout"):
        logout_user()
        st.session_state.auth = {"logged_in": False, "user": None}
        st.experimental_rerun()

# Logged in
if st.session_state.auth["logged_in"]:
    page = st.sidebar.radio("Navigation", list(PAGES.keys()))
    PAGES[page]()
else:
    st.info("Please log in (try demo users in README).")