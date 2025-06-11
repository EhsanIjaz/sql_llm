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
from constants import MAX_HISTORY_LENGTH, LETTER_LIMIT
from constants import *
from common_utils.logging import logger
from .sql_gen_and_exec import generate_sql, execute_sql, generate_sql_chat
from .prompts.prompts import prompt
from .data_processor_and_loader import latest_month_year, data_loader


# Session State Initialization
def init_session_state():
    """Intialize session states in Streamlit"""

    session_defaults = {
        "chat_history": [],
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
    }

    # Initialize session state variables if they do not exist
    for key, value in session_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def stream_response(response: str, delay: float = 0.05) -> Generator[str, None, None]:
    """Generate streaming response with typing effect."""
    
    for word in response.split():
        print(word)
        yield word + " "
        time.sleep(delay)


def greet_generator() -> Generator[str, None, None]:
    """Generate initial greeting message."""
    greetings = [
        "Hello there! How can I assist you today?",
        "Hi, Is there anything I can help you with?",
        "Do you need help? I'm here to assist you.",
    ]
    return stream_response(random.choice(greetings))


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
    """Display interactive chart analytics with improved formatting, hover tooltips, and 'All' highlight option."""

    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        st.warning("No data available for chart visualization.")
        return None, None, unique_key

    df.columns = [convert_to_readable_format_simple(col) for col in df.columns]
    non_numeric_columns, all_numeric_columns, percentage_columns = process_columns(df)

    if not non_numeric_columns or not all_numeric_columns:
        st.warning("Insufficient data types for visualization.")
        return None, None, unique_key

    # Default chart settings
    chart_config = {"x_axis": None, "highlight_column": "All"}  # Default: All highlighted

    st.write("##### ⚙️ Chart Settings")
    col1, col2 = st.columns([1, 1])

        # X-Axis selection (non-numeric columns)
    with col1:
        chart_config["x_axis"] = st.selectbox(
            "Location Column (X-Axis)",
            non_numeric_columns,
            key=f"x_axis_{unique_key}",
            disabled=not is_editable,
        )


    # Highlight Column Selection (with "All" option)
    with col2:
        chart_config["highlight_column"] = st.selectbox(
            "Highlight Column",
            ["All"] + all_numeric_columns,
            key=f"highlight_column_{unique_key}",
            disabled=not is_editable,
        )

    if chart_config["x_axis"]:
        df_chart = df.copy()
        y_axis_numeric = []
        percentage_format_map = {}

        # Convert percentage columns to numeric values
        for col in all_numeric_columns:
            if "percentage" in col.lower():  
                df_chart[col + "_numeric"] = df_chart[col].astype(float)
                y_axis_numeric.append(col + "_numeric")
                percentage_format_map[col + "_numeric"] = col  # Map numeric column to original
            else:
                y_axis_numeric.append(col)

        # Create the bar chart with all numeric columns
        try:
            fig = px.bar(
                df_chart,
                x=chart_config["x_axis"],
                y=y_axis_numeric,
                barmode="group",
                title=f"Comparison of Metrics by {chart_config['x_axis'].title()}",
                labels={chart_config["x_axis"]: chart_config["x_axis"].title()},
                color_discrete_sequence=px.colors.qualitative.Set3,  # Colorful bars
            )


            # Adjust bar transparency based on selected highlight column
            highlight_col = chart_config["highlight_column"]
            for trace, col in zip(fig.data, all_numeric_columns):
                trace.opacity = 1.0 if highlight_col == "All" or col == highlight_col else 0.3  # Dim others

            # Add value labels on top of bars
            for trace, col in zip(fig.data, y_axis_numeric):
                original_col = percentage_format_map.get(col, col)  # Get original column name
                
                # Format values (add % sign for percentage columns)
                if "percentage" in original_col.lower():
                    df_chart["text_label"] = df_chart[col].apply(lambda x: f"{x:.2f}%")
                else:
                    df_chart["text_label"] = df_chart[col].apply(lambda x: f"{x:.2f}")

                trace.text = df_chart["text_label"]
                trace.textposition = "outside"
                trace.textfont = dict(size=14, color="black", family="Arial Black")

            # Improve hover info
            for trace, col in zip(fig.data, y_axis_numeric):
                original_col = percentage_format_map.get(col, col)  # Get original column name
                trace.hovertemplate = (
                    f"<b>{original_col}</b><br>{chart_config['x_axis']}: %{{x}}<br><b>Value</b>: %{{y:.2f}}%"
                    if "percentage" in original_col.lower()
                    else f"<b>{original_col}</b><br>{chart_config['x_axis']}: %{{x}}<br><b>Value</b>: %{{y:.2f}}"
                )

            # Improve layout and design
            fig.update_layout(
                    yaxis_title="Value",
                    xaxis_title=chart_config["x_axis"].title(),
                    title_font=dict(size=14, family="Arial", color="#2c3e50"),
                    legend_title_text="",  # Remove legend title to avoid overlap
                    legend=dict(
                        orientation="h",
                        yanchor="top",  
                        y=-0.15,  # Move legend below chart title
                        x=0.5,
                        xanchor="center"
                    ),
                    height=510,
                    plot_bgcolor="rgba(240, 248, 255, 0.9)",  # AliceBlue background
                    paper_bgcolor="white",
                    font=dict(color="#2c3e50"),
                    bargap=0.4,
                    hovermode="x unified",
                    clickmode="event+select",
                )

            # Ensure the chart is placed inside a container (prevents layout breaking)
            with st.container():
                st.plotly_chart(fig, use_container_width=True, key=f"plotly_chart_{unique_key}")

        except Exception as e:
            st.error(f"Error generating visualization: {e}")
            return None, None, unique_key

    else:
        st.write("Please select an X-Axis.")

    return fig, chart_config, unique_key


