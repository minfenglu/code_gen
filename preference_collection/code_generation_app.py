import streamlit as st

from preference_selection_panel import (
    call_codellama,
    display_code_pair,
    display_operation_status,
    run_unit_tests_on_update,
)
from duckdb_utils import (
    init_database,
)
from sidebar import (
    display_sidebar,
)


st.set_page_config(layout="wide")


# initialize app session data
if "db_con" not in st.session_state:
    init_database()
    st.session_state.debug_mode = False
    st.session_state.submit_status = None
    st.session_state.unit_test_results = {}
    run_unit_tests_on_update()


# remove hamburger item
hide_st_style = """
            <style>
            #header {visibility: hidden;}
            MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# reduce extra padding
st.markdown(
    """
        <style> 
               .block-container {
                    padding-top: 1rem;
                    padding-bottom: 0rem;
                }
        </style>
        """,
    unsafe_allow_html=True,
)


def main():
    # side bar
    display_sidebar()

    # main panel for preference selection
    if st.session_state.version1 and st.session_state.version2:
        # display preference selection
        header, button = st.columns([4,1])
        with header:
            st.header("Which version is better?")
        with button:
            st.button(
                "Generate Again ↻",
                key="regenerate_code_button",
                on_click=call_codellama,
                type="primary",
            )
        display_code_pair()
    else:
        # display code pair generation
        st.header("Hey Labeler!")
        st.write('Let\'s play "Which version is better?"')
        st.button(
            "Oh yeah! Let's play!",
            key="generate_code_button",
            type="primary",
            on_click=call_codellama,
        )

    display_operation_status()


if __name__ == "__main__":
    main()
