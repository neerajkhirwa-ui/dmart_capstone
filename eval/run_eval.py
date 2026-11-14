"""Evaluation runner script for DMart Conversational Analytics Agent.
Runs all test cases from eval/golden_set.csv through the agent handle pipeline,
validates expected vs actual statuses and contents, and outputs eval_results.csv.
"""

from datetime import datetime
import csv
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Set environment paths for eval run
os.environ["AGENT_LOG_PATH"] = "eval/eval_runs.jsonl"
os.environ["WEATHER_MODE"] = "stub"

from agent.run_agent import handle


def parse_expected_contains(exp_str: str) -> list:
  if not exp_str:
    return []
  return [x.strip() for x in exp_str.split("|")]


def check_contains(answer_text: str, expected_list: list) -> bool:
  for item in expected_list:
    # Check if item exists in answer_text (case-insensitive or exact)
    # Also support numeric float matching within tolerance 0.01 if item is numeric
    found = False
    if item.lower() in answer_text.lower():
      found = True
    else:
      # Check if item is a numeric value and check within tolerance
      try:
        item_float = float(item)
        nums_in_ans = re.findall(r"\b\d+(?:\.\d+)?\b", answer_text)
        for n in nums_in_ans:
          if abs(float(n) - item_float) <= 0.01:
            found = True
            break
      except ValueError:
        pass

    if not found:
      return False
  return True


def run_evaluation():
  golden_path = "eval/golden_set.csv"
  fallback_golden_path = "eval/golden_set.csv.txt"
  results_path = "eval/eval_results.csv"
  eval_log_path = "eval/eval_runs.jsonl"

  # Empty eval run log
  os.makedirs("eval", exist_ok=True)
  open(eval_log_path, "w", encoding="utf-8").close()

  if not os.path.exists(golden_path):
    if os.path.exists(fallback_golden_path):
      golden_path = fallback_golden_path
    else:
      print(f"Error: {golden_path} not found.")
      return

  results = []
  passed_count = 0
  total_count = 0

  with open(golden_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
      total_count += 1
      case_id = row["case_id"]
      category = row["category"]
      session_id = row["session_id"]
      question = row["question"]
      sim_failures = int(row["simulate_failures"])
      exp_status = row["expected_status"]
      exp_intent = row["expected_intent"]
      exp_contains_str = row["expected_contains"]

      # Set simulate failures environment variable
      os.environ["SIMULATE_DB_FAILURES"] = str(sim_failures)

      # Handle question through agent pipeline
      res = handle(question, session_id=session_id, user_id="eval_user")

      actual_status = res["status"]
      actual_intent = res["intent"]
      answer_text = res["answer_text"]
      latency_ms = res["latency_ms"]
      tokens_est = res["tokens_est"]
      tool_calls = res["tool_calls"]
      ungrounded_numbers = res["ungrounded_numbers"]
      budget_exceeded = res["budget_exceeded"]

      intent_match = actual_intent == exp_intent
      status_match = actual_status == exp_status

      exp_list = parse_expected_contains(exp_contains_str)
      contains_match = check_contains(answer_text, exp_list)

      passed = status_match and intent_match and contains_match
      if passed:
        passed_count += 1

      results.append({
          "case_id": case_id,
          "category": category,
          "expected_status": exp_status,
          "actual_status": actual_status,
          "intent_match": str(intent_match),
          "contains_match": str(contains_match),
          "latency_ms": latency_ms,
          "tokens_est": tokens_est,
          "tool_calls": tool_calls,
          "ungrounded_numbers": ungrounded_numbers,
          "budget_exceeded": str(budget_exceeded),
          "passed": str(passed),
      })

  # Write results CSV
  fieldnames = [
      "case_id",
      "category",
      "expected_status",
      "actual_status",
      "intent_match",
      "contains_match",
      "latency_ms",
      "tokens_est",
      "tool_calls",
      "ungrounded_numbers",
      "budget_exceeded",
      "passed",
  ]
  with open(results_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)

  print(
      f"Evaluation completed: {passed_count}/{total_count} cases passed."
      f" Results written to {results_path}."
  )


if __name__ == "__main__":
  run_evaluation()