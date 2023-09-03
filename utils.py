from enum import Enum
import json


class DBOperationStatus(Enum):
    SUCCESS = 1
    ERROR = 2


def fix_quote(line):
    line = line.replace('"(""', '"("').replace('"")"', '")"')
    return line


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
        print(output)
        raise e


def fetch_start_idx(connection):
    try:
        return connection.sql(
            f"SELECT MIN(id) AS min_id FROM leetcode_problems WHERE version1 is NULL"
        ).df().loc[0, 'min_id'] - 1
    except:
        return 0


def record_preference(connection, id, version1, version2, preference):
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
        return DBOperationStatus.SUCCESS, "Preference has been recorded sucessfully!"
    except Exception as e:
        return DBOperationStatus.ERROR, e


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
