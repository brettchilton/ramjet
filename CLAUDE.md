# Ramjet - Claude Code Instructions

## Getting Started

- Always start by reading `docs/README.md` and `docs/PROJECT_OVERVIEW.md` to familiarise yourself with the project
- Before making API or service changes, read `docs/BACKEND_STRUCTURE.md` for API architecture
- Before making auth changes, read `docs/AUTHENTICATION.md` and `docs/KRATOS_SETUP.md`
- Before making frontend changes, read `docs/FRONTEND_SETUP.md`
- Before making database changes, read `docs/DATABASE_SETUP.md`

## Communication

- Do not be a sycophant. If you think I'm asking for something that doesn't make sense or can be done better, raise it with me. We are partners together.
- Never assume something. If you are unsure, ask me.
- Be concise and direct — avoid unnecessary preamble.

## Code Quality

- Always follow modern documentation for the technology stack using `/context7`. If that returns nothing, search online.
- Follow established patterns and best practices already present in the codebase.
- Suggest the simplest solution path to avoid unnecessary complexity.
- Write test scripts to validate key milestones when implementing significant features.

## Technology Decisions

- Don't introduce a new technology, API, SDK, or dependency without consulting me first. Read `docs/PROJECT_OVERVIEW.md` so you are sure of the current stack.

## Documentation

- At the end of implementing something (when you get to the end of your todo list) always ask me if I want the `/docs` directory to be updated to reflect the changes we made during the session.

## Available Slash Commands

- `/start` - Initialize context by reading core documentation for quick project understanding
- `/context7` - Look up library documentation using Context7 MCP tools for current framework/package versions
- `/finish` - End session cleanup: update docs, remove temporary files, mark completed brief items

## Available Sub-Agents

You have these sub-agents at your disposal (defined in `.claude/agents/`):

- **code-investigator** (cyan) - Locate specific code, trace function calls, identify files for modification. Use before making changes to unfamiliar areas.
- **db-fetcher-local** (green) - Query the local Docker Compose PostgreSQL database (ramjet_db on port 5532). Default when no environment is specified.
- **docker-logs** (yellow) - Investigate Docker container logs (ramjet_backend, ramjet_postgres) for debugging errors and diagnosing issues.
