Markdown
# DMart Conversational Analytics Agent & Store Diagnosis Capstone

## Purpose
This repository contains the complete capstone project for the DMart Regional Director Assistant. It integrates data cleaning and validation (Part A), rigorous agent specifications (Part B), a robust conversational analytics agent with sqlite and python routing (Part C), and an evaluation harness with a weather tool and release gate decision (Part D).

## Repository Layout
README.md
.gitignore
requirements.txtdata/store_daily.csvinventory.csvfeedback.csvstore_daily_clean.csvscripts/generate_data.pyclean_data.pyanalyze.pyrun_acceptance.pyanalysis/data_quality_report.mdcleaning_log.csvfindings.mdexecutive_summary.mddocs/requirement.mddata_context.mdagent_spec.mdrelease_gate.mdagent/understand.pyfetch.pyanswer.pyrun_agent.pytools/weather.pytests/weather_tool_tests.mdoutputs/acceptance_transcript.mdlogs/runs.jsonleval/golden_set.csvgolden_set_derivation.mdrun_eval.pyeval_results.csveval_runs.jsonleval_summary.md


## Setup and Execution Guide
Run all scripts in order from the repository root using Python 3.9+:

1. **Generate Raw Data:**
   ```bash
   python scripts/generate_data.py
Clean Data & Generate Logs:

Bash
python scripts/clean_data.py
Run Statistical Analysis & Findings:

Bash
python scripts/analyze.py
Run Agent Acceptance Tests:

Bash
python scripts/run_acceptance.py
Run Golden Set Evaluation:

Bash
python eval/run_eval.py
Free Offline Path
LLM Mode: Mock / Rule-based interpreter (LLM_MODE=mock).

Weather Mode: Stub deterministic formula (WEATHER_MODE=stub).

Database: Local SQLite database (data/dmart.db).

No API keys or external service accounts are required.

Rounding Method
All arithmetic averages and metric computations are rounded using Round Half-Up to 2 decimal places, implemented via Python's decimal.Decimal module with ROUND_HALF_UP.

Known Limitations
The intent parser uses rule-based keyword matching and fuzzy string matching (difflib), which may require tuning for highly unstructured conversational phrasing outside the specified grammar.

Multi-intent compound questions in a single turn are handled through disambiguation rules rather than multi-step action planning.

Prioritised Iteration-2 Backlog
Trend Analysis Questions: Enable queries analysing month-over-month or week-over-week revenue trajectories.

Input: "How did Pune's revenue trend over May 2026?"

Output: Time-series growth percentage and directional summary.

Success Criteria: Correct percentage delta calculation against cleaned baseline.

Failure Behaviour: Safe fallback to standard range lookup if aggregation fails.

Hosted PostgreSQL Database Migration: Move from local SQLite to a scalable PostgreSQL instance for multi-user concurrent access.

Input: Database connection string via .env.

Output: Seamless query execution across concurrent sessions.

Success Criteria: Zero downtime migration with parity in SQL query results.

Failure Behaviour: Automatic reconnection retry logic with graceful degradation.

Deep Follow-up Context Retention: Extend multi-turn session memory to retain comparative constraints across successive questions.

Weather data by Open-Meteo.com https://open-meteo.com/