"""
KLIQ Dashboard Authentication System
- Users register with email + password
- Admin approves/rejects registrations
- All pages gated behind login + approval
- Forgot password via email reset link
- Magic link (passwordless) login via email
"""

import os
import sqlite3
import hashlib
import secrets
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st

DB_PATH = os.environ.get(
    "AUTH_DB_PATH", os.path.join(os.path.dirname(__file__), "users.db")
)
ADMIN_EMAILS = [
    e.strip().lower()
    for e in os.environ.get("ADMIN_EMAILS", "ben@joinkliq.io").split(",")
]

# SMTP config for sending emails (set these env vars or defaults to Gmail SMTP)
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")  # e.g. ben@joinkliq.io
SMTP_PASS = os.environ.get("SMTP_PASS", "")  # App Password (not your Google password)
SMTP_FROM = os.environ.get("SMTP_FROM", SMTP_USER or "noreply@joinkliq.io")

# Base URL for links in emails (auto-detected or set via env)
APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:8501")


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
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS remember_tokens (
            token TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL
        )
    """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS magic_links (
            token TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            purpose TEXT NOT NULL DEFAULT 'login',
            expires_at TIMESTAMP NOT NULL,
            used INTEGER NOT NULL DEFAULT 0
        )
    """
    )
    conn.commit()
    return conn


_TOKEN_EXPIRY_DAYS = 30
_TOKEN_FILE = os.path.join(os.path.dirname(DB_PATH), ".kliq_remember_token")


def _write_token_file(token: str):
    """Persist a remember-me token to a local file."""
    try:
        with open(_TOKEN_FILE, "w") as f:
            f.write(token)
    except OSError:
        pass


def _read_token_file() -> str:
    """Read the persisted remember-me token, or return empty string."""
    try:
        with open(_TOKEN_FILE, "r") as f:
            return f.read().strip()
    except OSError:
        return ""


def _clear_token_file():
    """Remove the persisted remember-me token file."""
    try:
        os.remove(_TOKEN_FILE)
    except OSError:
        pass


def _create_remember_token(email: str) -> str:
    """Create a remember-me token, store in DB, return the token string."""
    token = secrets.token_hex(32)
    expires = datetime.datetime.utcnow() + datetime.timedelta(days=_TOKEN_EXPIRY_DAYS)
    conn = _get_db()
    conn.execute(
        "INSERT OR REPLACE INTO remember_tokens (token, email, expires_at) VALUES (?, ?, ?)",
        (token, email.strip().lower(), expires.isoformat()),
    )
    conn.commit()
    conn.close()
    return token


def _validate_remember_token(token: str):
    """Check if a remember token is valid. Returns (email, full_name) or (None, None)."""
    if not token:
        return None, None
    conn = _get_db()
    row = conn.execute(
        "SELECT rt.email, u.full_name, rt.expires_at "
        "FROM remember_tokens rt "
        "JOIN users u ON rt.email = u.email "
        "WHERE rt.token = ? AND u.status = 'approved'",
        (token,),
    ).fetchone()
    if not row:
        conn.close()
        return None, None
    email, full_name, expires_at = row
    if datetime.datetime.fromisoformat(expires_at) < datetime.datetime.utcnow():
        conn.execute("DELETE FROM remember_tokens WHERE token = ?", (token,))
        conn.commit()
        conn.close()
        return None, None
    conn.close()
    return email, full_name


def _delete_remember_token(token: str):
    if not token:
        return
    conn = _get_db()
    conn.execute("DELETE FROM remember_tokens WHERE token = ?", (token,))
    conn.commit()
    conn.close()


# ── Email Sending ──


def _send_email(to_email: str, subject: str, html_body: str) -> bool:
    """Send an email via SMTP. Returns True on success."""
    if not SMTP_USER or not SMTP_PASS:
        st.warning(
            "Email not configured. Set SMTP_USER and SMTP_PASS environment variables. "
            "For Gmail, use an App Password (Google Account > Security > App Passwords)."
        )
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"KLIQ Dashboard <{SMTP_FROM}>"
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_FROM, to_email, msg.as_string())
        return True
    except Exception as e:
        st.error(f"Failed to send email: {e}")
        return False


# ── Magic Link / Reset Token ──

_MAGIC_LINK_EXPIRY_MINUTES = 15


def _create_magic_token(email: str, purpose: str = "login") -> str:
    """Create a magic link token, store in DB, return the token."""
    token = secrets.token_urlsafe(48)
    expires = datetime.datetime.utcnow() + datetime.timedelta(
        minutes=_MAGIC_LINK_EXPIRY_MINUTES
    )
    conn = _get_db()
    conn.execute(
        "INSERT INTO magic_links (token, email, purpose, expires_at) VALUES (?, ?, ?, ?)",
        (token, email.strip().lower(), purpose, expires.isoformat()),
    )
    conn.commit()
    conn.close()
    return token


