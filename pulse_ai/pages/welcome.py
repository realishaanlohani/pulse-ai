"""pages/welcome.py — Pulse AI Welcome Screen"""
import streamlit as st


def render():
    st.markdown("""
    <div style="min-height:100vh;display:flex;flex-direction:column;align-items:center;
    justify-content:center;padding:40px 24px;text-align:center;position:relative;overflow:hidden;">

    <div style="position:absolute;width:600px;height:600px;border-radius:50%;
    background:radial-gradient(circle,rgba(232,255,71,0.06) 0%,transparent 70%);
    top:50%;left:50%;transform:translate(-50%,-50%);pointer-events:none;"></div>

    <div style="width:72px;height:72px;border-radius:50%;border:2px solid #e8ff47;
    display:flex;align-items:center;justify-content:center;margin:0 auto 24px;
    box-shadow:0 0 30px rgba(232,255,71,0.2);">
      <span style="font-size:28px;">⚡</span>
    </div>

    <p style="font-family:'Syne',sans-serif;font-size:11px;letter-spacing:3px;
    text-transform:uppercase;color:#e8ff47;margin-bottom:14px;opacity:0.8;">
    Intelligent Fitness Coach</p>

    <h1 style="font-family:'Syne',sans-serif;font-size:clamp(52px,10vw,88px);
    font-weight:800;line-height:0.9;letter-spacing:-3px;margin-bottom:20px;color:#EFEFEF;">
    PULSE<span style="color:#e8ff47;">AI</span></h1>

    <p style="font-size:16px;color:#7a7a8a;max-width:360px;line-height:1.7;
    margin-bottom:12px;font-weight:300;">
    Your adaptive fitness coach that learns your body every week — diet, workouts, and form correction in one place.</p>

    <div style="display:flex;gap:32px;margin:40px 0;justify-content:center;">
      <div><div style="font-family:'Syne',sans-serif;font-size:20px;font-weight:700;color:#e8ff47;">AI</div>
      <div style="font-size:11px;color:#7a7a8a;text-transform:uppercase;letter-spacing:1px;">Powered</div></div>
      <div><div style="font-family:'Syne',sans-serif;font-size:20px;font-weight:700;color:#e8ff47;">7-Day</div>
      <div style="font-size:11px;color:#7a7a8a;text-transform:uppercase;letter-spacing:1px;">Adaptive Plan</div></div>
      <div><div style="font-family:'Syne',sans-serif;font-size:20px;font-weight:700;color:#e8ff47;">Live</div>
      <div style="font-size:11px;color:#7a7a8a;text-transform:uppercase;letter-spacing:1px;">Form Check</div></div>
    </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("⚡  Start My Journey", use_container_width=True,
                     type="primary"):
            st.session_state.page = "onboarding"
            st.rerun()
        st.markdown("<p style='text-align:center;font-size:12px;color:#7a7a8a;margin-top:8px;'>Takes 2 minutes · Completely personalized</p>",
                    unsafe_allow_html=True)
