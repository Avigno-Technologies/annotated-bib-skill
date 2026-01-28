# annotated-bib-skill
'Skill' for Claude to better manage web search and context management
# Annotated Bibliography Skill: STAR Overview

## Situation

During a complex research-to-publication project on AI, granular data, and behavior change, we encountered a critical workflow problem: systematic literature searches were accumulating raw content in the context window, leading to compaction and loss of research progress. The project required synthesizing 33+ peer-reviewed sources across multiple research domains (behavior change, digital health, personality psychology, neurochemistry) to support an evidence-based thesis.

## Task

Create a reusable skill that would:
1. Preserve research findings across long sessions without context window bloat
2. Provide a structured, consistent format for capturing source annotations
3. Enable efficient retrieval and synthesis of findings during content creation
4. Be transferable to future research projects with similar requirements

## Action

We developed the **annotated-bibliography skill** with the following components:

**Workflow Design:**
- Search → Fetch → Format entry immediately (rather than accumulating raw content)
- Store findings in external file, not context
- Reference file when synthesizing

**Structured Entry Format:**
Each bibliography entry captures:
- Full citation with authors, year, title, and journal
- URL for source retrieval
- Key Findings section (3-5 bullet points of most relevant insights)
- Collapsible content preview for reference without context bloat

**Organization Schema:**
- Entries organized by research gap/topic area
- Sequential numbering for easy reference
- Markdown formatting for readability and portability

**File Management:**
- Entries appended to persistent external file (`gap1_bibliography.md`)
- File serves as single source of truth for literature review
- Can be referenced during synthesis without re-loading full content

## Result

**Quantitative Outcomes:**
- 33 sources preserved across the session without loss
- Zero context compaction failures after adoption
- Single-session completion of full research-to-publication pipeline

**Qualitative Outcomes:**
- Research synthesis maintained consistency and traceability
- Evidence claims in final blog post directly linked to bibliography entries
- Skill documentation created for reuse in future projects

**Transferable Asset:**
- Workflow documentation
- Entry formatting templates
- Best practices for context-efficient research synthesis
- Integration guidance with other document creation skills
