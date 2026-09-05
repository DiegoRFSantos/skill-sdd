#!/usr/bin/env python3
"""Print one slice of an SDD artifact instead of the whole file.

Context is re-read on every subsequent turn, so a section pulled out of a
200-line design costs a fraction of the file it came from — and keeps costing
that fraction for the rest of the session. Use this wherever a task, a
subagent, or a question needs part of an artifact rather than all of it.

    sdd_extract.py design.md --outline              # headings only, to find what you want
    sdd_extract.py design.md --section 3.1          # one section, subsections included
    sdd_extract.py design.md --section 3.1,9        # several
    sdd_extract.py spec.md   --ids BR-01,AC-02      # table rows or ### blocks for those ids
    sdd_extract.py spec.md   --glance               # just the 15-line summary

Exits 1 when nothing matched, so a wrong section number fails loudly instead of
handing back an empty string that reads like "this section is empty."
"""
import argparse
import re
import sys
from pathlib import Path

HEADING = re.compile(r"^(#{2,4})\s+(.*)$")
# "## 3. Contracts" / "### 3.1 API Contracts" / "## 0. At a Glance"
NUMBERED = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+(.*)$")
ID_TOKEN = re.compile(r"^(?:BR|AC|EC|TC|Q)-\d+$", re.ASCII)


def _headings(lines):
    """(index, level, number, title) for every heading in the file."""
    out = []
    in_fence = False
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = HEADING.match(line)
        if not match:
            continue
        hashes, rest = match.group(1), match.group(2).strip()
        number_match = NUMBERED.match(rest)
        number = number_match.group(1) if number_match else None
        title = number_match.group(2) if number_match else rest
        out.append((i, len(hashes), number, title))
    return out


def outline(text):
    lines = text.split("\n")
    out = []
    for _, level, number, title in _headings(lines):
        indent = "  " * (level - 2)
        label = f"{number} {title}" if number else title
        out.append(f"{indent}{label}")
    return out


def sections(text, wanted):
    """Every requested section, each running to the next heading at its level or above."""
    lines = text.split("\n")
    heads = _headings(lines)
    picked = []
    for want in wanted:
        want = want.strip().rstrip(".")
        for position, (index, level, number, _title) in enumerate(heads):
            if number != want:
                continue
            end = len(lines)
            for later_index, later_level, _n, _t in heads[position + 1:]:
                if later_level <= level:
                    end = later_index
                    break
            picked.append((index, lines[index:end]))
            break
    picked.sort()
    out = []
    for _, block in picked:
        while block and not block[-1].strip():
            block.pop()
        out.extend(block)
        out.append("")
    return out[:-1] if out else []


def ids(text, wanted):
    """Table rows and ### blocks declaring the given BR/AC/EC/TC/Q ids."""
    lines = text.split("\n")
    wanted = [w.strip() for w in wanted]
    heads = _headings(lines)
    out = []
    seen_header = set()

    for want in wanted:
        # A ### block whose title starts with the id.
        for position, (index, level, _number, title) in enumerate(heads):
            if not title.startswith(want):
                continue
            end = len(lines)
            for later_index, later_level, _n, _t in heads[position + 1:]:
                if later_level <= level:
                    end = later_index
                    break
            out.append((index, lines[index:end]))
            break

        # A table row whose first cell is the id — carry its header so the
        # columns still mean something out of context.
        for i, line in enumerate(lines):
            if not line.startswith("|"):
                continue
            first = line.split("|")[1].strip() if line.count("|") >= 2 else ""
            if first != want:
                continue
            header = _table_header(lines, i)
            if header and header[0] not in seen_header:
                seen_header.add(header[0])
                out.append((header[0], [lines[header[0]], lines[header[0] + 1]]))
            out.append((i, [line]))
            break

    out.sort()
    flat = []
    for _, block in out:
        flat.extend(block)
    return flat


def _table_header(lines, row_index):
    """(index,) of the header row for the table containing row_index."""
    i = row_index - 1
    while i >= 0 and lines[i].startswith("|"):
        i -= 1
    header = i + 1
    if header < len(lines) - 1 and lines[header].startswith("|"):
        return (header,)
    return None


def main(argv=None):
    parser = argparse.ArgumentParser(description="Extract part of an SDD artifact")
    parser.add_argument("path")
    parser.add_argument("--section", help="comma-separated section numbers, e.g. 3.1,9")
    parser.add_argument("--ids", help="comma-separated spec ids, e.g. BR-01,AC-02")
    parser.add_argument("--glance", action="store_true", help="the At a Glance section")
    parser.add_argument("--outline", action="store_true", help="headings only")
    args = parser.parse_args(argv)

    path = Path(args.path)
    if not path.exists():
        print("no such file: %s" % path, file=sys.stderr)
        return 1
    text = path.read_text(encoding="utf-8")

    if args.outline:
        result = outline(text)
    elif args.glance:
        result = sections(text, ["0"])
    elif args.section:
        result = sections(text, args.section.split(","))
    elif args.ids:
        bad = [i for i in args.ids.split(",") if not ID_TOKEN.match(i.strip())]
        if bad:
            print("not a spec id: %s" % ", ".join(bad), file=sys.stderr)
            return 1
        result = ids(text, args.ids.split(","))
    else:
        parser.error("give one of --outline, --section, --ids, --glance")
        return 1

    if not result:
        print("nothing matched in %s" % path, file=sys.stderr)
        return 1
    print("\n".join(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