def display_chat_history():
    """Display chat history with preserved editable/non-editable state, including 'Why' analysis."""
    
    for idx, exchange in enumerate(st.session_state.chat_history):
        is_editable = idx == len(st.session_state.chat_history) - 1
        unique_key = f"chart_{idx}"

        with st.chat_message("user"):
            st.markdown(f"***{exchange['question']}***")
        st.divider()
        with st.chat_message("assistant"):
            
        # Get Data
            df_data = exchange.get("data")

            if isinstance(df_data, pd.DataFrame):
                df = df_data.copy()
            elif isinstance(df_data, list):
                df = pd.DataFrame(df_data)
            elif isinstance(df_data, dict):
                df = pd.DataFrame.from_dict(df_data)
            else:
                df = pd.DataFrame()
            
            # --- GRID LAYOUT ---
            with st.container():
                display_table(df)


            # WHY ANALYSIS
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
                            st.session_state[f"why_clicked_{idx}"] = True  # ✅ Store state before rerun
                            st.rerun()

            with st.container(border=True):
                col1, col2 = st.columns([2, 2.5])  # Two-column layout (Summary + Chart)

            # Ensure column names are valid
            df.columns = [
                col if col is not None else f"Unnamed_{i}"
                for i, col in enumerate(df.columns)
            ]

            # SUMMARY VIEW
            with col1:
                with st.container(border=True, height= 666):
                    display_summary(df)

            # CHART ANALYTICS
            with col2:
                with st.container(border=True):
                    fig, _, unique_key = display_chart_analytics(
                        df, unique_key=unique_key, is_editable=is_editable
                    )

            st.divider()


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
            if (i > 0 and words[i - 1] == "month") or (
                i < len(words) - 1 and words[i + 1] == "month"
            ):
                return True

        for suffix in ORDINAL_SUFFIXES:
            if word.endswith(suffix):
                num_part = word[: -len(suffix)]
                if num_part.isdigit() and 1 <= int(num_part) <= 12:
                    if (i > 0 and words[i - 1] == "month") or (
                        i < len(words) - 1 and words[i + 1] == "month"
                    ):
                        return True

    return False


def check_specific_word (question):

    list_words = ["assortment" , "productivity" , "stockout" , "stockouts"]

    for word in list_words:
        if word in question.lower():
            return word
    return None


def safe_to_numeric(val):
    try:
        return pd.to_numeric(val)
    except Exception:
        return val


