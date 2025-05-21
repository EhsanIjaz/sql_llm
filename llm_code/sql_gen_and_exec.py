import torch
import sqlparse
import streamlit as st
from typing import Optional
import duckdb
import pandas as pd

from aisight_llm.utils.decorators import time_checker
from transformers import AutoTokenizer, AutoModelForCausalLM
from aisight_llm.common_utils.logging import logger

from .settings import MODEL_NAME, MODEL_CHACHED_DIR

logger.info(f"Initialized Model : {MODEL_NAME} ")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
logger.info(f"Initialized Device: {DEVICE}")


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
def generate_sql(
    question: str, latest_month: int, latest_year: int, prompt: str
) -> str:

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
