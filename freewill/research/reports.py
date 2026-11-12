"""Reports and reproduction packs.

A report is assembled by code from a campaign's results: every figure in it
is one the lab computed, with the identifier of its evidence. It is written
in one language at a time. It stays a draft until a person, and only a
person, marks it validated for publication.
"""

from __future__ import annotations

import csv
import io
import json
import platform
import sys
import zipfile
from datetime import datetime
from pathlib import Path

from freewill import __version__
from freewill.research import LAB_VERSION, metrics, stats, texts
from freewill.research.evidence import read_journal, without_words
from freewill.research.schemas import new, new_id, utc_now


def _show(value, na: str) -> str:
    if value is None:
        return na
    if isinstance(value, list):
        return "[" + ", ".join(f"{x:+.4f}" for x in value) + "]"
    if isinstance(value, float):
        return f"{value:+.4f}"
    return str(value)


def markdown(results: dict, protocol: dict, experiment: dict, language: str, *, author: str = "Freewill Research Lab",
             report: dict | None = None, reviews: list[dict] | None = None) -> str:
    words = texts.t(language)
    r, na = words["report"], words["digest"]["na"]
    title = protocol["title"][texts.lang(language)]
    status = r["draft"]
    if report and report.get("status") == "validated":
        status = r["validated"].format(who=report["validated_by"], when=report["validated_utc"])
    out = [f"# {r['title']} : {protocol['protocol_id']}, {title}" if language == "fr"
           else f"# {r['title']}: {protocol['protocol_id']}, {title}", "",
           f"- {r['date']} : {results['computed_utc']}" if language == "fr" else f"- {r['date']}: {results['computed_utc']}",
           f"- {r['version']} : Freewill {__version__}, Research Lab {LAB_VERSION}, commit {results['code_commit'][:12]}"
           if language == "fr" else f"- {r['version']}: Freewill {__version__}, Research Lab {LAB_VERSION}, commit {results['code_commit'][:12]}",
           f"- {r['author']} : {author}" if language == "fr" else f"- {r['author']}: {author}",
           f"- {r['status']} : {status}" if language == "fr" else f"- {r['status']}: {status}", ""]

    def section(name: str, *paragraphs: str) -> None:
        out.extend([f"## {r[name]}", ""])
        for paragraph in paragraphs:
            out.extend([paragraph, ""])

    section("summary", r["summary_text"].format(
        protocol=protocol["protocol_id"], version=protocol["protocol_version"], sha=protocol["sha256"][:12],
        runs=len(experiment["runs"]), t0=results["baseline_snapshot_sha256"][:12],
        engine=results["engine"].get("kind"), units=len(results["units"]), planned=results["units_planned"]))
    divergence = results["divergence"]
    main = protocol["primary_outcome"]
    wanted = [main] + list(protocol["secondary_outcomes"])
    if main == "h5.heldout_divergence":
        intervals = [(row["excess_over_twin"] or {}).get("interval_95") for row in divergence]
    else:
        intervals = [row["interval_95"] for row in results["comparisons"] if row["metric_id"] == main]
    if intervals and all(i is not None for i in intervals):
        out.extend([r["primary_null"] if all(i[0] <= 0 <= i[1] for i in intervals) else r["primary_nonnull"], ""])
    known = {h["id"]: h for h in texts.hypotheses(language)}
    section("question", *[f"**{h}. {known[h]['title']}.** {known[h]['claim']} {known[h]['limits']}"
                          for h in protocol["hypotheses"]])
    section("prereg", r["prereg_text"].format(primary=protocol["primary_outcome"],
                                              secondary=", ".join(protocol["secondary_outcomes"]) or na,
                                              reference=protocol["reference"]))
    section("population", r["population_text"].format(metrics=results["metrics_version"], stats=stats.STATS_VERSION))
    out.extend([f"## {r['conditions']}", ""])
    for condition in protocol["conditions"]:
        detail = {k: v for k, v in condition.items() if k != "name"}
        out.append(f"- `{condition['name']}` : `{json.dumps(detail, ensure_ascii=False)}`" if language == "fr"
                   else f"- `{condition['name']}`: `{json.dumps(detail, ensure_ascii=False)}`")
    out.extend(["", f"`seeds = {protocol['seeds']}`", ""])
    section("statistics", r["stat_text"].format(min_ci=stats.MIN_UNITS_FOR_INTERVAL, min_test=stats.MIN_UNITS_FOR_TEST))

    out.extend([f"## {r['results']}", ""])
    has_twin = any(row["excess_over_twin"] for row in divergence)
    if divergence and (has_twin or main == "h5.heldout_divergence"):  # shown only where its noise floor is known
        head = r["h5_head"] + (f" ({r['primary_mark']})" if main == "h5.heldout_divergence" else "")
        out.extend([f"### {head}", "", "| " + " | ".join(r["h5_cols"]) + " |", "|" + "---|" * len(r["h5_cols"])])
        for row in divergence:
            excess = row["excess_over_twin"]
            out.append("| " + " | ".join([
                f"`{row['condition']}`", _show(row["mean_distance"], na),
                _show(excess["mean_difference"], na) if excess else r["no_twin"],
                _show(excess["interval_95"], na) if excess else na, _show(excess["p_sign_flip"], na) if excess else na,
                f"`{row['evidence_id']}`"]) + " |")
        out.append("")

    long = results.get("longitudinal")
    if long:  # EXP-10: the trajectory over the days, then the sealed probe, by the preregistered rule
        out.extend([f"### {r['long_head']}", "", r["long_text"], "", "| " + " | ".join(r["long_cols"]) + " |",
                    "|" + "---|" * len(r["long_cols"])])
        for row in long["waves"] + [long["sealed"]]:
            x, a = row["excess_over_twin"] or {}, row["affect_on_divergence"] or {}
            mean = lambda v: na if not v else f"{sum(v) / len(v):.6f}"  # noqa: E731
            label = r["long_sealed"] if row["when"] == "sealed" else r["long_wave"].format(n=row["when"][4:])
            out.append("| " + " | ".join([label, mean(row["distance_B_A"]), mean(row["distance_twin"]),
                                          _show(x.get("mean_difference"), na), _show(x.get("interval_95"), na),
                                          _show(x.get("p_sign_flip"), na), _show(a.get("mean_difference"), na),
                                          _show(a.get("interval_95"), na)]) + " |")
        met = long["primary_criterion_met"]
        out.extend(["", r["long_met"] if met else (r["long_undetermined"] if met is None else r["long_not_met"]), ""])
        if long["excluded"]:
            out.extend([r["long_excluded"]] + [f"- `{k}`: {', '.join(v)}" for k, v in long["excluded"].items()] + [""])
        else:
            out.extend([r["long_none_excluded"], ""])
        prereg = (protocol.get("preregistration") or {}).get(texts.lang(language)) or {}
        if prereg:
            out.extend([f"### {r['long_prereg']}", ""] + [f"- `{k}`: {v if not isinstance(v, list) else '; '.join(v)}"
                                                         for k, v in prereg.items()] + [""])

    def rows(keep) -> list[str]:
        lines = ["| " + " | ".join(r["cols"]) + " |", "|" + "---|" * len(r["cols"])]
        for row in results["comparisons"]:
            if not keep(row["metric_id"]):
                continue
            name = f"`{row['metric_id']}`" + (f" ({r['primary_mark']})" if row["metric_id"] == main else "")
            lines.append("| " + " | ".join([
                name, f"`{row['condition']}`", words["levels"][row["level"]],
                _show(row["mean_difference"], na), _show(row["effect_size_dz"], na), _show(row["interval_95"], na),
                _show(row["p_sign_flip"], na), f"`{row['evidence_id']}`"]) + " |")
        return lines if len(lines) > 2 else []

    stated = rows(lambda metric_id: metric_id in wanted)
    if stated:
        out.extend([f"### {r['table_head']}", "", r["mechanism_note"], ""] + stated + [""])
    others = rows(lambda metric_id: metric_id not in wanted and not metric_id.startswith("tech."))
    if others:
        out.extend([f"### {r['other_head']}", "", r["other_note"], ""] + others)
    missing = sorted({(m, reason) for table in results["conditions"].values() for m, cell in table.items()
                      for reason in cell["not_computable"]})
    if missing:
        out.append("")
        out.extend(f"- `{metric_id}` : {na} ({words['reasons'].get(reason, reason)})" if language == "fr"
                   else f"- `{metric_id}`: {na} ({words['reasons'].get(reason, reason)})" for metric_id, reason in missing)
    out.append("")
    section("qualitative", r["no_qual"])
    out.extend([f"## {r['anomalies']}", ""] + ([f"- {a}" for a in results["anomalies"]] or [f"- {na}" if False else "- 0"]) + [""])
    specific = r["design_threats"].get(protocol["design"])
    section("threats", *[f"- {line}" for line in ((specific,) if specific else ()) + tuple(r["threats_text"])])
    section("interpretation", r["interpretation_text"])
    section("not_shown", *[f"- {line}" for line in r["not_shown_text"]])
    used = [step for review in (reviews or []) for step in review["steps"]]
    out.extend([f"## {r['review']}", ""])
    for step in used:
        bad = f" ({len(step['invalid_citations'])} !)" if step["invalid_citations"] else ""
        out.extend([f"**{step['name']}** ({step['llm'] or '-'}){bad}", "", "> " + step["text"].replace("\n", "\n> "), ""])
    section("llm", r["llm_some"] if any(step["llm"] for step in used) else r["llm_none"])
    section("references", *[f"- {reference}" for reference in texts.REFERENCES])
    section("annexes", r["repro"].format(protocol=protocol["protocol_id"]),
            f"`results_sha256 = {results['results_sha256']}`")
    return "\n".join(out).rstrip() + "\n"


