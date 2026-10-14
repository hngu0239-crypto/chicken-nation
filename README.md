# The Chicken Nation — FIT3179 Data Visualisation 2

How chicken became Australia's favourite meat. Built with Vega-Lite.

Author: Lê Hồng Nhung · 2026

## Folder structure
```
index.html        the web page
css/style.css     layout and typography
js/main.js        loads every chart into the page
specs/            one Vega-Lite spec (.vg.json) per chart
data/             small, tidy data files read by the charts (see data/README.md)
raw/              original downloads from ABARES and the ABS (never edited)
scripts/          Python scripts that turn raw/ into data/
lib/              Vega, Vega-Lite, Vega-Embed (local copies, so it works offline)
sketch/           hand-drawn sketch (PDF)
```

## Rebuild the data
```
pip3 install -r requirements.txt
python3 scripts/prepare_data.py
python3 scripts/build_maps.py
```

## View locally
```
python3 -m http.server 8000
```
then open http://localhost:8000

## Data sources
* ABARES, Agricultural Commodity Statistics 2025 — Meat general tables (Tables 12.1, 12.3)
* ABS, Livestock Products, Australia (cat. 7215.0) — Tables 8, 15, 18
* ABS, Australian Agriculture: Livestock, 2024-25 — Tables 1 & 2
* ABS, Value of Agricultural Commodities Produced, Australia, 2020-21 (by ASGS region) and 2021-22
* ABS, Australian Statistical Geography Standard (ASGS) Edition 3, SA4 2021 boundaries, via the absmapsdata package

(Add the exact URLs of each page you downloaded from.)
