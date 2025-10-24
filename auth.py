import streamlit as st

DEMO_USERS = {
    "admin@example.com": "admin123",  # admin (can edit rules)
    "agent@example.com": "agent123",  # normal user (send messages)
}


def init_auth():
    if "auth_db" not in st.session_state:
        st.session_state["auth_db"] = DEMO_USERS.copy()


def login_user(email, password):
    if not email or not password:
        return False, "Please enter email and password."
    db = st.session_state.get("auth_db", {})
    if email in db and db[email] == password:
        return True, "Logged in"
    return False, "Incorrect email or password"


def logout_user():
    pass


def require_login():
    if "auth" not in st.session_state or not st.session_state.auth.get("logged_in"):
        raise RuntimeError("Not logged in")
