---
name: annotated-bibliography
description: Create and manage annotated bibliographies for research projects. Use when building literature reviews, gathering sources on a topic, or organizing research with citations and key findings. Handles web search → URL collection → content fetching → structured annotation workflow. Ideal for research synthesis that spans multiple sessions or hits context limits.
---

# Annotated Bibliography Skill

Build research bibliographies efficiently across sessions without context bloat.

## Workflow Overview

1. **Search** → Use web_search to find sources, collect URLs
2. **Fetch** → Use web_fetch to get content, pipe to format_entry.py
3. **Annotate** → Add key findings via manage_bib.py or directly
4. **Repeat** → Append new topics to same bibliography file
5. **Synthesize** → Generate clean summary when ready to write

## Quick Start

### Single Entry (inline)
```bash
# After web_fetch, save content to JSON and format
echo '{"url": "https://example.com/article", "content": "Article text here..."}' | \
  python3 scripts/format_entry.py -o bibliography.md -t "Topic Name"
```

### Batch Processing
```bash
# Append additional entries
echo '{"url": "...", "content": "..."}' | \
  python3 scripts/format_entry.py -o bibliography.md -a

# With annotation
echo '{"url": "...", "content": "..."}' | \
  python3 scripts/format_entry.py -o bibliography.md -a --annotation "Key finding: X reduces Y by 50%"
```

## Scripts

### format_entry.py

Formats fetched content into structured bibliography entries.

**Input:** JSON via stdin or file with `url` and `content` fields

**Arguments:**
- `--input, -i` - Input JSON file
- `--output, -o` - Output markdown file
- `--append, -a` - Append to existing file
- `--topic, -t` - Section header (for new files)
- `--annotation` - Add key findings text
- `--title` - Override extracted title
- `--authors` - Override authors (comma-separated)
- `--date` - Override date

### manage_bib.py

Manage and annotate bibliography files.

```bash
# List entries (✓=annotated, ○=needs annotation)
python3 scripts/manage_bib.py list bibliography.md

# Show only unannotated
python3 scripts/manage_bib.py list bibliography.md -u

# Add annotation (match URL substring)
python3 scripts/manage_bib.py annotate bibliography.md "nature.com/123" "Key finding text"

# Generate clean summary
python3 scripts/manage_bib.py summary bibliography.md -o summary.md
```

## Recommended Workflow for Research Projects

### Phase 1: Collect URLs
After each web_search, save promising URLs to a tracking file:
```bash
echo "https://pmc.ncbi.nlm.nih.gov/articles/PMC123/" >> urls_topic1.txt
```

### Phase 2: Fetch and Format
For each URL, use web_fetch then pipe content to formatter:
```python
# Pattern: fetch content, extract key text, format entry
content = fetch_result['text']  # from web_fetch
entry_json = json.dumps({"url": url, "content": content})
# Then run format_entry.py
```

### Phase 3: Annotate
Review entries and add findings:
```bash
python3 scripts/manage_bib.py annotate bib.md "pmc.ncbi" "N=500 RCT showing 40% improvement"
```

### Phase 4: Synthesize
Generate summary for writing:
```bash
python3 scripts/manage_bib.py summary bibliography.md -o synthesis_ready.md
```

## Context-Efficient Pattern

When approaching context limits:
1. Save current progress to bibliography file
2. On resume: load only summary.md (not full bibliography)
3. Full content stays in files, not context window

## Entry Format

```markdown
### Author (2024). **Title**. *source.com*
**URL:** https://...

**Key Findings:**
Annotation text here

<details><summary>Content preview</summary>
```
Full extracted text...
```
</details>
```

## Tips

- Annotate as you go - don't wait until end
- Use URL substrings for matching (e.g., "PMC123" not full URL)
- Topic headers help organize multi-gap research
- Summary output excludes unannotated entries
