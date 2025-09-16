import streamlit as st
from streamlit_lottie import st_lottie



from src.llm_code.streamlit_helper import *
from src.llm_code.data_processor_and_loader import data_loader
from src.prompts.prompts import prompt, prompt_2 
from src.utils.logging import logger

loading_anim = load_lottie_url("https://assets2.lottiefiles.com/packages/lf20_usmfx6bp.json")
no_data_lottie = load_lottie_url("https://assets2.lottiefiles.com/packages/lf20_qp1q7mct.json")


def single_query (user_input, llm_df):
    logger.info(f"\n")
    logger.info(f"Single Query function running ...")
    llm_df = data_loader()
    LATEST_MONTH, LATEST_YEAR = latest_month_year(llm_df)

    question = user_input.strip().lower() if user_input else ""

    if user_input:
        st.session_state.query_processed = False
    
    if question and not st.session_state.query_processed:
        enhanced_question = generate_enhanced_question(question, LATEST_YEAR)

    prompt_used = prompt_2 if check_specific_word(question) else prompt


    if check_month_in_question(question):
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
                anim_placeholder = st.empty()
                step_placeholder = st.empty()
                sql_query, df_result = None, None

                with anim_placeholder:
                    st_lottie(loading_anim, height=200, key="loader")

                for step, progress in st.session_state.processing_steps:
                    step_placeholder.write(f"### {step}")
                    progress_bar.progress(progress)

                    if "Thinking" in step:
                        # sql_query = generate_sql_openrouterai(enhanced_question, LATEST_MONTH, LATEST_YEAR, prompt_used)
                        sql_query = generate_sql_openai(enhanced_question, LATEST_MONTH, LATEST_YEAR, prompt_used)
                        st.session_state.ex_sql = sql_query
                        logger.info(f"Generated SQL Query \n {sql_query}")

                    if "Searching Database" in step:
                        result_data = execute_sql(sql_query, llm_df)
                        df_result = result_data if isinstance(result_data, pd.DataFrame) else pd.DataFrame(result_data)
                        
                anim_placeholder.empty()
                step_placeholder.empty()
                progress_bar.empty()
                status.update(label="**Analysis Complete**", state="complete")

            st.divider()

            if result_data is not None and not result_data.empty:
                
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

                # st.divider()

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

            else:
                st_lottie(no_data_lottie, height=200, key="no_data")
                st.info("No data for Display")

        except Exception as e:
            st.error(f"Processing error: {str(e)}")
            logger.error(f"Error: {str(e)}")
    else:
        if not st.session_state.show_month_prompt:
            st.session_state.show_month_prompt = True
            with st.chat_message("assistant"):
                st.write_stream(re_write_query_with_month())
                st.write_stream(write_question(question))

# st.divider()

