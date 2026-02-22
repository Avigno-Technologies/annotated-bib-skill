#!/usr/bin/env python3
"""
Manage annotated bibliography files.
List, search, annotate, summarize, and export bibliography entries.

Usage:
  python manage_bib.py list bibliography.md
  python manage_bib.py list bibliography.md -u
  python manage_bib.py search bibliography.md "allostatic load"
  python manage_bib.py search bibliography.md "RCT" --tags "nutrition"
  python manage_bib.py annotate bibliography.md AB001 "Key finding text"
  python manage_bib.py annotate bibliography.md "nature.com/123" "Key finding text"
  python manage_bib.py stats bibliography.md
  python manage_bib.py summary bibliography.md -o summary.md
  python manage_bib.py summary bibliography.md --format json
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path


def _parse_entries(content):
    """Parse bibliography markdown into structured entries."""
    entries = []
    blocks = re.split(r"\n---\n", content)
    for block in blocks:
        entry = {}
        # Entry ID
        m = re.search(r"### \[(\w+)\]", block)
        if m:
            entry["id"] = m.group(1)
        # Title (bold text in header line only, skip metadata like "URL:")
        header_line = block.strip().split("\n")[0] if block.strip() else ""
        m = re.search(r"\*\*(.+?)\*\*", header_line)
        if m and m.group(1) not in ("URL:", "PMID:", "DOI:", "Tags:", "Key Findings:"):
            entry["title"] = m.group(1)
        # URL
        m = re.search(r"\*\*URL:\*\*\s*(.+)", block)
        if m:
            entry["url"] = m.group(1).strip()
        # Tags
        m = re.search(r"\*\*Tags:\*\*\s*(.+)", block)
        if m:
            entry["tags"] = [t.strip().lstrip("#") for t in m.group(1).split() if t.strip()]
        else:
            entry["tags"] = []
        # PMID
        m = re.search(r"\*\*PMID:\*\*\s*\[?(\w+)", block)
        if m:
            entry["pmid"] = m.group(1)
        # DOI
        m = re.search(r"\*\*DOI:\*\*\s*\[?(10\.\S+?)[\]\s)]", block)
        if m:
            entry["doi"] = m.group(1)
        # Annotation
        m = re.search(r"\*\*Key Findings:\*\*\n(.+?)(?:\n\n|\n<details|\Z)", block, re.DOTALL)
        if m:
            entry["annotation"] = m.group(1).strip()
        # Source (italic text after last period in header)
        m = re.search(r"\*([^*]+)\*\s*$", block.split("\n")[0] if block.strip() else "")
        if m:
            entry["source"] = m.group(1)

        if entry.get("url"):
            entries.append(entry)
    return entries


def _find_entry_range(content, pattern):
    """Find entry by ID (AB001) or URL substring. Returns (start, end) indices."""
    # Try ID match first
    if re.match(r"^AB\d{3}$", pattern, re.IGNORECASE):
        m = re.search(
            r"### \[%s\].*?\n\*\*URL:\*\*\s*[^\n]+\n" % re.escape(pattern),
            content, re.IGNORECASE,
        )
        if m:
            return m.start(), m.end()
    # Fall back to URL substring
    m = re.search(
        r"### .*?\n\*\*URL:\*\*\s*[^\n]*%s[^\n]*\n" % re.escape(pattern),
        content,
    )
    if m:
        return m.start(), m.end()
    return None, None


def list_entries(bib_file, unannotated_only=False):
    """List all entries in the bibliography."""
    content = Path(bib_file).read_text(encoding="utf-8")
    entries = _parse_entries(content)

    if not entries:
        print("No entries found.", file=sys.stderr)
        return

    for i, entry in enumerate(entries, 1):
        has_ann = bool(entry.get("annotation"))
        if unannotated_only and has_ann:
            continue

        status = "[x]" if has_ann else "[ ]"
        eid = entry.get("id", "???")
        title = entry.get("title", "(no title)")
        if len(title) > 65:
            title = title[:62] + "..."
        tag_str = ""
        if entry.get("tags"):
            tag_str = "  " + " ".join("#%s" % t for t in entry["tags"])

        print("%2d. %s [%s] %s%s" % (i, status, eid, title, tag_str))
        url = entry.get("url", "")
        if len(url) > 80:
            url = url[:77] + "..."
        print("    %s" % url)


def add_annotation(bib_file, pattern, annotation):
    """Add or update annotation for a specific entry."""
    content = Path(bib_file).read_text(encoding="utf-8")
    start, end = _find_entry_range(content, pattern)

    if start is None:
        print("Entry not found for: %s" % pattern, file=sys.stderr)
        return False

    # Find the block boundary (next --- or EOF)
    block_end = content.find("\n---\n", end)
    if block_end == -1:
        block_end = len(content)
    block = content[end:block_end]

    # Check if Key Findings already exists in this block
    kf_match = re.search(r"\*\*Key Findings:\*\*\n.*?\n\n", block, re.DOTALL)
    if kf_match:
        # Replace existing
        new_block = block[:kf_match.start()] + "**Key Findings:**\n%s\n\n" % annotation + block[kf_match.end():]
    else:
        # Insert after header lines (URL, identifiers, tags)
        # Find first blank line or content start
        insert_at = 0
        for m in re.finditer(r"\n", block):
            line_after = block[m.end():m.end() + 1]
            if line_after == "\n" or m.end() >= len(block):
                insert_at = m.end()
                break
            insert_at = m.end()
        new_block = block[:insert_at] + "**Key Findings:**\n%s\n\n" % annotation + block[insert_at:]

    content = content[:end] + new_block + content[block_end:]
    Path(bib_file).write_text(content, encoding="utf-8")
    print("Updated annotation for: %s" % pattern, file=sys.stderr)
    return True


def search_entries(bib_file, query, tag_filter=None):
    """Search entries by text query and optional tag filter."""
    content = Path(bib_file).read_text(encoding="utf-8")
    entries = _parse_entries(content)

    query_lower = query.lower()
    results = []
    for entry in entries:
        searchable = " ".join([
            entry.get("title", ""),
            entry.get("url", ""),
            entry.get("annotation", ""),
            entry.get("pmid", ""),
            entry.get("doi", ""),
            " ".join(entry.get("tags", [])),
        ]).lower()
        if query_lower not in searchable:
            continue
        if tag_filter:
            required = {t.strip().lower() for t in tag_filter.split(",") if t.strip()}
            entry_tags = {t.lower() for t in entry.get("tags", [])}
            if not required.issubset(entry_tags):
                continue
        results.append(entry)

    if not results:
        print("No entries matching '%s'" % query, file=sys.stderr)
        return

    print("Found %d entries matching '%s':" % (len(results), query))
    for entry in results:
        eid = entry.get("id", "???")
        title = entry.get("title", "(no title)")
        if len(title) > 60:
            title = title[:57] + "..."
        tag_str = ""
        if entry.get("tags"):
            tag_str = "  " + " ".join("#%s" % t for t in entry["tags"])
        print("  [%s] %s%s" % (eid, title, tag_str))
        print("    %s" % entry.get("url", "")[:80])


def show_stats(bib_file):
    """Display bibliography statistics."""
    content = Path(bib_file).read_text(encoding="utf-8")
    entries = _parse_entries(content)

    if not entries:
        print("No entries found.", file=sys.stderr)
        return

    annotated = sum(1 for e in entries if e.get("annotation"))
    with_pmid = sum(1 for e in entries if e.get("pmid"))
    with_doi = sum(1 for e in entries if e.get("doi"))

    tags = {}
    sources = {}
    for entry in entries:
        for tag in entry.get("tags", []):
            tags[tag] = tags.get(tag, 0) + 1
        src = entry.get("source", urlparse_netloc(entry.get("url", "")))
        if src:
            sources[src] = sources.get(src, 0) + 1

    print("Entries:      %d" % len(entries))
    print("Annotated:    %d/%d" % (annotated, len(entries)))
    print("Unannotated:  %d" % (len(entries) - annotated))
    print("With PMID:    %d" % with_pmid)
    print("With DOI:     %d" % with_doi)

    if tags:
        print("\nTags:")
        for tag, count in sorted(tags.items(), key=lambda x: -x[1]):
            print("  #%-20s %d" % (tag, count))

    if sources:
        print("\nSources:")
        for src, count in sorted(sources.items(), key=lambda x: -x[1])[:10]:
            print("  %-30s %d" % (src, count))


def urlparse_netloc(url):
    """Extract domain from URL."""
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return ""


def create_summary(bib_file, output_file=None, fmt="markdown"):
    """Create summary of annotated entries."""
    content = Path(bib_file).read_text(encoding="utf-8")
    entries = _parse_entries(content)
    annotated = [e for e in entries if e.get("annotation")]

    if fmt == "json":
        result = json.dumps(annotated, indent=2, ensure_ascii=False)
        if output_file:
            Path(output_file).write_text(result, encoding="utf-8")
            print("JSON summary written to: %s" % output_file, file=sys.stderr)
        else:
            print(result)
        return

    summary = "# Annotated Bibliography Summary\n\n"
    summary += "*Generated: %s*\n\n" % datetime.now().strftime("%Y-%m-%d")
    summary += "**%d annotated sources**\n\n---\n\n" % len(annotated)

    for entry in annotated:
        eid = entry.get("id", "")
        title = entry.get("title", "(no title)")
        url = entry.get("url", "")
        ann = entry.get("annotation", "")

        if eid:
            summary += "### [%s] %s\n" % (eid, title)
        else:
            summary += "### %s\n" % title
        summary += "%s\n\n" % url

        id_parts = []
        if entry.get("pmid"):
            id_parts.append("PMID: %s" % entry["pmid"])
        if entry.get("doi"):
            id_parts.append("DOI: %s" % entry["doi"])
        if id_parts:
            summary += "%s\n\n" % " | ".join(id_parts)

        summary += "%s\n\n---\n\n" % ann

    if output_file:
        Path(output_file).write_text(summary, encoding="utf-8")
        print("Summary written to: %s" % output_file, file=sys.stderr)
    else:
        print(summary)


def main():
    parser = argparse.ArgumentParser(description="Manage annotated bibliography files")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # List
    lp = subparsers.add_parser("list", help="List entries")
    lp.add_argument("bib_file", help="Bibliography file")
    lp.add_argument("--unannotated", "-u", action="store_true", help="Unannotated only")

    # Annotate
    ap = subparsers.add_parser("annotate", help="Add annotation to entry")
    ap.add_argument("bib_file", help="Bibliography file")
    ap.add_argument("pattern", help="Entry ID (AB001) or URL substring")
    ap.add_argument("annotation", help="Annotation text")

    # Search
    sp = subparsers.add_parser("search", help="Search across entries")
    sp.add_argument("bib_file", help="Bibliography file")
    sp.add_argument("query", help="Search term")
    sp.add_argument("--tags", help="Filter by tags (comma-separated)")

    # Stats
    stp = subparsers.add_parser("stats", help="Show bibliography statistics")
    stp.add_argument("bib_file", help="Bibliography file")

    # Summary
    smp = subparsers.add_parser("summary", help="Create summary")
    smp.add_argument("bib_file", help="Bibliography file")
    smp.add_argument("--output", "-o", help="Output file")
    smp.add_argument("--format", choices=["markdown", "json"], default="markdown")

    args = parser.parse_args()

    if args.command == "list":
        list_entries(args.bib_file, args.unannotated)
    elif args.command == "annotate":
        add_annotation(args.bib_file, args.pattern, args.annotation)
    elif args.command == "search":
        search_entries(args.bib_file, args.query, getattr(args, "tags", None))
    elif args.command == "stats":
        show_stats(args.bib_file)
    elif args.command == "summary":
        create_summary(args.bib_file, args.output, args.format)


if __name__ == "__main__":
    main()
