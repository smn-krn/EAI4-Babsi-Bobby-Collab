#!/usr/bin/env python3
import time

# Our parameter for longer / shorter runtime
N = 10_000_000

x = 0.0
start = time.perf_counter_ns()

for i in range(N):
    x = x * 1.0000001 + i * 0.000001

end = time.perf_counter_ns()
duration_ms = (end - start)/1000000

print(f"Duration: {duration_ms:.6f} ms")

