"""
session_manager.py
Manages Streamlit session state for Pulse AI.
"""

import streamlit as st
from datetime import datetime, date
import uuid


def init_session():
    """Initialize all session state variables."""
    defaults = {
        "user_id": str(uuid.uuid4())[:8],
        "page": "welcome",           # welcome | onboarding | dashboard | gym_buddy | weekly_review
        "week_number": 1,
        "profile": {},
        "analysis": {},
        "diet_plan": {},
        "exercise_plan": {},
        "weekly_review": {},
        "free_start": "06:00 AM",
        "free_end": "07:00 AM",
        "onboarding_step": 1,
        "notifications": [],
        "exercise_logs": {},          # { "YYYY-MM-DD": { "Exercise Name": True/False } }
        "plan_generated": False,
        "setup_complete": False,
        "app_start_date": date.today().isoformat(),
        "gym_buddy_exercise": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def go_to(page: str):
    st.session_state.page = page
    st.rerun()


def get_today_str() -> str:
    return date.today().isoformat()


def days_since_start() -> int:
    start = date.fromisoformat(st.session_state.get("app_start_date", date.today().isoformat()))
    return (date.today() - start).days


def is_new_week() -> bool:
    """Returns True if 7 days have passed since app_start_date."""
    return days_since_start() >= 7


def add_notification(message: str, notif_type: str = "info"):
    if "notifications" not in st.session_state:
        st.session_state.notifications = []
    st.session_state.notifications.append({
        "message": message,
        "type": notif_type,
        "timestamp": datetime.now().strftime("%H:%M"),
        "read": False
    })


def mark_notifications_read():
    for n in st.session_state.get("notifications", []):
        n["read"] = True
