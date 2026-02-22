#!/usr/bin/env python3
"""
Create annotated bibliography entries from fetched content.
Accepts JSON input with URL and content, outputs formatted markdown entries.

Usage:
  # From JSON input (piped or file)
  echo '{"url": "...", "content": "..."}' | python format_entry.py -o bibliography.md -t "Topic"

  # Append with deduplication check
  echo '{"url": "...", "content": "..."}' | python format_entry.py -o bib.md -a

  # With annotation and tags
  python format_entry.py -i content.json -o bib.md -a --annotation "Key finding" --tags "RCT,nutrition"

  # JSON output instead of markdown
  python format_entry.py -i content.json --json
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


def _next_entry_id(output_file):
    """Generate next sequential entry ID (AB001, AB002, ...)."""
    if not output_file or not Path(output_file).exists():
        return "AB001"
    content = Path(output_file).read_text(encoding="utf-8")
    ids = re.findall(r"\[AB(\d{3})\]", content)
    if not ids:
        return "AB001"
    return "AB%03d" % (max(int(i) for i in ids) + 1)


def _extract_identifiers(url, content):
    """Extract PMID and DOI from URL and content."""
    pmid = None
    doi = None

    # PMID from PubMed/PMC URLs
    m = re.search(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)", url)
    if m:
        pmid = m.group(1)
    if not pmid:
        m = re.search(r"pmc\.ncbi\.nlm\.nih\.gov/articles/PMC(\d+)", url)
        if m:
            pmid = "PMC" + m.group(1)
    # PMID from content
    if not pmid:
        m = re.search(r"PMID:\s*(\d+)", content[:5000])
        if m:
            pmid = m.group(1)

    # DOI from URL
    m = re.search(r"doi\.org/(10\.\d{4,}/[^\s\"'>]+)", url)
    if m:
        doi = m.group(1).rstrip(".")
    # DOI from content
    if not doi:
        m = re.search(r"(?:doi|DOI)[:\s]+(10\.\d{4,}/[^\s\"'>]+)", content[:5000])
        if m:
            doi = m.group(1).rstrip(".")

    return pmid, doi


def _check_duplicate(url, output_file):
    """Check if URL already exists in bibliography file."""
    if not output_file or not Path(output_file).exists():
        return False
    content = Path(output_file).read_text(encoding="utf-8")
    normalized = url.rstrip("/").split("#")[0]
    return normalized in content


def _smart_truncate(content, max_chars=3000):
    """Truncate content preserving beginning (abstract) and end (conclusions)."""
    if len(content) <= max_chars:
        return content
    head_size = max_chars - 500
    head = content[:head_size]
    tail = content[-500:]
    omitted = len(content) - head_size - 500
    return "%s\n\n[...truncated %d chars...]\n\n%s" % (head, omitted, tail)


def extract_metadata_from_content(content, url):
    """Extract metadata heuristically from text content."""
    lines = content.split("\n")

    # Title: first substantial non-navigation line
    title = None
    skip_words = ("cookie", "menu", "search", "login", "sign in", "accept")
    for line in lines[:20]:
        line = line.strip()
        if line and 10 < len(line) < 200:
            if not any(s in line.lower() for s in skip_words):
                title = line
                break

    # Authors
    authors = []
    author_patterns = [
        r"[Aa]uthors?:\s*(.+?)(?:\n|$)",
        r"[Bb]y\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
        r"([A-Z][a-z]+(?:,?\s+[A-Z]\.?\s*)+(?:\s+et\s+al\.?)?)",
    ]
    for pattern in author_patterns:
        matches = re.findall(pattern, content[:2000])
        if matches:
            authors = matches[:3]
            break

    # Date
    date = None
    date_patterns = [
        r"(\d{4}-\d{2}-\d{2})",
        r"([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})",
        r"(\d{1,2}\s+[A-Z][a-z]+\s+\d{4})",
    ]
    for pattern in date_patterns:
        m = re.search(pattern, content[:3000])
        if m:
            date = m.group(1)
            break

    source = urlparse(url).netloc.replace("www.", "")

    return {
        "title": title,
        "authors": authors if isinstance(authors, list) else [authors] if authors else [],
        "date": date,
        "source": source,
    }


def format_entry(url, content, entry_id=None, title=None, authors=None,
                 date=None, source=None, annotation=None, tags=None,
                 pmid=None, doi=None):
    """Format a single bibliography entry in markdown."""

    if not any([title, authors, date]):
        extracted = extract_metadata_from_content(content, url)
        title = title or extracted["title"]
        authors = authors or extracted["authors"]
        date = date or extracted["date"]
        source = source or extracted["source"]
    else:
        source = source or urlparse(url).netloc.replace("www.", "")

    # Auto-detect identifiers if not provided
    if not pmid or not doi:
        auto_pmid, auto_doi = _extract_identifiers(url, content)
        pmid = pmid or auto_pmid
        doi = doi or auto_doi

    # Build citation line
    parts = []
    if authors:
        author_str = ", ".join(authors[:3]) if isinstance(authors, list) else authors
        if isinstance(authors, list) and len(authors) > 3:
            author_str += " et al."
        parts.append(author_str)
    if date:
        year = date[:4] if len(date) >= 4 else date
        parts.append("(%s)" % year)
    if title:
        title = title.strip()
        if len(title) > 150:
            title = title[:147] + "..."
        parts.append("**%s**" % title)
    if source:
        parts.append("*%s*" % source)

    citation = ". ".join(parts) if parts else "*(metadata unavailable)*"

    # Header with entry ID
    if entry_id:
        output = "### [%s] %s\n" % (entry_id, citation)
    else:
        output = "### %s\n" % citation

    output += "**URL:** %s\n" % url

    # Identifiers
    id_parts = []
    if pmid:
        if pmid.startswith("PMC"):
            id_parts.append("**PMID:** [%s](https://pmc.ncbi.nlm.nih.gov/articles/%s/)" % (pmid, pmid))
        else:
            id_parts.append("**PMID:** [%s](https://pubmed.ncbi.nlm.nih.gov/%s/)" % (pmid, pmid))
    if doi:
        id_parts.append("**DOI:** [%s](https://doi.org/%s)" % (doi, doi))
    if id_parts:
        output += " | ".join(id_parts) + "\n"

    # Tags
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        if tag_list:
            output += "**Tags:** %s\n" % " ".join("#%s" % t for t in tag_list)

    output += "\n"

    if annotation:
        output += "**Key Findings:**\n%s\n\n" % annotation

    # Content preview
    preview = _smart_truncate(content.strip())
    output += "<details><summary>Content preview (click to expand)</summary>\n\n"
    output += "```\n%s\n```\n</details>\n" % preview

    return output


def _entry_to_dict(url, content, entry_id=None, title=None, authors=None,
                   date=None, source=None, annotation=None, tags=None,
                   pmid=None, doi=None):
    """Build a structured dict for JSON output."""
    if not any([title, authors, date]):
        extracted = extract_metadata_from_content(content, url)
        title = title or extracted["title"]
        authors = authors or extracted["authors"]
        date = date or extracted["date"]
        source = source or extracted["source"]

    if not pmid or not doi:
        auto_pmid, auto_doi = _extract_identifiers(url, content)
        pmid = pmid or auto_pmid
        doi = doi or auto_doi

    tag_list = [t.strip() for t in (tags or "").split(",") if t.strip()]

    return {
        "id": entry_id,
        "url": url,
        "title": title,
        "authors": authors if isinstance(authors, list) else [authors] if authors else [],
        "date": date,
        "source": source,
        "pmid": pmid,
        "doi": doi,
        "tags": tag_list,
        "annotation": annotation,
        "content_preview": content[:3000] if content else "",
    }


def main():
    parser = argparse.ArgumentParser(
        description="Format bibliography entries from fetched content"
    )
    parser.add_argument("--input", "-i", help="Input JSON file")
    parser.add_argument("--output", "-o", help="Output markdown file")
    parser.add_argument("--append", "-a", action="store_true", help="Append to output file")
    parser.add_argument("--topic", "-t", help="Topic/section header (new files)")
    parser.add_argument("--annotation", help="Annotation text")
    parser.add_argument("--title", help="Override title")
    parser.add_argument("--authors", help="Override authors (comma-separated)")
    parser.add_argument("--date", help="Override date")
    parser.add_argument("--tags", help="Comma-separated tags")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of markdown")
    parser.add_argument("--force", action="store_true", help="Skip deduplication check")

    args = parser.parse_args()

    # Read input
    if args.input:
        with open(args.input, encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)

    entries = data if isinstance(data, list) else [data]

    output = ""
    json_entries = []

    if args.topic and not args.append and not args.json:
        output += "## %s\n\n" % args.topic
        output += "*Processed: %s*\n\n" % datetime.now().strftime("%Y-%m-%d %H:%M")

    for entry in entries:
        url = entry.get("url", entry.get("source_url", "Unknown URL"))
        content = entry.get("content", entry.get("text", ""))

        # Deduplication check
        if args.append and not args.force and _check_duplicate(url, args.output):
            print("SKIP (duplicate): %s" % url[:80], file=sys.stderr)
            continue

        title = args.title or entry.get("title")
        authors_raw = args.authors or entry.get("authors")
        if isinstance(authors_raw, str):
            authors_raw = [a.strip() for a in authors_raw.split(",")]
        date = args.date or entry.get("date")
        tags = args.tags or entry.get("tags", "")
        if isinstance(tags, list):
            tags = ",".join(tags)

        entry_id = _next_entry_id(args.output) if args.output else None

        if args.json:
            json_entries.append(_entry_to_dict(
                url=url, content=content, entry_id=entry_id,
                title=title, authors=authors_raw, date=date,
                annotation=args.annotation, tags=tags,
            ))
        else:
            output += format_entry(
                url=url, content=content, entry_id=entry_id,
                title=title, authors=authors_raw, date=date,
                annotation=args.annotation, tags=tags,
            )
            output += "\n---\n\n"

    # Write output
    if args.json:
        result = json.dumps(json_entries, indent=2, ensure_ascii=False)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result)
            print("Wrote JSON: %s" % args.output, file=sys.stderr)
        else:
            print(result)
    elif args.output:
        mode = "a" if args.append else "w"
        with open(args.output, mode, encoding="utf-8") as f:
            if args.append:
                f.write("\n")
            f.write(output)
        print("%s: %s" % ("Appended to" if args.append else "Wrote", args.output),
              file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