def _validate_magic_token(token: str, purpose: str = "login"):
    """Validate a magic token. Returns email or None. Marks as used."""
    if not token:
        return None
    conn = _get_db()
    row = conn.execute(
        "SELECT email, expires_at, used FROM magic_links WHERE token = ? AND purpose = ?",
        (token, purpose),
    ).fetchone()
    if not row:
        conn.close()
        return None
    email, expires_at, used = row
    if used:
        conn.close()
        return None
    if datetime.datetime.fromisoformat(expires_at) < datetime.datetime.utcnow():
        conn.execute("DELETE FROM magic_links WHERE token = ?", (token,))
        conn.commit()
        conn.close()
        return None
    # Mark as used
    conn.execute("UPDATE magic_links SET used = 1 WHERE token = ?", (token,))
    conn.commit()
    conn.close()
    return email


def send_magic_link(email: str) -> bool:
    """Send a magic login link to the user's email."""
    email = email.strip().lower()
    conn = _get_db()
    row = conn.execute(
        "SELECT full_name, status FROM users WHERE email = ?", (email,)
    ).fetchone()
    conn.close()
    if not row:
        return False
    full_name, status = row
    if status != "approved":
        return False

    token = _create_magic_token(email, purpose="login")
    link = f"{APP_BASE_URL}?magic_token={token}"

    html = f"""
    <div style="font-family:sans-serif; max-width:480px; margin:0 auto; padding:32px;">
        <h2 style="color:#1C3838; margin-bottom:8px;">KLIQ Growth Dashboard</h2>
        <p>Hi {full_name},</p>
        <p>Click the button below to sign in. This link expires in {_MAGIC_LINK_EXPIRY_MINUTES} minutes.</p>
        <a href="{link}" style="
            display:inline-block; padding:12px 32px; background:#1C3838;
            color:#FFFFF0; text-decoration:none; border-radius:8px;
            font-weight:600; font-size:14px; margin:16px 0;
        ">Sign In to Dashboard</a>
        <p style="font-size:12px; color:#888; margin-top:24px;">
            If the button doesn't work, copy and paste this link:<br>
            <code style="word-break:break-all;">{link}</code>
        </p>
        <p style="font-size:11px; color:#aaa;">If you didn't request this, you can safely ignore this email.</p>
    </div>
    """
    return _send_email(email, "Sign in to KLIQ Dashboard", html)


def send_password_reset(email: str) -> bool:
    """Send a password reset link to the user's email."""
    email = email.strip().lower()
    conn = _get_db()
    row = conn.execute(
        "SELECT full_name FROM users WHERE email = ?", (email,)
    ).fetchone()
    conn.close()
    if not row:
        return False
    full_name = row[0]

    token = _create_magic_token(email, purpose="reset")
    link = f"{APP_BASE_URL}?reset_token={token}"

    html = f"""
    <div style="font-family:sans-serif; max-width:480px; margin:0 auto; padding:32px;">
        <h2 style="color:#1C3838; margin-bottom:8px;">KLIQ Growth Dashboard</h2>
        <p>Hi {full_name},</p>
        <p>You requested a password reset. Click the button below to set a new password.
           This link expires in {_MAGIC_LINK_EXPIRY_MINUTES} minutes.</p>
        <a href="{link}" style="
            display:inline-block; padding:12px 32px; background:#1C3838;
            color:#FFFFF0; text-decoration:none; border-radius:8px;
            font-weight:600; font-size:14px; margin:16px 0;
        ">Reset Password</a>
        <p style="font-size:12px; color:#888; margin-top:24px;">
            If the button doesn't work, copy and paste this link:<br>
            <code style="word-break:break-all;">{link}</code>
        </p>
        <p style="font-size:11px; color:#aaa;">If you didn't request this, you can safely ignore this email.</p>
    </div>
    """
    return _send_email(email, "Reset your KLIQ Dashboard password", html)


