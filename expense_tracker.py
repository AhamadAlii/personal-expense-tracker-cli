#!/usr/bin/env python3
"""
Personal Expense Tracker (CLI)
- SQLite-backed
- Add/View/Update/Delete
- Categories, Filters, Summaries
- Basic validation & error handling
"""

import argparse
import sqlite3
from datetime import datetime
from pathlib import Path
from textwrap import dedent

DB_PATH = Path(__file__).parent / "expenses.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount REAL NOT NULL CHECK(amount >= 0),
    date TEXT NOT NULL,             -- ISO format YYYY-MM-DD
    category TEXT DEFAULT '',
    note TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_date ON expenses(date);
CREATE INDEX IF NOT EXISTS idx_category ON expenses(category);
"""

def valid_date(s: str) -> str:
    try:
        # Accept YYYY-MM-DD only
        datetime.strptime(s, "%Y-%m-%d")
        return s
    except ValueError:
        raise argparse.ArgumentTypeError("Date must be in YYYY-MM-DD format.")

def positive_amount(s: str) -> float:
    try:
        val = float(s)
        if val < 0:
            raise ValueError
        return val
    except ValueError:
        raise argparse.ArgumentTypeError("Amount must be a non-negative number.")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)

def add_expense(amount, date, category, note):
    init_db()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO expenses(amount, date, category, note) VALUES(?,?,?,?)",
            (amount, date, category or "", note or ""),
        )
        conn.commit()

def list_expenses(start=None, end=None, category=None, limit=None):
    init_db()
    q = "SELECT id, amount, date, category, note FROM expenses WHERE 1=1"
    args = []
    if start:
        q += " AND date >= ?"
        args.append(start)
    if end:
        q += " AND date <= ?"
        args.append(end)
    if category:
        q += " AND category = ?"
        args.append(category)
    q += " ORDER BY date DESC, id DESC"
    if limit:
        q += " LIMIT ?"
        args.append(limit)
    with get_conn() as conn:
        cur = conn.execute(q, args)
        rows = cur.fetchall()
    return rows

def update_expense(expense_id, amount=None, date=None, category=None, note=None):
    init_db()
    sets = []
    args = []
    if amount is not None:
        sets.append("amount = ?")
        args.append(amount)
    if date is not None:
        sets.append("date = ?")
        args.append(date)
    if category is not None:
        sets.append("category = ?")
        args.append(category)
    if note is not None:
        sets.append("note = ?")
        args.append(note)
    if not sets:
        raise ValueError("No fields provided to update.")
    args.append(expense_id)
    q = f"UPDATE expenses SET {', '.join(sets)} WHERE id = ?"
    with get_conn() as conn:
        cur = conn.execute(q, args)
        if cur.rowcount == 0:
            raise ValueError(f"Expense id {expense_id} not found.")
        conn.commit()

def delete_expense(expense_id):
    init_db()
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        if cur.rowcount == 0:
            raise ValueError(f"Expense id {expense_id} not found.")
        conn.commit()

def summarize(start=None, end=None, by=None, category=None):
    """
    by: None | 'category' | 'month'
    Optional filter: category (when grouping by month or none, we can still filter to a given category)
    """
    init_db()
    filters = []
    args = []
    if start:
        filters.append("date >= ?")
        args.append(start)
    if end:
        filters.append("date <= ?")
        args.append(end)
    if category:
        filters.append("category = ?")
        args.append(category)
    where = f"WHERE {' AND '.join(filters)}" if filters else ""

    with get_conn() as conn:
        if by == "category":
            q = f"""
                SELECT COALESCE(NULLIF(category, ''), 'uncategorized') AS grp, 
                       ROUND(SUM(amount), 2) AS total
                FROM expenses
                {where}
                GROUP BY grp
                ORDER BY total DESC;
            """
            cur = conn.execute(q, args)
            return cur.fetchall()
        elif by == "month":
            # Expect date in YYYY-MM-DD; use substr to get YYYY-MM
            q = f"""
                SELECT substr(date, 1, 7) AS grp, ROUND(SUM(amount), 2) AS total
                FROM expenses
                {where}
                GROUP BY grp
                ORDER BY grp DESC;
            """
            cur = conn.execute(q, args)
            return cur.fetchall()
        else:
            q = f"SELECT ROUND(SUM(amount), 2) FROM expenses {where};"
            cur = conn.execute(q, args)
            total = cur.fetchone()[0]
            return [("total", total or 0.0)]

def print_table(rows, headers):
    if not rows:
        print("No records found.")
        return
    widths = [len(h) for h in headers]
    str_rows = [[str(c) if c is not None else "" for c in row] for row in rows]
    for r in str_rows:
        widths = [max(w, len(c)) for w, c in zip(widths, r)]
    fmt = " | ".join("{:<" + str(w) + "}" for w in widths)
    print(fmt.format(*headers))
    print("-+-".join("-" * w for w in widths))
    for r in str_rows:
        print(fmt.format(*r))

def main():
    parser = argparse.ArgumentParser(
        prog="expense-tracker",
        description="Personal Expense Tracker (CLI) — SQLite-backed",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=dedent("""
            Examples:
              Add:    python expense_tracker.py add --amount 120.50 --date 2025-10-03 --category food --note "Lunch"
              List:   python expense_tracker.py list --start 2025-10-01 --end 2025-10-31 --category food
              Update: python expense_tracker.py update 3 --amount 200 --note "Corrected"
              Delete: python expense_tracker.py delete 3
              Sum:    python expense_tracker.py summary
              By cat: python expense_tracker.py summary --by category
              By mon: python expense_tracker.py summary --by month
        """),
    )

    sub = parser.add_subparsers(dest="cmd", required=True)

    # add
    p_add = sub.add_parser("add", help="Add a new expense")
    p_add.add_argument("--amount", type=positive_amount, required=True)
    p_add.add_argument("--date", type=valid_date, required=True)
    p_add.add_argument("--category", type=str, default="")
    p_add.add_argument("--note", type=str, default="")

    # list
    p_list = sub.add_parser("list", help="View expenses")
    p_list.add_argument("--start", type=valid_date)
    p_list.add_argument("--end", type=valid_date)
    p_list.add_argument("--category", type=str)
    p_list.add_argument("--limit", type=int)

    # update
    p_update = sub.add_parser("update", help="Update an expense by ID")
    p_update.add_argument("id", type=int)
    p_update.add_argument("--amount", type=positive_amount)
    p_update.add_argument("--date", type=valid_date)
    p_update.add_argument("--category", type=str)
    p_update.add_argument("--note", type=str)

    # delete
    p_delete = sub.add_parser("delete", help="Delete an expense by ID")
    p_delete.add_argument("id", type=int)

    # summary
    p_sum = sub.add_parser("summary", help="Show summary totals")
    p_sum.add_argument("--start", type=valid_date)
    p_sum.add_argument("--end", type=valid_date)
    p_sum.add_argument("--by", choices=["category", "month"])
    p_sum.add_argument("--category", type=str)

    args = parser.parse_args()

    try:
        if args.cmd == "add":
            add_expense(args.amount, args.date, args.category, args.note)
            print("✅ Added.")
        elif args.cmd == "list":
            rows = list_expenses(args.start, args.end, args.category, args.limit)
            print_table(rows, headers=["ID", "Amount", "Date", "Category", "Note"])
        elif args.cmd == "update":
            update_expense(args.id, args.amount, args.date, args.category, args.note)
            print("✅ Updated.")
        elif args.cmd == "delete":
            delete_expense(args.id)
            print("🗑️ Deleted.")
        elif args.cmd == "summary":
            rows = summarize(args.start, args.end, args.by, args.category)
            hdr = {"category": ["Category", "Total"],
                   "month": ["Month", "Total"]}.get(args.by, ["Metric", "Value"])
            print_table(rows, headers=hdr)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
