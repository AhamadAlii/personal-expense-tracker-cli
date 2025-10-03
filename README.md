# Personal Expense Tracker (CLI)

A simple, SQLite-backed command-line Personal Expense Tracker.

**Supports**
- Add, View, Update, Delete expenses
- Categories (food, travel, bills, etc.)
- Filters (by date range and/or category)
- Summary reports:
  - Total spent
  - Group by category
  - Group by month (YYYY-MM)
- Basic validation & error handling
- Data persisted in `expenses.db` (SQLite)

---

## Quick Start

**Requires:** Python 3.8+

```bash
# 1) Create & activate a virtual env (recommended)
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 2) Install (no 3rd-party deps needed)
pip install -r requirements.txt  # (empty, uses stdlib only)

# 3) Run
python expense_tracker.py --help
```

The first run auto-creates `expenses.db` in the project folder.

---

## Usage

### Add
```bash
python expense_tracker.py add --amount 120.50 --date 2025-10-03 --category food --note "Lunch"
```

### View (with optional filters)
```bash
python expense_tracker.py list
python expense_tracker.py list --start 2025-10-01 --end 2025-10-31
python expense_tracker.py list --category travel
python expense_tracker.py list --start 2025-10-01 --end 2025-10-31 --category food --limit 50
```

### Update
```bash
python expense_tracker.py update 3 --amount 200 --note "Corrected entry"
```

### Delete
```bash
python expense_tracker.py delete 3
```

### Summary
```bash
# Total spent (optionally filtered by date/category)
python expense_tracker.py summary
python expense_tracker.py summary --start 2025-10-01 --end 2025-10-31
python expense_tracker.py summary --category food

# Group by category
python expense_tracker.py summary --by category

# Group by month (YYYY-MM)
python expense_tracker.py summary --by month
```

---

## Sample I/O

**Add**
```
$ python expense_tracker.py add --amount 99.99 --date 2025-10-02 --category bills --note "Electricity"
✅ Added.
```

**List**
```
$ python expense_tracker.py list
ID | Amount | Date       | Category | Note
---+--------+------------+----------+----------------
1  | 99.99  | 2025-10-02 | bills    | Electricity
```

**Update**
```
$ python expense_tracker.py update 1 --amount 109.49
✅ Updated.
```

**Delete**
```
$ python expense_tracker.py delete 1
🗑️ Deleted.
```

**Summary by category**
```
$ python expense_tracker.py summary --by category
Category     | Total
-------------+-------
food         | 220.50
travel       | 120.00
bills        | 109.49
```

---

## Design & Assumptions

- **Storage**: SQLite (`expenses.db`) for reliability and easy portability.
- **Dates**: ISO format `YYYY-MM-DD` (validated). Stored as TEXT for compatibility.
- **Amounts**: Non-negative numbers (`REAL`, validated).
- **Categories**: Free-text string. Empty becomes `uncategorized` in summaries.
- **Summaries**: 
  - `--by category`: groups by `category`
  - `--by month`: groups by `substr(date, 1, 7)` → `YYYY-MM`
  - default: total spent
- **Indexes**: on `date` and `category` for faster filtering.
- **Error handling**: User input validation and helpful errors for common cases (e.g., bad date, missing ID).

---

## Project Structure

```
personal-expense-tracker-cli/
├─ expense_tracker.py
├─ requirements.txt
└─ README.md
```

---

## Notes

- No external packages required.
- You can safely version `expenses.db` (or add it to `.gitignore` if you prefer).
- Extend easily into a REST API or simple UI later using the same database.
