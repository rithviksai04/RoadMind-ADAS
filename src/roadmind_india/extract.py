"""Extract the official MoRTH 'Road Accidents in India 2023' tables into CSVs (with validation).

Run: python -m roadmind_india.extract      (downloads the PDF if missing; needs `pdftotext` from poppler)
Every parsed table is reconciled against the totals printed in the report; a mismatch raises.
"""
import re
import subprocess
import urllib.request

import pandas as pd

from roadmind_india.config import PDF, PDF_URL, PROC, RAW_DIR, SOURCE, TOTALS_2023, TXT

INT = re.compile(r"(?<![\d.,-])\d{1,3}(?:,\d{2,3})+(?![\d.])|(?<![\d.,-])\d{3,}(?![\d.,])")


def ints(line: str) -> list[int]:
    """Integers written in Indian/Western grouping (e.g. 3,65,865); skips %-changes (decimals / 1-2 digit values)."""
    return [int(m.replace(",", "")) for m in INT.findall(line)]


def load_pages() -> list[str]:
    if not PDF.exists():
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(PDF_URL, PDF)
    if not TXT.exists():
        TXT.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["pdftotext", "-layout", str(PDF), str(TXT)], check=True)
    return TXT.read_text().split("\f")


def find_page(pages, header_regex, after=15):
    hits = [i for i, p in enumerate(pages) if i > after and re.search(header_regex, p)]
    if not hits:
        raise ValueError(f"table not found: {header_regex}")
    return hits[0]


def row_numbers(page: str, anchor: str, need: int, look: int = 2) -> list[int]:
    """Numbers of the row whose label starts with `anchor`; labels may wrap, so numbers can be on the next line."""
    lines = page.splitlines()
    for i, l in enumerate(lines):
        if re.match(r"\s*" + anchor, l):
            for j in range(i, min(i + look + 1, len(lines))):
                n = ints(lines[j])
                if len(n) >= need:
                    return n[:need]
    raise ValueError(f"row not found/incomplete: {anchor}")


def cond_table(pages, header, rows, total_anchor="Total"):
    """Tables 2.1/3.5-3.8: per row 6 counts = accidents22, accidents23, killed22, killed23, injured22, injured23."""
    pg_i = find_page(pages, header)
    page = pages[pg_i]
    out = []
    for name, anchor in rows:
        n = row_numbers(page, anchor, 6)
        out.append({"category": name, "accidents_2022": n[0], "accidents_2023": n[1], "killed_2022": n[2],
                    "killed_2023": n[3], "injured_2022": n[4], "injured_2023": n[5]})
    df = pd.DataFrame(out)
    tot = row_numbers(page, total_anchor, 6)
    assert list(df[["accidents_2022", "accidents_2023", "killed_2022", "killed_2023", "injured_2022",
                    "injured_2023"]].sum()) == tot, f"rows do not sum to printed total for {header}"
    df["source"] = f"{SOURCE}; PDF page {pg_i + 1}"
    return df


