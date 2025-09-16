import re
import time
import random
import string
import pandas as pd
import streamlit as st
import requests
from sqlglot import parse_one, exp
from typing import Generator
from streamlit_echarts import st_echarts

from src.constants import *
from src.utils.logging import logger
from .sql_gen_and_exec import execute_sql, generate_sql_openai
from src.prompts.prompts import prompt, prompt_comparison
from src.prompts.prompt_examples import two_month_examples, three_month_examples, filter_two_examples, filter_three_examples
from .data_processor_and_loader import latest_month_year, data_loader


def streamlit_initializer():
    st.set_page_config(
        page_title="Chat GPC - Home",
        layout="wide",
        page_icon="💬",
        initial_sidebar_state="expanded",
    )

    st.title("💬 Chat CPG")

def init_session_state():
    """Initialize session states in Streamlit"""
    session_defaults = {
        "chat_history": [],
        "context_history": [],
        "context_counter": 0,
        "chat_mode": "Single Query",
        "active_tab": "📊 Table View",
        "greeted": False,
        "processing_steps": [
            ("🔍 Parsing Question", 20),
            ("🧠 Thinking", 40),
            ("📡 Searching Database", 60),
            ("📊 Rendering Visuals", 80),
            ("✅ Finalizing", 100),
        ],
        "show_month_prompt": False,
        "show_selected_query": False,
        "selected_query": None,
        "show_tabs": False,
        "analysis_counter": 0,
        "response_streamed": False,
        "query_processed": False,
    }

    # Initialize session state variables if they do not exist
    for key, value in session_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def sidebar_conversation_selector():

    reverse_map = {v: k for k, v in MODE_DISPLAY.items()}
    default_mode = st.session_state.get("chat_mode", "Single Query")
    selected_display = reverse_map.get(default_mode, "Single Query Mode")

    select_chat_mode = st.sidebar.selectbox(
        "Select Chat Mode:",
        options=list(MODE_DISPLAY.keys()),
        index=list(MODE_DISPLAY.keys()).index(selected_display),
        help="Pick 'Single Query Mode' for standalone questions or 'Contextual Conversation' for threaded queries."
    )

    return select_chat_mode

def render_contextual_reset_button():
    if st.session_state.chat_mode == "Contextual Query":
        context_len = len(st.session_state.get("context_history", []))
        
        if context_len > 0:
            st.sidebar.write(f"📜 {context_len}/5 questions in current conversation")
            if st.sidebar.button("🔄 Reset Conversation", key="reset_button_confirm"):
                st.session_state.context_history = []
                st.sidebar.success("✅ Conversation reset! Start fresh.")
                st.rerun()

def greeter():
    if not st.session_state.greeted:
        with st.chat_message("assistant"):
            st.write_stream(greet_generator())
        st.session_state.greeted = True

def render_contextual_limits():
    if st.session_state.chat_mode == "Contextual Query" and len(st.session_state.get("context_history", [])) >= 5:
        with st.chat_message("assistant"):
            st.warning("⛔ Limit reached (5 contextual questions). Please click below to start a new conversation.")
            if st.button("🔄 Start New Context", key="restart_context_button"):
                st.session_state.context_history = []
                st.rerun()
        st.stop()

def stream_response(response: str, delay: float = 0.05) -> Generator[str, None, None]:
    """Generate streaming response with typing effect."""
    for word in response.split():
        yield word + " "
        time.sleep(delay)
    logger.info(response)

def greet_generator() -> Generator[str, None, None]:
    """Generate initial greeting message."""
    greetings = [
        "Hello there! How can I assist you today?",
        "Hi, Is there anything I can help you with?",
        "Do you need help? I'm here to assist you.",
    ]
    return stream_response(random.choice(greetings))

