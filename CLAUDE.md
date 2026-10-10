# AA-Industry (Industry Reforged) - Agent Guidelines

> **Hoofdrichtlijn:** Dit project volgt strikt de centrale richtlijnen in het hoofd-instructiedocument:
> 👉 **[Workspace AGENTS.md](file:///g:/My%20Drive/Workbench%20001/AGENTS.md)**
> Zie tevens het lokale projectdocument: **[AGENTS.md](file:///g:/My%20Drive/Workbench%20001/plugins/aa-industry/AGENTS.md)**
> Lees tevens altijd eerst [.agent/memory.md](file:///g:/My%20Drive/Workbench%20001/.agent/memory.md) vóór analyse of modificaties.

<!-- BACKLOG.MD MCP GUIDELINES START -->
<!-- backlog.md-instructions-version: 1.53.0 -->

<CRITICAL_INSTRUCTION>

## BACKLOG WORKFLOW INSTRUCTIONS

This project uses Backlog.md MCP for all task and project management activities.

**CRITICAL GUIDANCE**

- If your client supports MCP resources, read `backlog://workflow/overview` to understand when and how to use Backlog for this project.
- If your client only supports tools or the above request fails, call `backlog.get_backlog_instructions()` to load the tool-oriented overview. Use the `instruction` selector when you need `task-creation`, `task-execution`, or `task-finalization`.

- **First time working here?** Read the overview resource IMMEDIATELY to learn the workflow
- **Already familiar?** You should have the overview cached ("## Backlog.md Overview (MCP)")
- **When to read it**: BEFORE creating tasks, or when you're unsure whether to track work

These guides cover:
- Decision framework for when to create tasks
- Search-first workflow to avoid duplicates
- Links to detailed guides for task creation, execution, and finalization
- MCP tools reference

You MUST read the overview resource to understand the complete workflow. The information is NOT summarized here.

</CRITICAL_INSTRUCTION>

<!-- BACKLOG.MD MCP GUIDELINES END -->

## Project Context & Backlog MCP Koppeling

- **Project / App:** `industry_reforged` (`plugins/aa-industry`)
- **Backlog Directory:** `plugins/aa-industry/backlog/`
- **MCP & Tooling Regels:**
  - Alle `backlog-md` taken en CLI commando's worden uitgevoerd binnen de werkmap `plugins/aa-industry`.
  - Vóór elke codewijziging: consulteer en registreer de taak via `backlog-md`.
  - Alle Python/Django/Alliance Auth codeer-, test- en stylingstandaarden zijn gedefinieerd in [AGENTS.md](file:///g:/My%20Drive/Workbench%20001/AGENTS.md) en [plugins/aa-industry/AGENTS.md](file:///g:/My%20Drive/Workbench%20001/plugins/aa-industry/AGENTS.md).
