"""
build_maps.py
=============
Builds the data for the three maps and the SA4 lollipop chart.

INPUTS
  raw/VACPDCASGS202021.xlsx       ABS Value of Agricultural Commodities Produced,
                                  2020-21, by ASGS region (latest regional data:
                                  it comes from the 2020-21 Agricultural Census)
  raw/boundaries/sa42021.rda      ABS ASGS Edition 3 (2021) SA4 boundaries, as
                                  packaged in the open-source R package absmapsdata
                                  (github.com/wfmackey/absmapsdata). Download once:
  https://raw.githubusercontent.com/wfmackey/absmapsdata/master/data/sa42021.rda

OUTPUTS (in data/)
  states.geojson               state outlines (SA4s merged)        -> maps 7, 8, 9
  c07_sa4_poultry.geojson      SA4 shapes + value + $ per km2      -> chart 7 choropleth
  c09_poultry_dots.csv         1 dot = $5 million                  -> chart 9 dot density
  c12_sa4_ranking.csv          SA4 regions ranked by meat value    -> chart 12 lollipop

RUN:  pip3 install rdata shapely      (once)
      python3 scripts/build_maps.py

All values are LOCAL value (the same measure as the AALDC tables).
"""
import json
import random
from pathlib import Path

import pandas as pd
import rdata
import shapely
from shapely.geometry import MultiPolygon, Point, Polygon, mapping
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent.parent
RAW, OUT = ROOT / "raw", ROOT / "data"
RDA = RAW / "boundaries" / "sa42021.rda"
SIMPLIFY = 0.02      # degrees (~2 km). Bigger number = smaller file, rougher coastline
DOT_VALUE = 5e6      # chart 9: one dot = $5 million
random.seed(3179)    # fixed seed -> identical dots every run

if not RDA.exists():
    raise SystemExit(f"Missing {RDA}. Download it once (see the top of this file).")


def to_geojson_geometry(geom):
    """Round coordinates to 0.001 degrees (~100 m) to keep the file small, drop
    tiny slivers, and make every OUTER ring run clockwise. Vega/d3 draw on a
    sphere: a ring in the wrong direction fills the whole map instead of the region."""
    geom = shapely.set_precision(geom, 0.001).buffer(0)
    parts = [geom] if geom.geom_type == "Polygon" else list(getattr(geom, "geoms", []))
    parts = [orient(p, sign=-1.0) for p in parts if p.geom_type == "Polygon" and p.area > 1e-5]
    return mapping(MultiPolygon(parts))


# ---- 1. read SA4 boundaries --------------------------------------------------
sa4 = rdata.conversion.convert(rdata.parser.parse_file(RDA), default_encoding="utf8")["sa42021"]
regions = {}
for _, r in sa4.iterrows():
    g = r["geometry"]
    if g is None or len(g) == 0:          # "No usual address", "Migratory" have no shape
        continue
    polys = [Polygon(ring[0], ring[1:]) for ring in g if len(ring[0]) >= 4]
    if not polys or str(r["state_name_2021"]) == "Other Territories":
        continue                          # skip Christmas Is., Norfolk Is. etc.
    regions[str(r["sa4_code_2021"])] = {
        "shape": MultiPolygon(polys).buffer(0), "name": str(r["sa4_name_2021"]),
        "state": str(r["state_name_2021"]), "area_km2": float(r["areasqkm_2021"])}

# ---- 2. read VACP values per SA4 (3-digit region codes) ---------------------
t = pd.read_excel(RAW / "VACPDCASGS202021.xlsx", sheet_name="Table 1",
                  header=None, skiprows=7).iloc[:, :8]
t.columns = ["code", "region", "ccode", "item", "gross", "gross_rse", "local", "local_rse"]
t["code"] = t["code"].astype(str)
t = t[t["code"].str.len() == 3]
RSE = {"^": "use with caution", "*": "unreliable"}   # ABS reliability flags


