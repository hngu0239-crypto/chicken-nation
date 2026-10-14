"""
prepare_data.py
===============
Turns the raw ABARES / ABS spreadsheets in  raw/  into small, tidy CSV files in
data/  that the Vega-Lite charts read. Maps are built by build_maps.py.

HOW TO RUN (from the project folder, in Terminal):
    python3 scripts/prepare_data.py

RULES THIS SCRIPT FOLLOWS (so you can defend it in the interview):
  * It never edits a number. It only selects rows/columns, reshapes tables
    (wide -> long), adds quarters into financial years, ranks, and divides
    where a chart needs a ratio or a percentage.
  * Units are converted only for readability ($ -> $ million, tonnes -> kt).
  * Every output file is described in data/README.md.
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "raw"
OUT = ROOT / "data"
OUT.mkdir(exist_ok=True)


def save(df, name):
    """Write a CSV and print a one-line summary."""
    df.to_csv(OUT / name, index=False)
    print(f"  {name:32s} {len(df):5d} rows  {(OUT / name).stat().st_size / 1024:6.1f} KB")


def fy(year_end):
    """2026 -> '2025-26' (Australian financial year ending 30 June)."""
    return f"{year_end - 1}-{str(year_end)[2:]}"


print("Writing data files:")

# =============================================================================
# SOURCE A: ABARES Agricultural Commodity Statistics 2025 — Meat General tables
#           raw/12_ACS2024_25_Meat-GeneralTables_v1_0_0.xlsx, sheet "MeatGeneral"
#           Header information sits in rows 0-10; yearly data start at row 11.
# =============================================================================
mg = pd.read_excel(RAW / "12_ACS2024_25_Meat-GeneralTables_v1_0_0.xlsx",
                   sheet_name="MeatGeneral", header=None)
years = mg.iloc[11:].copy()
years = years[years[0].astype(str).str.match(r"^\d{4}")]       # keep only year rows
years["year"] = years[0].astype(str).str.replace("–", "-")     # 1974–75 -> 1974-75
years["year_start"] = years["year"].str[:4].astype(int)

# --- C1 + C2: apparent consumption per person (kg), Table 12.1, columns 6-9 ---
cons = years[["year", "year_start", 6, 7, 8, 9]].rename(
    columns={6: "Beef & veal", 7: "Sheep meat", 8: "Pig meat", 9: "Chicken"})
cons = cons.melt(id_vars=["year", "year_start"], var_name="meat", value_name="kg")
cons = cons.dropna(subset=["kg"])                 # sheep meat only starts in 1988-89
cons["kg"] = cons["kg"].astype(float).round(1)
save(cons, "c01_c02_consumption.csv")

# --- C3: Consumer Price Index by meat, Table 12.3, columns 23-27 -------------
# ABARES publishes every index with 2011-12 = 100, so the RAW index numbers of
# two meats cannot be compared with each other. We "re-base" each series so the
# first year = 100: then every line starts at the same point and the end value
# reads as "how many times more expensive". Pork only starts in 1980-81, so
# 1980-81 is the first year with all four meats.
cpi = years.set_index("year")[[23, 24, 25, 26, 27]].astype(float)
cpi.columns = ["All prices (average)", "Beef & veal", "Lamb", "Pork", "Chicken"]
BASE, LATEST = "1980-81", "2024-25"
rows = []
for item in cpi.columns:
    for y in (BASE, LATEST):
        rows.append({"item": item, "year": y,
                     "index": round(100 * cpi.loc[y, item] / cpi.loc[BASE, item], 1)})
slope = pd.DataFrame(rows)
slope["times"] = (slope["index"] / 100).round(1)
slope["is_reference"] = slope["item"].eq("All prices (average)")
save(slope, "c03_cpi_slope.csv")

# =============================================================================
# SOURCE B: ABS Australian Agriculture: Livestock, 2024-25 (AALDC)
#           Table 1 = livestock disposals (animals sold), Table 2 = products
#           Values are LOCAL value in dollars.
# =============================================================================
AALDC = RAW / "AALDC_Value_of_livestock_and_products_2024-25.xlsx"
YEARS = ["2020-21", "2021-22", "2022-23", "2023-24", "2024-25"]


def read_aaldc(sheet):
    t = pd.read_excel(AALDC, sheet_name=sheet, header=3).iloc[:, :8]
    t = t[t["Region"].notna() & (t["Region"] != "Footnotes")]
    t.columns = ["region", "code", "item"] + YEARS     # "2020-21(a)" -> "2020-21"
    return t


t1, t2 = read_aaldc("Table 1"), read_aaldc("Table 2")
sector_names = {  # short, plain-English names for the general audience
    "Cattle disposals": "Cattle", "Sheep disposals": "Sheep & lambs",
    "Pig disposals": "Pigs", "Poultry disposals": "Poultry (meat)",
    "Wool": "Wool", "Milk": "Milk"}
group_of = {"Cattle": "Animals sold", "Sheep & lambs": "Animals sold",
            "Pigs": "Animals sold", "Poultry (meat)": "Animals sold",
            "Wool": "Products", "Milk": "Products"}

nat = pd.concat([t1, t2])
nat = nat[nat["region"] == "Australia"].copy()
nat["sector"] = nat["item"].str.split(" - ").str[0].map(sector_names)
nat = nat.dropna(subset=["sector"])          # drops "All other livestock n.e.c." (tiny)
nat = nat.melt(id_vars=["sector"], value_vars=YEARS, var_name="year", value_name="value")
nat["value_m"] = (nat["value"].astype(float) / 1e6).round(1)
nat = nat.drop(columns="value")

# --- C4: bump chart — rank of the six sectors each year ----------------------
bump = nat.copy()
bump["rank"] = bump.groupby("year")["value_m"].rank(ascending=False, method="first").astype(int)
save(bump.sort_values(["year", "rank"]), "c04_sector_rank.csv")

# --- C5: waterfall — contribution of each sector to the change in total ------
# A waterfall needs, for every bar, where it STARTS and where it ENDS.
# Bar 1 = total in 2020-21; then one bar per sector (its change); last bar = total 2024-25.
wide = nat.pivot(index="sector", columns="year", values="value_m")
change = (wide["2024-25"] - wide["2020-21"]).sort_values(ascending=False)
steps, running = [], wide["2020-21"].sum()
steps.append({"order": 0, "label": "Total 2020-21", "kind": "total",
              "start": 0, "end": round(running, 1), "change_m": round(running, 1)})
for i, (sector, delta) in enumerate(change.items(), start=1):
    steps.append({"order": i, "label": sector,
                  "kind": "increase" if delta >= 0 else "decrease",
                  "start": round(running, 1), "end": round(running + delta, 1),
                  "change_m": round(delta, 1)})
    running += delta
steps.append({"order": len(steps), "label": "Total 2024-25", "kind": "total",
              "start": 0, "end": round(running, 1), "change_m": round(running, 1)})
save(pd.DataFrame(steps), "c05_waterfall.csv")

# --- C6 (option A): treemap, two levels — group > sector, 2024-25 -------------
tm = nat[nat["year"] == "2024-25"].copy()
tm["group"] = tm["sector"].map(group_of)
tm["share_pct"] = (100 * tm["value_m"] / tm["value_m"].sum()).round(1)
save(tm[["group", "sector", "value_m", "share_pct"]], "c06_treemap.csv")

# --- C8: proportional symbols — poultry (meat) value by state, 2024-25 --------
pos = {  # label position = rough visual centre of each state (lon, lat)
    "New South Wales": ("NSW", 146.9, -32.2), "Victoria": ("Vic", 144.3, -36.9),
    "Queensland": ("Qld", 144.5, -22.5), "South Australia": ("SA", 135.5, -30.0),
    "Western Australia": ("WA", 121.5, -26.0), "Tasmania": ("Tas", 146.6, -42.0),
    "Northern Territory": ("NT", 133.4, -19.5),
    "Australian Capital Territory": ("ACT", 149.1, -35.3)}
poul = t1[t1["item"].str.startswith("Poultry") & (t1["region"] != "Australia")]
poul = poul.set_index("region")["2024-25"]
st = []
for state, (abbr, lon, lat) in pos.items():
    raw = poul.get(state, "np")        # NT has no poultry row at all -> treat as np
    published = str(raw) != "np"
    st.append({"state": state, "abbr": abbr, "lon": lon, "lat": lat,
               "published": published,
               "value_m": round(float(raw) / 1e6, 1) if published else None})
save(pd.DataFrame(st), "c08_state_poultry_2024_25.csv")

# =============================================================================
# SOURCE C: ABS 7215.0 Livestock Products, Australia (time series workbooks)
#           Columns 1-6 = ORIGINAL series, 7-12 = seasonally adjusted, 13-18 = trend.
#           We always use ORIGINAL (the actual counts/tonnes).
# =============================================================================
def read_7215(fname):
    d = pd.read_excel(RAW / fname, sheet_name="Data1", header=None)
    names = [str(x).split(";")[1].strip() for x in d.iloc[0, 1:7]]
    data = d.iloc[10:, :7].copy()
    data.columns = ["date"] + names
    data["date"] = pd.to_datetime(data["date"])
    for c in names:
        data[c] = pd.to_numeric(data[c], errors="coerce")
    return data


# --- C10: heatmap — chicken meat produced by state and financial year ---------
t15 = read_7215("7215015.xlsx")             # quarterly, tonnes
t15["fy_end"] = t15["date"].dt.year + (t15["date"].dt.month >= 7).astype(int)
states = ["New South Wales", "Victoria", "Queensland", "South Australia", "Western Australia"]
heat = []
for state in states:
    q = t15[["fy_end", state]].dropna()
    n = q.groupby("fy_end")[state].count()
    full = n[n == 4].index                   # keep only years with all 4 quarters
    yearly = q[q["fy_end"].isin(full)].groupby("fy_end")[state].sum()
    for y, tonnes in yearly.items():
        heat.append({"state": state, "fy": fy(y), "fy_end": y, "kt": round(tonnes / 1000, 1)})
heat = pd.DataFrame(heat).sort_values(["state", "fy_end"])
# change vs the previous year (only when the previous year exists)
prev = heat.groupby("state")["kt"].shift(1)
gap = heat["fy_end"] - heat.groupby("state")["fy_end"].shift(1)
heat["change_pct"] = ((heat["kt"] / prev - 1) * 100).where(gap == 1).round(1)
save(heat, "c10_state_meat_heatmap.csv")

# --- C11: national chickens slaughtered each year (Table 18, annual) -----------
t18 = read_7215("7215018.xlsx")             # annual, '000 birds, year ending June
nat18 = pd.DataFrame({"fy_end": t18["date"].dt.year,
                      "million_birds": (t18["Total (State)"] / 1000).round(1)})
nat18["fy"] = nat18["fy_end"].map(fy)
nat18["change_pct"] = (nat18["million_birds"].pct_change() * 100).round(1)
# option A (horizon chart) uses change_pct; option B (connected scatter) also
# needs kg of meat per bird = national meat produced / birds slaughtered
meat_fy = t15.groupby("fy_end")["Total (State)"].agg(["sum", "count"])
meat_fy = meat_fy[meat_fy["count"] == 4]["sum"]
nat18["kt_meat"] = nat18["fy_end"].map(meat_fy / 1000).round(1)
nat18["kg_per_bird"] = (nat18["kt_meat"] / nat18["million_birds"]).round(2)  # kt / million = kg
save(nat18[["fy", "fy_end", "million_birds", "change_pct", "kt_meat", "kg_per_bird"]],
     "c11_national_birds.csv")


# --- C11 (horizon chart): yearly % change in chickens slaughtered, Australia + 3 states
regions = ["Australia", "New South Wales", "Victoria", "Queensland"]
hz = t18.rename(columns={"Total (State)": "Australia"})
hz = hz[["date"] + regions].copy()
hz["fy_end"] = hz["date"].dt.year
hz = hz.melt(id_vars=["fy_end"], value_vars=regions, var_name="region", value_name="birds_000")
hz = hz.sort_values(["region", "fy_end"])
hz["change_pct"] = (hz.groupby("region")["birds_000"].pct_change() * 100).round(1)
hz["million_birds"] = (hz["birds_000"] / 1000).round(1)
hz["fy"] = hz["fy_end"].map(fy)
hz = hz.dropna(subset=["change_pct"])
save(hz[["region", "fy", "fy_end", "million_birds", "change_pct"]], "c11_horizon_change.csv")

# =============================================================================
# SOURCE D: ABS Value of Agricultural Commodities Produced 2021-22 (national/state)
#           Only needed for option B of chart 6 (waffle: chicken meat vs eggs),
#           because the 2024-25 AALDC tables no longer include eggs.
# =============================================================================
v = pd.read_excel(RAW / "VACPDCNAT_STATE202122.xlsx", sheet_name="Table 1",
                  header=None, skiprows=7).iloc[:, :8]
v.columns = ["code", "region", "ccode", "item", "gross", "gross_rse", "local", "local_rse"]
aus = v[v["code"].astype(str) == "0"]
meat = float(aus.loc[aus["item"].str.endswith("- Poultry"), "local"].iloc[0])
eggs = float(aus.loc[aus["item"].str.endswith("- Eggs"), "local"].iloc[0])
meat_squares = round(100 * meat / (meat + eggs))
waffle = pd.DataFrame([{"id": i, "col": i % 10, "row": i // 10,
                        "type": "Chicken meat" if i < meat_squares else "Eggs"}
                       for i in range(100)])
waffle["meat_m"], waffle["eggs_m"] = round(meat / 1e6), round(eggs / 1e6)
save(waffle, "c06b_waffle_meat_eggs.csv")

print("Done. Now run:  python3 scripts/build_maps.py")
