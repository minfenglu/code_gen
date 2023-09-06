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


# for debugging only
def on_toggle_debug_mode():
    st.session_state.debug_mode = st.session_state.debug_mode_toggle


def display_sidebar():
    with st.sidebar:
        # make sidebar header larger
        st.markdown(
            """
        <style>
        .big-font {
            font-size:32px !important;
        }
        </style>
        """,
            unsafe_allow_html=True,
        )

        st.markdown('<b class="big-font">Better Code AI</b>', unsafe_allow_html=True)

        problem_index = (
            st.session_state.prompt_index
            if "prompt_index" in st.session_state
            else st.session_state.initial_index
        )
        st.header(
            f"{st.session_state.problems['id'][problem_index]}. {st.session_state.problems['title'][problem_index]}"
        )
        st.markdown(f"tag: `{st.session_state.problems['difficulty'][problem_index]}`")
        st.markdown(st.session_state.problems["description"][problem_index])
        st.text_area("Instruction", DEFAULT_INSTRUCTION, key="instruction")
        st.toggle(
            "Debug",
            key="debug_mode_toggle",
            value=False,
            on_change=on_toggle_debug_mode,
        )
