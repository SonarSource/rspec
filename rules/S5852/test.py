import re
import time

pattern = re.compile("^([^,],){14}P")
for max in range(2, 99):
    print(f"=== {max} fields ===")

    input = "1"
    for i in range(2, max):
        input += f",{i}"

    start = time.perf_counter()
    match = pattern.match(input)
    end = time.perf_counter()

    print(f"Execution took {(end - start)}s")
    if match:
        print(f"Found match: {match.groups[0]}")
    else:
        print("No match")

    if end - start > 1:
        break