# -- a small PDF writer: text only, standard fonts, nothing to install ---------------------------

def _pdf_text(text: str) -> bytes:
    data = text.encode("cp1252", "replace")
    return data.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")


def _wrap(text: str, width: int) -> list[str]:
    lines, line = [], ""
    for word in text.split(" "):
        while len(word) > width:
            if line:
                lines.append(line)
                line = ""
            lines.append(word[:width])
            word = word[width:]
        if len(line) + len(word) + 1 > width and line:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + [line] if line or not lines else lines


def pdf(text: str, footer: str = "") -> bytes:
    """Render Markdown as a plain, readable A4 PDF: headings, paragraphs, lists, tables in fixed width."""
    rows: list[tuple[str, float, str]] = []  # (font, size, line)
    for raw in text.splitlines():
        line = raw.rstrip()
        plain = line.replace("**", "").replace("`", "")
        if line.startswith("# "):
            rows += [("F2", 16, part) for part in _wrap(plain[2:], 62)] + [("F1", 6, "")]
        elif line.startswith("## "):
            rows += [("F1", 6, "")] + [("F2", 12.5, part) for part in _wrap(plain[3:], 80)]
        elif line.startswith("### "):
            rows += [("F2", 10.5, part) for part in _wrap(plain[4:], 92)]
        elif line.startswith("|"):
            if set(line) <= set("|- "):
                continue
            cells = [cell.strip() for cell in plain.strip("|").split("|")]
            rows += [("F3", 6.6, part) for part in _wrap("  ".join(cells), 138)]
        elif not line:
            rows.append(("F1", 5, ""))
        else:
            rows += [("F1", 9.5, part) for part in _wrap(plain, 104)]
    pages, page, y = [], [], 800.0
    for font, size, line in rows:
        step = size * 1.38
        if y - step < 48:
            pages.append(page)
            page, y = [], 800.0
        y -= step
        if line:
            page.append(b"BT /%s %.1f Tf 50 %.1f Td (%s) Tj ET" % (font.encode(), size, y, _pdf_text(line)))
    pages.append(page)
    objects: list[bytes] = [b"", b""]  # 1: catalog, 2: pages; filled in below
    for name in (b"Helvetica", b"Helvetica-Bold", b"Courier"):
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /" + name + b" /Encoding /WinAnsiEncoding >>")
    kids = []
    for number, content in enumerate(pages, 1):
        mark = b"BT /F1 7.5 Tf 50 30 Td (%s) Tj ET" % _pdf_text(f"{footer}  {number}/{len(pages)}")
        stream = b"\n".join(content + [mark])
        objects.append(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream")
        objects.append(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents %d 0 R /Resources "
                       b"<< /Font << /F1 3 0 R /F2 4 0 R /F3 5 0 R >> >> >>" % len(objects))
        kids.append(len(objects))
    objects[0] = b"<< /Type /Catalog /Pages 2 0 R >>"
    objects[1] = b"<< /Type /Pages /Kids [%s] /Count %d >>" % (b" ".join(b"%d 0 R" % k for k in kids), len(kids))
    out, offsets = io.BytesIO(), []
    out.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    for index, body in enumerate(objects, 1):
        offsets.append(out.tell())
        out.write(b"%d 0 obj\n" % index + body + b"\nendobj\n")
    start = out.tell()
    out.write(b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1))
    for offset in offsets:
        out.write(b"%010d 00000 n \n" % offset)
    out.write(b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objects) + 1, start))
    return out.getvalue()


