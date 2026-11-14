"""Fetching module for DMart Conversational Analytics Agent.
Runs validated queries against local SQLite database or Python functions,
enforces approved field checks, date range limits, and retry logic.
"""

from decimal import Decimal, ROUND_HALF_UP
import os
import sqlite3
import time

DB_PATH = "data/dmart.db"

APPROVED_FIELDS = {
    "revenue_inr",
    "daily_target_inr",
    "footfall",
    "stockout_hours",
    "discount_pct",
    "achievement_pct",
    "performance_band",
    "stock_units",
    "reorder_threshold",
    "rating",
    "theme",
}

VALID_TABLES = {"store_daily_clean", "inventory", "feedback"}


def init_db():
  """Initializes local SQLite database from CSV files if not already present."""
  os.makedirs("data", exist_ok=True)
  conn = sqlite3.connect(DB_PATH)
  cursor = conn.cursor()

  # Load store_daily_clean
  import pandas as pd

  if os.path.exists("data/store_daily_clean.csv"):
    df_daily = pd.read_csv("data/store_daily_clean.csv")
    df_daily.to_sql("store_daily_clean", conn, if_exists="replace", index=False)

  if os.path.exists("data/inventory.csv"):
    df_inv = pd.read_csv("data/inventory.csv")
    df_inv.to_sql("inventory", conn, if_exists="replace", index=False)

  if os.path.exists("data/feedback.csv"):
    df_fb = pd.read_csv("data/feedback.csv")
    df_fb.to_sql("feedback", conn, if_exists="replace", index=False)

  conn.commit()
  conn.close()


init_db()


def validate_fields(fields: list):
  for f in fields:
    if f not in APPROVED_FIELDS and f != "*":
      raise ValueError(f"Unapproved field requested: {f}")


def validate_date_range(date_str: str = None, date_range: tuple = None) -> bool:
  """Validates dates are within the permitted range 2026-04-01 to 2026-06-29."""
  min_date = "2026-04-01"
  max_date = "2026-06-29"

  if date_str:
    if not (min_date <= date_str <= max_date):
      return False
  if date_range:
    start, end = date_range
    if not (min_date <= start <= max_date and min_date <= end <= max_date):
      return False
    if start > end:
      return False
  return True


def round_half_up(val, decimals=2):
  if val is None:
    return 0.0
  d = Decimal(str(val))
  return float(
      d.quantize(
          Decimal("1." + "0" * decimals if decimals > 0 else "1"),
          rounding=ROUND_HALF_UP,
      )
  )


