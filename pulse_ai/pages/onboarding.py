"""pages/onboarding.py — 6-step onboarding form"""
import streamlit as st
from datetime import date
from utils.gemini_ai import analyze_body_state, generate_diet_plan, generate_exercise_plan
from utils.firebase_manager import FirebaseManager


TOTAL_STEPS = 6


def _header(step: int, title: str, subtitle: str):
    progress = step / TOTAL_STEPS
    st.markdown(f"""
    <div style="padding:28px 0 20px;">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;">
        <p style="font-family:'Syne',sans-serif;font-size:11px;letter-spacing:2px;
        text-transform:uppercase;color:#e8ff47;margin:0;">Step {step} of {TOTAL_STEPS}</p>
        <p style="font-size:12px;color:#7a7a8a;margin:0;">{int(progress*100)}% complete</p>
      </div>
      <div style="height:3px;background:#16161f;border-radius:2px;overflow:hidden;margin-bottom:28px;">
        <div style="width:{int(progress*100)}%;height:100%;background:#e8ff47;border-radius:2px;
        transition:width 0.5s ease;"></div>
      </div>
      <h2 style="font-family:'Syne',sans-serif;font-size:26px;font-weight:700;
      margin-bottom:6px;color:#EFEFEF;">{title}</h2>
      <p style="font-size:14px;color:#7a7a8a;margin-bottom:28px;line-height:1.5;">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)


def render(db: FirebaseManager):
    _, mid, _ = st.columns([1, 2, 1])

    with mid:
        step = st.session_state.onboarding_step

        # ── STEP 1: Basic Info ────────────────────────────────────────────────
        if step == 1:
            _header(1, "Tell us about yourself",
                    "Basic information helps us calculate your body's baseline needs.")

            name = st.text_input("Your first name", placeholder="Alex",
                                 value=st.session_state.profile.get("name", ""))
            col1, col2 = st.columns(2)
            with col1:
                age = st.number_input("Age", min_value=14, max_value=80,
                                      value=st.session_state.profile.get("age", 22))
            with col2:
                gender = st.selectbox("Gender",
                                      ["Male", "Female", "Non-binary / Prefer not to say"],
                                      index=["Male", "Female", "Non-binary / Prefer not to say"].index(
                                          st.session_state.profile.get("gender", "Male")))
            col3, col4 = st.columns(2)
            with col3:
                weight = st.number_input("Weight (kg)", min_value=30.0, max_value=250.0,
                                         step=0.5, value=float(st.session_state.profile.get("weight_kg", 68)))
            with col4:
                height = st.number_input("Height (cm)", min_value=100, max_value=250,
                                         value=st.session_state.profile.get("height_cm", 170))

            if st.button("Continue →", use_container_width=True, type="primary"):
                if not name:
                    st.error("Please enter your name.")
                else:
                    st.session_state.profile.update({
                        "name": name, "age": age, "gender": gender,
                        "weight_kg": weight, "height_cm": height
                    })
                    st.session_state.onboarding_step = 2
                    st.rerun()

        # ── STEP 2: Goal & Activity ───────────────────────────────────────────
        elif step == 2:
            _header(2, "What's your fitness goal?",
                    "Be specific — this shapes every single recommendation we make.")

            goals = {
                "🔥 Fat Loss": "Lose body fat while preserving muscle",
                "💪 Muscle Gain": "Build lean muscle mass",
                "⚡ Improve Fitness": "Better endurance, stamina, and energy",
                "🧘 General Wellness": "Feel healthier, sleep better, reduce stress",
                "🏃 Athletic Performance": "Improve speed, strength, and agility"
            }

            current_goal = st.session_state.profile.get("goal", "")
            selected_goal = None

            for goal_key, goal_desc in goals.items():
                is_selected = current_goal == goal_key
                border = "#e8ff47" if is_selected else "rgba(255,255,255,0.07)"
                bg = "rgba(232,255,71,0.05)" if is_selected else "#12121a"

                st.markdown(f"""
                <div style="background:{bg};border:1px solid {border};border-radius:14px;
                padding:14px 18px;margin-bottom:8px;cursor:pointer;">
                  <div style="font-size:15px;font-weight:500;color:#EFEFEF;">{goal_key}</div>
                  <div style="font-size:12px;color:#7a7a8a;margin-top:2px;">{goal_desc}</div>
                </div>""", unsafe_allow_html=True)

            selected_goal = st.radio("Select your goal", list(goals.keys()),
                                     label_visibility="collapsed",
                                     index=list(goals.keys()).index(current_goal) if current_goal in goals else 0)

            activity = st.selectbox("Current activity level", [
                "Sedentary (desk job, little exercise)",
                "Lightly active (1-3 days/week)",
                "Moderately active (3-5 days/week)",
                "Very active (6-7 days/week)",
                "Athlete (2x/day training)"
            ], index=["Sedentary (desk job, little exercise)",
                      "Lightly active (1-3 days/week)",
                      "Moderately active (3-5 days/week)",
                      "Very active (6-7 days/week)",
                      "Athlete (2x/day training)"].index(
                          st.session_state.profile.get("activity_level",
                          "Lightly active (1-3 days/week)")))

            col1, col2 = st.columns(2)
            with col1:
                if st.button("← Back", use_container_width=True):
                    st.session_state.onboarding_step = 1
                    st.rerun()
            with col2:
                if st.button("Continue →", use_container_width=True, type="primary"):
                    st.session_state.profile.update({
                        "goal": selected_goal,
                        "activity_level": activity
                    })
                    st.session_state.onboarding_step = 3
                    st.rerun()

        # ── STEP 3: Diet Preferences ──────────────────────────────────────────
        elif step == 3:
            _header(3, "Your diet preferences",
                    "We'll build your meal plan around what you actually eat.")

            diet_type = st.selectbox("Dietary preference", [
                "No restriction (omnivore)",
                "Vegetarian",
                "Vegan",
                "Pescatarian",
                "Keto / Low-carb",
                "Gluten-free"
            ])

            health_conditions = st.multiselect(
                "Any health conditions? (select all that apply)",
                ["Diabetes", "Hypertension", "High cholesterol", "PCOS", "Thyroid issues",
                 "Lactose intolerant", "Nut allergy", "Gluten intolerant", "None"],
                default=st.session_state.profile.get("health_conditions", ["None"])
                    if isinstance(st.session_state.profile.get("health_conditions"), list)
                    else ["None"]
            )

            sleep_hours = st.slider("Average sleep per night (hours)",
                                    min_value=4, max_value=10,
                                    value=st.session_state.profile.get("sleep_hours", 7))

            water_intake = st.selectbox("Daily water intake", [
                "Less than 1L", "1-2L", "2-3L", "More than 3L"
            ])

            col1, col2 = st.columns(2)
            with col1:
                if st.button("← Back", use_container_width=True):
                    st.session_state.onboarding_step = 2
                    st.rerun()
            with col2:
                if st.button("Continue →", use_container_width=True, type="primary"):
                    st.session_state.profile.update({
                        "diet_type": diet_type,
                        "health_conditions": health_conditions,
                        "sleep_hours": sleep_hours,
                        "water_intake": water_intake
                    })
                    st.session_state.onboarding_step = 4
                    st.rerun()

        # ── STEP 4: Free Time Slot ────────────────────────────────────────────
        elif step == 4:
            _header(4, "When are you free to exercise?",
                    "We'll schedule workouts that fit your life — never your whole day.")

            st.markdown("""
            <div style="background:rgba(232,255,71,0.04);border:1px solid rgba(232,255,71,0.12);
            border-radius:12px;padding:14px 18px;margin-bottom:24px;font-size:13px;color:#b0b0b0;">
            ⏱️  We recommend 45-60 min sessions. We'll never schedule more than 1 hour of exercise per day.
            </div>""", unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("<p style='font-size:12px;color:#7a7a8a;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;'>FREE FROM</p>",
                            unsafe_allow_html=True)
                start_hour = st.selectbox("Start Hour",
                    [f"{h:02d}" for h in range(0, 24)],
                    index=6, key="s_hour")
                start_min = st.selectbox("Start Min", ["00", "15", "30", "45"], key="s_min")
                start_period = st.selectbox("AM/PM", ["AM", "PM"], key="s_period")

            with col2:
                st.markdown("<p style='font-size:12px;color:#7a7a8a;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;'>FREE UNTIL</p>",
                            unsafe_allow_html=True)
                end_hour = st.selectbox("End Hour",
                    [f"{h:02d}" for h in range(0, 24)],
                    index=8, key="e_hour")
                end_min = st.selectbox("End Min", ["00", "15", "30", "45"], key="e_min")
                end_period = st.selectbox("AM/PM", ["AM", "PM"], key="e_period")

            free_start = f"{start_hour}:{start_min} {start_period}"
            free_end = f"{end_hour}:{end_min} {end_period}"

            # Calculate duration
            def to_minutes(h, m, p):
                h = int(h)
                m = int(m)
                if p == "PM" and h != 12:
                    h += 12
                if p == "AM" and h == 12:
                    h = 0
                return h * 60 + m

            start_mins = to_minutes(start_hour, start_min, start_period)
            end_mins = to_minutes(end_hour, end_min, end_period)
            duration = end_mins - start_mins

            if duration <= 0:
                st.warning("⚠️  End time must be after start time.")
            elif duration < 30:
                st.warning("⚠️  You need at least 30 minutes for a proper session.")
            elif duration > 120:
                st.info("ℹ️  We'll schedule a max of 60 min workout within your free window.")
            else:
                st.markdown(f"""
                <div style="background:#12121a;border:1px solid rgba(232,255,71,0.2);
                border-radius:12px;padding:14px;text-align:center;margin-top:12px;">
                  <span style="font-family:'Syne',sans-serif;font-size:18px;color:#e8ff47;">
                  {free_start} → {free_end}</span>
                  <p style="font-size:12px;color:#7a7a8a;margin-top:4px;">
                  {duration} min window · Exercises will be ≤60 min</p>
                </div>""", unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("← Back", use_container_width=True):
                    st.session_state.onboarding_step = 3
                    st.rerun()
            with col2:
                if st.button("Continue →", use_container_width=True, type="primary",
                             disabled=(duration <= 0)):
                    st.session_state.free_start = free_start
                    st.session_state.free_end = free_end
                    st.session_state.profile.update({
                        "free_start": free_start,
                        "free_end": free_end,
                        "available_minutes": min(duration, 60)
                    })
                    st.session_state.onboarding_step = 5
                    st.rerun()

        # ── STEP 5: Optional Stats ────────────────────────────────────────────
        elif step == 5:
            _header(5, "A few more details",
                    "Optional but helps us get really precise. Skip any you're not sure about.")

            col1, col2 = st.columns(2)
            with col1:
                waist = st.number_input("Waist circumference (cm) — optional",
                                        min_value=0.0, max_value=200.0, value=0.0, step=0.5)
            with col2:
                hip = st.number_input("Hip circumference (cm) — optional",
                                      min_value=0.0, max_value=200.0, value=0.0, step=0.5)

            stress_level = st.select_slider("Stress level",
                options=["Very Low", "Low", "Moderate", "High", "Very High"],
                value=st.session_state.profile.get("stress_level", "Moderate"))

            fitness_exp = st.selectbox("Fitness experience level", [
                "Beginner (never worked out consistently)",
                "Intermediate (6+ months experience)",
                "Advanced (2+ years, familiar with most exercises)"
            ])

            equipment = st.multiselect("Equipment available", [
                "No equipment (bodyweight only)",
                "Resistance bands",
                "Dumbbells",
                "Barbell & plates",
                "Pull-up bar",
                "Full gym access"
            ], default=["No equipment (bodyweight only)"])

            col1, col2 = st.columns(2)
            with col1:
                if st.button("← Back", use_container_width=True):
                    st.session_state.onboarding_step = 4
                    st.rerun()
            with col2:
                if st.button("Continue →", use_container_width=True, type="primary"):
                    st.session_state.profile.update({
                        "waist_cm": waist if waist > 0 else None,
                        "hip_cm": hip if hip > 0 else None,
                        "stress_level": stress_level,
                        "fitness_experience": fitness_exp,
                        "equipment": equipment
                    })
                    st.session_state.onboarding_step = 6
                    st.rerun()

        # ── STEP 6: Generate Plan ─────────────────────────────────────────────
        elif step == 6:
            _header(6, "Generating your plan",
                    "Pulse AI is analyzing your body and building a personalized plan.")

            profile = st.session_state.profile
            name = profile.get("name", "there")

            # Show summary card
            bmi = round(profile["weight_kg"] / ((profile["height_cm"] / 100) ** 2), 1)
            st.markdown(f"""
            <div style="background:#12121a;border:1px solid rgba(255,255,255,0.07);
            border-radius:16px;padding:20px;margin-bottom:24px;">
              <p style="font-family:'Syne',sans-serif;font-size:18px;font-weight:700;
              color:#e8ff47;margin-bottom:14px;">📋 Your Summary</p>
              <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">
                <div style="background:#0d0d1a;border-radius:10px;padding:12px;text-align:center;">
                  <div style="font-size:20px;font-weight:700;color:#EFEFEF;">{profile['weight_kg']}kg</div>
                  <div style="font-size:11px;color:#7a7a8a;">Weight</div>
                </div>
                <div style="background:#0d0d1a;border-radius:10px;padding:12px;text-align:center;">
                  <div style="font-size:20px;font-weight:700;color:#EFEFEF;">{bmi}</div>
                  <div style="font-size:11px;color:#7a7a8a;">BMI</div>
                </div>
                <div style="background:#0d0d1a;border-radius:10px;padding:12px;text-align:center;">
                  <div style="font-size:20px;font-weight:700;color:#e8ff47;">{profile.get('goal','').split()[1] if len(profile.get('goal','').split()) > 1 else 'Goal'}</div>
                  <div style="font-size:11px;color:#7a7a8a;">Focus</div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("← Back", use_container_width=True):
                    st.session_state.onboarding_step = 5
                    st.rerun()
            with col2:
                generate = st.button("⚡ Generate My Plan", use_container_width=True, type="primary")

            if generate or st.session_state.get("_generating"):
                st.session_state._generating = True

                with st.spinner("🧠 Analyzing your body state..."):
                    analysis = analyze_body_state(profile)
                    st.session_state.analysis = analysis

                with st.spinner("🥗 Building your personalized diet plan..."):
                    diet = generate_diet_plan(profile, analysis)
                    st.session_state.diet_plan = diet

                with st.spinner("💪 Scheduling your workout week..."):
                    exercise = generate_exercise_plan(
                        profile, analysis,
                        st.session_state.free_start,
                        st.session_state.free_end
                    )
                    st.session_state.exercise_plan = exercise

                # Save to Firebase/local
                snapshot = {
                    "profile": profile,
                    "analysis": analysis,
                    "diet_plan": diet,
                    "exercise_plan": exercise,
                    "free_start": st.session_state.free_start,
                    "free_end": st.session_state.free_end
                }
                db.save_user_profile(st.session_state.user_id, profile)
                db.save_weekly_snapshot(
                    st.session_state.user_id,
                    st.session_state.week_number,
                    snapshot
                )

                st.session_state.setup_complete = True
                st.session_state.plan_generated = True
                st.session_state._generating = False
                st.session_state.page = "dashboard"
                st.rerun()