def process_columns(df: pd.DataFrame) -> Tuple[List[str], List[str], List[str]]:
    """
    Processes columns to separate numeric and non-numeric columns, and identifies percentage columns.
    """

    # Ensure numeric-looking columns are properly converted
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

        # Format percentage columns (rounding and adding '%')
        for col in df_readable.columns:
            if "percentage" in col.lower():  # Check if column name contains 'Percentage'
                df_readable[col] = df_readable[col].apply(lambda x: f"{int(x)} %" if x == int(x) else f"{round(x, 1)} %" if len(str(x).split(".")[1]) == 1 else f"{round(x, 2)} %" if pd.notna(x) else x)


        df_readable.index = df_readable.index + 1  # Adjust index for readability
        st.dataframe(data= df_readable, use_container_width=True)
    else:
        st.warning("No data available for the table.")


def display_summary(df_result):
    """Display a summary of the DataFrame with percentage formatting."""

    st.write("### Summary View")
    if df_result is not None and isinstance(df_result, pd.DataFrame) and not df_result.empty:

        # Convert column names to readable format
        df_result.columns = [convert_to_readable_format_simple(str(col)) for col in df_result.columns]

        # Identify column types
        non_numeric_columns, all_numeric_columns, _ = process_columns(df_result)

        for _, row in df_result.iterrows():
            # Display non-numeric values
            non_numeric_display = ", ".join([f"**{col}** is '{row[col]}'" for col in non_numeric_columns])
            stream_response(type(st.markdown(f"- {non_numeric_display}")) )
            
            subpoints = []
            for i, col in enumerate(all_numeric_columns):
                value = row[col]

                # Automatically detect percentage columns
                if "percentage" in col.lower():
                    try:
                        float_value = float(value)
                        if float_value == int(float_value):  # If whole number
                            value = f"{int(float_value)} %"
                        elif len(str(float_value).split(".")[1]) == 1:  # If one decimal place
                            value = f"{round(float_value, 1)} %"
                        else:  # Otherwise, round to two decimal places
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

            if st.button(f"Select Q{idx}", key=f"query_{unique_key}"):
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


# "Why" Logic

def get_last_non_numeric_column(result_df):
    """Get the Last non mumeric column and their unique values"""

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
    why_sql = generate_sql_chat(why_question, latest_month=LATEST_MONTH, latest_year=LATEST_YEAR, prompt=prompt)
    logger.info(f"This is WHY SQL : \n{why_sql}")

    try:
        why_result = execute_sql(why_sql, llm_df)

        if why_result.empty:
            st.write("No data available for the 'Why' analysis.")
            return pd.DataFrame()

        # Ensure calculations don't break
        for col in ["total_unproductive_mro", "total_unassorted_mro", "total_stockout_mro"]:
            if col in why_result.columns and "total_mro" in why_result.columns:
                why_result[col] = why_result[col].astype(float)  # Convert to float for calculation
                why_result["total_mro"] = why_result["total_mro"].astype(float)
                why_result[col] = why_result[col].astype(str) + " (" + (why_result[col] / why_result["total_mro"] * 100).round(2).astype(str) + "%)"

        logger.info(f"Generated 'Why' Results: \n{why_result}")

        why_result.columns = [ convert_to_readable_format_simple(col) for col in why_result.columns ]
        df_why_result = why_result.rename( columns=lambda col: col.title() if isinstance(col, str) else col )
        df_why_result.index = df_why_result.index + 1

        for idx, entry in enumerate(st.session_state.chat_history):
            if entry.get("sql") == st.session_state.ex_sql:
                logger.info(f"Match found! Now updating why result in chat history")
                st.session_state.chat_history[idx]["why_result"] = df_why_result
                st.session_state[f"why_clicked_{idx}"] = True  # ✅ Store state before rerun
                break

        st.dataframe(df_why_result, use_container_width=True)
        return df_why_result  # ✅ Always return a DataFrame
        
    except Exception as e:
        logger.error(f"Error generating percentages of 'Why' result: {e}")
        st.write_stream(
            stream_response("**An error occurred while generating the 'Why' results.**")
        )
        return pd.DataFrame()


def extract_month_year_from_sql(sql_query):
    """Extract month and year from SQL WHERE clause and CASE WHEN statements."""
    try:
        expression = parse_one(sql_query)
        month_values = []
        year_values = []

        # Extract from WHERE clause
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

        # Extract from CASE WHEN statements
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
