// fixture: deck for inspection (3-slide deck)
const pptxgen = require("pptxgenjs");
const pptx = new pptxgen();
pptx.defineLayout({ name: "WIDE", width: 13.33, height: 7.5 });
pptx.layout = "WIDE";
const s1 = pptx.addSlide();
s1.addText("Key Project Updates", { x: 0.8, y: 2.4, w: 11.7, h: 1.3, fontSize: 40, bold: true });
const s2 = pptx.addSlide();
s2.addText("Agenda", { x: 0.5, y: 0.3, w: 12, h: 0.9, fontSize: 24, bold: true });
s2.addText("Status, numbers, next steps.", { x: 0.6, y: 1.3, w: 12, h: 4, fontSize: 16 });
const s3 = pptx.addSlide();
s3.addText("Numbers", { x: 0.5, y: 0.3, w: 12, h: 0.9, fontSize: 24, bold: true });
pptx.writeFile({ fileName: "task_000119_deck.pptx" }).then(() => console.log(JSON.stringify({ exit: 0 })));