def question_exist_generator()  -> Generator[str, None, None]:
    """Generate Month if exsist"""
    month_exsist = [
        "Please select the month and year from the dropdown instead of typing it manually and Try Again.",
        "Please don't enter the month manually in the question, choose it from the given dropdown.",
        "Make sure to pick the options from the given dropdown instead of typing them out. Thanks",
        "Could you please use the provided filters to narrow down the results instead of free-text input?"
    ]
    return stream_response(random.choice(month_exsist))

def check_specific_word(question: str):
    list_words = ["assortment", "productivity", "stockout", "stockouts", "assortments"]
    for word in list_words:
        if word in question.lower():
            return word
    return None

def check_month_in_question(question: str) -> bool:
    """Check if the question contains a valid month reference (full names, numbers with 'month', ordinals)."""
    translator = str.maketrans("", "", string.punctuation)
    cleaned_question = question.lower().translate(translator)
    words = cleaned_question.split()

    month_terms = MONTH_NAMES + MONTH_ABBREVIATIONS
    if any(word in month_terms for word in words):
        return True

    for i, word in enumerate(words):
        if word.isdigit() and 1 <= int(word) <= 12:
            if (i > 0 and words[i - 1] == "month") or (i < len(words) - 1 and words[i + 1] == "month"):
                return True

        for suffix in ORDINAL_SUFFIXES:
            if word.endswith(suffix):
                num_part = word[:-len(suffix)]
                if num_part.isdigit() and 1 <= int(num_part) <= 12:
                    if (i > 0 and words[i - 1] == "month") or (i < len(words) - 1 and words[i + 1] == "month"):
                        return True

    return False

def re_write_query_with_month() -> Generator[str, None, None]:
    """Prompt user to include month in query."""
    prompts = [
        "Could you please include the specific month in your query so I can assist you better?",
        "It seems your query doesn't mention a month. Could you kindly rewrite it and specify the month you’re referring to?",
        "To provide accurate information, could you please rephrase your question and include the relevant month?",
    ]
    return stream_response(random.choice(prompts))

def write_question(user_question: str) -> Generator[str, None, None]:
    """Repeat user question for confirmation."""
    prefixes = [
        "Let me repeat your question for clarity: ",
        "Here’s how I understood your question: ",
        "You asked: ",
        "Just to confirm, your question is: ",
    ]
    return stream_response(random.choice(prefixes) + f"**{user_question}**")

def display_chart_analytics(df: pd.DataFrame, unique_key, is_editable=True):
    """Interactive bar chart using Apache ECharts in Streamlit."""

    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        st.warning("No data available for chart visualization.")
        return None, None, unique_key

    df.columns = [convert_to_readable_format_simple(col) for col in df.columns]
    df = df.rename(columns=lambda col: col.title() if isinstance(col, str) else col)

    non_numeric_columns, all_numeric_columns, _ = process_columns(df)

    for col in df.columns:
        if "percentage" in col.lower():
                df[col] = df[col].apply(lambda x: f"{int(x)} %" if x == int(x) else f"{round(x, 1)} %" if len(str(x).split(".")[1]) == 1 else f"{round(x, 2)} %" if pd.notna(x) else x)

    if not non_numeric_columns or not all_numeric_columns:
        st.warning("Insufficient data for chart.")
        return None, None, unique_key

    st.write("##### ⚙️ Chart Settings")
    col1, col2 = st.columns(2)
    with col1:
        x_axis = st.selectbox(
            "X-Axis (Dimension)",
            non_numeric_columns,
            key=f"x_axis_{unique_key}",
            disabled=not is_editable
        )
    with col2:
        highlight_col = st.selectbox(
            "Highlight Metric",
            ["All"] + all_numeric_columns,
            key=f"highlight_col_{unique_key}",
            disabled=not is_editable
        )

    if not x_axis:
        st.info("Please select a valid X-Axis to view chart.")
        return None, None, unique_key

    # ✅ Prepare chart data
    x_data = df[x_axis].astype(str).tolist()
    series = []

    for col in all_numeric_columns:
        y_data = df[col].fillna(0).tolist()
        opacity = 1.0 if highlight_col == "All" or highlight_col == col else 0.5
        series.append({
            "name": col,
            "type": "bar",
            "data": y_data,
            "emphasis": {"focus": "series"},
            "itemStyle": {"opacity": opacity}
        })

    option = {
        "tooltip": {"trigger": "axis"},
        "legend": {"data": all_numeric_columns},
        "xAxis": {"type": "category", "data": x_data, "name": x_axis.title()},
        "yAxis": {"type": "value", "name": "Metric Value"},
        "series": series,
        "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True}
    }

    st_echarts(options=option, height="520px", key=f"echart_{unique_key}")

    return option, {"x_axis": x_axis, "highlight_column": highlight_col}, unique_key