def fetch_data(parsed_intent: dict) -> dict:
  """Executes data retrieval based on intent with retry logic and validation."""
  intent = parsed_intent["intent"]
  store = parsed_intent.get("store")
  metric = parsed_intent.get("metric")
  date = parsed_intent.get("date")
  date_range = parsed_intent.get("date_range")
  product = parsed_intent.get("product")

  # Simulate DB failures check from environment
  sim_failures = int(os.environ.get("SIMULATE_DB_FAILURES", 0))

  attempts = 0
  max_attempts = 3
  success = False
  data_result = None
  last_error = None

  while attempts < max_attempts and not success:
    attempts += 1
    if attempts <= sim_failures:
      last_error = RuntimeError("Simulated database connection failure")
      continue

    try:
      conn = sqlite3.connect(DB_PATH)
      cursor = conn.cursor()

      if intent == "lookup":
        # Check date range validity
        if date and not validate_date_range(date_str=date):
          conn.close()
          return {
              "status": "Safe Failure",
              "reason": "out_of_range_date",
              "attempts": attempts,
          }
        if date_range and not validate_date_range(date_range=date_range):
          conn.close()
          return {
              "status": "Safe Failure",
              "reason": "out_of_range_date",
              "attempts": attempts,
          }

        # Single store, single date lookup for specific metric or all
        if store and date and not date_range:
          cursor.execute(
              "SELECT store, date, revenue_inr, daily_target_inr, footfall,"
              " stockout_hours, discount_pct, achievement_pct, performance_band"
              " FROM store_daily_clean WHERE store = ? AND date = ?",
              (store, date),
          )
          row = cursor.fetchone()
          if not row:
            conn.close()
            return {
                "status": "Safe Failure",
                "reason": "no_record_found",
                "attempts": attempts,
            }
          cols = [
              [
                  "store",
                  "date",
                  "revenue_inr",
                  "daily_target_inr",
                  "footfall",
                  "stockout_hours",
                  "discount_pct",
                  "achievement_pct",
                  "performance_band",
              ][i]
              for i in range(len(row))
          ]
          data_result = dict(zip(cols, row))
          success = True

        # Range lookup (average over date range)
        elif store and date_range:
          start, end = date_range
          cursor.execute(
              "SELECT AVG(revenue_inr), AVG(daily_target_inr),"
              " AVG(footfall), AVG(stockout_hours), AVG(discount_pct),"
              " AVG(achievement_pct) FROM store_daily_clean WHERE store = ?"
              " AND date BETWEEN ? AND ?",
              (store, start, end),
          )
          row = cursor.fetchone()
          if not row or row[0] is None:
            conn.close()
            return {
                "status": "Safe Failure",
                "reason": "no_record_found",
                "attempts": attempts,
            }
          data_result = {
              "store": store,
              "start_date": start,
              "end_date": end,
              "revenue_inr": round_half_up(row[0]),
              "daily_target_inr": round_half_up(row[1]),
              "footfall": round_half_up(row[2]),
              "stockout_hours": round_half_up(row[3]),
              "discount_pct": round_half_up(row[4]),
              "achievement_pct": round_half_up(row[5]),
          }
          success = True
        else:
          conn.close()
          return {
              "status": "Clarification Needed",
              "reason": "missing_entities",
              "attempts": attempts,
          }

      elif intent == "target_vs_actual":
        if date and not validate_date_range(date_str=date):
          conn.close()
          return {
              "status": "Safe Failure",
              "reason": "out_of_range_date",
              "attempts": attempts,
          }
        cursor.execute(
            "SELECT store, date, revenue_inr, daily_target_inr,"
            " achievement_pct, performance_band FROM store_daily_clean WHERE"
            " store = ? AND date = ?",
            (store, date),
        )
        row = cursor.fetchone()
        if not row:
          conn.close()
          return {
              "status": "Safe Failure",
              "reason": "no_record_found",
              "attempts": attempts,
          }
        data_result = {
            "store": row[0],
            "date": row[1],
            "revenue_inr": row[2],
            "daily_target_inr": row[3],
            "achievement_pct": row[4],
            "performance_band": row[5],
        }
        success = True

      elif intent == "comparison":
        if date_range and not validate_date_range(date_range=date_range):
          conn.close()
          return {
              "status": "Safe Failure",
              "reason": "out_of_range_date",
              "attempts": attempts,
          }
        if date and not validate_date_range(date_str=date):
          conn.close()
          return {
              "status": "Safe Failure",
              "reason": "out_of_range_date",
              "attempts": attempts,
          }

        start = date_range[0] if date_range else date
        end = date_range[1] if date_range else date

        # Determine metric to sort by (default revenue_inr)
        sort_metric = metric if metric else "revenue_inr"
        validate_fields([sort_metric])

        # Determine sort direction (highest first by default, lowest first if requested)
        direction = parsed_intent.get("sort_order", "desc").upper()
        if direction not in ["ASC", "DESC"]:
          direction = "DESC"

        query = (
            f"SELECT store, AVG({sort_metric}) as avg_val,"
            " AVG(revenue_inr), AVG(footfall), AVG(stockout_hours),"
            " AVG(achievement_pct) FROM store_daily_clean WHERE date BETWEEN ?"
            f" AND ? GROUP BY store ORDER BY avg_val {direction}, store ASC"
        )
        cursor.execute(query, (start, end))
        rows = cursor.fetchall()
        if not rows:
          conn.close()
          return {
              "status": "Safe Failure",
              "reason": "no_record_found",
              "attempts": attempts,
          }

        results = []
        for r in rows:
          results.append({
              "store": r[0],
              "metric_avg": round_half_up(r[1]),
              "revenue_inr": round_half_up(r[2]),
              "footfall": round_half_up(r[3]),
              "stockout_hours": round_half_up(r[4]),
              "achievement_pct": round_half_up(r[5]),
          })
        data_result = results
        success = True

      elif intent == "inventory":
        query = (
            "SELECT store, product, stock_units, reorder_threshold FROM"
            " inventory WHERE stock_units < reorder_threshold"
        )
        params = []
        if store:
          query += " AND store = ?"
          params.append(store)
        if product:
          query += " AND product LIKE ?"
          params.append(f"%{product}%")

        cursor.execute(query, params)
        rows = cursor.fetchall()
        results = []
        for r in rows:
          results.append({
              "store": r[0],
              "product": r[1],
              "stock_units": r[2],
              "reorder_threshold": r[3],
          })
        data_result = results
        success = True

      elif intent == "feedback":
        query = (
            "SELECT store, AVG(CAST(rating AS FLOAT)) as avg_rating, COUNT("
            "CASE WHEN rating != '' THEN 1 END) as rated_count, COUNT(*) as"
            " total_count FROM feedback WHERE store = ? GROUP BY store"
        )
        cursor.execute(query, (store,))
        row = cursor.fetchone()

        # Get most frequent theme
        cursor.execute(
            "SELECT theme, COUNT(*) as cnt FROM feedback WHERE store = ? GROUP"
            " BY theme ORDER BY cnt DESC LIMIT 1",
            (store,),
        )
        theme_row = cursor.fetchone()
        top_theme = theme_row[0] if theme_row else "N/A"

        if not row:
          conn.close()
          return {
              "status": "Safe Failure",
              "reason": "no_record_found",
              "attempts": attempts,
          }

        data_result = {
            "store": row[0],
            "avg_rating": round_half_up(row[1]),
            "rated_count": row[2],
            "total_count": row[3],
            "top_theme": top_theme,
        }
        success = True

      conn.close()
    except Exception as e:
      last_error = e

  if not success:
    return {
        "status": "Escalated",
        "reason": str(last_error),
        "attempts": attempts,
    }

  return {"status": "Success", "data": data_result, "attempts": attempts}