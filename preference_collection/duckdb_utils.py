"""
This module provides utilities for handling and processing data related to LeetCode problems and their solutions. 
It includes functions for parsing Python code from API outputs, saving code pairs and human preferences to a database, 
and initializing the Streamlit app with data fetched from the database.

Functions:
    - fix_quote(line: str) -> str: Handles edge cases in quotes.
    - post_process_response(response: str) -> Tuple[str, str]: Parses Python code from API output.
    - record_code_and_preference(connection, id: int, version1: str, version2: str, preference: int) -> Tuple[DBOperationStatus, str]: Saves code pair and human preference to the database.
    - record_preference_only(connection, id: int, preference: int) -> Tuple[DBOperationStatus, str]: Saves only the human preference to the database.
    - save_comparison(connection, id: int, version1: str, version2: str) -> Tuple[DBOperationStatus, str]: Saves only the code pair to the database.
    - extract_function_name(signature: str) -> str: Extracts the function name from a function signature.
    - update_function_name(connection, id: int, function_name: str) -> Tuple[DBOperationStatus, str]: Updates the function name in the database.
    - init_database() -> None: Initializes the Streamlit app with data from the database.

Dependencies:
    - duckdb: For database operations.
    - json: For JSON data parsing.
    - math: For mathematical operations.
    - re: For regular expression operations.
    - streamlit as st: For web application framework.
    - constants: For predefined constants.
    - enum: For creating enumerations.

Classes:
    - DBOperationStatus(Enum): Represents the status of database operations.
"""

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
from typing import List, Tuple


# enum to represent databse operation status
class DBOperationStatus(Enum):
    SUCCESS = 1
    ERROR = 2


# edge case handling
def fix_quote(line: str) -> str:
    """
    Handles edge cases in quotes within a given line.

    Parameters:
        line (str): The input line containing quotes.

    Returns:
        str: The modified line with corrected quotes.
    """
    line = line.replace('"(""', '"("').replace('"")"', '")"')
    return line


# parse the python code from API output
def post_process_response(response: str) -> Tuple[str, str]:
    """
    Parses Python code from the given API output.

    Parameters:
        response (str): The API output containing code information.

    Returns:
        Tuple[str, str]: The parsed Python code and its associated output.
    """
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


def record_code_and_preference(
    connection, id: str, version1: str, version2: str, preference: int
) -> Tuple[DBOperationStatus, str]:
    """
    Saves a code pair and human preference to the database.

    Parameters:
        connection: The database connection.
        id (int): The ID of the LeetCode problem.
        version1 (str): The first version of the code.
        version2 (str): The second version of the code.
        preference (int): The human preference between the two code versions.

    Returns:
        Tuple[DBOperationStatus, str]: The status of the database operation and a message.
    """
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


def record_preference_only(connection, id: int, preference: int):
    """
    Saves only the human preference to the database.

    Parameters:
        connection: The database connection.
        id (int): The ID of the LeetCode problem.
        preference (int): The human preference between the two code versions.

    Returns:
        Tuple[DBOperationStatus, str]: The status of the database operation and a message.
    """
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


def save_comparison(
    connection, id: int, version1: str, version2: str
) -> Tuple[DBOperationStatus, str]:
    """
    Saves only the code pair to the database.

    Parameters:
        connection: The database connection.
        id (int): The ID of the LeetCode problem.
        version1 (str): The first version of the code.
        version2 (str): The second version of the code.

    Returns:
        Tuple[DBOperationStatus, str]: The status of the database operation and a message.
    """
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
    """
    Extracts the function name from a given function signature.

    Parameters:
        signature (str): The function signature.

    Returns:
        str: The extracted function name or None if not found.
    """
    signature = signature.replace("\n", "")
    match = re.search(r"def (\w+)\(", signature)
    if match:
        return match.group(1)
    else:
        return None


# update function name when code is regenerated
def update_function_name(connection, id, function_name):
    """
    Updates the function name in the database when the code is regenerated.

    Parameters:
        connection: The database connection.
        id (int): The ID of the LeetCode problem.
        function_name (str): The new function name.

    Returns:
        Tuple[DBOperationStatus, str]: The status of the database operation and a message.
    """
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


def init_database():
    """
    Initializes the Streamlit app with data fetched from the database.

    Parameters:
        None

    Returns:
        None
    """
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