def reset_password(email: str, new_password: str) -> bool:
    """Reset a user's password."""
    email = email.strip().lower()
    salt = secrets.token_hex(16)
    password_hash = _hash_password(new_password, salt)
    conn = _get_db()
    conn.execute(
        "UPDATE users SET password_hash = ?, salt = ? WHERE email = ?",
        (password_hash, salt, email),
    )
    conn.commit()
    conn.close()
    return True


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

    # Try file-based auto-login
    token = _read_token_file()
    if token:
        email, full_name = _validate_remember_token(token)
        if email:
            st.session_state.authenticated = True
            st.session_state.user_email = email
            st.session_state.user_name = full_name
            return True

    # Check for magic link token in URL
    params = st.query_params
    magic_token = params.get("magic_token")
    if magic_token:
        email = _validate_magic_token(magic_token, purpose="login")
        if email:
            conn = _get_db()
            row = conn.execute(
                "SELECT full_name FROM users WHERE email = ? AND status = 'approved'",
                (email,),
            ).fetchone()
            conn.close()
            if row:
                st.session_state.authenticated = True
                st.session_state.user_email = email
                st.session_state.user_name = row[0]
                # Set remember token automatically for magic link logins
                rem_token = _create_remember_token(email)
                _write_token_file(rem_token)
                st.query_params.clear()
                st.rerun()
                return True
        else:
            st.error(
                "This magic link has expired or already been used. Please request a new one."
            )

    # Check for password reset token in URL
    reset_token = params.get("reset_token")
    if reset_token:
        _show_reset_password_page(reset_token)
        st.stop()
        return False

    _show_login_page()
    st.stop()
    return False


def _show_reset_password_page(reset_token: str):
    """Render the password reset form when user clicks a reset link."""
    from kliq_ui_kit import inject_css, GREEN, DARK, IVORY, NEUTRAL

    inject_css()

    email = _validate_magic_token(reset_token, purpose="reset")
    if not email:
        st.error(
            "This reset link has expired or already been used. Please request a new one."
        )
        if st.button("Back to Sign In"):
            st.query_params.clear()
            st.rerun()
        return

    st.markdown(
        f"""
        <div style="text-align:center; padding:48px 0 24px;">
            <h1 style="font-size:20px; font-weight:700; color:{DARK}; margin:0;">
                Reset Your Password
            </h1>
            <p style="color:{NEUTRAL}; font-size:13px; margin-top:8px;">
                Setting new password for <strong>{email}</strong>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("reset_password_form"):
        new_pw = st.text_input("New Password", type="password")
        confirm_pw = st.text_input("Confirm New Password", type="password")
        submitted = st.form_submit_button("Set New Password", use_container_width=True)

        if submitted:
            if not new_pw or not confirm_pw:
                st.error("Please fill in both fields.")
            elif new_pw != confirm_pw:
                st.error("Passwords do not match.")
            elif len(new_pw) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                reset_password(email, new_pw)
                st.success(
                    "Password updated! You can now sign in with your new password."
                )
                st.query_params.clear()
                st.rerun()


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

    tab_login, tab_magic, tab_forgot, tab_register = st.tabs(
        ["🔑 Sign In", "✨ Magic Link", "� Forgot Password", "�� Register"]
    )

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            remember = st.checkbox("Remember me", value=True)
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
                        if remember:
                            token = _create_remember_token(email)
                            _write_token_file(token)
                        st.rerun()

    with tab_magic:
        st.markdown("**Sign in without a password** — we'll email you a secure link.")
        with st.form("magic_link_form"):
            magic_email = st.text_input("Email", key="magic_email")
            magic_submitted = st.form_submit_button(
                "Send Magic Link", use_container_width=True
            )
            if magic_submitted:
                if not magic_email:
                    st.error("Please enter your email.")
                else:
                    sent = send_magic_link(magic_email)
                    if sent:
                        st.success(
                            f"Magic link sent to **{magic_email}**! "
                            "Check your inbox and click the link to sign in. "
                            f"It expires in {_MAGIC_LINK_EXPIRY_MINUTES} minutes."
                        )
                    else:
                        if SMTP_USER and SMTP_PASS:
                            st.error(
                                "Could not send magic link. Make sure the email is "
                                "registered and approved."
                            )

    with tab_forgot:
        st.markdown(
            "**Forgot your password?** Enter your email and we'll send a reset link."
        )
        with st.form("forgot_form"):
            forgot_email = st.text_input("Email", key="forgot_email")
            forgot_submitted = st.form_submit_button(
                "Send Reset Link", use_container_width=True
            )
            if forgot_submitted:
                if not forgot_email:
                    st.error("Please enter your email.")
                else:
                    sent = send_password_reset(forgot_email)
                    if sent:
                        st.success(
                            f"Password reset link sent to **{forgot_email}**! "
                            "Check your inbox. "
                            f"The link expires in {_MAGIC_LINK_EXPIRY_MINUTES} minutes."
                        )
                    else:
                        if SMTP_USER and SMTP_PASS:
                            st.error(
                                "Could not send reset link. Make sure the email is registered."
                            )

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
        # Clear remember-me token
        token = _read_token_file()
        if token:
            _delete_remember_token(token)
        _clear_token_file()
        st.session_state.authenticated = False
        st.session_state.user_email = ""
        st.session_state.user_name = ""
        st.rerun()
