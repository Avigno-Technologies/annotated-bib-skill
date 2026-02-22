# Annotated Bibliography Skill for Claude Code

A Claude Code skill for building and managing research bibliographies across sessions without exhausting the context window.

## Features

- **Entry IDs** -- Sequential IDs (AB001, AB002, ...) for reliable referencing
- **PMID/DOI detection** -- Auto-extracts from PubMed/PMC URLs and content; renders as clickable links
- **Deduplication** -- Prevents duplicate entries when appending
- **Tags** -- Categorize entries with hashtags for filtering and search
- **Search** -- Full-text search across titles, URLs, annotations, and tags
- **Statistics** -- Entry counts, annotation coverage, tag and source distribution
- **JSON export** -- Structured output for programmatic downstream processing
- **Smart truncation** -- Preserves abstract and conclusions when trimming long content
- **Cross-platform** -- Works on Windows, macOS, and Linux (Python stdlib only)
- **Backward compatible** -- Parses v1 bibliographies without entry IDs or tags

## Installation

### Option 1: Install the .skill file (recommended)

Download `annotated-bibliography.skill` and copy it to your project or user skills directory:

```bash
# Project-level (scoped to one repo)
mkdir -p .claude/skills
cp annotated-bibliography.skill .claude/skills/

# User-level (available in all projects)
# macOS/Linux:
cp annotated-bibliography.skill ~/.claude/skills/
# Windows:
copy annotated-bibliography.skill %USERPROFILE%\.claude\skills\
```

Restart Claude Code. The skill will be available via `/annotated-bibliography`.

### Option 2: Use the scripts directly

Clone the repo and use the Python scripts without the skill wrapper:

```bash
git clone https://github.com/Avigno-Technologies/annotated-bib-skill.git
cd annotated-bib-skill

# Create a bibliography
echo '{"url": "https://example.com", "content": "Article text"}' | \
  python scripts/format_entry.py -o my_bibliography.md -t "Research Topic"

# List entries
python scripts/manage_bib.py list my_bibliography.md
```

## Quick Start

```bash
# 1. Create a new bibliography with a topic header
echo '{"url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC1495095/", "content": "McGee 2002..."}' | \
  python scripts/format_entry.py -o bib.md -t "Likelihood Ratios" \
    --annotation "LR 2 = +15%, LR 5 = +30%, LR 10 = +45%" \
    --tags "EBM,clinical-decision"

# 2. Append more entries (auto-dedup, auto-PMID detection)
echo '{"url": "https://pubmed.ncbi.nlm.nih.gov/35393143/", "content": "ALI meta-analysis..."}' | \
  python scripts/format_entry.py -o bib.md -a \
    --annotation "HR 1.24 per unit ALI increase (95% CI: 1.22-1.27)" \
    --tags "allostatic-load,meta-analysis"

# 3. Search, list, and get stats
python scripts/manage_bib.py search bib.md "meta-analysis"
python scripts/manage_bib.py list bib.md
python scripts/manage_bib.py stats bib.md

# 4. Generate summary for writing
python scripts/manage_bib.py summary bib.md -o summary.md
python scripts/manage_bib.py summary bib.md --format json
```

## Requirements

- Python 3.7+ (stdlib only, no external dependencies)

## License

GPL-3.0
