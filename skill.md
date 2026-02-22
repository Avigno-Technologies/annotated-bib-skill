---
name: annotated-bibliography
description: Create and manage annotated bibliographies for any research domain. Use when building literature reviews, gathering sources on a topic, organizing research citations with key findings, or synthesizing references across sessions. Supports PMID/DOI detection, deduplication, tags, search, and JSON export. Works cross-platform (Windows, macOS, Linux).
version: 2.0.0
---

# Annotated Bibliography Skill

Build research bibliographies efficiently across sessions without context bloat.

## Workflow

1. **Search** -- Find sources via web search, collect URLs
2. **Fetch** -- Retrieve content via web fetch, pipe to format_entry.py
3. **Annotate** -- Add key findings immediately (do not defer)
4. **Repeat** -- Append new entries to the same bibliography file
5. **Synthesize** -- Generate clean summary for writing

## Quick Start

### Create a new bibliography

```bash
echo '{"url": "https://example.com/article", "content": "Article text..."}' | \
  python scripts/format_entry.py -o bibliography.md -t "Research Topic"
```

### Append an entry with annotation and tags

```bash
echo '{"url": "...", "content": "..."}' | \
  python scripts/format_entry.py -o bibliography.md -a \
    --annotation "Key finding: X reduces Y by 50%" \
    --tags "RCT,nutrition,meta-analysis"
```

### Manage entries

```bash
# List all entries ([x] = annotated, [ ] = needs annotation)
python scripts/manage_bib.py list bibliography.md

# Show only unannotated entries
python scripts/manage_bib.py list bibliography.md -u

# Search across titles, URLs, annotations, and tags
python scripts/manage_bib.py search bibliography.md "allostatic load"
python scripts/manage_bib.py search bibliography.md "cortisol" --tags "RCT"

# Add annotation by entry ID or URL substring
python scripts/manage_bib.py annotate bibliography.md AB001 "N=500 RCT showing 40% improvement"
python scripts/manage_bib.py annotate bibliography.md "nature.com/123" "Key finding text"

# Show statistics (entry counts, tag distribution, sources)
python scripts/manage_bib.py stats bibliography.md

# Generate summary (markdown or JSON)
python scripts/manage_bib.py summary bibliography.md -o summary.md
python scripts/manage_bib.py summary bibliography.md --format json
```

Note: Use `python` on all platforms. Claude Code's Bash tool resolves the correct interpreter.

## Scripts Reference

### format_entry.py

Format fetched content into structured bibliography entries.

**Input:** JSON via stdin or file with `url` and `content` fields.

| Flag | Description |
|------|-------------|
| `--input, -i` | Input JSON file (alternative to stdin) |
| `--output, -o` | Output markdown file |
| `--append, -a` | Append to existing file (with dedup check) |
| `--topic, -t` | Section header for new files |
| `--annotation` | Key findings text |
| `--title` | Override extracted title |
| `--authors` | Override authors (comma-separated) |
| `--date` | Override date |
| `--tags` | Comma-separated tags (rendered as #tag) |
| `--json` | Output structured JSON instead of markdown |
| `--force` | Skip deduplication check |

**Features:**
- **Entry IDs**: Each entry receives a sequential ID (AB001, AB002, ...) for reliable referencing
- **PMID/DOI detection**: Automatically extracts from PubMed/PMC URLs and content text; renders as clickable links
- **Deduplication**: Skips URLs already present in the bibliography (override with `--force`)
- **Smart truncation**: Preserves beginning (title/abstract) and end (conclusions) of long content

### manage_bib.py

Manage, search, and export bibliography files.

| Command | Description |
|---------|-------------|
| `list FILE` | List all entries with annotation status |
| `list FILE -u` | List only unannotated entries |
| `search FILE QUERY` | Search titles, URLs, annotations, tags |
| `search FILE QUERY --tags T` | Filter search results by tag |
| `annotate FILE PATTERN TEXT` | Add annotation by entry ID or URL substring |
| `stats FILE` | Entry counts, tag distribution, source breakdown |
| `summary FILE` | Generate summary of annotated entries |
| `summary FILE --format json` | Export annotated entries as JSON |
| `summary FILE -o OUT` | Write summary to file |

## Entry Format

```markdown
### [AB001] Author (2024). **Title**. *source.com*
**URL:** https://example.com/article
**PMID:** [12345678](https://pubmed.ncbi.nlm.nih.gov/12345678/) | **DOI:** [10.1234/example](https://doi.org/10.1234/example)
**Tags:** #nutrition #RCT #meta-analysis

**Key Findings:**
1. Primary finding with effect size
2. Secondary finding with clinical relevance
3. Limitation or caveat

<details><summary>Content preview (click to expand)</summary>

```
Extracted text from source...
```
</details>
```

All fields except URL are optional. Entries without IDs, tags, or identifiers still parse correctly (backward compatible with v1 bibliographies).

## Recommended Workflow

### Phase 1: Collect URLs
After each web search, save promising URLs to a tracking list or add entries directly.

### Phase 2: Fetch and Format
For each URL, fetch content and pipe to the formatter. Annotate immediately -- do not defer annotation to end of session.

### Phase 3: Search and Organize
Use `search` and `stats` to identify gaps. Filter by tags to focus on specific subtopics.

### Phase 4: Synthesize
Generate a summary for writing. Use `--format json` for programmatic downstream processing.

## Context-Efficient Pattern

When approaching context limits:
1. Save current progress to the bibliography file
2. On resume: load only `summary.md` (not the full bibliography)
3. Full content stays in files, not the context window

## Tips

- Annotate entries immediately after fetching -- do not batch annotations
- Match entries by ID (AB001) for reliability, URL substrings as fallback
- Use tags consistently across entries for effective filtering
- Topic headers help organize multi-gap research within a single file
- The `summary` command excludes unannotated entries
- Use `--json` output for integration with other tools or scripts
