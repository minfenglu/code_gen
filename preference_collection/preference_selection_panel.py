import numpy as np
import streamlit as st
from constants import (
    VERSIONS,
)
from duckdb_utils import (
    record_code_and_preference,
    record_preference_only,
    save_comparison,
    DBOperationStatus,
)
from unit_test_utils import (
    run_unit_tests,
    display_test_results,
)


# store code pair and human preference in the databse
def on_submit_code_and_preference():
    id = st.session_state.problems["id"][st.session_state.prompt_index]
    (
        st.session_state.submit_status,
        st.session_state.app_status,
    ) = record_code_and_preference(
        st.session_state.db_con,
        id,
        st.session_state.version1,
        st.session_state.version2,
        VERSIONS.index(st.session_state.preference_choice.replace("`", "")),
    )


# store human preference in the databse
def on_submit_preference_only():
    id = st.session_state.problems["id"][st.session_state.prompt_index]
    selection = VERSIONS.index(st.session_state.preference_choice.replace("`", ""))
    # update local copy 
    st.session_state.problems.loc[
        st.session_state.problems["id"] == id, "preference"
    ] = selection
    (
        st.session_state.submit_status,
        st.session_state.app_status,
    ) = record_preference_only(
        st.session_state.db_con,
        id,
        selection,
    )


# store code pair in the databse
def on_save_comparison():
    id = st.session_state.problems["id"][st.session_state.prompt_index]
    st.session_state.submit_status, st.session_state.app_status = save_comparison(
        st.session_state.db_con,
        id,
        st.session_state.version1,
        st.session_state.version2,
    )


# check if unit tests are available for current problem
def contains_test():
    id = st.session_state.problems["id"][st.session_state.prompt_index]
    test = st.session_state.tests[st.session_state.tests["id"] == id]
    return not test.empty


# fetch human preference if available
def get_preference():
    preference = st.session_state.problems["preference"][st.session_state.prompt_index]
    if np.isnan(preference):
        return None
    return preference


# run available unit tests
def on_click_run_unit_tests():
    id = st.session_state.problems["id"][st.session_state.prompt_index]
    test = st.session_state.tests[st.session_state.tests["id"] == id]
    function_name = test["function_name"].iloc[0]
    inputs = test["inputs"].iloc[0]
    outputs = test["outputs"].iloc[0]
    version1, version2 = st.session_state.version1, st.session_state.version2
    results = []
    for i in [1, 2]:
        unit_test_results = run_unit_tests(
            f"solution{i}.py",
            f"test{i}.py",
            function_name,
            version1 if i == 1 else version2,
            inputs,
            outputs,
        )
        print("unit_test_results", unit_test_results)
        results.append(unit_test_results)

    st.session_state.unit_test_results[id] = results


# display alert/confirmation for database operation
def display_operation_status():
    if st.session_state.submit_status:
        st.header("Submit Status")
        if st.session_state.submit_status == DBOperationStatus.SUCCESS:
            st.success(st.session_state.app_status, icon="✅")
        elif st.session_state.submit_status == DBOperationStatus.ERROR:
            st.error(st.session_state.app_status, icon="🚨")


# display two versions of python code
def display_code_pair():
    preference = get_preference()
    version1_code_column, version2_code_column = st.columns(2)
    with version1_code_column:
        st.markdown("`version 1`")
        st.code(st.session_state.version1, line_numbers=True)
    with version2_code_column:
        st.markdown("`version 2`")
        st.code(st.session_state.version2, line_numbers=True)
    if contains_test():
        st.button("Run Unit Tests", on_click=on_click_run_unit_tests)
        id = st.session_state.problems["id"][st.session_state.prompt_index]
        if id in st.session_state.unit_test_results:
            test1_column, test2_column = st.columns(2)
            with test1_column:
                st.markdown(
                    display_test_results(
                        st.session_state.unit_test_results[id][0], 3, "version1"
                    )
                )
            with test2_column:
                st.markdown(
                    display_test_results(
                        st.session_state.unit_test_results[id][1], 3, "version2"
                    )
                )
    st.header("Preference Selection")
    st.radio(
        "Which version is better?",
        [f"`{version}`" for version in VERSIONS],
        key="preference_choice",
        index=int(preference) if preference else 0
    )
    code_only_button, code_and_preference_button, preference_only_button, _ = st.columns(4)
    with code_only_button:
        st.button(
            f"Update (Code Only)", key="save_code_comparison_button", on_click=on_save_comparison
        )
    with code_and_preference_button:
        st.button(
            f"{'Submit' if not preference else 'Update'} (Code + Preference)",
            key="code_and_preference_confirm_button",
            on_click=on_submit_code_and_preference,
        )
    with preference_only_button:
        st.button(
            f"{'Submit' if not preference else 'Update'} (Preference Only)",
            key="preference_only_confirm_button",
            on_click=on_submit_preference_only,
        )
