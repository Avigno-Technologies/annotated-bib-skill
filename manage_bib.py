#!/usr/bin/env python3
"""
Manage annotated bibliography files.
Add annotations, organize sections, export formats.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from datetime import datetime


def add_annotation(bib_file, url_pattern, annotation):
    """Add or update annotation for a specific entry."""
    content = Path(bib_file).read_text()
    
    # Find the entry containing this URL
    pattern = rf'(### .*?\n\*\*URL:\*\* [^\n]*{re.escape(url_pattern)}[^\n]*\n\n)'
    match = re.search(pattern, content)
    
    if not match:
        print(f"Entry not found for URL pattern: {url_pattern}", file=sys.stderr)
        return False
    
    # Check if Key Findings already exists
    entry_start = match.end()
    remaining = content[entry_start:]
    
    if remaining.startswith('**Key Findings:**'):
        # Replace existing annotation
        end_pattern = r'\*\*Key Findings:\*\*\n.*?\n\n'
        content = content[:entry_start] + re.sub(
            end_pattern, 
            f'**Key Findings:**\n{annotation}\n\n', 
            remaining, 
            count=1
        )
    else:
        # Insert new annotation
        content = content[:entry_start] + f'**Key Findings:**\n{annotation}\n\n' + content[entry_start:]
    
    Path(bib_file).write_text(content)
    print(f"Updated annotation for: {url_pattern}", file=sys.stderr)
    return True


def list_entries(bib_file, unannotated_only=False):
    """List all entries in the bibliography."""
    content = Path(bib_file).read_text()
    
    # Find all entries
    entries = re.findall(r'### (.*?)\n\*\*URL:\*\* (.*?)\n', content)
    
    for i, (title, url) in enumerate(entries, 1):
        # Check if annotated
        entry_section = content[content.find(f'**URL:** {url}'):]
        has_annotation = '**Key Findings:**' in entry_section.split('---')[0]
        
        if unannotated_only and has_annotation:
            continue
            
        status = '✓' if has_annotation else '○'
        title_short = title[:70] + '...' if len(title) > 70 else title
        print(f"{i}. [{status}] {title_short}")
        print(f"   {url[:80]}")


def create_summary(bib_file, output_file=None):
    """Create a clean summary of annotated entries only."""
    content = Path(bib_file).read_text()
    
    # Extract annotated entries
    pattern = r'### (.*?)\n\*\*URL:\*\* (.*?)\n\n\*\*Key Findings:\*\*\n(.*?)\n\n'
    entries = re.findall(pattern, content, re.DOTALL)
    
    summary = f"# Annotated Bibliography Summary\n\n"
    summary += f"*Generated: {datetime.now().strftime('%Y-%m-%d')}*\n\n"
    summary += f"**{len(entries)} annotated sources**\n\n---\n\n"
    
    for title, url, findings in entries:
        summary += f"### {title}\n"
        summary += f"{url}\n\n"
        summary += f"{findings.strip()}\n\n---\n\n"
    
    if output_file:
        Path(output_file).write_text(summary)
        print(f"Summary written to: {output_file}", file=sys.stderr)
    else:
        print(summary)


def main():
    parser = argparse.ArgumentParser(description='Manage annotated bibliography files')
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # List command
    list_parser = subparsers.add_parser('list', help='List entries')
    list_parser.add_argument('bib_file', help='Bibliography file')
    list_parser.add_argument('--unannotated', '-u', action='store_true', help='Show only unannotated')
    
    # Annotate command
    ann_parser = subparsers.add_parser('annotate', help='Add annotation to entry')
    ann_parser.add_argument('bib_file', help='Bibliography file')
    ann_parser.add_argument('url_pattern', help='URL pattern to match')
    ann_parser.add_argument('annotation', help='Annotation text')
    
    # Summary command
    sum_parser = subparsers.add_parser('summary', help='Create clean summary')
    sum_parser.add_argument('bib_file', help='Bibliography file')
    sum_parser.add_argument('--output', '-o', help='Output file')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        list_entries(args.bib_file, args.unannotated)
    elif args.command == 'annotate':
        add_annotation(args.bib_file, args.url_pattern, args.annotation)
    elif args.command == 'summary':
        create_summary(args.bib_file, args.output)


if __name__ == '__main__':
    main()
