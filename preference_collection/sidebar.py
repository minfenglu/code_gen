import streamlit as st
from constants import (
    DEFAULT_INSTRUCTION,
)
from preference_selection_panel import on_change_question


# for debugging only
def on_toggle_debug_mode():
    st.session_state.debug_mode = st.session_state.debug_mode_toggle


def display_sidebar():
    with st.sidebar:
        # make sidebar header larger
        _ = st.markdown(
            """
            <style>
                .big-font {
                    font-size:32px !important;
                }
            </style>
            """,
            unsafe_allow_html=True,
        )
        _ = st.markdown(
            """
            <style>
                .block-container.css-ysnqb2.ea3mdgi4 {
                margin-top: -132px;
                }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<b class="big-font">BttrCode.AI</b>',
                    unsafe_allow_html=True)

        problem_index = (
            st.session_state.prompt_index
            if "prompt_index" in st.session_state
            else st.session_state.initial_index
        )
        st.header(
            f"{st.session_state.problems['id'][problem_index]}. {st.session_state.problems['title'][problem_index]}"
        )

        st.markdown(
            f"tag: `{st.session_state.problems['difficulty'][problem_index]}`")
        st.markdown(st.session_state.problems["description"][problem_index])
        st.text_area("Instruction", DEFAULT_INSTRUCTION, key="instruction")
        back, forward, _ = st.columns([1, 1, 4])

        with back:
            st.button("◀️", on_click=on_change_question, args=(-1,))
        with forward:
            st.button("▶️", on_click=on_change_question, args=(1,))
