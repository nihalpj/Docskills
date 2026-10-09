"""PPTX generator (pptxgenjs via Node) — English-only."""
from string import Template
import json as _json
from .. import content as C

_CREATE = Template("""// DocSLM pptx create — pptxgenjs ($scene)
const pptxgen = require("pptxgenjs");
const pptx = new pptxgen();
pptx.defineLayout({ name: "WIDE", width: 13.33, height: 7.5 });
pptx.layout = "WIDE";
const PRIMARY = "$primary", ACCENT = "$accent", LIGHT = "$light";

function titleBar(slide, text) {
  slide.addText(text, { x: 0, y: 0, w: 13.33, h: 0.9, fill: { color: PRIMARY },
    fontSize: 24, bold: true, color: "FFFFFF", align: "left", margin: 12 });
}

// Slide 1 — title
const s1 = pptx.addSlide();
s1.addText("$title", { x: 0.8, y: 2.4, w: 11.7, h: 1.3, fontSize: 40, bold: true,
  color: PRIMARY, align: "center" });
s1.addText("$subtitle", { x: 0.8, y: 3.7, w: 11.7, h: 0.8, fontSize: 20,
  color: "666666", align: "center" });
s1.background = { color: LIGHT };

$slides_block

pptx.writeFile({ fileName: "$artifact" }).then(() => {
  console.log(JSON.stringify({ exit: 0, artifact: "$artifact" }));
}).catch((e) => { console.error(e.message); process.exit(1); });
""")

_BULLET_SLIDE = Template("""{
  const s = pptx.addSlide();
  titleBar(s, $heading);
  s.addText([
    $bullets
  ], { x: 0.7, y: 1.3, w: 12, h: 5.4, fontSize: 16, color: "333333", lineSpacingMultiple: 1.2 });
}""")

_TABLE_SLIDE = Template("""{
  const s = pptx.addSlide();
  titleBar(s, $heading);
  const rows = [
    [$hdr_cells],
    $body_cells
  ];
  s.addTable(rows, { x: 0.7, y: 1.4, w: 12, colW: [5, 3.5, 3.5],
    border: { pt: 1, color: "CCCCCC" }, fontSize: 13, rowH: 0.5 });
}""")

_CHART_SLIDE = Template("""{
  const s = pptx.addSlide();
  titleBar(s, $heading);
  s.addChart(pptx.ChartType.bar, [{ name: "$series", labels: $labels, values: $values }],
    { x: 0.9, y: 1.4, w: 11.5, h: 5.3, barDir: "col", chartColors: [PRIMARY, ACCENT] });
}""")


def gen_create(spec, rng):
    primary, accent, light = C.palette(rng)
    artifact = f"{spec.task_id}_deck.pptx"
    title = ("Quarterly Business Review" if spec.scene == "report"
             else "Pitch Deck" if spec.scene == "pitch"
             else "Onboarding Training")
    subtitle = f"{C.company(rng, spec.lang)} · 2026-09"
    kpi = C.kpi_rows(rng, spec.lang, 4)
    labels = _json.dumps([r[0] for r in kpi], ensure_ascii=False)
    values = _json.dumps([r[1] for r in kpi])
    secs = C.report_sections(rng, spec.lang, 3)
    bullet_lines = []
    for heading, body in secs[:2]:
        bullets = ",\n    ".join(
            '{ text: %s, options: { bullet: true } }' % _json.dumps(s, ensure_ascii=False)
            for s in body.split(". ")[:3])
        bullet_lines.append(_BULLET_SLIDE.substitute(
            heading=_json.dumps(heading, ensure_ascii=False), bullets=bullets))
    hdr = ["Item", "Revenue (k)", "YoY"]
    hdr_cells = ", ".join(
        '{ text: %s, options: { bold: true, color: "FFFFFF", fill: { color: PRIMARY } } }'
        % _json.dumps(h, ensure_ascii=False) for h in hdr)
    body_cells = ",\n    ".join(
        "[" + ", ".join(_json.dumps(str(c), ensure_ascii=False) for c in row) + "]"
        for row in kpi)
    slides = bullet_lines + [
        _TABLE_SLIDE.substitute(heading=_json.dumps("Key Numbers", ensure_ascii=False),
                                hdr_cells=hdr_cells, body_cells=body_cells),
        _CHART_SLIDE.substitute(heading=_json.dumps("Revenue Trend", ensure_ascii=False),
                                series="Revenue", labels=labels, values=values),
    ]
    code = _CREATE.substitute(scene=spec.scene, primary=primary,
                              accent=accent, light=light, title=title, subtitle=subtitle,
                              artifact=artifact, slides_block="\n".join(slides))
    request = (f"Build '{title}' with pptxgenjs: 16:9, title slide + 3 content slides (bullets, "
               f"data table, bar chart), theme color #{primary}, save as {artifact}.")
    return {"runner": "node", "code": code, "artifact": artifact,
            "expect": {"kind": "pptx", "min_slides": 4},
            "request": request, "mutation": None}
