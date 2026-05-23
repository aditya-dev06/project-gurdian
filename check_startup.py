import time
import sys
import os

# Ensure UTF-8 output encoding for standard streams
if sys.stdout is not None and getattr(sys.stdout, 'encoding', None) != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import guardian

print("--- STARTING PERFORMANCE DIAGNOSTIC BENCHMARK ---")

# 1. Habit Tracker Load
start = time.perf_counter()
habits_data = guardian.load_data()
elapsed_load_habits = (time.perf_counter() - start) * 1000
print(f"Habit Tracker Load Data: {elapsed_load_habits:.2f} ms")

# 2. Habit Tracker Save
start = time.perf_counter()
guardian.save_data(habits_data)
elapsed_save_habits = (time.perf_counter() - start) * 1000
print(f"Habit Tracker Save Data (with 14-day window filtering & batch transaction): {elapsed_save_habits:.2f} ms")

# 3. Japanese Learning Load
start = time.perf_counter()
kanji_data = guardian.load_kanji_data()
elapsed_load_kanji = (time.perf_counter() - start) * 1000
print(f"Japanese Learning Load Data: {elapsed_load_kanji:.2f} ms")

# 4. Japanese Learning Save
start = time.perf_counter()
guardian.save_kanji_data(kanji_data)
elapsed_save_kanji = (time.perf_counter() - start) * 1000
print(f"Japanese Learning Save Data (batch transaction): {elapsed_save_kanji:.2f} ms")

print("\n--- PERFORMANCE DIAGNOSTIC COMPLETE ---")