def build() -> dict[str, pd.DataFrame]:
    pages = load_pages()
    T: dict[str, pd.DataFrame] = {}
    T["weather"] = cond_table(pages, r"Table 3\.8: Road Accidents by Weather", [
        ("Sunny/Clear", r"Sunny/clear"), ("Rainy", r"Rainy"), ("Foggy & misty", r"Foggy"),
        ("Hail/Sleet", r"Hail/"), ("Others", r"Others")])
    T["road_feature"] = cond_table(pages, r"Table 3\.5: Accidents, Persons killed and Injuries by Road Feature", [
        ("Straight road", r"Straight road"), ("Curved road", r"Curved road"), ("Bridge", r"Bridge"),
        ("Culvert", r"Culvert"), ("Potholes", r"Potholes"), ("Steep grade", r"Steep grade"),
        ("Ongoing road works", r"Ongoing"), ("Others", r"Others")])
    T["junction"] = cond_table(pages, r"Table 3\.6: Accident by Type of Road Junction", [
        ("T-Junction", r"T-Junction"), ("Y-Junction", r"Y-Junction"), ("Four arm junction", r"Four arm"),
        ("Staggered junction", r"Staggered"), ("Roundabout", r"Round about"), ("No junction (Others)", r"Others")])
    T["traffic_control"] = cond_table(pages, r"Table 3\.7: Accidents, Persons Killed and Injured by Type of Traffic Control", [
        ("Traffic light signal", r"Traffic light"), ("Police controlled", r"Police"), ("Stop sign", r"Stop Sign"),
        ("Flashing signal/blinker", r"Flashing"), ("Uncontrolled", r"Uncontrolled"),
        ("No control point (Others)", r"Others")])
    # Table 2.1 has 3 category rows with 2022+2023 accidents/killed/injured in a different column order
    p = pages[find_page(pages, r"Table 2\.1: Road Accidents, Fatalities and Injuries by Road Category")]
    rows = []
    for name, anchor in [("National Highway", r"National Highways"), ("State Highway", r"State Highways"),
                         ("Other roads", r"Other Roads")]:
        n = row_numbers(p, anchor, 6)  # acc22, kill22, inj22, acc23, kill23, inj23
        rows.append({"category": name, "accidents_2022": n[0], "killed_2022": n[1], "injured_2022": n[2],
                     "accidents_2023": n[3], "killed_2023": n[4], "injured_2023": n[5]})
    T["road_category"] = pd.DataFrame(rows)
    T["road_category"]["source"] = f"{SOURCE}; Table 2.1"
    # Table 7.1 urban/rural, 2023 row: year, urban acc/killed/injured, rural acc/killed/injured, all-India
    p = pages[find_page(pages, r"Table 7\.1: Number of road accidents, persons killed and injured in Rural")]
    line = next(l for l in p.splitlines() if re.match(r"\s*2023\s", l))
    n = ints(line)[1:]
    T["area"] = pd.DataFrame([
        {"category": "Urban", "accidents_2023": n[0], "killed_2023": n[1], "injured_2023": n[2]},
        {"category": "Rural", "accidents_2023": n[3], "killed_2023": n[4], "injured_2023": n[5]}])
    T["area"]["source"] = f"{SOURCE}; Table 7.1"
    # Table 7.2 monthly: 2023 = last two numbers on each month row (accidents, killed)
    p = pages[find_page(pages, r"Table 7\.2: Trends of month-wise")]
    mrows = []
    for m in ["JAN", "FEB", "MAR", "APR", "MAY", "JUNE", "JULY", "AUG", "SEPT", "OCT", "NOV", "DEC"]:
        n = ints(next(l for l in p.splitlines() if re.match(r"\s*" + m + r"\s", l)))
        mrows.append({"month": m, "accidents_2023": n[8], "killed_2023": n[9]})
    T["month"] = pd.DataFrame(mrows)
    T["month"]["source"] = f"{SOURCE}; Table 7.2"
    # Table 7.3 time-of-day (accidents only - the report gives no deaths by time of day)
    p = pages[find_page(pages, r"Table 7\.3: Number of Road Accidents by time interval")]
    lines = p.splitlines()
    blocks = ["06-09 (Day)", "09-12 (Day)", "12-15 (Day)", "15-18 (Day)", "18-21 (Night)", "21-24 (Night)",
              "00-03 (Night)", "03-06 (Night)"]
    vals = [ints(l) for l in lines if re.search(r"hrs\s+\d", l) and len(ints(l)) >= 5][:8]
    T["time_of_day"] = pd.DataFrame({"block": blocks, "accidents_2023": [v[4] for v in vals]})
    T["time_of_day"]["source"] = f"{SOURCE}; Table 7.3 (accidents only, no deaths published)"
    # State tables: Annexure 2 (accidents), 3 (killed), 6 (severity = deaths per 100 accidents), by S.No.
    T["state"] = state_table(pages)
    return T


STATES = ["Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat", "Haryana",
          "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
          "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana",
          "Tripura", "Uttarakhand", "Uttar Pradesh", "West Bengal", "Andaman & Nicobar Islands", "Chandigarh",
          "Dadra & Nagar Haveli and Daman & Diu", "Delhi", "Jammu & Kashmir", "Ladakh", "Lakshadweep", "Puducherry"]


def state_rows(pages, header, start_idx, span=3):
    """Return {S.No: line} for rows 1..36 from the `span` pages beginning at the page whose header matches."""
    i0 = find_page(pages, header, after=100)
    txt = "\n".join(pages[i0:i0 + span])
    rows = {}
    for l in txt.splitlines():
        m = re.match(r"\s*(\d{1,2})\s+(.*)$", l)
        if not m:
            continue
        toks = m.group(2).split()
        is_header = toks and all(t.isdigit() for t in toks) and [int(t) for t in toks] == list(range(2, 2 + len(toks)))
        if 1 <= int(m.group(1)) <= 36 and int(m.group(1)) not in rows and re.search(r"\d", m.group(2)) and not is_header:
            rows[int(m.group(1))] = m.group(2)
    return rows, i0


