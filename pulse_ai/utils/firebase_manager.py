"""
firebase_manager.py
Handles all Firebase Firestore operations for Pulse AI.
Falls back to local history.json if Firebase is not configured.
"""

import json
import os
from datetime import datetime
from pathlib import Path
import streamlit as st

HISTORY_PATH = Path("history.json")

# ── Try to load Firebase ─────────────────────────────────────────────────────
_firebase_available = False
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    _firebase_available = True
except ImportError:
    pass


class FirebaseManager:
    def __init__(self):
        self.db = None
        self._init_firebase()

    def _init_firebase(self):
        """Initialize Firebase if credentials exist, else use local JSON."""
        global _firebase_available
        if not _firebase_available:
            return

        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase_credentials.json")
        if not Path(cred_path).exists():
            return

        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
            self.db = firestore.client()
        except Exception as e:
            st.warning(f"Firebase init failed, using local storage: {e}")
            self.db = None

    # ── User Profile ──────────────────────────────────────────────────────────

    def save_user_profile(self, user_id: str, profile: dict):
        """Save or update user onboarding profile."""
        profile["updated_at"] = datetime.now().isoformat()
        if self.db:
            self.db.collection("users").document(user_id).set(profile, merge=True)
        self._save_local(user_id, "profile", profile)

    def get_user_profile(self, user_id: str) -> dict:
        """Retrieve user profile."""
        if self.db:
            doc = self.db.collection("users").document(user_id).get()
            if doc.exists:
                return doc.to_dict()
        return self._load_local(user_id, "profile")

    # ── Weekly History ────────────────────────────────────────────────────────

    def save_weekly_snapshot(self, user_id: str, week_number: int, snapshot: dict):
        """Save a weekly snapshot to history."""
        snapshot["week"] = week_number
        snapshot["timestamp"] = datetime.now().isoformat()

        if self.db:
            self.db.collection("users").document(user_id)\
                .collection("history").document(f"week_{week_number}").set(snapshot)

        # Always save locally too
        history = self._load_full_history()
        if user_id not in history:
            history[user_id] = {}
        history[user_id][f"week_{week_number}"] = snapshot
        self._write_history_file(history)

    def get_all_history(self, user_id: str) -> dict:
        """Get all weekly history for a user."""
        if self.db:
            try:
                docs = self.db.collection("users").document(user_id)\
                    .collection("history").stream()
                return {doc.id: doc.to_dict() for doc in docs}
            except Exception:
                pass
        history = self._load_full_history()
        return history.get(user_id, {})

    def get_previous_week(self, user_id: str, current_week: int) -> dict:
        """Get last week's snapshot for comparison."""
        if current_week <= 1:
            return {}
        all_history = self.get_all_history(user_id)
        return all_history.get(f"week_{current_week - 1}", {})

    # ── Exercise Tracking ─────────────────────────────────────────────────────

    def save_exercise_log(self, user_id: str, date_str: str, exercises: dict):
        """Log which exercises were completed on a given day."""
        log = {"date": date_str, "exercises": exercises, "logged_at": datetime.now().isoformat()}
        if self.db:
            self.db.collection("users").document(user_id)\
                .collection("exercise_logs").document(date_str).set(log)
        self._save_local(user_id, f"exercise_log_{date_str}", log)

    def get_exercise_log(self, user_id: str, date_str: str) -> dict:
        """Get exercise log for a specific day."""
        if self.db:
            doc = self.db.collection("users").document(user_id)\
                .collection("exercise_logs").document(date_str).get()
            if doc.exists:
                return doc.to_dict()
        return self._load_local(user_id, f"exercise_log_{date_str}")

    # ── Notifications ─────────────────────────────────────────────────────────

    def save_notification(self, user_id: str, message: str, notif_type: str = "info"):
        """Store a notification for the user."""
        notif = {
            "message": message,
            "type": notif_type,
            "timestamp": datetime.now().isoformat(),
            "read": False
        }
        if self.db:
            self.db.collection("users").document(user_id)\
                .collection("notifications").add(notif)
        # Also track in session
        if "notifications" not in st.session_state:
            st.session_state.notifications = []
        st.session_state.notifications.append(notif)

    def get_unread_notifications(self, user_id: str) -> list:
        """Get all unread notifications."""
        if self.db:
            try:
                docs = self.db.collection("users").document(user_id)\
                    .collection("notifications")\
                    .where("read", "==", False).stream()
                return [doc.to_dict() for doc in docs]
            except Exception:
                pass
        return st.session_state.get("notifications", [])

    # ── Local JSON Helpers ────────────────────────────────────────────────────

    def _load_full_history(self) -> dict:
        if HISTORY_PATH.exists():
            try:
                with open(HISTORY_PATH, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _write_history_file(self, data: dict):
        with open(HISTORY_PATH, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def _save_local(self, user_id: str, key: str, data: dict):
        history = self._load_full_history()
        if user_id not in history:
            history[user_id] = {}
        history[user_id][key] = data
        self._write_history_file(history)

    def _load_local(self, user_id: str, key: str) -> dict:
        history = self._load_full_history()
        return history.get(user_id, {}).get(key, {})
