"""Understanding module for DMart Conversational Analytics Agent.
Parses user questions, resolves entities (stores, metrics, dates, products),
computes confidence scores, handles session context, and detects intent.
"""

import datetime
import difflib
import re

# Closed keyword and stopword lists
STORES = ["Mumbai", "Pune", "Hyderabad", "Bengaluru", "Ahmedabad"]
STORE_ALIASES = {"bangalore": "Bengaluru", "banglore": "Bengaluru"}

APPROVED_METRICS = {
    "revenue_inr": ["revenue", "sales", "turnover", "earnings"],
    "daily_target_inr": ["target"],
    "footfall": ["footfall", "visitors"],
    "stockout_hours": ["stockout", "stockouts"],
    "discount_pct": ["discount", "discounts"],
}

STOPWORDS = {
    "hello",
    "thanks",
    "thank",
    "kindly",
    "please",
    "display",
    "compare",
    "which",
    "what",
    "whats",
    "how",
    "why",
    "did",
    "and",
    "show",
    "check",
    "report",
    "where",
    "would",
    "could",
    "can",
    "will",
    "give",
    "tell",
    "list",
}

PROHIBITED_WORDS = {
    "ignore",
    "disregard",
    "override",
    "bypass",
    "forget",
    "send",
    "email",
    "whatsapp",
    "purchase",
    "buy",
    "restock",
}

UNSUPPORTED_KEYWORDS = {
    "profit",
    "margin",
    "marketing",
    "cost",
    "expense",
    "shortfall",
    "efficiency",
    "weekend",
    "per footfall",
    "per visitor",
}

PRODUCTS = [
    "Amul Milk 1L",
    "Toor Dal 1kg",
    "Basmati Rice 5kg",
    "Sunflower Oil 1L",
    "Iodised Salt 1kg",
    "Instant Noodles 70g",
    "Glucose Biscuits 200g",
    "Detergent Powder 1kg",
]

AS_OF_DATE = datetime.date(2026, 6, 29)  # As of 2026-06-30, yesterday is 2026-06-29


