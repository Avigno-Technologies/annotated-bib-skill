#!/usr/bin/env python3
"""
Create annotated bibliography entries from fetched content.
Accepts JSON input with URL and content, outputs formatted markdown entries.

Usage:
  # From JSON input (piped or file)
  echo '{"url": "...", "content": "..."}' | python3 format_entry.py
  
  # From JSON file
  python3 format_entry.py -i fetched_content.json -o bibliography.md
  
  # Add annotation directly
  python3 format_entry.py -i content.json -o bib.md --annotation "Key findings here"
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


def extract_metadata_from_content(content, url):
    """Extract metadata heuristically from text content."""
    lines = content.split('\n')
    
    # Title: usually first non-empty line or line with specific patterns
    title = None
    for line in lines[:20]:
        line = line.strip()
        if line and len(line) > 10 and len(line) < 200:
            # Skip navigation-like lines
            if not any(skip in line.lower() for skip in ['cookie', 'menu', 'search', 'login', 'sign in']):
                title = line
                break
    
    # Try to find authors (look for patterns like "by Author" or "Author et al")
    authors = []
    author_patterns = [
        r'[Bb]y\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
        r'([A-Z][a-z]+(?:,?\s+[A-Z]\.?\s*)+(?:\s+et\s+al\.?)?)',
    ]
    for pattern in author_patterns:
        matches = re.findall(pattern, content[:2000])
        if matches:
            authors = matches[:3]
            break
    
    # Date patterns
    date = None
    date_patterns = [
        r'(\d{4}-\d{2}-\d{2})',
        r'([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})',
        r'(\d{1,2}\s+[A-Z][a-z]+\s+\d{4})',
    ]
    for pattern in date_patterns:
        match = re.search(pattern, content[:3000])
        if match:
            date = match.group(1)
            break
    
    # Source from URL
    source = urlparse(url).netloc.replace('www.', '')
    
    return {
        'title': title,
        'authors': authors if isinstance(authors, list) else [authors] if authors else [],
        'date': date,
        'source': source
    }


def format_entry(url, content, title=None, authors=None, date=None, source=None, annotation=None):
    """Format a single bibliography entry in markdown."""
    
    # Use provided metadata or extract from content
    if not any([title, authors, date]):
        extracted = extract_metadata_from_content(content, url)
        title = title or extracted['title']
        authors = authors or extracted['authors']
        date = date or extracted['date']
        source = source or extracted['source']
    else:
        source = source or urlparse(url).netloc.replace('www.', '')
    
    # Build citation line
    parts = []
    if authors:
        author_str = ', '.join(authors[:3]) if isinstance(authors, list) else authors
        if isinstance(authors, list) and len(authors) > 3:
            author_str += ' et al.'
        parts.append(author_str)
    if date:
        year = date[:4] if len(date) >= 4 else date
        parts.append(f"({year})")
    if title:
        # Clean title
        title = title.strip()
        if len(title) > 150:
            title = title[:147] + "..."
        parts.append(f"**{title}**")
    if source:
        parts.append(f"*{source}*")
    
    citation = '. '.join(parts) if parts else "*(metadata unavailable)*"
    
    output = f"### {citation}\n"
    output += f"**URL:** {url}\n\n"
    
    if annotation:
        output += f"**Key Findings:**\n{annotation}\n\n"
    
    # Include content snippet
    content_preview = content[:3000].strip()
    if len(content) > 3000:
        content_preview += "\n\n[...truncated...]"
    
    output += f"<details><summary>Content preview (click to expand)</summary>\n\n"
    output += f"```\n{content_preview}\n```\n</details>\n"
    
    return output


def main():
    parser = argparse.ArgumentParser(description='Format bibliography entries from fetched content')
    parser.add_argument('--input', '-i', help='Input JSON file with fetched content')
    parser.add_argument('--output', '-o', help='Output markdown file')
    parser.add_argument('--append', '-a', action='store_true', help='Append to output file')
    parser.add_argument('--topic', '-t', help='Topic/section header')
    parser.add_argument('--annotation', help='Annotation to add')
    parser.add_argument('--title', help='Override title')
    parser.add_argument('--authors', help='Override authors (comma-separated)')
    parser.add_argument('--date', help='Override date')
    
    args = parser.parse_args()
    
    # Read input
    if args.input:
        with open(args.input) as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)
    
    # Handle single entry or list
    entries = data if isinstance(data, list) else [data]
    
    # Format output
    output = ""
    if args.topic and not args.append:
        output += f"## {args.topic}\n\n"
        output += f"*Processed: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"
    
    for entry in entries:
        url = entry.get('url', entry.get('source_url', 'Unknown URL'))
        content = entry.get('content', entry.get('text', ''))
        
        # Allow metadata override
        title = args.title or entry.get('title')
        authors = args.authors.split(',') if args.authors else entry.get('authors')
        date = args.date or entry.get('date')
        
        output += format_entry(
            url=url,
            content=content,
            title=title,
            authors=authors,
            date=date,
            annotation=args.annotation
        )
        output += "\n---\n\n"
    
    # Write output
    if args.output:
        mode = 'a' if args.append else 'w'
        with open(args.output, mode) as f:
            if args.append:
                f.write("\n")
            f.write(output)
        print(f"{'Appended to' if args.append else 'Wrote'}: {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == '__main__':
    main()