def display_chat_history():
    """Display chat history with preserved editable/non-editable state, including 'Why' analysis."""
    for idx, exchange in enumerate(st.session_state.chat_history):
        is_editable = idx == len(st.session_state.chat_history) - 1
        unique_key = f"chart_{idx}"

        with st.chat_message("user"):
            st.markdown(f"***{exchange['question']}***")
        st.divider()
        with st.chat_message("assistant"):
            df_data = exchange.get("data")

            if isinstance(df_data, pd.DataFrame):
                df = df_data.copy()
            elif isinstance(df_data, list):
                df = pd.DataFrame(df_data)
            elif isinstance(df_data, dict):
                df = pd.DataFrame.from_dict(df_data)
            else:
                df = pd.DataFrame()

            with st.container():
                display_table(df)

            why_results = exchange.get("why_result")
            if why_results is not None:
                st.write("### Why Results")
                st.dataframe(why_results, use_container_width=True)
            else:
                if not st.session_state.get(f"why_clicked_{idx}", False):
                    if st.button("Process 'Why'", key=f"process_why_{unique_key}_{idx}", disabled=not is_editable):
                        logger.info("Processing 'Why' button clicked...")
                        why_results = get_why_result(df)
                        if why_results is not None and not why_results.empty:
                            exchange["why_result"] = why_results
                            st.session_state.chat_history[idx]["why_result"] = why_results
                            st.session_state[f"why_clicked_{idx}"] = True
                            st.rerun()

            with st.container(border=True):
                col1, col2 = st.columns([2, 2.5])

            df.columns = [
                col if col is not None else f"Unnamed_{i}"
                for i, col in enumerate(df.columns)
            ]

            with col1:
                with st.container(border=True, height=666):
                    display_summary(df)

            with col2:
                with st.container(border=True):
                    st_echarts(exchange["chart_option"], height="520px", key=f"echart_hist_{idx}")
                    fig, _, unique_key = display_chart_analytics(
                        df, unique_key=unique_key, is_editable=is_editable
                    )

            st.divider()

def store_query_result(question, df_result, sql_query, why_result=None, unique_key=None):
    """Stores the current query result into chat_history with mode awareness."""
    mode = "contextual" if st.session_state.chat_mode == "Contextual Query" else "single"

    entry = {
        "question": question,
        "data": df_result,
        "sql": sql_query,
        "why_result": why_result,
        "unique_key": unique_key,
        "mode": mode,
    }

    if mode == "contextual":
        if "context_history" not in st.session_state:
            st.session_state.context_history = []

        if question and question.strip():
            print(f"Appending to context_history: {question}")
            st.session_state.context_history.append(question.strip())

            if len(st.session_state.context_history) > 5:
                st.session_state.context_history.pop(0)

            print(f"Updated context_history: {st.session_state.context_history}")
            entry["context_chain"] = st.session_state.context_history.copy()

    st.session_state.chat_history.append(entry)
    if len(st.session_state.chat_history) > MAX_HISTORY_LENGTH:
        st.session_state.chat_history.pop(0)