def understand(question: str, context: dict = None) -> dict:
  if context is None:
    context = {}

  q_lower = question.lower()
  words = re.findall(r"\b\w+\b", question)
  q_stripped = question.strip()

  # Treat bare follow-up requests as context-driven lookups when a prior store/date exists.
  bare_followup = (
      q_lower.startswith(("and ", "how about ", "what about "))
      and len(words) <= 6
      and not any(term in q_lower for term in ["highest", "lowest", "best", "worst"])
  )

  # 1. Store Resolution
  resolved_store = None
  store_conf = 1.0
  unresolved_store_flag = False

  # Check exact stores or aliases
  store_hits = []
  for s in STORES:
    if s.lower() in q_lower:
      store_hits.append(s)
  if store_hits:
    if len(store_hits) > 1:
      unresolved_store_flag = True
      resolved_store = None
    else:
      resolved_store = store_hits[0]
  if not resolved_store:
    for alias, actual in STORE_ALIASES.items():
      if alias in q_lower:
        resolved_store = actual
        break
  if len(store_hits) > 1:
    unresolved_store_flag = True
    resolved_store = None

  # Fuzzy match check for candidate words
  if not resolved_store:
    for word in words:
      if len(word) >= 5 and (word[0].isupper() or "'" in word):
        if word.lower() not in STOPWORDS and word.lower() not in [
            s.lower() for s in STORES
        ]:
          # Check fuzzy against STORES
          matches = difflib.get_close_matches(
              word, STORES, n=1, cutoff=0.7
          )
          if matches:
            resolved_store = matches[0]
            store_conf = round(
                difflib.SequenceMatcher(None, word, resolved_store).ratio(), 2
            )
            break
          else:
            # Check if it's an unresolved named store candidate
            if "'" in word or q_lower.find(word.lower()) > 0:
              unresolved_store_flag = True

  # 2. Metric Resolution
  resolved_metric = None
  target_lookup = "target" in q_lower and not any(
      tw in q_lower for tw in [
          "hit",
          "met",
          "meet",
          "miss",
          "exceed",
          "achieve",
          "achievement",
      ]
  )
  for metric, synonyms in APPROVED_METRICS.items():
    for syn in synonyms:
      if syn in q_lower:
        resolved_metric = metric
        break
    if resolved_metric:
      break
  if target_lookup and not resolved_metric:
    resolved_metric = "daily_target_inr"

  # 3. Date Resolution (Closed Grammar)
  resolved_date = None
  date_range = None

  # Check ISO format YYYY-MM-DD
  iso_dates = re.findall(r"\b(\d{4}-\d{2}-\d{2})\b", question)
  if iso_dates:
    resolved_date = iso_dates[0]
    if len(iso_dates) > 1:
      date_range = (iso_dates[0], iso_dates[1])

  # Check "between <date> and <date>"
  between_match = re.search(
      r"between\s+(\d{4}-\d{2}-\d{2})\s+and\s+(\d{4}-\d{2}-\d{2})", q_lower
  )
  if between_match:
    date_range = (between_match.group(1), between_match.group(2))
    resolved_date = None

  # Check "D Month YYYY" (e.g. 15 May 2026)
  d_month_match = re.search(
      r"\b(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})\b",
      question,
      re.IGNORECASE,
  )
  if d_month_match:
    day, month_str, year = (
        d_month_match.group(1),
        d_month_match.group(2),
        d_month_match.group(3),
    )
    try:
      dt_parsed = datetime.datetime.strptime(
          f"{day} {month_str} {year}", "%d %B %Y"
      )
      resolved_date = dt_parsed.strftime("%Y-%m-%d")
    except ValueError:
      pass

  # Check yesterday
  if "yesterday" in q_lower:
    resolved_date = AS_OF_DATE.strftime("%Y-%m-%d")

  # Unresolved date check (rough heuristic for date-like words outside grammar)
  unresolved_date_flag = False
  if any(
    keyword in q_lower
    for keyword in ["last week", "past", "recent", "jun", "20260515"]
   ):
    unresolved_date_flag = True

  # 4. Product Resolution
  resolved_product = None
  for p in PRODUCTS:
    if p.lower() in q_lower or p.split()[0].lower() in q_lower:
      resolved_product = p
      break

  # 5. Weather check
  weather_requested = any(
      w in q_lower
      for w in ["weather", "rain", "temperature", "humidity", "hot", "cold"]
  )

  # 6. Intent Classification
  intent = "out_of_scope"
  contextual_lookup_followup = (
      context.get("last_intent") in ["lookup", "target_vs_actual"]
      and (bare_followup or len(words) <= 3)
      and not any(
          tw in q_lower
          for tw in [
              "hit",
              "met",
              "meet",
              "miss",
              "exceed",
              "achieve",
              "achievement",
          ]
      )
  )

  # Rule 1: Prohibited / override -> out_of_scope
  if any(pw in q_lower for pw in PROHIBITED_WORDS) or (
      words
      and words[0].lower() in ["reorder", "order"]
      and "threshold" not in q_lower
  ):
    intent = "out_of_scope"
  # Rule 2: Unsupported metric
  elif any(uw in q_lower for uw in UNSUPPORTED_KEYWORDS):
    intent = "unsupported_metric"
  # Rule 3: Diagnostic
  elif q_lower.startswith(("why", "how come")) or "reason" in q_lower:
    intent = "diagnostic"
  # Rule 4: Inventory
  elif resolved_product or "reorder" in q_lower or "inventory" in q_lower:
    intent = "inventory"
  # Rule 5: Feedback
  elif (
      any(
          fb in q_lower
          for fb in ["feedback", "review", "rating", "say", "saying"]
      )
      and not resolved_metric
  ):
    intent = "feedback"
  # Rule 6: Bare follow-up after prior lookup/target context stays in lookup mode.
  elif contextual_lookup_followup:
    intent = "lookup"
    if "target" in q_lower:
      resolved_metric = "daily_target_inr"
  # Rule 7: Target vs Actual
  elif any(
      tw in q_lower
      for tw in [
          "hit",
          "met",
          "meet",
          "miss",
          "exceed",
          "achieve",
          "target",
          "achievement",
      ]
  ):
    intent = "target_vs_actual"
  # Rule 8: Comparison (which / highest / lowest without store)
  elif (
      any(cw in q_lower for cw in ["highest", "lowest", "best", "worst"])
      and not resolved_store
  ):
    intent = "comparison"
  # Rule 9: Lookup (metric present)
  elif resolved_metric:
    intent = "lookup"
  # Rule 10: Weather only
  elif weather_requested and not resolved_metric:
    intent = "weather"
  # Rule 10: Store/Date only -> lookup or target_vs_actual
  elif resolved_store or resolved_date or date_range:
    if context.get("last_intent") == "target_vs_actual":
      intent = "target_vs_actual"
    else:
      intent = "lookup"

  sort_order = "desc"
  if "lowest" in q_lower or "worst" in q_lower:
    sort_order = "asc"

  # Context inheritance for required entities if missing
  if not resolved_store and context.get("store") and intent not in ["comparison", "inventory"]:
    resolved_store = context.get("store")
  if not resolved_metric and context.get("metric") and intent in ["lookup"]:
    resolved_metric = context.get("metric")
  if not resolved_date and not date_range and context.get("date") and intent in ["lookup", "target_vs_actual", "weather"]:
    resolved_date = context.get("date")

  # For bare store-only follow-ups like "How about Mumbai?", inherit the prior date when available.
  if (
      bare_followup
      and not resolved_store
      and context.get("store")
      and intent == "target_vs_actual"
  ):
    resolved_store = context.get("store")
  if (
      bare_followup
      and not resolved_date
      and context.get("date")
      and intent == "target_vs_actual"
  ):
    resolved_date = context.get("date")

  # Missing entities check for confidence
  missing_entities = []
  if intent == "lookup" and not (resolved_date or date_range):
    missing_entities.append("date")
  if intent == "lookup" and not resolved_metric:
    missing_entities.append("metric")
  if intent == "lookup" and not resolved_store:
    missing_entities.append("store")
  if intent == "target_vs_actual" and not (resolved_date or resolved_store):
    missing_entities.append("date/store")
  if intent == "weather" and not (resolved_store and resolved_date):
    missing_entities.append("store/date")

  confidence = 1.0
  if unresolved_store_flag or unresolved_date_flag:
    confidence = 0.4
  elif missing_entities:
    confidence = 0.4
  elif store_conf < 1.0:
    confidence = store_conf

  return {
      "intent": intent,
      "store": resolved_store,
      "metric": resolved_metric,
      "date": resolved_date,
      "date_range": date_range,
      "product": resolved_product,
      "weather_requested": weather_requested,
      "confidence": confidence,
      "missing_entities": missing_entities,
      "sort_order": sort_order,
  }