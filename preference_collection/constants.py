# columns for leetcode problems
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

# columns for leetcode unit tests
TEST_COLUMNS = [
    "id",
    "function_name",
    "inputs",
    "outputs",
]

# default prompt
DEFAULT_INSTRUCTION = (
    "Give two different solutions in python to the following"
    " coding question. add ``` to start and end of each solution"
)

# ollama api endpoint for running codellama
OLLAMA_API_ENDPOINT = "http://146.235.195.194:11434/api/generate"

# code versions
VERSIONS = ["version1", "version2"]