def lookup(code, ending):
    """Return (value in $, status, reliability note) for one SA4 and product."""
    row = t[(t["code"] == code) & t["item"].str.endswith(ending)]
    if row.empty:
        return 0.0, "none", ""            # no row = no production recorded
    val, flag = row["local"].iloc[0], row["local_rse"].iloc[0]
    if str(val).strip() == "np":
        return None, "np", ""             # not published (confidential)
    return float(val), "ok", RSE.get(str(flag), "")


# ---- 3. build the SA4 file, the dots and the ranking ------------------------
features, dots, ranking = [], [], []
for code, d in regions.items():
    meat, meat_status, meat_note = lookup(code, "- Poultry")
    eggs, eggs_status, eggs_note = lookup(code, "- Eggs")
    props = {
        "code": code, "name": d["name"], "state": d["state"], "area_km2": round(d["area_km2"]),
        "meat_m": None if meat is None else round(meat / 1e6, 2), "meat_status": meat_status,
        "meat_note": meat_note,
        "eggs_m": None if eggs is None else round(eggs / 1e6, 2), "eggs_status": eggs_status,
        "eggs_note": eggs_note,
        # Choropleths must show a RATE, not a total: $ of production per km2
        "meat_per_km2": None if meat is None else round(meat / d["area_km2"]),
        "eggs_per_km2": None if eggs is None else round(eggs / d["area_km2"]),
    }
    simple = d["shape"].simplify(SIMPLIFY, preserve_topology=True)
    features.append({"type": "Feature", "properties": props,
                     "geometry": to_geojson_geometry(simple)})

    if meat:
        ranking.append({"region": d["name"], "state": d["state"],
                        "meat_m": round(meat / 1e6, 1), "note": meat_note})

    for product, value in (("Chicken meat", meat), ("Eggs", eggs)):
        if not value:
            continue
        minx, miny, maxx, maxy = d["shape"].bounds
        for _ in range(round(value / DOT_VALUE)):
            while True:   # random point; keep it only if it falls inside the region
                p = Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
                if d["shape"].contains(p):
                    break
            dots.append({"lon": round(p.x, 3), "lat": round(p.y, 3),
                         "type": product, "region": d["name"]})

with open(OUT / "c07_sa4_poultry.geojson", "w") as f:
    json.dump({"type": "FeatureCollection", "features": features}, f, separators=(",", ":"))
pd.DataFrame(dots).to_csv(OUT / "c09_poultry_dots.csv", index=False)

rank = pd.DataFrame(ranking).sort_values("meat_m", ascending=False)
rank["share_pct"] = (100 * rank["meat_m"] / rank["meat_m"].sum()).round(1)  # of PUBLISHED regions
rank["rank"] = range(1, len(rank) + 1)
rank.to_csv(OUT / "c12_sa4_ranking.csv", index=False)

# ---- 4. state outlines: merge the SA4 shapes of each state ------------------
abbr = {"New South Wales": "NSW", "Victoria": "Vic", "Queensland": "Qld",
        "South Australia": "SA", "Western Australia": "WA", "Tasmania": "Tas",
        "Northern Territory": "NT", "Australian Capital Territory": "ACT"}
state_features = []
for state, ab in abbr.items():
    merged = unary_union([d["shape"].buffer(0.01) for d in regions.values()
                          if d["state"] == state]).buffer(-0.01)
    merged = merged.simplify(SIMPLIFY * 1.5, preserve_topology=True)
    state_features.append({"type": "Feature", "properties": {"state": state, "abbr": ab},
                           "geometry": to_geojson_geometry(merged)})
with open(OUT / "states.geojson", "w") as f:
    json.dump({"type": "FeatureCollection", "features": state_features}, f, separators=(",", ":"))

print(f"{len(features)} SA4 regions, {len(dots)} dots, {len(rank)} regions ranked")
for name in ["states.geojson", "c07_sa4_poultry.geojson", "c09_poultry_dots.csv", "c12_sa4_ranking.csv"]:
    print(f"  {name:32s} {(OUT / name).stat().st_size / 1024:7.1f} KB")
