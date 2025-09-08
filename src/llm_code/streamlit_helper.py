import re
import time
import random
import string
import pandas as pd
import streamlit as st
import plotly.express as px
from sqlglot import parse_one, exp
from datetime import datetime
from typing import Generator, Tuple, List

from src.constants import *
from src.utils.logging import logger
from .sql_gen_and_exec import generate_sql, execute_sql, generate_sql_chat, generate_sql_openrouterai, generate_summary_openrouterai, generate_sql_openai
from src.prompts.prompts import prompt
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

def greetor():
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

def check_specific_word(question):
    list_words = ["assortment", "productivity", "stockout", "stockouts"]
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
    """Elegant interactive bar chart with highlight, hover, and percentage handling."""

    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        st.warning("No data available for chart visualization.")
        return None, None, unique_key

    df.columns = [convert_to_readable_format_simple(col) for col in df.columns]
    non_numeric_columns, all_numeric_columns, percentage_columns = process_columns(df)

    if not non_numeric_columns or not all_numeric_columns:
        st.warning("Insufficient data for chart.")
        return None, None, unique_key

    # -- Chart Config UI
    st.write("##### ⚙️ Chart Settings")
    col1, col2 = st.columns(2)
    with col1:
        x_axis = st.selectbox("X-Axis (Dimension)", non_numeric_columns, key=f"x_axis_{unique_key}", disabled=not is_editable)
    with col2:
        highlight_col = st.selectbox("Highlight Metric", ["All"] + all_numeric_columns, key=f"highlight_col_{unique_key}", disabled=not is_editable)

    if not x_axis:
        st.info("Please select a valid X-Axis to view chart.")
        return None, None, unique_key

    df_chart = df.copy()
    y_axis_cols, y_labels_map = [], {}

    for col in all_numeric_columns:
        col_clean = col.strip()
        if "percentage" in col_clean.lower():
            new_col = f"{col_clean}_numeric"
            df_chart[new_col] = df_chart[col_clean].astype(float)
            y_labels_map[new_col] = col_clean
            y_axis_cols.append(new_col)
        else:
            y_axis_cols.append(col_clean)

    try:
        fig = px.bar(
            df_chart,
            x=x_axis,
            y=y_axis_cols,
            barmode="group",
            title=f"📊 Metrics by {x_axis.title()}",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )

        for trace in fig.data:
            orig_name = trace.name
            trace.opacity = 1.0 if highlight_col == "All" or orig_name == highlight_col else 0.5

        for trace in fig.data:
            name = trace.name
            col = y_labels_map.get(name, name)
            values = df_chart[name] if name in df_chart.columns else []
            is_pct = "percentage" in col.lower()

            # Show text only if value is reasonably large (auto adapts to filtered data)
            text = []
            text_position = []

            for val in values:
                if is_pct:
                    if val >= 10:  # >=10% visible inside the bar
                        text.append(f"{val:.1f}%")
                        text_position.append("inside")
                    elif val >= 5:  # between 5%-10% visible but no text
                        text.append("")
                        text_position.append("none")
                    else:  # hide completely
                        text.append("")
                        text_position.append("none")
                else:
                    if val >= 1000:  # big numeric values
                        text.append(f"{val:,.0f}")
                        text_position.append("auto")
                    elif val >= 100:
                        text.append(f"{val:,.0f}")
                        text_position.append("inside")
                    else:
                        text.append("")
                        text_position.append("none")

            trace.text = text
            trace.textposition = text_position
            trace.textfont = dict(size=13, color="black")

            trace.hovertemplate = (
                f"<b>{col}</b><br>{x_axis}: %{{x}}<br>Value: %{{y:.1f}}%" if is_pct
                else f"<b>{col}</b><br>{x_axis}: %{{x}}<br>Value: %{{y:,.0f}}"
            )

        fig.update_layout(
            height=520,
            yaxis_title="Metric Value",
            xaxis_title=x_axis.title(),
            legend=dict(orientation="h", x=0.3, xanchor="center", y=-0.1),
            title_font=dict(size=10, family="Arial", color="#333"),
            bargap=0.2,
            hovermode="closest",
            plot_bgcolor="rgba(250,250,255,0.9)",
            paper_bgcolor="white",
        )

        st.plotly_chart(fig, use_container_width=True, key=f"plot_{unique_key}")
        return fig, {"x_axis": x_axis, "highlight_column": highlight_col}, unique_key

    except Exception as e:
        st.error(f"Chart error: {e}")
        return None, None, unique_key


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

def process_columns(df: pd.DataFrame) -> Tuple[List[str], List[str], List[str]]:
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

