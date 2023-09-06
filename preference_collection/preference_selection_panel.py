import math
import numpy as np
import streamlit as st
import re
import requests
import time
from constants import (
    VERSIONS,
    DEFAULT_INSTRUCTION,
    OLLAMA_API_ENDPOINT,
)
from duckdb_utils import (
    extract_function_name,
    record_preference_only,
    post_process_response,
    save_comparison,
    DBOperationStatus,
)
from unit_test_utils import (
    run_unit_tests,
)


# store human preference in the databse
def on_submit_preference_only(version):
    version -= 1
    id = st.session_state.problems["id"][st.session_state.prompt_index]
    # update local copy
    st.session_state.problems.loc[
        st.session_state.problems["id"] == id, "preference"
    ] = version
    (
        st.session_state.submit_status,
        st.session_state.app_status,
    ) = record_preference_only(
        st.session_state.db_con,
        id,
        version,
    )
    time.sleep(0.5)
    on_change_question(1)


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
def run_unit_tests_on_update():
    if contains_test():
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


def align_code_versions(version1, version2):
    n1 = len(version1.split("\n"))
    n2 = len(version2.split("\n"))
    if n1 < n2:
        version1 += "".join(["\n"] * (n2 - n1 - 1))
        version1 += "# added extra padding"
    elif n2 < n1:
        version2 += "".join(["\n"] * (n1 - n2 - 1))
        version2 += "# added extra padding"
    return version1, version2


def render_test_status(status):
    if status == "F":
        return "❌"
    elif status == ".":
        return "✅"
    else:
        return "❗"


def render_selection(preference, code_version):
    if preference == 1.0 * (code_version - 1):
        return "✅"
    return " ```  ```"


def version_selection_column(code_version, python_code):
    id = st.session_state.problems["id"][st.session_state.prompt_index]
    preference = st.session_state.problems["preference"][st.session_state.prompt_index]

    st.button(
        f"``` ``` ```Version {code_version}```{render_selection(preference, code_version)}",
        key=f"version{code_version}_selection_button",
        on_click=on_submit_preference_only,
        args=(code_version,),
    )

    st.code(python_code, line_numbers=True)
    if id in st.session_state.unit_test_results:
        results = st.session_state.unit_test_results[id][code_version - 1]
        text, test0, test1, test2, _ = st.columns([2.5, 1, 1, 1, 5])
        with text:
            st.text("test cases:")
        if len(results) > 0:
            with test0:
                st.text(render_test_status(results[0]))
        if len(results) > 1:
            with test1:
                st.text(render_test_status(results[1]))
        if len(results) > 2:
            with test2:
                st.text(render_test_status(results[2]))


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
    new_function_name = extract_function_name(st.session_state.version1)
    st.session_state.tests.loc[
        st.session_state.problems["id"] == id, "function_name"
    ] = new_function_name
    # display update status
    st.session_state.show_submit_status = True
    run_unit_tests_on_update()


# reset app status for database operation confirmation
def init_app_status():
    st.session_state.submit_status = None
    st.session_state.app_status = None


# change the question to display
def on_change_question(delta):
    init_app_status()
    st.session_state.prompt_index += delta
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
    run_unit_tests_on_update()


# display two versions of python code
def display_code_pair():
    preference = get_preference()
    version1_code_column, version2_code_column = st.columns(2)
    version1, version2 = align_code_versions(
        st.session_state.version1, st.session_state.version2
    )
    with version1_code_column:
        version_selection_column(1, version1)
    with version2_code_column:
        version_selection_column(2, version2)
    _, center_regenerate_button, _ = st.columns(3)
    with center_regenerate_button:
        st.button(
            "Regenerate Code 😔", key="regenerate_code_button", on_click=call_codellama
        )
    if st.session_state.debug_mode:
        back, forward, _ = st.columns([1, 1, 10])
        with back:
            st.button("Prev", on_click=on_change_question, args=(-1,))
        with forward:
            st.button("Next", on_click=on_change_question, args=(1,))
