import streamlit as st

from preference_selection_panel import (
    display_code_pair,
    display_operation_status,
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
    st.session_state.submit_status = None
    st.session_state.unit_test_results = {}


############################################
# Build App UI
############################################

display_sidebar()

st.header("Code Comparison")
if st.session_state.version1 and st.session_state.version2:
    display_code_pair()
else:
    st.write("Node code is generated")

display_operation_status()