def generate_enhanced_question(question: str) -> str:
    """Generates an enhanced question by determining GROUP BY clause and necessary calculations."""
    keyword_groupby_map = {
        r"\broute(s)?\b": "region, city, area, territory, distributor, route",
        r"\bdistributor(s)?\b": "region, city, area, territory, distributor",
        r"\bterritory|territories\b": "region, city, area, territory",
        r"\barea(s)?\b": "region, city, area",
        r"\bcity|cities\b": "region, city",
        r"\bregion(s)?\b": "region",
    }

    metric_formulas = {
        "stockout": """'COUNT(DISTINCT CASE WHEN month = given_month AND year = given_year AND stockout = 1 THEN customer END) AS stockout_shops,
                      COUNT(DISTINCT CASE WHEN month = given_month AND year = given_year AND stockout = 0 THEN customer END) AS not_stockout_shops,
                      COUNT(DISTINCT customer) AS total_shops, 
                      (COUNT(DISTINCT CASE WHEN month = given_month AND year = given_year AND stockout = 1 THEN customer END) * 100.0 / COUNT(DISTINCT customer)) AS stockout_percentage,
                      (COUNT(DISTINCT CASE WHEN month = given_month AND year = given_year AND stockout = 0 THEN customer END) * 100.0 / COUNT(DISTINCT customer)) AS no_stockout_percentage' see Example 2 and 3 """,
        "productivity": """'COUNT(DISTINCT CASE WHEN month = given_month AND year = given_year AND productivity = 1 THEN customer END) AS productive_shops, 
                        COUNT(DISTINCT CASE WHEN month = given_month AND year = given_year AND productivity = 0 THEN customer END) AS un_productive_shops,
                        COUNT(DISTINCT customer) AS total_shops, 
                        (COUNT(DISTINCT CASE WHEN month = given_month AND year = given_year AND productivity = 1 THEN customer END) * 100.0 / COUNT(DISTINCT customer)) AS productivity_percentage,
                        (COUNT(DISTINCT CASE WHEN month = given_month AND year = given_year AND productivity = 0 THEN customer END) * 100.0 / COUNT(DISTINCT customer)) AS unproductivity_percentage' see Example 2 and 3 """,
        "assortment": """'COUNT(DISTINCT CASE WHEN month = given_month AND year = given_year AND assortment = 1 THEN customer END) AS un_assorted_shops,
                      COUNT(DISTINCT CASE WHEN month = given_month AND year = given_year AND assortment = 0 THEN customer END) AS assorted_shops, 
                      COUNT(DISTINCT customer) AS total_shops, 
                      (COUNT(DISTINCT CASE WHEN month = given_month AND year = given_year AND assortment = 1 THEN customer END) * 100.0 / COUNT(DISTINCT customer)) AS high_assortment_percentage,
                      (COUNT(DISTINCT CASE WHEN month = given_month AND year = given_year AND assortment = 0 THEN customer END) * 100.0 / COUNT(DISTINCT customer)) AS low_assortment_percentage' see Example 2 and 3 """
    }

    question_lower = question.lower()
    group_by_clause = ""

    for pattern, group_by in keyword_groupby_map.items():
        if re.search(pattern, question_lower):
            group_by_clause = f"strictly use SELECT {group_by} and GROUP BY {group_by} and always filter it by year and months"
            break

    formula_parts = [
        formula
        for keyword, formula in metric_formulas.items()
        if keyword in question_lower
    ]

    if formula_parts:
        return f"{group_by_clause} and also use this formula in the SELECT clause {', '.join(formula_parts)}, {question}"

    return f"{group_by_clause if group_by_clause else 'strictly use SELECT and GROUP BY as defined and always filter it by year and months'},{question}"

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
        st.warning("No data available for the table.")

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

    if not last_col:
        logger.info("No value for the 'WHY analysis")
        return pd.DataFrame()

    why_question = f"Strictly retrieve only the following aggregates: SUM(mro) AS total_mro, SUM(unproductive_mro) AS total_unproductive_mro, SUM(unassorted_mro) AS total_unassorted_mro, SUM(stockout_mro) AS total_stockout_mro, should be based on the filtered data, also utilize SELECT and GROUP BY as defined below. The column is {last_col} with values are {last_col_values}, for the month {month} and year {year}."
    # why_sql = generate_sql_chat(why_question, latest_month=LATEST_MONTH, latest_year=LATEST_YEAR, prompt=prompt)
    why_sql = generate_sql_openrouterai(why_question, latest_month=LATEST_MONTH, latest_year=LATEST_YEAR, prompt=prompt)
    # why_sql = generate_sql_openai(why_question, latest_month=LATEST_MONTH, latest_year=LATEST_YEAR, prompt=prompt)
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
    
    # except Exception as e:
    #     logger.error(f"Error generating percentages of 'Why' result: {e}")
    #     st.write_stream(
    #         stream_response("**An error occurred while generating the 'Why' results.**")
    #     )
    #     return pd.DataFrame()

def extract_month_year_from_sql(sql_query):
    """Extract month and year from SQL WHERE clause and CASE WHEN statements."""
    try:
        expression = parse_one(sql_query)
        month_values = []
        year_values = []

        where = expression.find(exp.Where)
        if where:
            def _extract_condition(condition):
                if isinstance(condition, exp.EQ):
                    col = condition.left.name.lower()
                    value = condition.right.this
                    if col == "month":
                        month_values.append(value)
                    elif col == "year":
                        year_values.append(value)
                elif isinstance(condition, exp.In):
                    col = condition.this.name.lower()
                    values = [v.this for v in condition.expressions]
                    if col == "month":
                        month_values.extend(values)
                    elif col == "year":
                        year_values.extend(values)

            for condition in where.iter_expressions():
                if isinstance(condition, exp.And):
                    for child in condition.flatten():
                        _extract_condition(child)
                else:
                    _extract_condition(condition)

        for case_expr in expression.find_all(exp.Case):
            for condition in case_expr.args.get("ifs", []):
                if isinstance(condition.this, exp.And):
                    for child in condition.this.flatten():
                        _extract_condition(child)
                else:
                    _extract_condition(condition.this)

        month = month_values[-1] if month_values else None
        year = year_values[-1] if year_values else None
        return year, month
    except Exception as e:
        print(f"Error parsing SQL: {e}")
        return None, None
    