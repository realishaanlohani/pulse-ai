"""pages/gym_buddy.py — Gym Buddy feature with camera + pose detection template"""
import streamlit as st
import time
from gym_buddy.pose_detector import PoseDetector


EXERCISES = {
    "Push-ups": {
        "description": "Classic upper body strength exercise targeting chest, triceps, and shoulders.",
        "instructions": [
            "Place hands slightly wider than shoulder-width",
            "Keep body in a straight line from head to heels",
            "Lower chest to just above the ground",
            "Push back up to full arm extension",
            "Keep core tight throughout"
        ],
        "common_mistakes": [
            "Hips sagging down",
            "Elbows flaring too wide",
            "Not reaching full depth",
            "Head dropping forward"
        ],
        "emoji": "💪",
        "target_reps": 12,
        "sets": 3
    }
    # 🔜 Add more exercises here: Squats, Plank, Lunges, etc.
}


def render():
    selected = st.session_state.get("gym_buddy_exercise")

    # ── Exercise Selection Screen ─────────────────────────────────────────────
    if not selected:
        _, mid, _ = st.columns([1, 2, 1])
        with mid:
            # Back button
            if st.button("← Back to Dashboard"):
                st.session_state.page = "dashboard"
                st.rerun()

            st.markdown("""
            <div style="padding:40px 0 24px;text-align:center;">
              <p style="font-family:'Syne',sans-serif;font-size:11px;letter-spacing:3px;
              text-transform:uppercase;color:#e8ff47;margin-bottom:10px;">AI Form Coach</p>
              <h2 style="font-family:'Syne',sans-serif;font-size:32px;font-weight:800;
              color:#EFEFEF;margin-bottom:8px;">Gym Buddy 🏋️</h2>
              <p style="font-size:14px;color:#7a7a8a;line-height:1.6;max-width:320px;margin:0 auto 32px;">
              Choose an exercise and our AI will analyze your form in real time using your camera.</p>
            </div>""", unsafe_allow_html=True)

            for ex_name, ex_data in EXERCISES.items():
                st.markdown(f"""
                <div style="background:#12121a;border:1px solid rgba(255,255,255,0.07);
                border-radius:16px;padding:20px;margin-bottom:12px;">
                  <div style="display:flex;align-items:center;gap:14px;margin-bottom:10px;">
                    <div style="width:50px;height:50px;background:#1a1a26;border-radius:12px;
                    display:flex;align-items:center;justify-content:center;font-size:24px;">
                    {ex_data['emoji']}</div>
                    <div>
                      <div style="font-family:'Syne',sans-serif;font-size:17px;font-weight:700;
                      color:#EFEFEF;">{ex_name}</div>
                      <div style="font-size:12px;color:#7a7a8a;">{ex_data['description']}</div>
                    </div>
                  </div>
                  <div style="display:flex;gap:10px;">
                    <span style="background:#1a1a26;border-radius:50px;padding:4px 12px;
                    font-size:11px;color:#e8ff47;">{ex_data['sets']} sets</span>
                    <span style="background:#1a1a26;border-radius:50px;padding:4px 12px;
                    font-size:11px;color:#47c8ff;">{ex_data['target_reps']} reps</span>
                  </div>
                </div>""", unsafe_allow_html=True)

                if st.button(f"Start {ex_name} Coach →", key=f"start_{ex_name}",
                             use_container_width=True, type="primary"):
                    st.session_state.gym_buddy_exercise = ex_name
                    st.rerun()

            # Coming soon
            st.markdown("""
            <div style="background:#0d0d1a;border:1px dashed rgba(255,255,255,0.1);
            border-radius:16px;padding:20px;margin-bottom:12px;opacity:0.5;text-align:center;">
              <p style="font-size:13px;color:#7a7a8a;">🔜 Squats, Lunges, Plank — coming soon</p>
            </div>""", unsafe_allow_html=True)

    # ── Active Exercise Coach Screen ──────────────────────────────────────────
    else:
        ex_data = EXERCISES.get(selected, {})
        _, mid, _ = st.columns([1, 3, 1])

        with mid:
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("← Back"):
                    st.session_state.gym_buddy_exercise = None
                    st.rerun()
            with col2:
                st.markdown(f"""
                <div style="padding:10px 0;">
                  <span style="font-family:'Syne',sans-serif;font-size:18px;font-weight:700;
                  color:#e8ff47;">{ex_data.get('emoji','')} {selected} Coach</span>
                </div>""", unsafe_allow_html=True)

            # Instructions
            with st.expander("📋 How to do it correctly", expanded=False):
                for i, instruction in enumerate(ex_data.get("instructions", []), 1):
                    st.markdown(f"**{i}.** {instruction}")
                st.markdown("**⚠️ Common mistakes to avoid:**")
                for mistake in ex_data.get("common_mistakes", []):
                    st.markdown(f"- {mistake}")

            # Camera + detection
            _camera_coach(selected, ex_data)

            # Back to dashboard
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("✅ Done — Back to Dashboard", use_container_width=True, type="primary"):
                st.session_state.gym_buddy_exercise = None
                st.session_state.page = "dashboard"
                st.rerun()