def build_contextual_question(new_question: str) -> str:
    """Construct a contextual query with Main/Follow-up style, limiting to 5 questions."""
    context = st.session_state.get("context_history", [])
    
    
    if not context:
        context.append(f"Main: {new_question.strip()}")
        st.session_state["context_history"] = context
        return new_question.strip()

    main_parts = []
    for i, item in enumerate(context):
        if isinstance(item, str):
            if "Follow-up:" in item:
                parts = item.split("Follow-up:")
                main = parts[0].replace("Main:", "").strip()
                follow = parts[1].strip()
                main_parts.extend([q.strip() for q in main.split(" | ") if q.strip()])
                main_parts.append(follow)
            else:
                main_parts.append(item.replace("Main:", "").strip())

    main_parts = [part for part in main_parts if part]
    main_combined = " | ".join(main_parts)
    
    contextual = f"Main: {main_combined}\nFollow-up: {new_question.strip()}"
    context.append(contextual)
    st.session_state["context_history"] = context

    if len(context) == 1:
        prompt = f"Main Query: {new_question.strip()}"
    elif len(context) == 2:
        prompt = f"Main Query: {main_parts[0]}\nFocus on this: {new_question.strip()}"
    elif len(context) == 3:
        prompt = f"Main Query: {main_parts[0]}\n2nd Question: {main_parts[1]}\nFocus on this 3rd Question: {new_question.strip()}"
    elif len(context) == 4:
        prompt = f"Main Query: {main_parts[0]}\n2nd Question: {main_parts[1]}\n3rd Question: {main_parts[2]}\nFocus on this 4th Question: {new_question.strip()}"
    elif len(context) == 5:
        prompt = f"Main Query: {main_parts[0]}\n2nd Question: {main_parts[1]}\n3rd Question: {main_parts[2]}\n4th Question: {main_parts[3]}\nFocus on this 5th Question: {new_question.strip()}"

    return prompt

def safe_to_numeric(val):
    try:
        return pd.to_numeric(val)
    except Exception:
        return val

def process_columns(df: pd.DataFrame) -> tuple[list[str], list[str], list[str]]:
    """Processes columns to separate numeric and non-numeric columns, and identifies percentage columns."""
    df = df.replace(",", "", regex=True).apply(safe_to_numeric)
    non_numeric_columns = df.select_dtypes(exclude=["number"]).columns.tolist()
    numeric_columns = df.select_dtypes(include=["number"]).columns.tolist()
    percentage_columns = []

    for col in non_numeric_columns:
        if df[col].astype(str).str.contains("%").any():
            percentage_columns.append(col)

    all_numeric_columns = numeric_columns + percentage_columns
    non_numeric_columns = [
        col for col in non_numeric_columns if col not in all_numeric_columns
    ]

    return non_numeric_columns, all_numeric_columns, percentage_columns

def convert_to_readable_format_simple(col_name):
    """Converts column from snake_case to a more readable Title Case format."""
    return col_name.replace("_", " ").title()

def generate_enhanced_question(question: str, latest_year) -> str:
    """Generates an enhanced question by determining GROUP BY clause and necessary calculations."""

    question_lower = question.lower()
    group_by_clause = ""

    for pattern, group_by in KEYWORD_GROUPBY_MAP.items():
        if re.search(pattern, question_lower):
            group_by_clause = f"strictly use SELECT {group_by} and GROUP BY {group_by} and always filter it by months and year, and if year is missing, use {latest_year}. "
            break

    return f"{group_by_clause if group_by_clause else f'strictly use SELECT and GROUP BY as defined and always filter it by year and months, and if year is missing, use {latest_year}'},{question}"

def upated_cached_queries(question):
    st.session_state.cached_queries.append(question)
    if len(st.session_state.cached_queries) > MAX_HISTORY_LENGTH:
        st.session_state.cached_queries.pop(0)

