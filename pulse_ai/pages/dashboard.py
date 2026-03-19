"""pages/dashboard.py — Main dashboard with nutrients, diet, exercise plan"""
import streamlit as st
import plotly.graph_objects as go
from datetime import date, datetime, timedelta
from utils.session_manager import add_notification, get_today_str
from utils.firebase_manager import FirebaseManager


def _nav():
    """Top navigation bar"""
    profile = st.session_state.profile
    notifs = [n for n in st.session_state.get("notifications", []) if not n.get("read")]
    notif_count = len(notifs)
    week = st.session_state.week_number

    col1, col2, col3 = st.columns([3, 4, 3])
    with col1:
        st.markdown(f"""
        <div style="padding:20px 24px;">
          <span style="font-family:'Syne',sans-serif;font-size:20px;font-weight:800;color:#EFEFEF;">
          PULSE<span style="color:#e8ff47;">AI</span></span>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style="padding:20px 0;text-align:center;">
          <span style="background:#12121a;border:1px solid rgba(255,255,255,0.07);
          border-radius:50px;padding:6px 16px;font-size:12px;color:#7a7a8a;
          font-family:'Syne',sans-serif;">Week {week}</span>
        </div>""", unsafe_allow_html=True)
    with col3:
        cols = st.columns([1, 1])
        with cols[0]:
            if notif_count > 0:
                if st.button(f"🔔 {notif_count}", key="notif_btn"):
                    st.session_state.show_notifications = not st.session_state.get("show_notifications", False)
        with cols[1]:
            if st.button("📸 Gym Buddy", key="gym_btn"):
                st.session_state.page = "gym_buddy"
                st.rerun()

    # Show notifications panel
    if st.session_state.get("show_notifications") and notifs:
        with st.container():
            st.markdown("""
            <div style="background:#12121a;border:1px solid rgba(255,255,255,0.1);
            border-radius:14px;padding:16px;margin:0 24px 16px;">
            <p style="font-family:'Syne',sans-serif;font-size:14px;font-weight:700;
            color:#e8ff47;margin-bottom:12px;">Notifications</p>""", unsafe_allow_html=True)
            for n in notifs:
                icon = "⚠️" if n.get("type") == "warning" else "ℹ️"
                st.info(f"{icon} {n['message']}")
            st.markdown("</div>", unsafe_allow_html=True)
            if st.button("Mark all read"):
                for n in st.session_state.notifications:
                    n["read"] = True
                st.session_state.show_notifications = False
                st.rerun()

    st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,0.06);margin:0 0 8px;'/>",
                unsafe_allow_html=True)


