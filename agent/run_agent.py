"""Runner module for DMart Conversational Analytics Agent.
Connects understand, fetch, answer, and weather tools, manages session state,
measures latency, estimates tokens, and logs execution runs to JSON lines.
"""

from datetime import datetime
import json
import os
import time

from agent.answer import build_answer
from agent.fetch import fetch_data
from agent.understand import understand
from tools.weather import get_weather

# In-memory session store
SESSIONS = {}


def handle(question: str, session_id: str, user_id: str = "u1") -> dict:
  start_time = time.perf_counter()

  # 1. Get session context
  if session_id not in SESSIONS:
    SESSIONS[session_id] = {
        "store": None,
        "metric": None,
        "date": None,
        "date_range": None,
        "product": None,
        "last_intent": None,
        "last_target_flag": False,
    }

  session_ctx = SESSIONS[session_id]

  # Check bare follow-up for target_vs_actual
  q_lower = question.lower()
  is_bare_followup = session_ctx["last_target_flag"] and (
      ("store" not in q_lower and len(q_lower.split()) <= 3)
      or q_lower.startswith(("and ", "how about ", "what about "))
  ) and "target" not in q_lower

  # 2. Understand question
  parsed = understand(question, context=session_ctx)

  if is_bare_followup and parsed["intent"] in ["lookup", "out_of_scope"]:
    parsed["intent"] = "target_vs_actual"
    if not parsed["store"] and session_ctx["store"]:
      parsed["store"] = session_ctx["store"]
    if not parsed["date"] and session_ctx["date"]:
      parsed["date"] = session_ctx["date"]

  # 3. Weather check / tool invocation
  weather_data = None
  tools_called = []
  route = "python"

  if parsed.get("weather_requested") or parsed["intent"] == "weather":
    store = parsed.get("store")
    date = parsed.get("date")
    if store and date:
      w_res = get_weather(store, date)
      if w_res.get("ok"):
        weather_data = w_res
        tools_called.append("weather_tool")

  # 4. Fetch data
  fetch_res = {"status": "Success", "data": None, "attempts": 1}

  if parsed["intent"] in [
      "lookup",
      "target_vs_actual",
      "comparison",
      "inventory",
      "feedback",
  ]:
    fetch_res = fetch_data(parsed)
    if parsed["intent"] in ["comparison", "inventory", "feedback"]:
      route = "sql"
    else:
      route = "python"
  elif parsed["intent"] == "weather":
    route = "weather" if weather_data else "none"
  elif weather_data and parsed["intent"] in ["lookup", "target_vs_actual"]:
    route = "python+weather"
  else:
    route = "none"

  # Build answer & ground
  ans_res = build_answer(
      parsed["intent"], fetch_res, parsed, weather_data=weather_data
  ) or {}
  ans_res.setdefault("status", "Answered")
  ans_res.setdefault("answer_text", "")
  ans_res.setdefault("evidence", [])
  ans_res.setdefault("grounded_values", [])
  ans_res.setdefault("ungrounded_numbers", 0)

  end_time = time.perf_counter()
  latency_ms = round((end_time - start_time) * 1000, 2)

  # Token estimation: words in question + words in answer
  tokens_est = len(question.split()) + len(
      ans_res.get("answer_text", "").split()
  )
  budget_exceeded = tokens_est > 150

  # 6. Update session context
  if parsed["store"]:
    session_ctx["store"] = parsed["store"]
  if parsed["metric"]:
    session_ctx["metric"] = parsed["metric"]
  if parsed["date"]:
    session_ctx["date"] = parsed["date"]
    session_ctx["date_range"] = None
  if parsed["date_range"]:
    session_ctx["date_range"] = parsed["date_range"]
    session_ctx["date"] = None
  if parsed["product"]:
    session_ctx["product"] = parsed["product"]

  session_ctx["last_intent"] = parsed["intent"]
  if parsed["intent"] == "target_vs_actual":
    session_ctx["last_target_flag"] = True
  else:
    session_ctx["last_target_flag"] = False

  # 7. Audit Logging
  log_path = os.environ.get("AGENT_LOG_PATH", "logs/runs.jsonl")
  os.makedirs(os.path.dirname(log_path), exist_ok=True)

  run_id = f"run_{int(time.time()*1000)}"
  timestamp = datetime.utcnow().isoformat() + "Z"

  executed_query_or_func = None
  if route in ["sql", "python", "python+weather"]:
    if parsed["intent"] == "comparison":
      executed_query_or_func = "SELECT store, AVG(...) GROUP BY store ORDER BY..."
    elif parsed["intent"] == "inventory":
      executed_query_or_func = (
          "SELECT store, product, stock_units, reorder_threshold FROM inventory..."
      )
    elif parsed["intent"] == "feedback":
      executed_query_or_func = (
          "SELECT store, AVG(rating), COUNT(*) FROM feedback..."
      )
    else:
      executed_query_or_func = f"fetch_data({parsed['intent']})"

  tool_calls_count = 0
  if route in ["python", "sql"]:
    tool_calls_count = 1
  elif route == "python+weather":
    tool_calls_count = 2  # data + weather
  elif route == "weather":
    tool_calls_count = 1

  log_entry = {
      "run_id": run_id,
      "user_id": user_id,
      "session_id": session_id,
      "timestamp": timestamp,
      "question": question,
      "intent": parsed["intent"],
      "confidence": parsed["confidence"],
      "route": route,
      "executed": executed_query_or_func,
      "attempts": fetch_res.get("attempts", 1)
      if route != "none" and fetch_res.get("status") != "Safe Failure"
      else 0,
      "tools_called": tools_called,
      "status": ans_res["status"],
      "answer_text": ans_res["answer_text"],
      "evidence": ans_res["evidence"],
      "grounded_values": ans_res["grounded_values"],
      "latency_ms": latency_ms,
      "tokens_est": tokens_est,
      "tool_calls": tool_calls_count,
      "ungrounded_numbers": ans_res["ungrounded_numbers"],
      "budget_exceeded": budget_exceeded,
  }

  with open(log_path, "a", encoding="utf-8") as log_file:
    log_file.write(json.dumps(log_entry) + "\n")

  return log_entry