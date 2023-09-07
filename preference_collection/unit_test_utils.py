import subprocess
import re


# extract function name from the function signature
def extract_function_name(signature: str) -> str:
    signature = signature.replace("\n", "")
    match = re.search(r"def (\w+)\(", signature)
    if match:
        return match.group(1)
    else:
        return None


# create python script for the provided code snippet
# create unit test script for the corresponding code
def generate_solution_file(
    solution_path: str,
    test_path: str,
    function_name: str,
    script: str,
    inputs: str,
    outputs: str,
):
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


def execute_script(script_path):
    # Run a python script and capture its output
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


def process_unit_tests(script_path):
    stdout, stderr = execute_script(script_path)
    output = stdout.splitlines()[0] if stdout else stderr.splitlines()[0]
    results = []
    for result in output:
        results.append(result)
    return results


def run_unit_tests(solution_path, test_path, function_name, script, inputs, outputs):
    generate_solution_file(
        solution_path,
        test_path,
        function_name,
        script,
        inputs,
        outputs,
    )
    return process_unit_tests(test_path)
