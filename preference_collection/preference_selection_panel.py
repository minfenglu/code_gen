import math
import numpy as np
import requests
import streamlit as st
import time
from constants import (
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
def on_submit_preference_only(version: int):
    version -= 1
    id = st.session_state.problems["id"][st.session_state.prompt_index]
    # update local copy
    st.session_state.problems.loc[
        st.session_state.problems["id"] == id, "preference"
    ] = version
    # update database
    (
        st.session_state.submit_status,
        st.session_state.app_status,
    ) = record_preference_only(
        st.session_state.db_con,
        id,
        version,
    )
    time.sleep(0.5)
    # move on to the next question after preference submitssion
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
def _contains_test():
    id = st.session_state.problems["id"][st.session_state.prompt_index]
    test = st.session_state.tests[st.session_state.tests["id"] == id]
    return not test.empty


# run available unit tests
def run_unit_tests_on_update():
    if _contains_test():
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


# add extra padding (front-end only)
# to make sure two code blocks have the same height
def _align_code_versions(version1: str, version2: str):
    n1 = len(version1.split("\n"))
    n2 = len(version2.split("\n"))
    if n1 < n2:
        version1 += "".join(["\n"] * (n2 - n1 - 1))
        version1 += "# added extra padding (for UI only)"
    elif n2 < n1:
        version2 += "".join(["\n"] * (n1 - n2 - 1))
        version2 += "# added extra padding (for UI only)"
    return version1, version2


def _render_test_status(status):
    if status == "F":
        return "❌"
    elif status == ".":
        return "✅"
    else:
        return "❗"


def _render_selection(preference, code_version):
    if preference == 1.0 * (code_version - 1):
        return "✅"
    return ""


def _render_code_header(version, icon=""):
    _ = st.markdown(
        """
        <style>
        .code-header {
            font-size:20px;
            padding: 0px 0px 0px 12px ;
            margin-top: -10px
        }
        #check-img {
            margin-top: -6px
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    icon_image = (
        ' <img id="check-img" src="https://raw.githubusercontent.com/minfenglu/code_gen/master/preference_collection/img/check.png" width=24 alt="✅" />'
        if icon
        else ""
    )
    return st.markdown(
        f'<b class="code-header">{version} {icon_image}</b>',
        unsafe_allow_html=True,
    )


def _render_test_header(text, class_name, margin_top=-18):
    _ = st.markdown(
        f"""
        <style>
        .{class_name} {{
            font-size:12;
            padding: 0px 0px 0px 12px ;
            margin-top: {margin_top}px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    return st.markdown(f'<div class="{class_name}">{text}</>', unsafe_allow_html=True)


# display header, code and unit test results
def version_selection_column(code_version, python_code):
    id = st.session_state.problems["id"][st.session_state.prompt_index]
    preference = st.session_state.problems["preference"][st.session_state.prompt_index]
    header, _, slection_button = st.columns([5, 6, 4])
    # display header
    # (version name, whether selected as preferred, selection button)
    with header:
        _render_code_header(
            f"Version {code_version}", _render_selection(preference, code_version)
        )
    with slection_button:
        st.button(
            f"This One",
            key=f"version{code_version}_{id}_selection_button",
            on_click=on_submit_preference_only,
            args=(code_version,),
        )
    # display
    st.code(python_code, line_numbers=True)

    # display unit test results if available
    if id in st.session_state.unit_test_results:
        results = st.session_state.unit_test_results[id][code_version - 1]
        text, test0, test1, test2, _ = st.columns([0.5, 0.25, 0.25, 0.25, 5])
        with st.container():
            with text:
                _render_test_header("Tests:", "test-header", -20)
            if len(results) > 0:
                with test0:
                    _render_test_header(_render_test_status(results[0]), "test-result")
            if len(results) > 1:
                with test1:
                    _render_test_header(_render_test_status(results[1]), "test-result")
            if len(results) > 2:
                with test2:
                    _render_test_header(_render_test_status(results[2]), "test-result")


# reset solutions
def reset_solutions():
    st.session_state.version1 = None
    st.session_state.version2 = None


# call codellama to generate code pairs
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
    # update unit test funtion_name
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
# delta = 1 : move to next question
# delta = -1: move to prev question
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
    # highlight the code versoin when hover
    _ = st.markdown(
        """
            <style>
                div[data-testid="column"].css-keje6w.e1f1d6gn1 {
                    background-color: #343440;
                    border-radius: 12px; 
                    padding: 8px 0px 16px 0px;
                    transition: filter 0.3s;
                }
                div[data-testid="column"].css-keje6w.e1f1d6gn1:hover {
                    filter: brightness(200%) saturate(100%) hue-rotate(20deg);
                  
                }
                div[data-testid="column"].css-keje6w.e1f1d6gn1:hover .code-header #check-img{
                    filter: brightness(50%);
                }
                 
                }
            </style>
        """,
        unsafe_allow_html=True,
    )
    # custom style for This One button
    _ = st.markdown(
        """
            <style>
                .stButton {
                    margin-top: 8px;
                    margin-left: 8px;
                    padding: 0px;
                }
                button[kind="primary"].css-nbt3vv.ef3psqc12 {
                    margin-top: 12px;
                    margin-left: 45px;
                }
            </style>
        """,
        unsafe_allow_html=True,
    )
    version1_code_column, version2_code_column = st.columns(2)
    version1, version2 = _align_code_versions(
        st.session_state.version1, st.session_state.version2
    )
    with version1_code_column:
        version_selection_column(1, version1)
    with version2_code_column:
        version_selection_column(2, version2)
