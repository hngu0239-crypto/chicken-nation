# Data dictionary

All files are created by `scripts/prepare_data.py` and `scripts/build_maps.py`
from the original files in `raw/`. Nothing is typed in by hand.
Money values are in **$ million** (`_m`), nominal (not adjusted for inflation).

| File | Chart | Source | Columns |
|---|---|---|---|
| c01_c02_consumption.csv | 1 Isotype, 2 Multi-line | ABARES ACS 2025, Table 12.1 | year, year_start, meat, kg (apparent consumption per person) |
| c03_cpi_slope.csv | 3 Slope | ABARES ACS 2025, Table 12.3 (ABS CPI) | item, year, index (1980-81 = 100), times, is_reference |
| c04_sector_rank.csv | 4 Bump | ABS Australian Agriculture: Livestock 2024-25, Tables 1 & 2 | sector, year, value_m (local value), rank |
| c05_waterfall.csv | 5 Waterfall | same as above | order, label, kind, start, end, change_m |
| c06_treemap.csv | 6 Treemap (option A) | same as above, 2024-25 | group, sector, value_m, share_pct |
| c06b_waffle_meat_eggs.csv | 6 Waffle (option B) | ABS VACP 2021-22, Australia | id, col, row, type, meat_m, eggs_m |
| c07_sa4_poultry.geojson | 7 Choropleth | ABS VACP 2020-21 by ASGS + ABS SA4 2021 boundaries | per SA4: name, state, area_km2, meat_m, eggs_m, *_status (ok / np / none), *_note (ABS reliability), *_per_km2 |
| states.geojson | 7, 8, 9 (base map) | ABS SA4 2021 boundaries merged by state | state, abbr |
| c08_state_poultry_2024_25.csv | 8 Proportional symbol | ABS Livestock 2024-25, Table 1 | state, abbr, lon, lat, published, value_m |
| c09_poultry_dots.csv | 9 Dot density | ABS VACP 2020-21 by ASGS | lon, lat, type, region (1 dot = $5 million, random position inside its SA4) |
| c10_state_meat_heatmap.csv | 10 Heatmap | ABS 7215.0 Table 15 (original series) | state, fy, fy_end, kt (thousand tonnes of chicken meat), change_pct vs previous year |
| c11_national_birds.csv | 11 Horizon (A) / Connected scatter (B) | ABS 7215.0 Tables 18 & 15 | fy, fy_end, million_birds, change_pct, kt_meat, kg_per_bird |
| c11_horizon_change.csv | 11 Horizon | ABS 7215.0 Table 18 | region (Australia, NSW, Vic, Qld), fy, fy_end, million_birds, change_pct vs previous year |
| c12_sa4_ranking.csv | 12 Lollipop | ABS VACP 2020-21 by ASGS | region, state, meat_m, note, share_pct (of published regions), rank |

## Known gaps (write these on the page, they are part of an honest story)
* **np** = "not published": the ABS hides figures that could reveal a single large business.
  Chicken meat is np for every SA4 in SA and WA, and for the SA, WA, Tas and NT state totals in 2024-25.
* ABS 7215.0 chicken meat by state: SA and WA stop after 1996-97; Tas, NT and ACT are never shown.
* ABS reliability flags in VACP: "use with caution" (^) and "unreliable" (*).
* AALDC 2024-25 has no egg data, so the meat-vs-eggs comparison uses VACP 2021-22.
* Around 2010-11 there is a jump in chicken meat figures: check the ABS 7215.0 explanatory notes before describing it.
