---
id: TASK-124
title: Fix Mermaid diagram formatting in DOC-14
status: Done
assignee: []
created_date: '2026-09-04 14:08'
updated_date: '2026-09-04 14:08'
labels: []
dependencies: []
priority: medium
type: bug
ordinal: 114000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Het Mermaid diagram in DOC-14 (Direct ESI Market Pricing Architecture and Reference Guide) rendert niet correct. Analyse wijst uit dat het gebruik van 'flowchart TD' in plaats van de in het project gangbare 'graph TD', alsmede speciale karakters (&, ?, =) binnen node labels, de Mermaid parser van viewers en Backlog browser verstoort.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 Mermaid diagram in DOC-14 gebruikt 'graph TD' en correcte syntax
- [x] #2 Node labels bevatten geen verstorende query-strings of unescaped karakters
- [x] #3 Mermaid diagram rendert correct in Markdown viewers en Backlog browser

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Mermaid diagram in doc-14 bijgewerkt naar 'graph TD' syntax en node labels opgeschoond zodat er geen unescaped query string parameters (&, ?, =) of syntaxis-brekende tokens meer in staan. Het diagram rendert nu betrouwbaar in Backlog browser en markdown viewers.

<!-- SECTION:NOTES:END -->
