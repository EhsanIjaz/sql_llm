# import streamlit as st
# import pandas as pd
# from datetime import datetime
# from aisight_llm.data_processor_and_loader import latest_month_year, data_loader

# # Streamlit App Configuration
# st.set_page_config(
#     page_title="Chat GPC - Home",
#     layout="wide",
#     page_icon="💬",
#     initial_sidebar_state="expanded",
# )
# st.title("💬 Chat CPG")

# from aisight_llm.sql_gen_and_exec import generate_sql, execute_sql
# from aisight_llm.streamlit_helper import *
# from aisight_llm.settings import MAX_HISTORY_LENGTH
# from aisight_llm.prompts.prompts import prompt, prompt_2
# from aisight_llm.common_utils.logging import logger

# init_session_state()
# display_recent_queries()

# # Main Application Flow
# if not st.session_state.greeted:
#     with st.chat_message("assistant"):
#         st.write_stream(greet_generator())
#     st.session_state.greeted = True

# display_chat_history()

# # Handle new user input
# llm_df = data_loader()
# LATEST_MONTH, LATEST_YEAR = latest_month_year(llm_df)
# user_input = st.chat_input("Type your message and press Enter...")
# question = user_input.strip().lower() if user_input else ""
# month_exist = check_month_in_question(question)
# word_exsist = check_specific_word(question)

# if word_exsist:
#     logger.info(f"yes word exsist")
#     prompt = prompt_2

# if not question:
#     st.session_state.show_month_prompt = False
# else:
#     if month_exist:
#         updated_question = (
#             question.replace("why", "").strip() if "why" in question else question
#         )
#         st.session_state.show_why = "why" in question
#         # st.session_state.why_results = pd.DataFrame()
#         unique_key = f"{datetime.now().timestamp()}_{st.session_state.analysis_counter}"
#         st.session_state.analysis_counter += 1
#         st.session_state.chat_history.append(
#             {
#                 "question": question,
#                 "data": None,
#                 "sql": None,
#                 "why_result": None,
#                 "unique_key": unique_key,
#             }
#         )

#         try:
#             with st.status("🚀 Processing...", expanded=True) as status:
#                 progress_bar = st.progress(0)
#                 sql_query = None
#                 df_result = None

#                 for step, progress in st.session_state.processing_steps:
#                     progress_bar.progress(progress, text=step)
#                     time.sleep(1)

#                     if "Thinking" in step:
#                         enhanced_question = generate_enhanced_question(question)
#                         sql_query = generate_sql(
#                             enhanced_question, LATEST_MONTH, LATEST_YEAR, prompt
#                         )
#                         st.session_state.ex_sql = sql_query
#                         logger.info(f"Generated SQL Query \n {sql_query}")

#                     if "Searching Database" in step:
#                         result_data = execute_sql(sql_query, llm_df)
#                         df_result = (
#                             pd.DataFrame(result_data)
#                             if not isinstance(result_data, pd.DataFrame)
#                             else result_data
#                         )

#                 progress_bar.empty()
#                 status.update(label="✅ Analysis Complete", state="complete")

#             # Display current results
#             with st.chat_message("assistant"):
#                 with st.expander("Current Analysis", expanded=True):
#                     tab1, tab2, tab3, tab4 = st.tabs(
#                         [
#                             "📊 Table",
#                             "📈 Chart Analytics",
#                             "🔘 Summary View",
#                             "❓ Why View",
#                         ]
#                     )

#                     with tab2:
#                         current_fig, chart_config, unique_key = display_chart_analytics(
#                             df_result.copy(), unique_key=unique_key, is_editable=True
#                         )

#             if len(st.session_state.chat_history) > MAX_HISTORY_LENGTH:
#                 st.session_state.chat_history.pop(0)

#             st.session_state.chat_history[-1].update(
#                 {
#                     "data": df_result,
#                     "sql": sql_query,
#                 }
#             )

#             st.rerun()

#         except Exception as e:
#             st.error(f"Processing error: {str(e)}")
#             logger.error(f"Error: {str(e)}")
#     else:
#         if not st.session_state.show_month_prompt:
#             st.session_state.show_month_prompt = True
#             with st.chat_message("assistant"):
#                 st.write_stream(re_write_query_with_month())
#                 st.write_stream(write_question(question))

