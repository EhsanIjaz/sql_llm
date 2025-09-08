import streamlit as st
import pandas as pd
from datetime import datetime

from src.llm_code.data_processor_and_loader import data_loader
from src.llm_code.sql_gen_and_exec import *
from src.llm_code.streamlit_helper import *
from src.constants.app_constant import MODE_DISPLAY
from src.prompts.prompts import prompt, prompt_2 
from src.utils.logging import logger


streamlit_initializer()
init_session_state()

st.sidebar.write("## 💬 Chat Mode")

select_chat_mode = sidebar_conversation_selector()
st.session_state.chat_mode = MODE_DISPLAY[select_chat_mode]
render_contextual_reset_button()
display_recent_queries()
greetor()
display_chat_history()
render_contextual_limits()

llm_df = data_loader()
LATEST_MONTH, LATEST_YEAR = latest_month_year(llm_df)
user_input = st.chat_input("Type your message and press Enter...")
question = user_input.strip().lower() if user_input else ""


if user_input:
    st.session_state.query_processed = False

if question and not st.session_state.query_processed:
    if st.session_state.chat_mode == "Contextual Query":
        context_question = build_contextual_question(question)
        enhanced_question = generate_enhanced_question(context_question)
        logger.info(f"Generated Contextual Question \n {enhanced_question}")
    else:
        enhanced_question = generate_enhanced_question(question)
        logger.info(f"Generated Single Question \n {enhanced_question}")

    prompt_used = prompt_2 if check_specific_word(question) else prompt

    # Month check: check all context + question to ensure valid month reference
    full_context = st.session_state.get("context_history", []) + [question]
    combined_text = " ".join(full_context).lower()

    if check_month_in_question(combined_text):
        updated_question = question.replace("why", "").strip() if "why" in question else question
        st.session_state.show_why = "why" in question
        unique_key = f"{datetime.now().timestamp()}_{st.session_state.analysis_counter}"
        st.session_state.analysis_counter += 1
        label = st.session_state.chat_mode

        try:
            with st.chat_message("user"):
                st.markdown(f"**_{question}_**")
            with st.status("🚀 Processing...", expanded=True) as status:
                progress_bar = st.progress(0)
                sql_query, df_result = None, None

                for step, progress in st.session_state.processing_steps:
                    progress_bar.progress(progress, text=step)
                    time.sleep(1)

                    if "Thinking" in step:
                        sql_query = generate_sql_openrouterai(enhanced_question, LATEST_MONTH, LATEST_YEAR, prompt_used)
                        # sql_query = generate_sql_openai(enhanced_question, LATEST_MONTH, LATEST_YEAR, prompt_used)
                        st.session_state.ex_sql = sql_query
                        logger.info(f"Generated SQL Query \n {sql_query}")

                    if "Searching Database" in step:
                        result_data = execute_sql(sql_query, llm_df)
                        df_result = result_data if isinstance(result_data, pd.DataFrame) else pd.DataFrame(result_data)

                progress_bar.empty()
                status.update(label="✅ Analysis Complete", state="complete")

            # --- GRID LAYOUT ---
            st.divider()
            col1, col2 = st.columns([2, 3])

            with col1:
                st.subheader("📄 Summary View")
                display_summary(df_result)

            with col2:
                st.subheader("📈 Chart Analytics")
                with st.container():
                    current_fig, chart_config, unique_key = display_chart_analytics(
                        df_result.copy(), unique_key=unique_key, is_editable=True
                    )

            st.divider()

            st.subheader("📋 Result View")
            display_table(df_result)

            st.divider()

            if st.session_state.show_why:
                st.subheader("❓ Why Results")
                why_result = get_why_result(df_result)
                if why_result is not None and not why_result.empty:
                    st.dataframe(why_result, use_container_width=True)
                else:
                    st.warning("No 'Why' results available for this query.")

            store_query_result(
                question=question,
                df_result=df_result,
                sql_query=sql_query,
                why_result=why_result if st.session_state.show_why else None,
                unique_key=unique_key,
            )

            st.session_state.query_processed = True
            st.rerun()

        except Exception as e:
            st.error(f"Processing error: {str(e)}")
            logger.error(f"Error: {str(e)}")
    else:
        if not st.session_state.show_month_prompt:
            st.session_state.show_month_prompt = True
            with st.chat_message("assistant"):
                st.write_stream(re_write_query_with_month())
                st.write_stream(write_question(enhanced_question))

st.divider()