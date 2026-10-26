/* =========================================================
   main.js — puts every chart on the page.
   To add a chart: create specs/cXX_name.vg.json, add a
   <div id="cXX" class="chart"></div> in index.html, then add
   one line to the CHARTS list below.
   ========================================================= */

// Shared look for every chart, so each spec file stays short and readable.
const VEGA_CONFIG = {
  font: "Bricolage Grotesque, Avenir Next, Segoe UI, system-ui, sans-serif",
  background: null,                       // transparent: the page colour shows through
  view: { stroke: null },
  title: {
    anchor: "start", fontSize: 18, fontWeight: 800, color: "#1E2621",
    subtitleFontSize: 13, subtitleColor: "#5A635D", subtitlePadding: 6, offset: 18
  },
  axis: {
    labelColor: "#5A635D", titleColor: "#5A635D", labelFontSize: 12, titleFontSize: 12,
    titleFontWeight: 600, domainColor: "#C4CAC1", tickColor: "#C4CAC1", gridColor: "#E1E5DE"
  },
  legend: { labelColor: "#5A635D", titleColor: "#1E2621", labelFontSize: 12, titleFontSize: 12 },
  text: { color: "#1E2621" }
};

const CHARTS = [
  { id: "c01", spec: "specs/c01_isotype.vg.json" },
  { id: "c02", spec: "specs/c02_consumption_lines.vg.json" },
  { id: "c03", spec: "specs/c03_cpi_slope.vg.json" },
  { id: "c04", spec: "specs/c04_sector_bump.vg.json" },
  { id: "c05", spec: "specs/c05_waterfall.vg.json" },
  { id: "c06", spec: "specs/c06_treemap.vg.json" },        // Vega (not Vega-Lite)
  { id: "c07", spec: "specs/c07_choropleth.vg.json" },     // map 1
  { id: "c08", spec: "specs/c08_state_symbols.vg.json" },  // map 2
  { id: "c09", spec: "specs/c09_dot_density.vg.json" },    // map 3
  { id: "c10", spec: "specs/c10_state_heatmap.vg.json" },
  { id: "c11", spec: "specs/c11_horizon.vg.json" },
  { id: "c12", spec: "specs/c12_sa4_lollipop.vg.json" },
];

CHARTS.forEach(({ id, spec }) => {
  vegaEmbed("#" + id, spec, { actions: false, config: { font: "Bricolage Grotesque", background: null }, renderer: "svg", config: VEGA_CONFIG })
    .catch(err => {
      console.error(id, err);
      document.getElementById(id).innerHTML =
        `<p class="chart-error">Chart ${id} could not load: ${err.message}. ` +
        `Open the page through http://localhost:8000, not by double-clicking the file.</p>`;
    });
});
