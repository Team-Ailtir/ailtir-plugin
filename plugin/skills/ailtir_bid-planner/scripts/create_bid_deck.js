// Ailtir bid kick-off deck. Internal working document, not a client pitch.
// Reads a JSON config (Claude builds it from the workbook data) and emits .pptx.
const pptxgen = require("pptxgenjs");
const fs = require("fs");

const NAVY = "0A1128";
const PURPLE = "7C3AED";
const WHITE = "FFFFFF";
const AMBER = "F59E0B";
const RED = "C0392B";
const GREEN = "2E7D32";

function arg(flag) {
  const i = process.argv.indexOf(flag);
  return i >= 0 ? process.argv[i + 1] : null;
}

function main() {
  const configPath = arg("--config");
  const output = arg("--output") || "Bid_KickOff.pptx";
  if (!configPath) {
    console.error("Usage: node create_bid_deck.js --config <json> --output <pptx>");
    process.exit(2);
  }
  const c = JSON.parse(fs.readFileSync(configPath, "utf8"));
  const p = new pptxgen();
  p.defineLayout({ name: "A4", width: 11.7, height: 8.27 });
  p.layout = "A4";

  const H = (s, o = {}) => ({ text: s, options: { fontFace: "Space Grotesk", ...o } });
  const B = (s, o = {}) => ({ text: s, options: { fontFace: "Inter", ...o } });

  // Slide 1 — Title
  let s = p.addSlide();
  s.background = { color: NAVY };
  s.addText(c.project || "Bid Kick-Off", { x: 0.5, y: 2.6, w: 10.7, h: 1, fontFace: "Space Grotesk", fontSize: 40, bold: true, color: WHITE });
  s.addText(
    [B(`${c.client || ""}   `, { color: WHITE }), B(`${c.value || ""}  ${c.sector || ""}`, { color: "CFD3DC" })],
    { x: 0.5, y: 3.7, w: 10.7, h: 0.5, fontSize: 16 }
  );
  s.addText(`Tender return: ${c.returnDate || "TBC"}`, { x: 6.7, y: 7.2, w: 4.5, h: 0.6, align: "right", fontFace: "Inter", fontSize: 16, bold: true, color: WHITE, fill: { color: RED } });

  // Slide 2 — Project overview
  s = p.addSlide();
  s.addText("Project Overview", { x: 0.5, y: 0.3, w: 10.7, h: 0.6, fontFace: "Space Grotesk", fontSize: 24, bold: true, color: NAVY });
  s.addText((c.overview || []).map((t) => B(t, { color: "222222", bullet: true })), { x: 0.5, y: 1.2, w: 10.7, h: 6, fontSize: 13 });

  // Slide 3 — Tender pack status
  s = p.addSlide();
  s.addText("Tender Pack Status", { x: 0.5, y: 0.3, w: 10.7, h: 0.6, fontFace: "Space Grotesk", fontSize: 24, bold: true, color: NAVY });
  const ps = c.packStatus || {};
  const stat = (label, val, color, x) =>
    s.addText([H(String(val), { fontSize: 40, bold: true, color: WHITE }), B(`\n${label}`, { fontSize: 12, color: WHITE })], { x, y: 1.2, w: 3.3, h: 1.6, align: "center", fill: { color } });
  stat("Received", ps.received ?? 0, GREEN, 0.5);
  stat("Missing", ps.missing ?? 0, RED, 4.1);
  stat("Gaps", ps.gaps ?? 0, AMBER, 7.7);
  if ((c.missingDocs || []).length) {
    s.addTable([["Missing Document", "Impact"], ...c.missingDocs.map((d) => [d.doc || d, d.impact || ""])], { x: 0.5, y: 3.1, w: 10.7, fontFace: "Inter", fontSize: 11, border: { pt: 0.5, color: "D9D9D9" }, fill: { color: "F5F7FA" } });
  }

  // Slide 4 — Submission requirements (skip quality for price-only)
  s = p.addSlide();
  s.addText("Submission Requirements", { x: 0.5, y: 0.3, w: 10.7, h: 0.6, fontFace: "Space Grotesk", fontSize: 24, bold: true, color: NAVY });
  if (c.priceOnly) {
    s.addText("Price-dominant tender — no formal quality submission. Returnable documents only.", { x: 0.5, y: 1.2, w: 10.7, h: 0.6, fontFace: "Inter", fontSize: 13, italic: true, color: "555555" });
  }
  if ((c.requirements || []).length) {
    s.addTable([["Ref", "Requirement", "Weight", "Owner"], ...c.requirements.map((r) => [r.ref || "", r.text || "", r.weight || "", r.owner || ""])], { x: 0.5, y: 1.9, w: 10.7, fontFace: "Inter", fontSize: 11, border: { pt: 0.5, color: "D9D9D9" } });
  }

  // Slide 5 — Programme
  s = p.addSlide();
  s.background = { color: NAVY };
  s.addText("Bid Programme", { x: 0.5, y: 0.3, w: 10.7, h: 0.6, fontFace: "Space Grotesk", fontSize: 24, bold: true, color: WHITE });
  s.addText((c.programme || []).map((m) => B(`${m.date || ""}  —  ${m.label || m}`, { color: WHITE, bullet: true })), { x: 0.5, y: 1.2, w: 10.7, h: 6, fontSize: 13 });

  // Slide 6 — Work packages
  s = p.addSlide();
  s.addText("Work Packages", { x: 0.5, y: 0.3, w: 10.7, h: 0.6, fontFace: "Space Grotesk", fontSize: 24, bold: true, color: NAVY });
  s.addText((c.packages || []).map((pk) => B(String(pk.name || pk), { color: "222222", bullet: true })), { x: 0.5, y: 1.2, w: 10.7, h: 6, fontSize: 13 });

  // Slide 7 — Top risks
  s = p.addSlide();
  s.background = { color: NAVY };
  s.addText("Top Risks", { x: 0.5, y: 0.3, w: 10.7, h: 0.6, fontFace: "Space Grotesk", fontSize: 24, bold: true, color: WHITE });
  (c.risks || []).slice(0, 7).forEach((r, i) => {
    s.addText([H(`${i + 1}. `, { color: RED, bold: true }), H(r.title || r, { color: WHITE, bold: true }), B(`   ${r.owner || ""}`, { color: AMBER })], { x: 0.5, y: 1.2 + i * 0.75, w: 10.7, h: 0.6, fontSize: 13 });
  });

  // Slide 8 — Immediate actions
  s = p.addSlide();
  s.addText("Immediate Actions", { x: 0.5, y: 0.3, w: 10.7, h: 0.6, fontFace: "Space Grotesk", fontSize: 24, bold: true, color: NAVY });
  if ((c.actions || []).length) {
    s.addTable([["When", "What", "Who"], ...c.actions.map((a) => [a.when || "", a.what || a, a.who || ""])], { x: 0.5, y: 1.2, w: 10.7, fontFace: "Inter", fontSize: 12, border: { pt: 0.5, color: "D9D9D9" } });
  }

  p.writeFile({ fileName: output }).then(() => console.log(`Created ${output}`));
}

main();