# st.divider()


######################################


import streamlit as st
import pandas as pd
from datetime import datetime
from aisight_llm.data_processor_and_loader import latest_month_year, data_loader
from aisight_llm.sql_gen_and_exec import generate_sql, execute_sql
from aisight_llm.streamlit_helper import *
from aisight_llm.settings import MAX_HISTORY_LENGTH
from aisight_llm.prompts.prompts import prompt, prompt_2
from aisight_llm.common_utils.logging import logger

# Streamlit App Configuration
st.set_page_config(
    page_title="Chat GPC - Home",
    layout="wide",
    page_icon="💬",
    initial_sidebar_state="expanded",
)

st.title("💬 Chat CPG")

# Initialize session state
init_session_state()
display_recent_queries()

# Greet user
if not st.session_state.greeted:
    with st.chat_message("assistant"):
        st.write_stream(greet_generator())
    st.session_state.greeted = True

# Display chat history
display_chat_history()

# Load data
llm_df = data_loader()
LATEST_MONTH, LATEST_YEAR = latest_month_year(llm_df)
user_input = st.chat_input("Type your message and press Enter...")
question = user_input.strip().lower() if user_input else ""

if check_specific_word(question):
    prompt = prompt_2

if not question:
    st.session_state.show_month_prompt = False
else:
    if check_month_in_question(question):
        updated_question = question.replace("why", "").strip() if "why" in question else question
        st.session_state.show_why = "why" in question
        unique_key = f"{datetime.now().timestamp()}_{st.session_state.analysis_counter}"
        st.session_state.analysis_counter += 1

        st.session_state.chat_history.append(
            {"question": question, "data": None, "sql": None, "why_result": None, "unique_key": unique_key}
        )

        try:
            with st.status("🚀 Processing...", expanded=True) as status:
                progress_bar = st.progress(0)
                sql_query, df_result = None, None

                for step, progress in st.session_state.processing_steps:
                    progress_bar.progress(progress, text=step)
                    time.sleep(1)

                    if "Thinking" in step:
                        enhanced_question = generate_enhanced_question(question)
                        sql_query = generate_sql(enhanced_question, LATEST_MONTH, LATEST_YEAR, prompt)
                        st.session_state.ex_sql = sql_query
                        logger.info(f"Generated SQL Query \n {sql_query}")

                    if "Searching Database" in step:
                        result_data = execute_sql(sql_query, llm_df)
                        df_result = result_data if isinstance(result_data, pd.DataFrame) else pd.DataFrame(result_data)

                progress_bar.empty()
                status.update(label="✅ Analysis Complete", state="complete")

            # --- GRID LAYOUT ---
            st.divider()
            col1, col2 = st.columns([2, 3])  # Two-column layout (Summary + Chart)
            
            # SUMMARY VIEW
            with col1:
                st.subheader("📄 Summary View")
                st.info("One-line summary here.")

            # CHART ANALYTICS
            with col2:
                st.subheader("📊 Chart Analytics")
                with st.container():
                    current_fig, chart_config, unique_key = display_chart_analytics(
                        df_result.copy(), unique_key=unique_key, is_editable=True
                    )

            st.divider()
            
            # TABLE VIEW (RESULTS)
            st.subheader("📋 Result View")
            st.dataframe(df_result, use_container_width=True)

            st.divider()

            # WHY ANALYSIS
            if st.session_state.show_why:
                st.subheader("❓ Why Results")
                st.dataframe(df_result, use_container_width=True)

            # Store analysis result
            st.session_state.chat_history[-1].update({"data": df_result, "sql": sql_query})

            if len(st.session_state.chat_history) > MAX_HISTORY_LENGTH:
                st.session_state.chat_history.pop(0)

            st.rerun()

        except Exception as e:
            st.error(f"Processing error: {str(e)}")
            logger.error(f"Error: {str(e)}")
    else:
        if not st.session_state.show_month_prompt:
            st.session_state.show_month_prompt = True
            with st.chat_message("assistant"):
                st.write_stream(re_write_query_with_month())
                st.write_stream(write_question(question))

st.divider()