def display_table(df_result):
    """Display the DataFrame as a readable table with percentage formatting."""
    st.write("### Result View")
    if df_result is not None and isinstance(df_result, pd.DataFrame) and not df_result.empty:
        df_result.columns = [
            convert_to_readable_format_simple(col) for col in df_result.columns
        ]
        
        df_readable = df_result.rename(columns=lambda col: col.title() if isinstance(col, str) else col)

        for col in df_readable.columns:
            if "percentage" in col.lower():
                df_readable[col] = df_readable[col].apply(lambda x: f"{int(x)} %" if x == int(x) else f"{round(x, 1)} %" if len(str(x).split(".")[1]) == 1 else f"{round(x, 2)} %" if pd.notna(x) else x)

        df_readable.index = df_readable.index + 1
        st.dataframe(data=df_readable, use_container_width=True)
    else:
        st.info("No Results Found Please Check Your Query, Thanks")

def display_summary(df_result):
    """Display a summary of the DataFrame with percentage formatting."""
    st.write("### Summary View")
    if df_result is not None and isinstance(df_result, pd.DataFrame) and not df_result.empty:
        
        ### New Code
        # summary = generate_summary_openrouterai(df_result)
        # st.markdown(f"{summary}")
        
        #### OLD Code
        df_result.columns = [convert_to_readable_format_simple(str(col)) for col in df_result.columns]
        non_numeric_columns, all_numeric_columns, _ = process_columns(df_result)

        for _, row in df_result.iterrows():
            non_numeric_display = ", ".join([f"**{col}** is '{row[col]}'" for col in non_numeric_columns])
            st.markdown(f"- {non_numeric_display}")
            
            subpoints = []
            for col in all_numeric_columns:
                value = row[col]
                if "percentage" in col.lower():
                    try:
                        float_value = float(value)
                        if float_value == int(float_value):
                            value = f"{int(float_value)} %"
                        elif len(str(float_value).split(".")[1]) == 1:
                            value = f"{round(float_value, 1)} %"
                        else:
                            value = f"{round(float_value, 2)} %"
                    except (ValueError, TypeError):
                        value = "N/A %"

                subpoints.append(f"**-** {col} **: {value}**")

            for sub in subpoints:
                st.markdown(f"   {sub}")

    else:
        st.warning("No data available for summary.")

def display_recent_queries():
    """Displays recent queries in the sidebar."""
    st.sidebar.title("📜 Recent Queries")
    for idx, exchange in enumerate(st.session_state.chat_history, start=1):
        full_question = exchange["question"]
        truncated = (
            (full_question[:LETTER_LIMIT] + "...")
            if len(full_question) > 30
            else full_question
        )
        unique_key = exchange.get("unique_key", f"default_{idx}")
        why_result = exchange["why_result"]

        with st.sidebar.expander(f"Q{idx}: {truncated}", expanded=False):
            st.write(full_question)
            if st.button(f"Select Q{idx}", key=f"query_{idx}_{unique_key}"):
                confirm_query_selection(
                    full_question,
                    exchange["data"],
                    unique_key,
                    exchange["sql"],
                    why_result,
                )

@st.dialog("Confirm Query Selection", width="large")
def confirm_query_selection(question, df_result, unique_key, sql_query, why_result):
    if (
        "response_streamed" not in st.session_state
        or not st.session_state.response_streamed
    ):
        st.write_stream(stream_response(f"**Question: {question}**"))
        st.write("Result:")
        st.session_state.response_streamed = True

    tab1, tab2, tab3, tab4 = st.tabs(
        ["📊 Table", "📈 Analytics", "🔘 Summary", "❓ Why View"]
    )

    with tab1:
        display_table(df_result)
    with tab2:
        fig, _, unique_key = display_chart_analytics(
            df_result, unique_key=unique_key, is_editable=False
        )
    with tab3:
        display_summary(df_result)
    with tab4:
        if why_result is not None:
            st.write("### Why Results ")
            st.dataframe(why_result, use_container_width=True)
        else:
            st.warning("No 'Why' results available for this query.")

    if st.button("Close"):
        st.session_state.response_streamed = False
        st.rerun()

