import torch
import sqlparse
import streamlit as st
from typing import Optional
import duckdb
import pandas as pd
import openai
from openai import OpenAI
import os
import requests
from dotenv import load_dotenv


from src.utils.decorator import time_checker
from transformers import AutoTokenizer, AutoModelForCausalLM
from src.utils.logging import logger
from src.constants import *

logger.info(f"Initialized Model : {MODEL_NAME} ")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
logger.info(f"Initialized Device: {DEVICE}")

load_dotenv(DEFAULT_ENV_VARS_PATH)

@st.cache_resource(show_spinner=False)
def load_model():
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
        device_map=DEVICE,
        use_cache=True,
        cache_dir=MODEL_CHACHED_DIR,
    )
    # logger.info("Model loaded successfully")
    return model


@st.cache_resource(show_spinner=False)
def get_tokenizer():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, cache_dir=MODEL_CHACHED_DIR)
    # logger.info("Tokenizer loaded successfully")
    return tokenizer


@time_checker
@st.cache_resource(show_spinner=False)
def generate_sql(question: str, latest_month: int, latest_year: int, prompt: str) -> str:

    logger.info(f"Question: {question}")
    model = load_model()
    tokenizer = get_tokenizer()

    updated_prompt = prompt.format(
        question=question, latest_month=latest_month, latest_year=latest_year
    )

    if DEVICE == "cpu":
        inputs = tokenizer(updated_prompt, return_tensors="pt")
    else:
        inputs = tokenizer(updated_prompt, return_tensors="pt").to("cuda")

    generated_ids = model.generate(
        **inputs,
        num_return_sequences=1,
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.eos_token_id,
        max_new_tokens=400,
        do_sample=False,
        num_beams=1,
    )
    outputs = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)
    # logger.info("SQL generated successfully")
    return sqlparse.format(outputs[0].split("[SQL]")[-1], reindent=True)


def generate_sql_chat(question: str, latest_month: int, latest_year: int, prompt: str):
    print("running generate_sql_chat")
    updated_prompt = prompt.format(
        question=question, latest_month=latest_month, latest_year=latest_year
    )
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": updated_prompt},
            {"role": "user", "content": question}
        ],
        temperature=0,
        max_tokens=400
    )
    sql_query = response.choices[0].message.content.strip()
    print(sql_query)
    return sql_query


def generate_sql_openrouterai (question: str, latest_month: str, latest_year:str, prompt:str):

    print("running generate_sql_openrouterai")
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_api_key:
        print("Key Not FOUND")
    else:
        print("Key Found")    
    client = openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key= openrouter_api_key
    )

    updated_prompt = prompt.format(
        question=question, latest_month=latest_month, latest_year=latest_year
    )

    try:
        response = client.chat.completions.create(

            # model="sarvamai/sarvam-m:free",
            model= "google/gemma-3n-e4b-it:free",
            messages=[
                # {"role": "system", "content": updated_prompt},
                # {"role": "user", "content": question} 
                {"role": "user", "content": f"{updated_prompt}\n\n{question}"}
            ],
            temperature=0,
            max_tokens=400
        )

        
        sql_query = response.choices[0].message.content.strip()
        lines = sql_query.strip().split('\n')

        if len(lines) >= 2:
            stripped_sql = '\n'.join(lines[1:-1])
        else:
            stripped_sql = sql_query
  
        # 🔹 Fetch usage/quota info
        usage_url = "https://openrouter.ai/api/v1/auth/key"
        headers = {"Authorization": f"Bearer {openrouter_api_key}"}
        usage_resp = requests.get(usage_url, headers=headers)

        # if usage_resp.status_code == 200:
        #     usage_data = usage_resp.json()
        #     print("🔹 API Usage Info:", usage_data)
        # else:
        #     print(f"⚠️ Could not fetch usage info (status {usage_resp.json()})")

        return stripped_sql
        
    except Exception as e:
        print(f"Error calling OpenRouter API for Sarvam-M: {e}")
        return f"Error: API call failed - {e}"
    

def generate_summary_openrouterai(df, prompt: str = None):
    """
    Generate bullet-point summary from a dataframe using OpenRouter API.
    """
    print("running generate_summary_openrouterai")
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_api_key:
        print("Key Not FOUND")
        return None
    else:
        print("Key Found")

    client = openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=openrouter_api_key
    )

    df_text = df.head(10).to_string(index=False)  # show top 10 rows only
    if prompt is None:
        prompt = """You are a data summarizer.
        Given the following dataframe, generate a bullet-point or bullet-points  summary.
        Each bullet should describe one row with key column information.
        Keep it short and clear.
        """

    updated_prompt = f"{prompt}\n\nDataFrame Preview:\n{df_text}"

    try:
        response = client.chat.completions.create(
            model="google/gemma-3n-e4b-it:free",
            messages=[
                {"role": "user", "content": updated_prompt}
            ],
            temperature=0.2,
            max_tokens=400
        )

        summary = response.choices[0].message.content.strip()
        return summary

    except Exception as e:
        print(f"Error calling OpenRouter API for summary: {e}")
        return f"Error: API call failed - {e}"


def execute_sql(query: str, df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """Execute SQL query on the DataFrame using DuckDB."""
    try:
        with duckdb.connect() as conn:
            conn.register("llm_df", df)
            result = conn.execute(query).fetchdf()
            return result if not result.empty else None

    except duckdb.Error as e:
        logger.error(f"SQL execution failed: {str(e)}")
        st.error("Invalid query format. Please check your syntax.")
        return None


def generate_sql_openai(question: str, latest_month: str, latest_year: str, prompt: str):
    """
    Generates SQL using OpenAI API instead of OpenRouter.
    Requires OPENAI_API_KEY in environment variables.
    """

    print("running generate_sql_openai")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("Key Not FOUND")
        return "Error: OPENAI_API_KEY not set"
    else:
        print("Key Found")

    client = OpenAI(api_key=openai_api_key)

    updated_prompt = prompt.format(
        question=question, latest_month=latest_month, latest_year=latest_year
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",   # ✅ choose your OpenAI model here
            messages=[
                {"role": "system", "content": "You are a SQL generator assistant."},
                {"role": "user", "content": f"{updated_prompt}\n\n{question}"}
            ],
            temperature=0,
            max_tokens=400
        )

        sql_query = response.choices[0].message.content.strip()

        # cleanup SQL (remove triple backticks etc.)
        lines = sql_query.strip().split("\n")
        if len(lines) >= 2:
            stripped_sql = "\n".join(lines[1:-1])
        else:
            stripped_sql = sql_query

        return stripped_sql

    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return f"Error: API call failed - {e}"
