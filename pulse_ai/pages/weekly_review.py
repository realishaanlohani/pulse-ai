"""pages/weekly_review.py — Weekly check-in with N vs N-1 comparison"""
import streamlit as st
from datetime import date
from utils.firebase_manager import FirebaseManager
from utils.gemini_ai import (analyze_body_state, generate_diet_plan,
                              generate_exercise_plan, generate_weekly_review)


def render(db: FirebaseManager):
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        week = st.session_state.week_number
        profile = st.session_state.profile
        name = profile.get("name", "there")

        # ── Week Complete Banner ───────────────────────────────────────────────
        st.markdown(f"""
        <div style="text-align:center;padding:40px 0 32px;">
          <div style="width:64px;height:64px;border-radius:50%;background:rgba(232,255,71,0.1);
          border:2px solid #e8ff47;display:flex;align-items:center;justify-content:center;
          margin:0 auto 16px;font-size:28px;">🎉</div>
          <p style="font-family:'Syne',sans-serif;font-size:11px;letter-spacing:3px;
          text-transform:uppercase;color:#e8ff47;margin-bottom:10px;">Week {week} Complete</p>
          <h2 style="font-family:'Syne',sans-serif;font-size:28px;font-weight:800;
          color:#EFEFEF;margin-bottom:8px;">Great work, {name}!</h2>
          <p style="font-size:14px;color:#7a7a8a;line-height:1.6;max-width:340px;margin:0 auto;">
          Update your stats below. Pulse AI will compare your progress and build a smarter plan for Week {week + 1}.</p>
        </div>""", unsafe_allow_html=True)

        # ── Previous Week's Review (if week > 1) ──────────────────────────────
        prev_snapshot = db.get_previous_week(st.session_state.user_id, week)
        if prev_snapshot and week > 1:
            review = st.session_state.get("weekly_review") or generate_weekly_review(
                profile, prev_snapshot, week
            )
            st.session_state.weekly_review = review

            status_colors = {
                "Improving": "#1D9E75",
                "Plateau": "#EF9F27",
                "Declining": "#E24B4A"
            }
            status = review.get("progress_status", "Improving")
            color = status_colors.get(status, "#e8ff47")
            weight_change = review.get("weight_change_kg", 0)
            change_sign = "+" if weight_change > 0 else ""

            st.markdown(f"""
            <div style="background:#12121a;border:1px solid {color}33;border-radius:16px;
            padding:20px;margin-bottom:24px;">
              <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
                <span style="font-family:'Syne',sans-serif;font-size:15px;font-weight:700;
                color:#EFEFEF;">📊 Last Week's Progress</span>
                <span style="background:{color}22;border:1px solid {color}44;border-radius:50px;
                padding:4px 12px;font-size:12px;color:{color};font-family:'Syne',sans-serif;">
                {status}</span>
              </div>

              <p style="font-size:14px;color:#b0b0b0;line-height:1.6;margin-bottom:14px;">
              {review.get('progress_message','')}</p>

              <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px;">
                <div>
                  <p style="font-size:11px;color:#7a7a8a;text-transform:uppercase;
                  letter-spacing:1px;margin-bottom:6px;">What worked</p>
                  {''.join([f"<p style='font-size:12px;color:#1D9E75;margin-bottom:3px;'>✓ {w}</p>" for w in review.get('what_worked',[])])}
                </div>
                <div>
                  <p style="font-size:11px;color:#7a7a8a;text-transform:uppercase;
                  letter-spacing:1px;margin-bottom:6px;">To improve</p>
                  {''.join([f"<p style='font-size:12px;color:#EF9F27;margin-bottom:3px;'>→ {w}</p>" for w in review.get('what_to_improve',[])])}
                </div>
              </div>

              <div style="display:flex;gap:12px;">
                <div style="background:#0d0d1a;border-radius:10px;padding:10px 14px;flex:1;text-align:center;">
                  <div style="font-family:'Syne',sans-serif;font-size:18px;font-weight:700;color:{color};">
                  {change_sign}{weight_change} kg</div>
                  <div style="font-size:11px;color:#7a7a8a;">Weight change</div>
                </div>
              </div>

              <div style="margin-top:14px;padding-top:12px;border-top:1px solid rgba(255,255,255,0.05);">
                <p style="font-size:12px;color:#555;font-style:italic;">
                "{review.get('motivational_quote','')}"</p>
              </div>
            </div>""", unsafe_allow_html=True)

        # ── New Week Form ──────────────────────────────────────────────────────
        st.markdown(f"""
        <div style="margin-bottom:20px;">
          <p style="font-family:'Syne',sans-serif;font-size:17px;font-weight:700;
          color:#EFEFEF;margin-bottom:4px;">📋 Update Your Stats — Week {week + 1}</p>
          <p style="font-size:13px;color:#7a7a8a;">Re-enter your current measurements to get a recalibrated plan.</p>
        </div>""", unsafe_allow_html=True)

        with st.form("weekly_review_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_weight = st.number_input("Current weight (kg)",
                    min_value=30.0, max_value=250.0, step=0.5,
                    value=float(profile.get("weight_kg", 68)))
                new_sleep = st.slider("Average sleep this week (hours)",
                    min_value=4, max_value=10,
                    value=profile.get("sleep_hours", 7))
            with col2:
                new_energy = st.select_slider("Energy levels this week",
                    options=["Very Low", "Low", "Moderate", "High", "Very High"],
                    value="Moderate")
                new_stress = st.select_slider("Stress levels this week",
                    options=["Very Low", "Low", "Moderate", "High", "Very High"],
                    value=profile.get("stress_level", "Moderate"))

            # Goal still the same?
            same_goal = st.checkbox("Same goal as last week", value=True)
            if not same_goal:
                new_goal = st.selectbox("New goal", [
                    "🔥 Fat Loss", "💪 Muscle Gain", "⚡ Improve Fitness",
                    "🧘 General Wellness", "🏃 Athletic Performance"
                ])
            else:
                new_goal = profile.get("goal", "")

            # Time slot
            st.markdown("<p style='font-size:13px;color:#7a7a8a;margin-top:8px;'>Free workout time this week:</p>",
                        unsafe_allow_html=True)
            col3, col4 = st.columns(2)
            with col3:
                new_start = st.text_input("Start time", value=st.session_state.free_start,
                                          placeholder="e.g. 06:00 AM")
            with col4:
                new_end = st.text_input("End time", value=st.session_state.free_end,
                                        placeholder="e.g. 07:00 AM")

            notes = st.text_area("Any notes for this week? (injuries, travel, etc.)",
                                 placeholder="Optional...", height=80)

            submitted = st.form_submit_button("⚡ Generate Week's Plan", use_container_width=True,
                                              type="primary")

        if submitted:
            # Update profile
            updated_profile = {**profile}
            updated_profile.update({
                "weight_kg": new_weight,
                "goal": new_goal or profile.get("goal", ""),
                "sleep_hours": new_sleep,
                "energy_level": new_energy,
                "stress_level": new_stress,
                "weekly_notes": notes,
                "week_number": week + 1
            })
            st.session_state.profile = updated_profile
            st.session_state.free_start = new_start
            st.session_state.free_end = new_end
            st.session_state.week_number = week + 1

            # Reset exercise logs for new week
            st.session_state.exercise_logs = {}
            st.session_state.app_start_date = date.today().isoformat()

            with st.spinner("🧠 Analyzing your updated body state..."):
                new_analysis = analyze_body_state(updated_profile)
                st.session_state.analysis = new_analysis

            with st.spinner("🥗 Rebuilding your diet plan..."):
                new_diet = generate_diet_plan(updated_profile, new_analysis)
                st.session_state.diet_plan = new_diet

            with st.spinner("💪 Scheduling your new workout week..."):
                new_exercise = generate_exercise_plan(
                    updated_profile, new_analysis,
                    new_start, new_end
                )
                st.session_state.exercise_plan = new_exercise

            # Save new snapshot
            snapshot = {
                "profile": updated_profile,
                "analysis": new_analysis,
                "diet_plan": new_diet,
                "exercise_plan": new_exercise,
                "free_start": new_start,
                "free_end": new_end
            }
            db.save_user_profile(st.session_state.user_id, updated_profile)
            db.save_weekly_snapshot(
                st.session_state.user_id,
                st.session_state.week_number,
                snapshot
            )

            st.session_state.weekly_review = {}
            st.session_state.page = "dashboard"
            st.rerun()