def get_last_non_numeric_column(result_df):
    """Get the last non-numeric column and their unique values"""
    non_numeric_columns = result_df.select_dtypes(exclude=["number"]).columns
    if len(non_numeric_columns) > 0:
        last_non_numeric_col = non_numeric_columns[-1]
        unique_values = result_df[last_non_numeric_col].unique().tolist()
        return last_non_numeric_col, unique_values
    return None, None

def get_why_result(result_df):
    """Display Why results"""
    llm_df = data_loader()
    LATEST_MONTH, LATEST_YEAR = latest_month_year(llm_df)
    st.write("### Why Results")
    sql_query = st.session_state.ex_sql
    last_col, last_col_values = get_last_non_numeric_column(result_df)
    year, month = extract_month_year_from_sql(sql_query)
    limit = extract_limit_from_sql(sql_query)
    print(f"LIMIT VALUE : {limit}")

    if not last_col:
        logger.info("No value for the 'WHY analysis")
        return pd.DataFrame()

    why_question = f"""
    Generate SQL to return:
    SUM(mro) AS total_mro, 
    SUM(unproductive_mro) AS total_unproductive_mro, 
    SUM(unassorted_mro) AS total_unassorted_mro, 
    SUM(stockout_mro) AS total_stockout_mro
    FROM the same table.

    Rules:
    - SELECT and GROUP BY only {last_col}
    - Use WHERE {last_col} IN ({', '.join(map(str, last_col_values))})
    - AND month = {month} AND year = {year}
    - LIMIT {limit if limit else 1}
    Do not add OR, IS NULL, or extra conditions.
    """
    why_sql = generate_sql_openai(why_question, latest_month=LATEST_MONTH, latest_year=LATEST_YEAR, prompt=prompt)
    logger.info(f"This is WHY SQL : \n{why_sql}")

    # try:
    why_result = execute_sql(why_sql, llm_df)
    if why_result.empty:
        st.write("No data available for the 'Why' analysis.")
        return pd.DataFrame()

    for col in ["total_unproductive_mro", "total_unassorted_mro", "total_stockout_mro"]:
        if col in why_result.columns and "total_mro" in why_result.columns:
            why_result[col] = why_result[col].astype(float)
            why_result["total_mro"] = why_result["total_mro"].astype(float)
            why_result[col] = why_result[col].astype(str) + " (" + (why_result[col] / why_result["total_mro"] * 100).round(2).astype(str) + "%)"

    logger.info(f"Generated 'Why' Results: \n{why_result}")
    why_result.columns = [convert_to_readable_format_simple(col) for col in why_result.columns]
    df_why_result = why_result.rename(columns=lambda col: col.title() if isinstance(col, str) else col)
    df_why_result.index = df_why_result.index + 1

    for idx, entry in enumerate(st.session_state.chat_history):
        if entry.get("sql") == st.session_state.ex_sql:
            logger.info(f"Match found! Now updating why result in chat history")
            st.session_state.chat_history[idx]["why_result"] = df_why_result
            st.session_state[f"why_clicked_{idx}"] = True
            break

    st.dataframe(df_why_result, use_container_width=True)
    return df_why_result

