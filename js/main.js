/* =========================================================
   main.js — puts every chart on the page.
   To add a chart: create specs/cXX_name.vg.json, add a
   <div id="cXX" class="chart"></div> in index.html, then add
   one line to the CHARTS list below.
   ========================================================= */

// Shared look for every chart, so each spec file stays short and readable.
// One font for all chart text, matching the page: Bricolage Grotesque.
// "sans-serif" is only a safety net if the web font fails to load.
const VEGA_CONFIG = {
  font: "Bricolage Grotesque, sans-serif",
  background: null,                       // transparent: the section colour shows through
  view: { stroke: null },
  title: {
    anchor: "start", fontSize: 18, fontWeight: 800, color: "#26382F",
    subtitleFontSize: 13, subtitleColor: "#535C56", subtitlePadding: 6, offset: 18
  },
  axis: {
    labelColor: "#535C56", titleColor: "#535C56", labelFontSize: 12, titleFontSize: 12,
    titleFontWeight: 600, domainColor: "#C4CAC1", tickColor: "#C4CAC1",
    gridColor: "#E4E2D9", gridWidth: 0.75
  },
  legend: { labelColor: "#535C56", titleColor: "#26382F", labelFontSize: 12, titleFontSize: 12 },
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

function embedChart({ id, spec }) {
  return vegaEmbed("#" + id, spec, { actions: false, renderer: "svg", config: VEGA_CONFIG })
    .catch(err => {
      console.error(id, err);
      document.getElementById(id).innerHTML =
        `<p class="chart-error">Chart ${id} could not load: ${err.message}. ` +
        `Open the page through http://localhost:8000, not by double-clicking the file.</p>`;
    });
}

// Wait until Bricolage Grotesque has loaded, so charts are drawn (and their
// labels measured) with the right font rather than a temporary fallback.
const fontsReady = document.fonts && document.fonts.ready
  ? document.fonts.ready
  : Promise.resolve();

fontsReady.then(() => CHARTS.forEach(embedChart));