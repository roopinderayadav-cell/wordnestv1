"""Wordnest - sign up, sign in and roles."""
import hashlib
import hmac
import os
import re

import streamlit as st

import wn_db

DEFAULT_ADMIN_EMAIL = "admin@wordnest.demo"
DEFAULT_ADMIN_PASSWORD = "ChangeMe123!"


def secret(name, default=None):
    """Read a value from Streamlit secrets (Settings > Secrets on Streamlit Cloud) or the environment."""
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.environ.get(name, default)


def hash_password(password, salt=None):
    salt = salt or os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 200_000).hex()
    return f"{salt}${digest}"


def check_password(password, stored):
    try:
        salt, _ = stored.split("$", 1)
    except ValueError:
        return False
    return hmac.compare_digest(hash_password(password, salt), stored)


def valid_email(email):
    return re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email or "") is not None


def ensure_admin():
    """Create the site owner's admin account from secrets (once)."""
    email = (secret("ADMIN_EMAIL", DEFAULT_ADMIN_EMAIL) or DEFAULT_ADMIN_EMAIL).strip().lower()
    password = secret("ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD) or DEFAULT_ADMIN_PASSWORD
    name = secret("ADMIN_NAME", "Site Admin")
    if not wn_db.q("SELECT id FROM users WHERE email=?", (email,), one=True):
        wn_db.x("INSERT INTO users(email, name, pen_name, password_hash, role, created_at) VALUES (?,?,?,?, 'admin', ?)",
                (email, name, name, hash_password(password), wn_db.now()))
    return email


def using_default_admin():
    return not secret("ADMIN_PASSWORD")


def register(email, name, pen_name, password):
    email = (email or "").strip().lower()
    if not valid_email(email):
        return None, "Please enter a valid email address."
    if len(password or "") < 8:
        return None, "Password must be at least 8 characters."
    if not (name or "").strip():
        return None, "Please enter your name."
    if wn_db.q("SELECT id FROM users WHERE email=?", (email,), one=True):
        return None, "An account with this email already exists. Please sign in."
    uid = wn_db.x("INSERT INTO users(email, name, pen_name, password_hash, role, created_at) VALUES (?,?,?,?, 'reader', ?)",
                  (email, name.strip(), (pen_name or name).strip(), hash_password(password), wn_db.now()))
    wn_db.notify(uid, "Welcome to Wordnest",
                 "You can now read, buy books and write for Wordnest. Before you write, please read the "
                 "Content guidelines: every article is checked by our AI review bot and an editor before it goes live.")
    return uid, None


def login(email, password):
    user = wn_db.q("SELECT * FROM users WHERE email=?", ((email or "").strip().lower(),), one=True)
    if not user or not check_password(password or "", user["password_hash"]):
        return None, "Email or password is incorrect."
    st.session_state["user_id"] = user["id"]
    return user, None


def logout():
    st.session_state.pop("user_id", None)


def current_user():
    uid = st.session_state.get("user_id")
    if not uid:
        return None
    return wn_db.q("SELECT id, email, name, pen_name, bio, role, status, strikes FROM users WHERE id=?", (uid,), one=True)


def is_staff(user):
    return bool(user) and user["role"] in ("admin", "editor")


def is_admin(user):
    return bool(user) and user["role"] == "admin"


def display_name(user):
    return (user.get("pen_name") or user.get("name") or "Author") if user else "Guest"