def extract_month_year_from_sql(sql_query):
    """Extract month and year from SQL WHERE clause and CASE WHEN statements."""
    try:
        expression = parse_one(sql_query)
        month_values, year_values = [], []

        def _extract_condition(expr):
            if isinstance(expr, exp.EQ):
                col = expr.left.name.lower()
                val = expr.right.this
                if col == "month":
                    month_values.append(val)
                elif col == "year":
                    year_values.append(val)
            elif isinstance(expr, exp.In):
                col = expr.this.name.lower()
                vals = [v.this for v in expr.expressions]
                if col == "month":
                    month_values.extend(vals)
                elif col == "year":
                    year_values.extend(vals)
            elif isinstance(expr, exp.And):
                for child in expr.flatten():
                    _extract_condition(child)

        # 1. WHERE clause
        where = expression.find(exp.Where)
        if where:
            for cond in where.iter_expressions():
                _extract_condition(cond)

        # 2. CASE WHEN conditions
        for case_expr in expression.find_all(exp.Case):
            for when_clause in case_expr.args.get("ifs", []):  # list of exp.When
                cond_expr = when_clause.this  # condition part of WHEN
                _extract_condition(cond_expr)

        month = month_values[-1] if month_values else None
        year = year_values[-1] if year_values else None
        return year, month
    except Exception as e:
        print(f"Error parsing SQL: {e}")
        return None, None

def extract_limit_from_sql(sql_query):
    """Extract LIMIT value from SQL query using sqlglot."""
    try:
        expression = parse_one(sql_query)
        limit_exp = expression.find(exp.Limit)
        if limit_exp:
            # LIMIT value is usually in `this`
            return int(limit_exp.expression.this)
        return None
    except Exception as e:
        print(f"Error parsing SQL for LIMIT: {e}")
        return None

def get_comparison_year_month(df: pd.DataFrame):
    """Get month/year comparison values (2 or 3 months based on user choice)."""
    available_years = sorted(df.year.unique().tolist(), reverse=True)
    available_months = sorted(df.month.unique().tolist())

    print("Enter in the Comparison Query")

    option = st.radio(
        "Select Comparison Type",
        ["Two Month Comparison", "Three Month Comparison"],
        key="comparison_type_radio"
    )

    if option == "Two Month Comparison":
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            year1 = st.selectbox("Select First Year", available_years, key="year1")
            month1 = st.selectbox("Select First Month", available_months, key="month1")
        with col3:
            year2 = st.selectbox("Select Second Year", available_years, key="year2")
            month2 = st.selectbox("Select Second Month", available_months, key="month2")
        return [(year1, month1), (year2, month2)]

    elif option == "Three Month Comparison":
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            year1 = st.selectbox("Year 1", available_years, key="year1")
            month1 = st.selectbox("Month 1", available_months, key="month1")
        with col3:
            year2 = st.selectbox("Year 2", available_years, key="year2")
            month2 = st.selectbox("Month 2", available_months, key="month2")
        with col5:
            year3 = st.selectbox("Year 3", available_years, key="year3")
            month3 = st.selectbox("Month 3", available_months, key="month3")
        return [(year1, month1), (year2, month2), (year3, month3)]

def build_comparision_query(question: str, selections: list):

    group_by_clause = ""
    q_lower = question.lower()
    for pattern, group_by in KEYWORD_GROUPBY_MAP.items():
        if re.search(pattern, q_lower):
            group_by_clause = f"strictly use SELECT {group_by} and GROUP BY {group_by}. "
            break
    
    if len(selections) == 2:
        (year1, month1), (year2, month2) = selections

        if check_specific_word(question):
            example_block = filter_two_examples
        else:
            example_block = two_month_examples

        enchanced_question = f"Compare between {month1}-{year1} and {month2}-{year2}, Questions : {question}" 
    elif len(selections) == 3:
        (year1, month1), (year2, month2), (year3, month3) = selections
        
        if check_specific_word(question):
            example_block = filter_three_examples
        else:
            example_block = three_month_examples
        
        enchanced_question = f"Compare between {month1}-{year1}, {month2}-{year2}, and {month3}-{year3}, Questions : {question}"
    
    prompt_used = prompt_comparison + example_block
    return enchanced_question, prompt_used

# --- Load Lottie animation ---
def load_lottie_url(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

LOADING_ANIM = load_lottie_url("https://assets2.lottiefiles.com/packages/lf20_usmfx6bp.json")
NO_DATA_ANIM = load_lottie_url("https://assets2.lottiefiles.com/packages/lf20_qp1q7mct.json")