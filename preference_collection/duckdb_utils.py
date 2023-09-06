import duckdb
import json
import math
import re
import streamlit as st

from constants import (
    PROBLEM_COLUMNS,
    TEST_COLUMNS,
)
from enum import Enum


# enum to represent databse operation status
class DBOperationStatus(Enum):
    SUCCESS = 1
    ERROR = 2


# edge case handling
def fix_quote(line):
    line = line.replace('"(""', '"("').replace('"")"', '")"')
    return line


# parse the python code from API output
def post_process_response(response):
    lines = [obj for obj in response.splitlines()]
    res = []
    prev_line = None
    output = ""
    for line in lines:
        if line.endswith('"response":"'):
            prev_line = line
        else:
            if prev_line:
                line = prev_line + line
                prev_line = None
                output += "\n"

            if line:
                json_data = json.loads(fix_quote(line))
                if not json_data["done"]:
                    output += json_data["response"]
            else:
                output += line
    outputs = output.split("```")
    try:
        return outputs[1], outputs[3]
    except Exception as e:
        print(e, output)
        return None, None


# save the code pair and human preference to databse
def record_code_and_preference(connection, id, version1, version2, preference):
    try:
        connection.sql(
            f"""
            UPDATE leetcode_problems 
            SET version1='{version1}', 
                version2='{version2}', 
                preference={preference} 
            where id={id}
            """
        )
        return (
            DBOperationStatus.SUCCESS,
            "Code and preference has been recorded sucessfully!",
        )
    except Exception as e:
        return DBOperationStatus.ERROR, e


# only save human prefrence to database
# applicable when lableler needs to update the answer
def record_preference_only(connection, id, preference):
    try:
        connection.sql(
            f"""
            UPDATE leetcode_problems 
            SET preference={preference} 
            where id={id}
            """
        )
        return DBOperationStatus.SUCCESS, "Preference has been recorded sucessfully!"
    except Exception as e:
        return DBOperationStatus.ERROR, e


# only save code pair to database
# applicable when lableler only wants to save generated code
def save_comparison(connection, id, version1, version2):
    try:
        connection.sql(
            f"""
            UPDATE leetcode_problems 
            SET version1='{version1}', 
                version2='{version2}'
            where id={id}
            """
        )
        return DBOperationStatus.SUCCESS, "Comparison has been save sucessfully!"
    except Exception as e:
        return DBOperationStatus.ERROR, e


# extract function name from function signature
def extract_function_name(signature: str) -> str:
    signature = signature.replace("\n", "")
    match = re.search(r"def (\w+)\(", signature)
    if match:
        return match.group(1)
    else:
        return None

# update function name when code is regenerated 
def update_function_name(connection, id, function_name):
    try:
        connection.sql(
            f"""
            UPDATE leetcode_tests 
            SET function_name='{function_name}', 
            where id={id}
            """
        )
        return DBOperationStatus.SUCCESS, "leetcode test has been updated sucessfully!"
    except Exception as e:
        return DBOperationStatus.ERROR, e


# fetch data from duckdb and initialize the streamlit app
# populate app data that comes from database
def init_database():
    st.session_state.db_con = duckdb.connect("md:dpo")
    # construct leetcode problems
    st.session_state.problems = st.session_state.db_con.sql(
        f"SELECT {','.join(PROBLEM_COLUMNS)} FROM leetcode_problems WHERE version1 IS NOT NULL"
    ).df()
    # construct leetcode unit tests
    st.session_state.tests = st.session_state.db_con.sql(
        f"SELECT {','.join(TEST_COLUMNS)} FROM leetcode_tests WHERE inputs IS NOT NULL"
    ).df()
    # initialize the first leetcode question to display
    st.session_state.problem_count = len(st.session_state.problems.index)
    st.session_state.initial_index = 0
    st.session_state.prompt_index = 0
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
