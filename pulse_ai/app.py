"""
app.py — Pulse AI Main Application
Run with: streamlit run app.py
"""

import streamlit as st
from dotenv import load_dotenv
load_dotenv()

from utils.session_manager import init_session, is_new_week
#from utils.session_manager import init_session
from utils.firebase_manager import FirebaseManager

st.set_page_config(
    page_title="Pulse AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');
html,body,[class*="css"],.stApp{font-family:'DM Sans',sans-serif!important;background-color:#080810!important;color:#EFEFEF!important;}
#MainMenu,footer,header{visibility:hidden!important;}
.block-container{padding:0!important;max-width:100%!important;}
section[data-testid="stSidebar"]{display:none!important;}
div[data-testid="stToolbar"]{display:none!important;}
::-webkit-scrollbar{width:4px;}
::-webkit-scrollbar-track{background:#0d0d1a;}
::-webkit-scrollbar-thumb{background:#e8ff47;border-radius:2px;}
.stButton>button{font-family:'Syne',sans-serif!important;font-weight:700!important;border-radius:50px!important;transition:all 0.2s!important;}
.stTextInput>div>div>input,.stNumberInput>div>div>input{background:#16161f!important;border:1px solid rgba(255,255,255,0.07)!important;border-radius:12px!important;color:#EFEFEF!important;}
.stSelectbox>div>div{background:#16161f!important;border:1px solid rgba(255,255,255,0.07)!important;border-radius:12px!important;}
div[data-testid="metric-container"]{background:#12121a!important;border:1px solid rgba(255,255,255,0.07)!important;border-radius:14px!important;padding:16px!important;}
.stCheckbox>label{color:#EFEFEF!important;}
</style>
""", unsafe_allow_html=True)

init_session()
db = FirebaseManager()

# Auto-detect new week
if (st.session_state.setup_complete
        and st.session_state.page not in ("weekly_review", "onboarding")
        and is_new_week()):
    st.session_state.page = "weekly_review"

page = st.session_state.get("page", "welcome")

if page == "welcome":
    from pages.welcome import render
    render()
elif page == "onboarding":
    from pages.onboarding import render
    render(db)
elif page == "dashboard":
    from pages.dashboard import render
    render(db)
elif page == "gym_buddy":
    from pages.gym_buddy import render
    render()
elif page == "weekly_review":
    from pages.weekly_review import render
    render(db)
else:
    st.session_state.page = "welcome"
    st.rerun()
