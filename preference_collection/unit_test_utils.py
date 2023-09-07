"""
This module provides utilities for generating and executing Python scripts and unit tests.

Functions:
    - extract_function_name(signature: str) -> str:
        Extracts the function name from a given function signature.
    
    - generate_solution_file(solution_path: str, test_path: str, function_name: str, script: str, inputs: str, outputs: str) -> None:
        Creates a Python script for the provided code snippet and generates a corresponding unit test script.
    
    - execute_script(script_path: str) -> Tuple[str, str]:
        Executes a Python script and captures its standard output and error.
    
    - process_unit_tests(script_path: str) -> List[str]:
        Processes the results of executed unit tests and returns the results as a list.
    
    - run_unit_tests(solution_path: str, test_path: str, function_name: str, script: str, inputs: str, outputs: str) -> List[str]:
        Generates solution and test files, runs the unit tests, and processes the results.

Dependencies:
    - subprocess: For running shell commands.
    - re: For regular expression operations.
"""

import subprocess
import re
from typing import List, Tuple


def extract_function_name(signature: str) -> str:
    """
    Extracts the function name from a given function signature.
    Parameters:
        signature (str): Function signature

    Returns:
        function_name (str): Function name extracted
    """
    signature = signature.replace("\n", "")
    match = re.search(r"def (\w+)\(", signature)
    if match:
        return match.group(1)
    else:
        return None


def generate_solution_file(
    solution_path: str,
    test_path: str,
    function_name: str,
    script: str,
    inputs: str,
    outputs: str,
) -> None:
    """
    Generates a Python script from the given code snippet and
    produces an associated unit test script.

    Parameters:
        solution_path (str): Destination path for the solution file.
        test_path (str): Destination path for the unit test file.
        function_name (str): Name of the function to be tested.
        script (str): Provided code snippet.
        inputs (List[str]): List of inputs for unit tests.
        outputs (List[str]): List of expected outputs for unit tests.

    Returns:
        None
    """
    # save python script to a .py file
    with open(solution_path, "w") as file:
        file.write(script)
    # generate unit test script
    test_cases_str = ""
    for idx, input_output in enumerate(zip(inputs, outputs)):
        input, output = input_output
        input = input[1:-1]
        output = output[1:-1]
        test_cases_str += f"    def test_{function_name}_{idx}(self):\n"
        test_cases_str += (
            f"        self.assertEqual({function_name}({input}), {output})\n"
        )
    test = f"""
import unittest
from {solution_path.split('.')[0]} import {function_name}

class TestSolution(unittest.TestCase):
{test_cases_str}
if __name__ == "__main__":
    unittest.main()
    """
    # save unit test script to .py file
    with open(test_path, "w") as file:
        file.write(test)


def execute_script(script_path: str) -> Tuple[str, str]:
    """
    Executes a Python script and captures its standard output and error.
    Parameters:
        script_path (str): Python script path

    Returns:
        None
    """
    result = subprocess.run(
        ["python", script_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Get the standard output and error from the executed script
    stdout = result.stdout
    stderr = result.stderr
    return stdout, stderr


def process_unit_tests(script_path: str) -> List[str]:
    """
    Processes the results of executed unit tests and returns the results as a list.
    Parameters:
        script_path (str): Python script path

    Returns:
        results (List(str)): List of unit test results
    """
    stdout, stderr = execute_script(script_path)
    # example output: "..FF." where . is pass and F is fail
    output = stdout.splitlines()[0] if stdout else stderr.splitlines()[0]
    results = []
    for result in output:
        results.append(result)
    return results


def run_unit_tests(
    solution_path: str,
    test_path: str,
    function_name: str,
    script: str,
    inputs: List[str],
    outputs: List[str],
) -> List[str]:
    """
    Generates solution and test files, runs the unit tests, and processes the results.
    Parameters:
        solution_path (str): Destination path for the solution file.
        test_path (str): Destination path for the unit test file.
        function_name (str): Name of the function to be tested.
        script (str): Provided code snippet.
        inputs (List[str]): List of inputs for unit tests.
        outputs (List[str]): List of expected outputs for unit tests.

    Returns:
        unit_test_results: (List(str)): List of unit test results
    """
    generate_solution_file(
        solution_path,
        test_path,
        function_name,
        script,
        inputs,
        outputs,
    )
    return process_unit_tests(test_path)