def _greeting_card():
    profile = st.session_state.profile
    analysis = st.session_state.analysis
    name = profile.get("name", "there")
    hour = datetime.now().hour
    greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening"
    bmi = analysis.get("bmi", 0)
    bmi_cat = analysis.get("bmi_category", "")

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#12121a 0%,#1a1a26 100%);
    border:1px solid rgba(255,255,255,0.07);border-radius:20px;padding:24px;
    margin-bottom:20px;position:relative;overflow:hidden;">
      <div style="position:absolute;right:-20px;top:-20px;width:180px;height:180px;
      border-radius:50%;background:rgba(232,255,71,0.03);"></div>

      <p style="font-family:'Syne',sans-serif;font-size:22px;font-weight:700;
      color:#EFEFEF;margin-bottom:4px;">{greeting}, {name} 👋</p>
      <p style="font-size:13px;color:#7a7a8a;margin-bottom:16px;">
      {analysis.get('motivational_insight','You are one consistent week away from feeling a real difference.')}</p>

      <div style="display:flex;gap:16px;flex-wrap:wrap;">
        <div style="background:rgba(232,255,71,0.08);border:1px solid rgba(232,255,71,0.15);
        border-radius:10px;padding:10px 16px;">
          <div style="font-family:'Syne',sans-serif;font-size:18px;font-weight:700;color:#e8ff47;">{bmi}</div>
          <div style="font-size:11px;color:#7a7a8a;">BMI · {bmi_cat}</div>
        </div>
        <div style="background:rgba(71,200,255,0.08);border:1px solid rgba(71,200,255,0.15);
        border-radius:10px;padding:10px 16px;">
          <div style="font-family:'Syne',sans-serif;font-size:18px;font-weight:700;color:#47c8ff;">
          {analysis.get('tdee_calories',2100)} kcal</div>
          <div style="font-size:11px;color:#7a7a8a;">Daily target</div>
        </div>
        <div style="background:rgba(255,107,71,0.08);border:1px solid rgba(255,107,71,0.15);
        border-radius:10px;padding:10px 16px;">
          <div style="font-family:'Syne',sans-serif;font-size:18px;font-weight:700;color:#ff6b47;">
          {profile.get('goal','').split(' ')[1] if len(profile.get('goal','').split()) > 1 else 'Goal'}</div>
          <div style="font-size:11px;color:#7a7a8a;">Current goal</div>
        </div>
      </div>

      {''.join([f"<span style='background:#1a1a26;border:1px solid rgba(255,107,71,0.3);border-radius:50px;padding:4px 12px;font-size:11px;color:#ff6b47;margin-right:6px;margin-top:10px;display:inline-block;'>⚠ {flag}</span>" for flag in analysis.get('health_flags',[])])}
    </div>
    """, unsafe_allow_html=True)


def _nutrient_section():
    """Pie chart + bars for nutrient priorities"""
    analysis = st.session_state.analysis
    nutrients = analysis.get("nutrient_priorities", {})

    st.markdown("""
    <div style="margin-bottom:16px;">
      <p style="font-family:'Syne',sans-serif;font-size:17px;font-weight:700;
      color:#EFEFEF;margin-bottom:4px;">🧬 Your Nutrient Priorities</p>
      <p style="font-size:13px;color:#7a7a8a;">Based on your body composition and goal</p>
    </div>""", unsafe_allow_html=True)

    if not nutrients:
        st.info("Analysis data not loaded. Please regenerate your plan.")
        return

    # Build pie chart
    labels = list(nutrients.keys())
    values = [nutrients[k].get("priority", 50) for k in labels]
    colors = ["#e8ff47", "#47c8ff", "#ff6b47", "#ff47a0", "#47ff9c",
              "#c847ff", "#ffa047", "#47ffea"]

    fig = go.Figure(data=[go.Pie(
        labels=labels, values=values,
        hole=0.55,
        marker=dict(colors=colors[:len(labels)], line=dict(color="#080810", width=2)),
        textinfo="label+percent",
        textfont=dict(size=11, color="#EFEFEF"),
        hovertemplate="<b>%{label}</b><br>Priority: %{value}<br>%{customdata}<extra></extra>",
        customdata=[nutrients[k].get("reason", "") for k in labels]
    )])

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=10, b=10, l=10, r=10),
        height=300,
        showlegend=False,
        annotations=[dict(
            text=f"<b>{labels[0]}</b><br>Top Priority",
            x=0.5, y=0.5, font_size=12,
            font_color="#e8ff47", showarrow=False
        )]
    )
    st.plotly_chart(fig, use_container_width=True)

    # Nutrient bars
    for i, (nutrient, data) in enumerate(nutrients.items()):
        prio = data.get("priority", 50)
        color = colors[i % len(colors)]
        # Format the amount label
        amount_label = ""
        if "daily_grams" in data:
            amount_label = f"{data['daily_grams']}g/day"
        elif "daily_mg" in data:
            amount_label = f"{data['daily_mg']}mg/day"
        elif "daily_iu" in data:
            amount_label = f"{data['daily_iu']} IU/day"
        elif "daily_mcg" in data:
            amount_label = f"{data['daily_mcg']}mcg/day"

        st.markdown(f"""
        <div style="margin-bottom:12px;">
          <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
            <div>
              <span style="font-size:13px;font-weight:500;color:#EFEFEF;">{nutrient}</span>
              <span style="font-size:11px;color:#7a7a8a;margin-left:8px;">{amount_label}</span>
            </div>
            <span style="font-size:11px;color:{color};">{prio}% priority</span>
          </div>
          <div style="height:5px;background:#16161f;border-radius:3px;overflow:hidden;">
            <div style="width:{prio}%;height:100%;background:{color};border-radius:3px;"></div>
          </div>
          <p style="font-size:11px;color:#555;margin-top:3px;">{data.get('reason','')}</p>
        </div>""", unsafe_allow_html=True)


def _diet_section():
    """Food recommendations"""
    diet = st.session_state.diet_plan
    if not diet:
        return

    st.markdown("""
    <div style="margin:24px 0 16px;">
      <p style="font-family:'Syne',sans-serif;font-size:17px;font-weight:700;color:#EFEFEF;margin-bottom:4px;">
      🥗 This Week's Food Plan</p>
      <p style="font-size:13px;color:#7a7a8a;">Foods chosen specifically for your nutrient gaps</p>
    </div>""", unsafe_allow_html=True)

    # Macro split
    macros = diet.get("macro_split", {})
    cal = diet.get("daily_calories_target", 2000)
    st.markdown(f"""
    <div style="background:#12121a;border:1px solid rgba(255,255,255,0.07);
    border-radius:14px;padding:16px;margin-bottom:16px;">
      <p style="font-family:'Syne',sans-serif;font-size:13px;color:#7a7a8a;margin-bottom:10px;
      text-transform:uppercase;letter-spacing:1px;">Daily target: {cal} kcal</p>
      <div style="display:flex;gap:0;border-radius:8px;overflow:hidden;height:10px;margin-bottom:10px;">
        <div style="width:{macros.get('protein_pct',30)}%;background:#e8ff47;"></div>
        <div style="width:{macros.get('carbs_pct',45)}%;background:#47c8ff;"></div>
        <div style="width:{macros.get('fat_pct',25)}%;background:#ff6b47;"></div>
      </div>
      <div style="display:flex;gap:20px;">
        <span style="font-size:12px;color:#e8ff47;">● Protein {macros.get('protein_pct',30)}%</span>
        <span style="font-size:12px;color:#47c8ff;">● Carbs {macros.get('carbs_pct',45)}%</span>
        <span style="font-size:12px;color:#ff6b47;">● Fats {macros.get('fat_pct',25)}%</span>
      </div>
    </div>""", unsafe_allow_html=True)

    # Key foods
    for food in diet.get("key_foods", []):
        st.markdown(f"""
        <div style="background:#12121a;border:1px solid rgba(255,255,255,0.07);
        border-radius:14px;padding:14px 16px;margin-bottom:10px;
        display:flex;align-items:flex-start;gap:12px;">
          <div style="font-size:28px;width:44px;height:44px;display:flex;align-items:center;
          justify-content:center;background:#1a1a26;border-radius:10px;flex-shrink:0;">
          {food.get('emoji','🍽')}</div>
          <div style="flex:1;">
            <div style="display:flex;align-items:center;justify-content:space-between;">
              <span style="font-weight:600;font-size:14px;color:#EFEFEF;">{food['food']}</span>
              <span style="font-size:11px;color:#7a7a8a;">{food['servings']}</span>
            </div>
            <p style="font-size:12px;color:#7a7a8a;margin:3px 0 6px;">{food['why']}</p>
            <div style="display:flex;gap:6px;flex-wrap:wrap;">
              {''.join([f"<span style='background:#1a1a26;border:1px solid rgba(255,255,255,0.06);border-radius:50px;padding:2px 8px;font-size:10px;color:#b0b0b0;'>{n}</span>" for n in food.get('nutrients',[])])}
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

    # Meal schedule
    schedule = diet.get("meal_schedule", {})
    if schedule:
        with st.expander("📅 Daily meal schedule"):
            meal_icons = {"breakfast": "🌅", "mid_morning": "☕", "lunch": "🍱",
                          "evening_snack": "🍎", "dinner": "🌙"}
            for meal_key, meal_val in schedule.items():
                icon = meal_icons.get(meal_key, "🍽")
                label = meal_key.replace("_", " ").title()
                st.markdown(f"""
                <div style="display:flex;gap:10px;padding:10px 0;
                border-bottom:1px solid rgba(255,255,255,0.05);">
                  <span style="font-size:18px;">{icon}</span>
                  <div><div style="font-size:13px;font-weight:500;color:#EFEFEF;">{label}</div>
                  <div style="font-size:12px;color:#7a7a8a;">{meal_val}</div></div>
                </div>""", unsafe_allow_html=True)

    tip = diet.get("weekly_tip", "")
    if tip:
        st.markdown(f"""
        <div style="background:rgba(232,255,71,0.04);border:1px solid rgba(232,255,71,0.12);
        border-radius:12px;padding:14px;margin-top:12px;">
          <span style="font-size:12px;color:#e8ff47;">💡 Tip of the week: </span>
          <span style="font-size:13px;color:#b0b0b0;">{tip}</span>
        </div>""", unsafe_allow_html=True)