def _camera_coach(exercise_name: str, ex_data: dict):
    """Camera interface with pose detection."""
    detector = PoseDetector()

    st.markdown("""
    <div style="background:rgba(232,255,71,0.04);border:1px solid rgba(232,255,71,0.1);
    border-radius:12px;padding:12px 16px;margin-bottom:16px;font-size:13px;color:#b0b0b0;">
    📸 <strong style="color:#e8ff47;">Camera required.</strong>
    Position yourself so your full body is visible. Ensure good lighting.
    </div>""", unsafe_allow_html=True)

    # Stats row
    if "rep_count" not in st.session_state:
        st.session_state.rep_count = 0
    if "set_count" not in st.session_state:
        st.session_state.set_count = 1
    if "form_feedback" not in st.session_state:
        st.session_state.form_feedback = []

    col1, col2, col3 = st.columns(3)
    col1.metric("Current Set", f"{st.session_state.set_count}/{ex_data.get('sets',3)}")
    col2.metric("Reps Done", st.session_state.rep_count)
    col3.metric("Target", ex_data.get("target_reps", 12))

    # Capture frame
    img_file = st.camera_input("Position yourself for the camera", key="gym_camera")

    if img_file:
        import numpy as np
        from PIL import Image
        import io

        img = Image.open(img_file)
        img_array = np.array(img)

        # Run pose detection
        with st.spinner("Analyzing your form..."):
            result = detector.analyze_pushup(img_array)

        # Display annotated image
        if result.get("annotated_image") is not None:
            st.image(result["annotated_image"], caption="Pose detected", use_column_width=True)
        else:
            st.image(img_array, caption="Frame captured", use_column_width=True)

        # Form feedback
        form_status = result.get("form_status", "unknown")
        feedback = result.get("feedback", [])
        rep_counted = result.get("rep_counted", False)

        if rep_counted:
            st.session_state.rep_count += 1
            if st.session_state.rep_count >= ex_data.get("target_reps", 12):
                st.success(f"✅ Set {st.session_state.set_count} complete!")
                if st.session_state.set_count < ex_data.get("sets", 3):
                    st.session_state.set_count += 1
                    st.session_state.rep_count = 0

        # Status badge
        if form_status == "correct":
            st.markdown("""
            <div style="background:rgba(29,158,117,0.1);border:1px solid rgba(29,158,117,0.3);
            border-radius:10px;padding:12px 16px;margin-bottom:12px;">
              <span style="font-family:'Syne',sans-serif;font-size:14px;font-weight:700;
              color:#1D9E75;">✅ GREAT FORM</span>
              <p style="font-size:12px;color:#7a7a8a;margin-top:4px;">Keep it up!</p>
            </div>""", unsafe_allow_html=True)
        elif form_status == "incorrect":
            st.markdown(f"""
            <div style="background:rgba(226,75,74,0.1);border:1px solid rgba(226,75,74,0.3);
            border-radius:10px;padding:12px 16px;margin-bottom:12px;">
              <span style="font-family:'Syne',sans-serif;font-size:14px;font-weight:700;
              color:#E24B4A;">⚠️ FORM CHECK</span>
              {''.join([f"<p style='font-size:13px;color:#b0b0b0;margin-top:6px;'>• {f}</p>" for f in feedback])}
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background:#12121a;border:1px solid rgba(255,255,255,0.07);
            border-radius:10px;padding:12px 16px;margin-bottom:12px;">
              <span style="font-size:13px;color:#7a7a8a;">👁 Detecting pose... Make sure your full body is visible.</span>
            </div>""", unsafe_allow_html=True)

        # AI coaching tip
        if feedback:
            from utils.gemini_ai import analyze_exercise_form
            ai_tip = analyze_exercise_form(exercise_name, st.session_state.rep_count, feedback)
            st.markdown(f"""
            <div style="background:rgba(71,200,255,0.04);border:1px solid rgba(71,200,255,0.12);
            border-radius:10px;padding:12px 16px;margin-top:8px;">
              <span style="font-size:11px;color:#47c8ff;text-transform:uppercase;
              letter-spacing:1px;">AI Coach</span>
              <p style="font-size:13px;color:#b0b0b0;margin-top:4px;">{ai_tip}</p>
            </div>""", unsafe_allow_html=True)

    # Manual rep counter fallback
    st.markdown("---")
    st.markdown("<p style='font-size:13px;color:#7a7a8a;'>Or count manually:</p>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        if st.button("➕ Rep", use_container_width=True):
            st.session_state.rep_count += 1
            st.rerun()
    with c2:
        if st.button("Next Set ✅", use_container_width=True):
            if st.session_state.set_count < ex_data.get("sets", 3):
                st.session_state.set_count += 1
                st.session_state.rep_count = 0
            st.rerun()
    with c3:
        if st.button("Reset 🔄", use_container_width=True):
            st.session_state.rep_count = 0
            st.session_state.set_count = 1
            st.rerun()
