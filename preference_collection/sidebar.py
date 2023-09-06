import streamlit as st
import math
import requests
from constants import (
    DEFAULT_INSTRUCTION,
    OLLAMA_API_ENDPOINT,
)
from duckdb_utils import (
    post_process_response,
)


# reset app status for database operation confirmation
def init_app_status():
    st.session_state.submit_status = None
    st.session_state.app_status = None


# change the question to display
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


# reset solutions
def reset_solutions():
    st.session_state.version1 = None
    st.session_state.version2 = None


# call codellama
def call_codellama():
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


def display_sidebar():
    with st.sidebar:
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
        problem_index = (
            st.session_state.prompt_index
            if "prompt_index" in st.session_state
            else st.session_state.initial_index
        )
        st.header(
            f"{st.session_state.problems['id'][problem_index]}. {st.session_state.problems['title'][problem_index]}"
        )
        tag_column, generate_button_column = st.columns(2)
        with tag_column:
            st.markdown(
                f"tag: `{st.session_state.problems['difficulty'][problem_index]}`"
            )
        with generate_button_column:
            st.button("Generate", on_click=call_codellama)
        st.markdown(st.session_state.problems["description"][problem_index])
        st.text_area("Instruction", DEFAULT_INSTRUCTION, key="instruction")