def _exercise_section(db: FirebaseManager):
    """7-day exercise checklist — today's boxes are clickable."""
    plan = st.session_state.exercise_plan
    if not plan:
        return

    week_plan = plan.get("week_plan", {})
    today = date.today()
    start = date.fromisoformat(st.session_state.app_start_date)
    free_start = st.session_state.free_start
    free_end = st.session_state.free_end

    st.markdown(f"""
    <div style="margin:24px 0 16px;">
      <p style="font-family:'Syne',sans-serif;font-size:17px;font-weight:700;color:#EFEFEF;margin-bottom:4px;">
      💪 Your Exercise Week</p>
      <p style="font-size:13px;color:#7a7a8a;">Scheduled {free_start} → {free_end} · Max 60 min/day</p>
    </div>""", unsafe_allow_html=True)

    for i, (day_key, day_data) in enumerate(week_plan.items()):
        if not day_data:
            continue

        day_date = start + timedelta(days=i)
        is_today = day_date == today
        is_past = day_date < today
        is_rest = day_data.get("is_rest", False)
        day_name = day_data.get("day_name", day_key)
        focus = day_data.get("focus", "")
        date_str = day_date.isoformat()

        # Load saved log for this day
        if date_str not in st.session_state.exercise_logs:
            saved = db.get_exercise_log(st.session_state.user_id, date_str)
            st.session_state.exercise_logs[date_str] = saved.get("exercises", {})

        # Header color
        if is_today:
            border_color = "#e8ff47"
            label = "TODAY"
            label_color = "#e8ff47"
        elif is_past:
            border_color = "rgba(255,255,255,0.1)"
            label = "COMPLETED" if not is_rest else "REST"
            label_color = "#7a7a8a"
        else:
            border_color = "rgba(255,255,255,0.05)"
            label = day_date.strftime("%b %d")
            label_color = "#555"

        st.markdown(f"""
        <div style="background:#0d0d1a;border:1px solid {border_color};border-radius:16px;
        padding:18px 20px;margin-bottom:12px;">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
            <div>
              <span style="font-family:'Syne',sans-serif;font-size:15px;font-weight:700;
              color:#EFEFEF;">{day_name}</span>
              <span style="font-size:12px;color:#7a7a8a;margin-left:8px;">· {focus}</span>
            </div>
            <span style="font-family:'Syne',sans-serif;font-size:10px;letter-spacing:2px;
            text-transform:uppercase;color:{label_color};">{label}</span>
          </div>
        """, unsafe_allow_html=True)

        if is_rest:
            st.markdown("""
            <div style="text-align:center;padding:12px;color:#555;font-size:13px;">
            😴 Rest day — let your body recover</div>""", unsafe_allow_html=True)
        else:
            exercises = day_data.get("exercises", [])
            warmup = day_data.get("warmup", "")
            cooldown = day_data.get("cooldown", "")
            total_min = day_data.get("total_duration_minutes", 0)

            if warmup:
                st.markdown(f"<p style='font-size:11px;color:#555;margin-bottom:8px;'>🔥 Warmup: {warmup}</p>",
                            unsafe_allow_html=True)

            all_done = True
            for ex in exercises:
                ex_name = ex.get("name", "Exercise")
                sets = ex.get("sets", "")
                reps = ex.get("reps", "")
                rest = ex.get("rest_seconds", 0)
                muscle = ex.get("muscle_group", "")
                ex_key = f"{date_str}_{ex_name}"

                current_done = st.session_state.exercise_logs.get(date_str, {}).get(ex_name, False)

                if is_today:
                    checked = st.checkbox(
                        f"**{ex_name}** — {sets} × {reps} | rest {rest}s | _{muscle}_",
                        value=current_done,
                        key=ex_key
                    )
                    if checked != current_done:
                        if date_str not in st.session_state.exercise_logs:
                            st.session_state.exercise_logs[date_str] = {}
                        st.session_state.exercise_logs[date_str][ex_name] = checked
                        db.save_exercise_log(
                            st.session_state.user_id, date_str,
                            st.session_state.exercise_logs[date_str]
                        )
                        if not checked:
                            add_notification(
                                f"⚠️ You unchecked '{ex_name}' — don't skip it today!",
                                "warning"
                            )
                        st.rerun()
                    if not checked:
                        all_done = False
                else:
                    # Non-today: show static, disabled
                    done_icon = "✅" if current_done else ("⬜" if not is_past else "❌")
                    opacity = "0.4" if not is_today and not is_past else "0.6"
                    st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:10px;
                    padding:8px 0;opacity:{opacity};">
                      <span style="font-size:16px;">{done_icon}</span>
                      <span style="font-size:13px;color:#EFEFEF;">{ex_name}</span>
                      <span style="font-size:11px;color:#555;">{sets}×{reps}</span>
                      <span style="font-size:11px;color:#555;font-style:italic;">{muscle}</span>
                    </div>""", unsafe_allow_html=True)

            # Notification if today and end of day with unchecked items
            if is_today and not all_done:
                hour_now = datetime.now().hour
                if hour_now >= 21:  # 9 PM reminder
                    add_notification(
                        "🏃 You still have exercises to complete today!",
                        "warning"
                    )

            if cooldown:
                st.markdown(f"<p style='font-size:11px;color:#555;margin-top:8px;'>🧘 Cooldown: {cooldown}</p>",
                            unsafe_allow_html=True)

            st.markdown(f"""
            <p style='font-size:11px;color:#555;text-align:right;margin-top:6px;'>
            ⏱ ~{total_min} min total</p>""", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    tip = plan.get("weekly_tip", "")
    if tip:
        st.markdown(f"""
        <div style="background:rgba(71,200,255,0.04);border:1px solid rgba(71,200,255,0.12);
        border-radius:12px;padding:14px;margin-top:4px;">
          <span style="font-size:12px;color:#47c8ff;">💡 Coach says: </span>
          <span style="font-size:13px;color:#b0b0b0;">{tip}</span>
        </div>""", unsafe_allow_html=True)


def render(db: FirebaseManager):
    if not st.session_state.get("setup_complete"):
        st.session_state.page = "onboarding"
        st.rerun()

    _nav()

    _, main, _ = st.columns([1, 6, 1])
    with main:
        _greeting_card()

        tab1, tab2, tab3 = st.tabs(["🧬 Nutrients", "🥗 Diet Plan", "💪 Workouts"])

        with tab1:
            _nutrient_section()

        with tab2:
            _diet_section()

        with tab3:
            _exercise_section(db)

        # Regenerate plan button
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            if st.button("🔄 Regenerate Plan", use_container_width=True):
                with st.spinner("Rebuilding your plan..."):
                    from utils.gemini_ai import generate_diet_plan, generate_exercise_plan, analyze_body_state
                    analysis = analyze_body_state(st.session_state.profile)
                    diet = generate_diet_plan(st.session_state.profile, analysis)
                    exercise = generate_exercise_plan(
                        st.session_state.profile, analysis,
                        st.session_state.free_start, st.session_state.free_end
                    )
                    st.session_state.analysis = analysis
                    st.session_state.diet_plan = diet
                    st.session_state.exercise_plan = exercise
                st.success("Plan updated!")
                st.rerun()

        st.markdown("<br><br>", unsafe_allow_html=True)