def strip_name(rest: str) -> str:
    """Drop the leading state-name words but keep an 'NA' (not available) data token."""
    return re.sub(r"^(?:(?!NA\b)[A-Za-z&.]+\s+)+", "", rest.strip() + " ")


def state_ints(rest: str) -> list[float]:
    """Whole-number tokens of a state row in position. 'NA' -> NaN (not available), '-' -> 0 (none reported)."""
    out = []
    for t in rest.split():
        if re.fullmatch(r"\d[\d,]*", t):
            out.append(int(t.replace(",", "")))
        elif t == "NA":
            out.append(float("nan"))
        elif t == "-":
            out.append(0)
    return out


def state_table(pages) -> pd.DataFrame:
    acc, i_acc = state_rows(pages, r"Annexure 2\s*\n\s*Total Number of Road Accidents in India", 0, 1)
    kil, i_kil = state_rows(pages, r"Annexure 3\s*\n\s*Total Number of Persons Killed in Road Accidents in India", 0, 1)
    sev, i_sev = state_rows(pages, r"Annexure 6\s*\n\s*Severity", 0, 1)
    out = []
    for k, name in enumerate(STATES, start=1):
        a = state_ints(strip_name(acc[k]))
        d = state_ints(strip_name(kil[k]))
        s = [float("nan") if t == "NA" else float(t) for t in sev[k].split() if re.fullmatch(r"\d+\.\d|NA", t)]
        # Annexure 2/3: 2020..2023 counts then rank; Annexure 6: 2020..2023 severity, rank
        out.append({"state": name, "accidents_2023": int(a[3]), "killed_2023": int(d[3]), "severity_published_2023": s[3]})
    df = pd.DataFrame(out)
    df["severity_computed_2023"] = (df["killed_2023"] / df["accidents_2023"] * 100).round(1)
    df["source"] = f"{SOURCE}; Annexures 2, 3, 6 (PDF pages {i_acc + 1}, {i_kil + 1}, {i_sev + 1})"
    return df


def validate(T: dict[str, pd.DataFrame]) -> dict:
    checks = {}
    for k in ["weather", "road_feature", "junction", "traffic_control", "road_category", "area", "month"]:
        d = T[k]
        assert d["accidents_2023"].sum() == TOTALS_2023["accidents"], (k, d["accidents_2023"].sum())
        assert d["killed_2023"].sum() == TOTALS_2023["killed"], (k, d["killed_2023"].sum())
        checks[k] = "sum(accidents)=480,583 and sum(killed)=172,890 match the printed national totals"
    tod = T["time_of_day"]["accidents_2023"].sum()
    assert tod + 5761 == TOTALS_2023["accidents"], "time-of-day blocks + 5,761 unknown-time != national total"
    checks["time_of_day"] = "8 blocks + 5,761 unknown-time = 480,583"
    s = T["state"]
    assert s["accidents_2023"].sum() == TOTALS_2023["accidents"], s["accidents_2023"].sum()
    assert s["killed_2023"].sum() == TOTALS_2023["killed"], s["killed_2023"].sum()
    pub = s["severity_published_2023"].fillna(-1)
    bad = s[(pub - s["severity_computed_2023"]).abs() > 0.11]
    assert bad.empty, f"computed vs published state severity mismatch:\n{bad}"
    checks["state"] = "36 states/UTs; accidents and killed sum to national totals; deaths/100 accidents recomputed from " \
                      "raw counts equals the published Annexure 6 value for every state (+/-0.1)"
    return checks


if __name__ == "__main__":
    T = build()
    checks = validate(T)
    PROC.mkdir(parents=True, exist_ok=True)
    for name, df in T.items():
        df.to_csv(PROC / f"{name}_2023.csv", index=False)
    print("All tables parsed and reconciled:")
    for k, v in checks.items():
        print(f"  {k:16s} {v}")
    w = T["weather"].assign(rate=lambda d: (d.killed_2023 / d.accidents_2023 * 100).round(1))
    print(w[["category", "accidents_2023", "killed_2023", "rate"]].to_string(index=False))
