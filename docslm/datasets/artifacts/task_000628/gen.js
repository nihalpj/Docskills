// DocSLM pptx create — pptxgenjs (report)
const pptxgen = require("pptxgenjs");
const pptx = new pptxgen();
pptx.defineLayout({ name: "WIDE", width: 13.33, height: 7.5 });
pptx.layout = "WIDE";
const PRIMARY = "33544A", ACCENT = "5B8C74", LIGHT = "E3EFE7";

function titleBar(slide, text) {
  slide.addText(text, { x: 0, y: 0, w: 13.33, h: 0.9, fill: { color: PRIMARY },
    fontSize: 24, bold: true, color: "FFFFFF", align: "left", margin: 12 });
}

// Slide 1 — title
const s1 = pptx.addSlide();
s1.addText("Quarterly Business Review", { x: 0.8, y: 2.4, w: 11.7, h: 1.3, fontSize: 40, bold: true,
  color: PRIMARY, align: "center" });
s1.addText("Meridian Health · 2026-09", { x: 0.8, y: 3.7, w: 11.7, h: 0.8, fontSize: 20,
  color: "666666", align: "center" });
s1.background = { color: LIGHT };

{
  const s = pptx.addSlide();
  titleBar(s, "Performance Analysis");
  s.addText([
    { text: "We recommend expanding channel investment and rebalancing resourcing to sustain growth", options: { bullet: true } },
    { text: "Cross-team efficiency rose and delivery lead times shortened versus last quarter", options: { bullet: true } },
    { text: "Revenue concentration in the main product line increased and retention improved.", options: { bullet: true } }
  ], { x: 0.7, y: 1.3, w: 12, h: 5.4, fontSize: 16, color: "333333", lineSpacingMultiple: 1.2 });
}
{
  const s = pptx.addSlide();
  titleBar(s, "Key Project Updates");
  s.addText([
    { text: "We recommend expanding channel investment and rebalancing resourcing to sustain growth", options: { bullet: true } },
    { text: "Revenue concentration in the main product line increased and retention improved", options: { bullet: true } },
    { text: "Cross-team efficiency rose and delivery lead times shortened versus last quarter.", options: { bullet: true } }
  ], { x: 0.7, y: 1.3, w: 12, h: 5.4, fontSize: 16, color: "333333", lineSpacingMultiple: 1.2 });
}
{
  const s = pptx.addSlide();
  titleBar(s, "Key Numbers");
  const rows = [
    [{ text: "Item", options: { bold: true, color: "FFFFFF", fill: { color: PRIMARY } } }, { text: "Revenue (k)", options: { bold: true, color: "FFFFFF", fill: { color: PRIMARY } } }, { text: "YoY", options: { bold: true, color: "FFFFFF", fill: { color: PRIMARY } } }],
    ["Pulse Dashboard", "646", "0.156"],
    ["Orbit CRM", "325", "0.237"],
    ["Marketing", "613", "0.359"],
    ["Pulse Dashboard", "672", "0.12"]
  ];
  s.addTable(rows, { x: 0.7, y: 1.4, w: 12, colW: [5, 3.5, 3.5],
    border: { pt: 1, color: "CCCCCC" }, fontSize: 13, rowH: 0.5 });
}
{
  const s = pptx.addSlide();
  titleBar(s, "Revenue Trend");
  s.addChart(pptx.ChartType.bar, [{ name: "Revenue", labels: ["Pulse Dashboard", "Orbit CRM", "Marketing", "Pulse Dashboard"], values: [646, 325, 613, 672] }],
    { x: 0.9, y: 1.4, w: 11.5, h: 5.3, barDir: "col", chartColors: [PRIMARY, ACCENT] });
}

pptx.writeFile({ fileName: "task_000628_deck.pptx" }).then(() => {
  console.log(JSON.stringify({ exit: 0, artifact: "task_000628_deck.pptx" }));
}).catch((e) => { console.error(e.message); process.exit(1); });