# -- the report on disk, and the reproduction pack --------------------------------------------------

def _csv(header: list[str], rows: list[list]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return buffer.getvalue()


def build(lab, experiment_id: str, language: str, *, author: str = "Freewill Research Lab",
          reviews: list[dict] | None = None, with_words: bool = False) -> dict:
    """Write a report (Markdown and PDF) and its reproduction pack. Returns the report record, a draft."""
    results = lab.results(experiment_id)
    if results is None:
        raise ValueError("this campaign has no results yet")
    folder = lab._experiment_dir(experiment_id)
    experiment = lab.experiment(experiment_id)
    protocol = json.loads((folder / "protocol.json").read_text(encoding="utf-8"))
    language = texts.lang(language)
    report_id = new_id("rep")
    target = lab.root / "reports" / report_id
    target.mkdir(parents=True)
    report = new("ResearchReport", report_id=report_id, experiment_id=experiment_id, language=language,
                 status="draft", created_utc=utc_now(), author=author[:80], files={}, validated_by=None,
                 validated_utc=None, llm_involved=any(s["llm"] for r in (reviews or []) for s in r["steps"]))
    text = markdown(results, protocol, experiment, language, author=author, report=report, reviews=reviews)
    stamp = f"Freewill Research Lab - {protocol['protocol_id']} - {results['results_sha256'][:12]}"
    (target / "report.md").write_text(text, encoding="utf-8")
    (target / "report.pdf").write_bytes(pdf(text, stamp))

    runs = [json.loads((folder / "runs" / e["run_id"] / "run.json").read_text(encoding="utf-8"))
            for e in experiment["runs"] if e["status"] == "done"]
    manifest = {
        "freewill_version": __version__, "lab_version": LAB_VERSION, "code_commit": results["code_commit"],
        "metrics_version": results["metrics_version"], "stats_version": stats.STATS_VERSION,
        "python": sys.version.split()[0], "platform": platform.platform(), "machine": platform.machine(),
        "protocol_sha256": protocol["sha256"], "baseline_snapshot_sha256": results["baseline_snapshot_sha256"],
        "results_sha256": results["results_sha256"], "seeds": protocol["seeds"], "engine": results["engine"],
        "runs": len(runs), "api_calls": 0 if results["engine"].get("kind") == "simulated" else None,
        "journals_contain_words": with_words, "created": datetime.now().isoformat(timespec="seconds"),
        "licence": "Freewill is source-available for non-commercial research; it is not an OSI open source licence.",
    }
    pack = target / "reproduction-pack.zip"
    with zipfile.ZipFile(pack, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.write(target / "report.md", "report.md")
        archive.write(target / "report.pdf", "report.pdf")
        archive.writestr("protocol.json", json.dumps(protocol, ensure_ascii=False, indent=2))
        archive.writestr("results.json", json.dumps(results, ensure_ascii=False, indent=2))
        archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        archive.writestr("metric_dictionary.json", json.dumps(list(metrics.DEFINITIONS.values()), indent=2))
        archive.writestr("runs.csv", _csv(
            ["run_id", "condition", "seed", "metric_id", "value", "computable", "reason", "n", "evidence_id"],
            [[run["run_id"], run["condition"], run["seed"], m["metric_id"], m["value"], m["computable"],
              m["reason"], m["n"], m["evidence_id"]] for run in runs for m in run["metrics"].values()]))
        archive.writestr("comparisons.csv", _csv(
            ["metric_id", "condition", "reference", "level", "n_units", "mean_difference", "sd_difference",
             "effect_size_dz", "interval_95", "p_sign_flip", "evidence_id"],
            [[c["metric_id"], c["condition"], c["reference"], c["level"], c["n_units"], c["mean_difference"],
              c["sd_difference"], c["effect_size_dz"], c["interval_95"], c["p_sign_flip"], c["evidence_id"]]
             for c in results["comparisons"]]))
        for run in runs:  # the raw journals, without the words unless a person asked for them
            records, _problems = read_journal(folder / "runs" / run["run_id"] / "journal.jsonl")
            lines = [json.dumps(record if with_words else without_words(record), ensure_ascii=False)
                     for record in records]
            archive.writestr(f"journals/{run['run_id']}.jsonl", "\n".join(lines) + "\n")
        archive.writestr("README.txt", "Reproduction pack of a Freewill Research Lab campaign.\n"
                         "python -m freewill.research run " + protocol["protocol_id"] + "\n"
                         "recomputes results.json; compare results_sha256 with manifest.json.\n")
    report["files"] = {"markdown": str(target / "report.md"), "pdf": str(target / "report.pdf"), "pack": str(pack)}
    (target / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def list_reports(lab) -> list[dict]:
    found = [json.loads(p.read_text(encoding="utf-8")) for p in (lab.root / "reports").glob("*/report.json")]
    return sorted(found, key=lambda r: r["created_utc"], reverse=True)


def validate_report(lab, report_id: str, who: str) -> dict:
    """A person marks a report validated for publication. No other code path sets this status."""
    if not report_id.replace("_", "").isalnum() or not str(who).strip():
        raise ValueError("a report is validated by a named person")
    path = lab.root / "reports" / report_id / "report.json"
    report = json.loads(path.read_text(encoding="utf-8"))
    report.update(status="validated", validated_by=str(who).strip()[:80], validated_utc=utc_now())
    words = texts.t(report["language"])["report"]
    text_path = path.with_name("report.md")
    text = text_path.read_text(encoding="utf-8").replace(
        words["draft"], words["validated"].format(who=report["validated_by"], when=report["validated_utc"]), 1)
    text_path.write_text(text, encoding="utf-8")
    path.with_name("report.pdf").write_bytes(pdf(text, "Freewill Research Lab"))
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
