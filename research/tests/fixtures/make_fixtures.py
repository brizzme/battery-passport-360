"""Writes the tiny synthetic Aalborg-shaped fixtures. Not measured data."""
import csv
from pathlib import Path

HERE = Path(__file__).parent


def rpt_rows():
    rows, t, v = [], 0.0, 3.30

    def hold(seconds, current, v_end, step):
        nonlocal t, v
        n = int(seconds / step)
        v0 = v
        for k in range(1, n + 1):
            t += step
            v = v0 + (v_end - v0) * k / n
            rows.append((t, current, round(v, 4)))

    rows.append((0.0, 0.0, v))
    hold(60, 0, 3.30, 60)
    hold(600, -45, 3.10, 60)       # short partial discharge (not the capacity test)
    hold(120, 0, 3.30, 60)
    hold(3600, -45, 2.50, 60)      # C/4 capacity test: 45 Ah
    hold(120, 0, 3.30, 60)
    drops = [0.045, 0.045, 0.09, 0.045]   # third discharge pulse = 50 % SOC, 0.09 V / 45 A = 2 mOhm
    for drop in drops:
        for current, dv in ((90, 0.05), (-90, -0.05), (45, 0.02), (-45, -drop)):
            hold(20, 0, 3.30, 10)
            v = 3.30
            hold(20, current, 3.30 + dv, 1)
            hold(20, 0, 3.30, 10)
    return rows


def ageing_rows():
    rows, t = [(1, 0.0, 0.0)], 0.0
    for seconds, current in ((14400, -90), (14400, 90), (7200, 0)):
        for _ in range(int(seconds / 60)):
            t += 60
            rows.append((1, t, current))
    return rows


def main():
    with open(HERE / "aalborg_rpt_small.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["Cell", "Round", "Time", "Current", "Voltage", "Energy", "Temperature"])
        w.writerows((9, 1, t, i, v, 0, 25) for t, i, v in rpt_rows())
    with open(HERE / "aalborg_ageing_small.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["Cell", "Round", "Part", "Time", "Current", "Voltage", "Energy", "Temperature"])
        w.writerows((9, 1, p, t, i, 3.3, 0, 40) for p, t, i in ageing_rows())


if __name__ == "__main__":
    main()
