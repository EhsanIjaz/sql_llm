import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_lottie import st_lottie

from src.llm_code.data_processor_and_loader import data_loader
from src.llm_code.sql_gen_and_exec import *
from src.llm_code.streamlit_helper import *
from src.constants.app_constant import MODE_DISPLAY
from src.prompts.prompts import prompt, prompt_2 
from src.utils.logging import logger
from src.llm_code.single_query import single_query
from src.llm_code.contextual_query import context_query
from src.llm_code.comparision_query import comparision_query


streamlit_initializer()
init_session_state()

st.sidebar.write("## 💬 Chat Mode")

select_chat_mode = sidebar_conversation_selector()
st.session_state.chat_mode = MODE_DISPLAY[select_chat_mode]
render_contextual_reset_button()
display_recent_queries()
greeter()
display_chat_history()
render_contextual_limits()


llm_df = data_loader()

if st.session_state.chat_mode == "Comparision Query":
    selections = get_comparison_year_month(llm_df)

user_input = st.chat_input("Type your message and press Enter...")
if user_input:
    if st.session_state.chat_mode == "Single Query":
        single_query(user_input, llm_df)
    if st.session_state.chat_mode == "Contextual Query":
        context_query(user_input, llm_df)
    if st.session_state.chat_mode == "Comparision Query":
        
        comparision_query(user_input, llm_df, selections)
    
st.divider()
