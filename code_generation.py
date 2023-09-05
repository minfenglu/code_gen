import duckdb
import streamlit as st
import pandas as pd
import math
import numpy as np
import requests

from duckdb_utils import (
    post_process_response,
    record_code_and_preference,
    record_preference_only,
    save_comparison,
    DBOperationStatus,
)

from unit_test_utils import run_unit_tests, display_test_results

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
TEST_COLUMNS = [
    "id",
    "function_name",
    "inputs",
    "outputs",
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
    st.session_state.tests = st.session_state.db_con.sql(
        f"SELECT {','.join(TEST_COLUMNS)} FROM leetcode_tests WHERE inputs IS NOT NULL"
    ).df()
    st.session_state.problem_count = len(st.session_state.problems.index)
    st.session_state.initial_index = 0
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
    st.session_state.unit_test_results = {}


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


def on_submit_preference_only():
    id = st.session_state.problems["id"][st.session_state.prompt_index]
    (
        st.session_state.submit_status,
        st.session_state.app_status,
    ) = record_preference_only(
        st.session_state.db_con,
        id,
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


def contains_test():
    id = st.session_state.problems["id"][st.session_state.prompt_index]
    test = st.session_state.tests[st.session_state.tests["id"] == id]
    return test is not None


def on_click_run_unit_tests():
    id = st.session_state.problems["id"][st.session_state.prompt_index]
    test = st.session_state.tests[st.session_state.tests["id"] == id]
    print(test)
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
        st.markdown(f"tag: `{st.session_state.problems['difficulty'][problem_index]}`")
    with generate_button_column:
        st.button("Generate", on_click=call_llama_code)
    st.markdown(st.session_state.problems["description"][problem_index])
    st.text_area("Instruction", DEFAULT_INSTRUCTION, key="instruction")

st.header("Code Comparison")
if st.session_state.version1 and st.session_state.version2:
    st.button(
        "Save Code Pair", key="save_code_comparison_button", on_click=on_save_comparison
    )
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
    )
    code_and_preference_button, preference_only_button = st.columns(2)
    with code_and_preference_button:
        st.button(
            "Submit (Code + Preference)",
            key="code_and_preference_confirm_button",
            on_click=on_submit_code_and_preference,
        )
    with preference_only_button:
        st.button(
            "Submit (Preference Only)",
            key="preference_only_confirm_button",
            on_click=on_submit_preference_only,
        )


else:
    st.write("Node code is generated")
if st.session_state.submit_status:
    st.header("Submit Status")
    if st.session_state.submit_status == DBOperationStatus.SUCCESS:
        st.success(st.session_state.app_status, icon="✅")
    elif st.session_state.submit_status == DBOperationStatus.ERROR:
        st.error(st.session_state.app_status, icon="🚨")
