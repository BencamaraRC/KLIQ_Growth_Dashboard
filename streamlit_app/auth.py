"""
KLIQ Dashboard Authentication System
- Users register with email + password
- Admin approves/rejects registrations
- All pages gated behind login + approval
"""

import os
import sqlite3
import hashlib
import secrets
import streamlit as st

DB_PATH = os.environ.get(
    "AUTH_DB_PATH", os.path.join(os.path.dirname(__file__), "users.db")
)
ADMIN_EMAILS = [
    e.strip().lower()
    for e in os.environ.get("ADMIN_EMAILS", "ben@joinkliq.io").split(",")
]


def _get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            full_name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )
    conn.commit()
    return conn


def _hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), 100_000
    ).hex()


def register_user(email: str, password: str, full_name: str) -> tuple[bool, str]:
    conn = _get_db()
    email = email.strip().lower()
    salt = secrets.token_hex(16)
    password_hash = _hash_password(password, salt)

    # Auto-approve admin emails
    status = "approved" if email in ADMIN_EMAILS else "pending"

    try:
        conn.execute(
            "INSERT INTO users (email, password_hash, salt, full_name, status) VALUES (?, ?, ?, ?, ?)",
            (email, password_hash, salt, full_name, status),
        )
        conn.commit()
        if status == "approved":
            return True, "Account created and auto-approved (admin)."
        return True, "Registration submitted! An admin will review your access."
    except sqlite3.IntegrityError:
        return False, "An account with this email already exists."
    finally:
        conn.close()


def authenticate(email: str, password: str) -> tuple[bool, str, str]:
    """Returns (success, status, full_name)."""
    conn = _get_db()
    email = email.strip().lower()
    row = conn.execute(
        "SELECT password_hash, salt, status, full_name FROM users WHERE email = ?",
        (email,),
    ).fetchone()
    conn.close()

    if not row:
        return False, "", ""

    password_hash, salt, status, full_name = row
    if _hash_password(password, salt) != password_hash:
        return False, "", ""

    return True, status, full_name


def get_pending_users() -> list[dict]:
    conn = _get_db()
    rows = conn.execute(
        "SELECT id, email, full_name, created_at FROM users WHERE status = 'pending' ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [
        {"id": r[0], "email": r[1], "full_name": r[2], "created_at": r[3]} for r in rows
    ]


def get_all_users() -> list[dict]:
    conn = _get_db()
    rows = conn.execute(
        "SELECT id, email, full_name, status, created_at FROM users ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "email": r[1],
            "full_name": r[2],
            "status": r[3],
            "created_at": r[4],
        }
        for r in rows
    ]


def update_user_status(user_id: int, status: str):
    conn = _get_db()
    conn.execute("UPDATE users SET status = ? WHERE id = ?", (status, user_id))
    conn.commit()
    conn.close()


def delete_user(user_id: int):
    conn = _get_db()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


def is_admin(email: str) -> bool:
    return email.strip().lower() in ADMIN_EMAILS


def require_auth():
    """Gate a page behind authentication. Call at the top of every page.
    Returns True if user is authenticated and approved, otherwise stops the page."""

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.user_email = ""
        st.session_state.user_name = ""

    if st.session_state.authenticated:
        return True

    _show_login_page()
    st.stop()
    return False


def _show_login_page():
    """Render the login/register UI."""
    from kliq_ui_kit import (
        inject_css,
        GREEN,
        DARK,
        IVORY,
        NEUTRAL,
        BG_CARD,
        SHADOW_CARD,
        CARD_RADIUS,
    )

    inject_css()

    st.markdown(
        f"""
        <div style="text-align:center; padding:48px 0 24px;">
            <h1 style="font-size:20px; font-weight:700; color:{DARK}; margin:0; letter-spacing:0;">
                KLIQ Growth Dashboard
            </h1>
            <p style="color:{NEUTRAL}; font-size:13px; margin-top:8px; font-weight:500;">
                Sign in to access the dashboard
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_login, tab_register = st.tabs(["🔑 Sign In", "📝 Register"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In", use_container_width=True)

            if submitted:
                if not email or not password:
                    st.error("Please enter both email and password.")
                else:
                    success, status, full_name = authenticate(email, password)
                    if not success:
                        st.error("Invalid email or password.")
                    elif status == "pending":
                        st.warning(
                            "Your account is pending admin approval. Please check back later."
                        )
                    elif status == "rejected":
                        st.error(
                            "Your access request has been declined. Contact an admin."
                        )
                    elif status == "approved":
                        st.session_state.authenticated = True
                        st.session_state.user_email = email.strip().lower()
                        st.session_state.user_name = full_name
                        st.rerun()

    with tab_register:
        with st.form("register_form"):
            reg_name = st.text_input("Full Name")
            reg_email = st.text_input("Work Email")
            reg_password = st.text_input("Create Password", type="password")
            reg_password2 = st.text_input("Confirm Password", type="password")
            reg_submitted = st.form_submit_button(
                "Request Access", use_container_width=True
            )

            if reg_submitted:
                if not reg_name or not reg_email or not reg_password:
                    st.error("Please fill in all fields.")
                elif reg_password != reg_password2:
                    st.error("Passwords do not match.")
                elif len(reg_password) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    ok, msg = register_user(reg_email, reg_password, reg_name)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)


def show_admin_panel():
    """Render admin panel for managing users. Only visible to admins."""
    if not is_admin(st.session_state.get("user_email", "")):
        return

    with st.expander("🔐 Admin: User Management", expanded=False):
        pending = get_pending_users()
        if pending:
            st.markdown(f"**{len(pending)} pending request(s):**")
            for user in pending:
                col1, col2, col3 = st.columns([3, 1, 1])
                col1.markdown(f"**{user['full_name']}** ({user['email']})")
                if col2.button("✅ Approve", key=f"approve_{user['id']}"):
                    update_user_status(user["id"], "approved")
                    st.rerun()
                if col3.button("❌ Reject", key=f"reject_{user['id']}"):
                    update_user_status(user["id"], "rejected")
                    st.rerun()
        else:
            st.info("No pending access requests.")

        st.markdown("---")
        st.markdown("**All Users:**")
        all_users = get_all_users()
        if all_users:
            import pandas as pd

            users_df = pd.DataFrame(all_users)
            users_df = users_df.rename(
                columns={
                    "full_name": "Name",
                    "email": "Email",
                    "status": "Status",
                    "created_at": "Registered",
                }
            )
            st.dataframe(
                users_df[["Name", "Email", "Status", "Registered"]],
                use_container_width=True,
                hide_index=True,
            )

            # Delete user (non-admin only)
            st.markdown("")
            del_col1, del_col2 = st.columns([3, 1])
            non_admin_users = [u for u in all_users if u["email"] not in ADMIN_EMAILS]
            if non_admin_users:
                selected = del_col1.selectbox(
                    "Remove user",
                    options=non_admin_users,
                    format_func=lambda u: f"{u['full_name']} ({u['email']})",
                    key="delete_user_select",
                )
                if del_col2.button("🗑️ Remove", key="delete_user_btn"):
                    delete_user(selected["id"])
                    st.rerun()


def logout_button():
    """Show logout button in sidebar."""
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"👤 **{st.session_state.get('user_name', '')}**")
    st.sidebar.caption(st.session_state.get("user_email", ""))
    if st.sidebar.button("🚪 Sign Out"):
        st.session_state.authenticated = False
        st.session_state.user_email = ""
        st.session_state.user_name = ""
        st.rerun()
