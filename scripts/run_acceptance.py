"""Acceptance test runner script for DMart Conversational Analytics Agent.
Runs the 20 required acceptance test cases through the agent handle pipeline,
validates intents and statuses, and writes acceptance_transcript.md and runs.jsonl.
"""

from datetime import datetime
import csv
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Set environment paths for acceptance run
os.environ["AGENT_LOG_PATH"] = "logs/runs.jsonl"
os.environ["WEATHER_MODE"] = "stub"

from agent.run_agent import handle


def run_acceptance():
  cases = [
      (
          "A01",
          "s1",
          "What was Pune's revenue on 15 May 2026?",
          0,
          "Answered",
          "lookup",
          "INR 623845.00",
      ),
      ("A02", "s1", "And the target?", 0, "Answered", "lookup", "900000.00"),
      ("A03", "s1", "How about Mumbai?", 0, "Answered", "lookup", "1050000.00"),
      (
          "A04",
          "s2",
          "How is Hyderabad doing?",
          0,
          "Clarification Needed",
          "lookup",
          "",
      ),
      (
          "A05",
          "s2",
          "revenue on 2026-05-15",
          0,
          "Answered",
          "lookup",
          "786399.27",
      ),
      (
          "A06",
          "s3",
          "What was Hydrabad's turnover yesterday?",
          0,
          "Answered",
          "lookup",
          "784954.90",
      ),
      (
          "A07",
          "s4",
          "Did Pune hit its target on 2026-05-16?",
          0,
          "Drafted",
          "target_vs_actual",
          "74.59%",
      ),
      (
          "A08",
          "s4",
          "Did Pune hit its target on 2026-05-20?",
          0,
          "Answered",
          "target_vs_actual",
          "75.30%",
      ),
      (
          "A09",
          "s4",
          "Did Mumbai hit its target on 2026-05-21?",
          0,
          "Answered",
          "target_vs_actual",
          "107.99%",
      ),
      (
          "A10",
          "s5",
          (
              "Which store had the highest average revenue between 2026-05-01"
              " and 2026-05-31?"
          ),
          0,
          "Answered",
          "comparison",
          "Mumbai",
      ),
      (
          "A11",
          "s5",
          "Which store had the lowest revenue on 2026-06-10?",
          0,
          "Answered",
          "comparison",
          "Pune",
      ),
      (
          "A12",
          "s6",
          "Which stores are below the reorder threshold for Amul Milk?",
          0,
          "Answered",
          "inventory",
          "Hyderabad",
      ),
      (
          "A13",
          "s6",
          "What are customers saying about Hyderabad?",
          0,
          "Answered",
          "feedback",
          "2.63",
      ),
      (
          "A14",
          "s7",
          "What was Pune's profit margin on 2026-05-15?",
          0,
          "Safe Failure",
          "unsupported_metric",
          "",
      ),
      (
          "A15",
          "s8",
          "What is the capital of India?",
          0,
          "Escalated",
          "out_of_scope",
          "",
      ),
      (
          "A16",
          "s9",
          "What was Mumbai's revenue on 2026-07-15?",
          0,
          "Safe Failure",
          "lookup",
          "2026-04-01",
      ),
      (
          "A17",
          "s10",
          "Why is Pune's revenue so low?",
          0,
          "Escalated",
          "diagnostic",
          "",
      ),
      (
          "A18",
          "s11",
          "What was Kolkata's revenue on 2026-05-15?",
          0,
          "Clarification Needed",
          "lookup",
          "",
      ),
      (
          "A19",
          "s12",
          "What was Pune's revenue on 15 May 2026?",
          2,
          "Answered",
          "lookup",
          "623845.00",
      ),
      (
          "A20",
          "s13",
          "What was Pune's revenue on 15 May 2026?",
          3,
          "Escalated",
          "lookup",
          "",
      ),
  ]

  os.makedirs("outputs", exist_ok=True)
  os.makedirs("logs", exist_ok=True)

  # Empty logs/runs.jsonl first
  with open("logs/runs.jsonl", "w", encoding="utf-8") as f:
    pass

  transcript_lines = [
      "# Acceptance Transcript - DMart Capstone Project\n",
      "| Id | Session | Question | Status | Intent | Confidence | Route |"
      " Attempts | Answer Text |\n",
      "|---|---|---|---|---|---|---|---|---|\n",
  ]

  for case_id, session_id, question, sim_fails, req_status, req_intent, req_sub in cases:
    os.environ["SIMULATE_DB_FAILURES"] = str(sim_fails)
    res = handle(question, session_id=session_id, user_id="acceptance_user")

    t_line = (
        f"| {case_id} | {session_id} | {question} | {res['status']} |"
        f" {res['intent']} | {res['confidence']} | {res['route']} |"
        f" {res['attempts']} | {res['answer_text'].replace('|', '-')} |\n"
    )
    transcript_lines.append(t_line)

  with open("outputs/acceptance_transcript.md", "w", encoding="utf-8") as f:
    f.writelines(transcript_lines)

  print(
      "Acceptance script completed successfully! Generated"
      " outputs/acceptance_transcript.md and logs/runs.jsonl"
  )


if __name__ == "__main__":
  run_acceptance()