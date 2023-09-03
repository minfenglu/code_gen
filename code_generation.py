import duckdb
import streamlit as st
import pandas as pd
import math
import numpy as np
import requests

from utils import (
    fetch_start_idx,
    post_process_response,
    record_preference,
    save_comparison,
    DBOperationStatus,
)

st.set_page_config(layout="wide")


PROBLEM_COLUMNS = [
    "id",
    "difficulty",
    "title",
    "description",
    "difficulty",
    "version1",
    "version2",
    "preference",
]
DEFAULT_INSTRUCTION = (
    "Give two different solutions in python to the following"
    " coding question. add ``` to start and end of each solution"
)
OLLAMA_API_ENDPOINT = "http://localhost:11434/api/generate"
VERSIONS = ["version1", "version2"]


def init_database():
    st.session_state.db_con = duckdb.connect("md:dpo")
    st.session_state.problems = st.session_state.db_con.sql(
        f"SELECT {','.join(PROBLEM_COLUMNS)} FROM leetcode_problems"
    ).df()
    st.session_state.problem_count = len(st.session_state.problems.index)
    st.session_state.initial_index = fetch_start_idx(st.session_state.db_con)
    st.session_state.version1 = st.session_state.problems["version1"][
        st.session_state.initial_index
    ]
    st.session_state.version2 = st.session_state.problems["version2"][
        st.session_state.initial_index
    ]
    st.session_state.preference = st.session_state.problems["preference"][
        st.session_state.initial_index
    ]
    if type(st.session_state.version1) is float and math.isnan(
            st.session_state.version1
        ):
            st.session_state.version1 = None
            st.session_state.version2 = None

def reset_solutions():
    st.session_state.version1 = None
    st.session_state.version2 = None


def init_app_status():
    st.session_state.submit_status = None
    st.session_state.app_status = None


if "db_con" not in st.session_state:
    init_database()
    st.session_state.submit_status = None


def call_llama_code():
    print("calling code llama...")
    reset_solutions()
    data = {
        "model": "codellama",
        "prompt": f"{st.session_state.instruction}: {st.session_state.problems['description'][st.session_state.prompt_index]}",
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(OLLAMA_API_ENDPOINT, headers=headers, json=data)
    # update session state
    st.session_state.version1, st.session_state.version2 = post_process_response(
        response.text
    )
    # update dataframe for local copy
    id = st.session_state.problems["id"][st.session_state.prompt_index]
    st.session_state.problems.loc[
        st.session_state.problems["id"] == id, "version1"
    ] = st.session_state.version1
    st.session_state.problems.loc[
        st.session_state.problems["id"] == id, "version2"
    ] = st.session_state.version2

    # display update status
    st.session_state.show_submit_status = True


def on_submit_preference():
    id = st.session_state.problems["id"][st.session_state.prompt_index]
    st.session_state.submit_status, st.session_state.app_status = record_preference(
        st.session_state.db_con,
        id,
        st.session_state.version1,
        st.session_state.version2,
        VERSIONS.index(st.session_state.preference_choice.replace("`", "")),
    )


def on_change_question():
    init_app_status()
    st.session_state.version1 = st.session_state.problems["version1"][
        st.session_state.prompt_index
    ]
    st.session_state.version2 = st.session_state.problems["version2"][
        st.session_state.prompt_index
    ]
    if type(st.session_state.version1) is float and math.isnan(
        st.session_state.version1
    ):
        st.session_state.version1 = None
        st.session_state.version2 = None

    preference = st.session_state.problems["preference"][st.session_state.prompt_index]
    st.session_state.preference = preference if preference else 0


def on_save_comparison():
    id = st.session_state.problems["id"][st.session_state.prompt_index]
    st.session_state.submit_status, st.session_state.app_status = save_comparison(
        st.session_state.db_con,
        id,
        st.session_state.version1,
        st.session_state.version2,
    )


with st.sidebar:
    problem_index = (
        st.session_state.prompt_index if "prompt_index" in st.session_state else st.session_state.initial_index
    )
    st.header(
        f"{st.session_state.problems['id'][problem_index]}. {st.session_state.problems['title'][problem_index]}"
    )
    tag_column, generate_button_column = st.columns(2)
    with tag_column:
        st.markdown(f"tag: `{st.session_state.problems['difficulty'][problem_index]}`")
    with generate_button_column:
        st.button("Generate", on_click=call_llama_code)
    st.markdown(st.session_state.problems["description"][problem_index])
    st.text_area("Instruction", DEFAULT_INSTRUCTION, key="instruction")
    st.number_input(
        f"Prompt Index (max {st.session_state.problem_count-1})",
        min_value=0,
        value=st.session_state.initial_index,
        max_value=st.session_state.problem_count - 1,
        step=1,
        format="%d",
        key="prompt_index",
        on_change=on_change_question,
    )
st.header("Code Comparison")
if st.session_state.version1 and st.session_state.version2:
    version1_code_column, version2_code_column = st.columns(2)
    with version1_code_column:
        st.markdown("`version 1`")
        st.code(st.session_state.version1, line_numbers=True)
    with version2_code_column:
        st.markdown("`version 2`")
        st.code(st.session_state.version2, line_numbers=True)
    st.button("Save", key="save_code_comparison_button", on_click=on_save_comparison)
    st.header("Preference Selection")
    st.radio(
        "Which version is better?",
        [f"`{version}`" for version in VERSIONS],
        key="preference_choice",
    )
    st.button("Submit", key="preference_confirm_button", on_click=on_submit_preference)
else:
    st.write("Node code is generated")
if st.session_state.submit_status:
    st.header("Submit Status")
    if st.session_state.submit_status == DBOperationStatus.SUCCESS:
        st.success(st.session_state.app_status, icon="✅")
    elif st.session_state.submit_status == DBOperationStatus.ERROR:
        st.error(st.session_state.app_status, icon="🚨")
