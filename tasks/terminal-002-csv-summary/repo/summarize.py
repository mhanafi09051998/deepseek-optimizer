"""Summarize an expense CSV from a file or stdin."""

import csv
import sys


def summarize(rows):
    totals = {}
    for row in rows:
        category, amount = row[0], float(row[1])
        totals[category] = totals.get(category, 0.0) + amount
    return totals


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv:
        with open(argv[0], encoding="utf-8", newline="") as handle:
            rows = list(csv.reader(handle))
    else:
        rows = list(csv.reader(sys.stdin))

    totals = summarize(rows)
    for category in sorted(totals):
        print(f"{category},{totals[category]:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
