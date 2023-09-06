import streamlit as st

from preference_selection_panel import (
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

############################################
# Initialize App Session Data
############################################

if "db_con" not in st.session_state:
    init_database()
    st.session_state.debug_mode = False
    st.session_state.submit_status = None
    st.session_state.unit_test_results = {}
    run_unit_tests_on_update()


############################################
# Build App UI
############################################

# remove hamburger item
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

display_sidebar()

st.header("Which version is better?")
if st.session_state.version1 and st.session_state.version2:
    display_code_pair()
else:
    st.write("Node code is generated")

display_operation_status()
