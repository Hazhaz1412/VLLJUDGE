import sys
import os
import subprocess
import time
import psutil

def load_hidden_testcases(problem_id):
    file_path = f'/app/hidden_testcases/hidden_testcases_{problem_id}.txt'
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Hidden test case file for problem ID {problem_id} not found. {file_path}")

    with open(file_path, 'r') as file:
        data = file.read().strip()

    testcases = []
    blocks = data.split('Testcase ')
    for block in blocks[1:]:
        lines = block.splitlines()
        try:
            input_index = lines.index('Input:') + 1
            output_index = lines.index('Output:')
            input_part = '\n'.join(lines[input_index:output_index]).strip()
            output_part = '\n'.join(lines[output_index + 1:]).strip()
            testcases.append((input_part, output_part))
        except ValueError:
            continue
    return testcases

def run_code(language, code_path, input_data, time_limit, memory_limit):
    if language == 'python':
        command = [sys.executable, code_path]
    elif language == 'cpp':
        exec_path = '/app/temp_exec'
        subprocess.run(['g++', '-o', exec_path, code_path], check=True)
        command = [exec_path]
    else:
        return "Unsupported language", False, 0, 0.0, ""

    start_time = time.time() * 1000
    p = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    if input_data:
        p.stdin.write(input_data)
    p.stdin.close()

    child_proc = psutil.Process(p.pid)
    max_mem_used = 0.0

    try:
        while p.poll() is None:
            time.sleep(0.01)
            mem_now = child_proc.memory_info().rss / 1024.0
            if mem_now > max_mem_used:
                max_mem_used = mem_now

            if (time.perf_counter() * 1000 - start_time) > (time_limit * 1000):
                p.kill()
                return "Time Limit Exceeded", False, 0, max_mem_used, ""

            if max_mem_used > float(memory_limit):
                p.kill()
                return f"Memory Limit Exceeded: {max_mem_used:.2f}KB used", False, 0, max_mem_used, ""

        end_time = time.time() * 1000
        execution_time_ms = end_time - start_time

        user_output = p.stdout.read().strip()
        error_output = p.stderr.read().strip()
    except Exception as e:
        p.kill()
        return f"Runtime Error: {str(e)}", False, 0, max_mem_used, ""

    if p.returncode != 0:
        err_info = error_output if error_output else "Unknown error"
        return f"Runtime Error: {err_info}", False, execution_time_ms, max_mem_used, user_output

    user_output_lower = user_output.lower()
    return user_output, user_output_lower, True, execution_time_ms, max_mem_used

def main():
    if len(sys.argv) < 6:
        print("Error: Not enough arguments.")
        print("Usage: python judge.py <language> <code_path> <problem_id> <time_limit> <memory_limit>")
        sys.exit(1)

    language = sys.argv[1]
    code_path = sys.argv[2]
    problem_id = sys.argv[3]
    time_limit = float(sys.argv[4])
    memory_limit = int(sys.argv[5]) * 1024

    try:
        testcases = load_hidden_testcases(problem_id)
    except FileNotFoundError as e:
        print(str(e))
        sys.exit(1)

    results = []
    user_outputs = []
    final_status = "Accepted"

    for i, (input_data, expected_output) in enumerate(testcases):
        mem_start = psutil.Process().memory_info().rss / 1024.0

        user_output, user_output_lower, success, exec_time_ms, mem_used_kb = run_code(
            language, code_path, input_data, time_limit, memory_limit
        )

        mem_end = psutil.Process().memory_info().rss / 1024.0
        mem_used_kb = float(mem_used_kb) if mem_used_kb else 0.0
        mem_now_diff = float(mem_end - mem_start)
        if mem_now_diff > mem_used_kb:
            mem_used_kb = mem_now_diff

        if len(user_output) <= 1000:
            user_outputs.append(f"Testcase {i + 1}: {user_output}")
        else:
            user_outputs.append(f"Testcase {i + 1}: ...")

        if not success:
            if user_output == "Time Limit Exceeded":
                final_status = "Time Limit Exceeded"
            elif "Memory Limit Exceeded" in user_output:
                final_status = "Memory Limit Exceeded"
            elif "Runtime Error" in user_output:
                final_status = "Runtime Error"
            elif "Compiler Error" in user_output:
                final_status = "Compiler Error"
            else:
                final_status = "Wrong Answer"
            break  # Stop checking further test cases
        else:
            if user_output_lower.strip() == str(expected_output).strip().lower():
                results.append(f"Testcase {i + 1}: Passed - Time: {exec_time_ms:.2f}ms, Memory: {mem_used_kb:.2f}KB")
            else:
                results.append(f"Testcase {i + 1}: Failed - Wrong Answer: Expected {expected_output}, Got {user_output}")
                final_status = "Wrong Answer"

    print(f"Final status: {final_status}")
    for r in results:
        print(r)

    print("User Outputs:")
    for uo in user_outputs:
        print(uo)

if __name__ == '__main__':
    main()
