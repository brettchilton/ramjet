---
description: End session cleanup - update docs, remove temp files, mark completed brief items
---

Now that we've completed our work, please perform the following cleanup tasks based on the project's documentation standards.

**First**: Read `/docs/README.md` to understand the documentation structure and conventions.

---

## 1. Document New Work

- [ ] Update `docs/FEATURE_OVERVIEW.md` if new features were added
- [ ] Update `docs/PROJECT_OVERVIEW.md` if architecture or capabilities changed
- [ ] Update `docs/BACKEND_STRUCTURE.md` if API endpoints or services changed
- [ ] Update `docs/FRONTEND_SETUP.md` if UI components or patterns changed
- [ ] Update `docs/DATABASE_SETUP.md` if schema or migrations changed
- [ ] Update `docs/AUTHENTICATION.md` or `docs/KRATOS_SETUP.md` if auth changed
- [ ] Create/update feature plan docs in `docs/feature_plans/` for new feature implementations
- [ ] Add handover notes to `docs/handover_docs/` for bug fixes or complex changes

**Naming**: Use UPPER_SNAKE_CASE for top-level docs, lowercase with hyphens for subdirectory files

---

## 2. Update Core Docs

- [ ] Update `docs/README.md` if new docs were added or project setup changed
- [ ] Update `docs/DEVELOPMENT.md` if development workflow changed
- [ ] Add troubleshooting notes to `docs/README.md` troubleshooting section

---

## 3. Archive Session Notes

- [ ] Move any `SESSION_*.md` files to `docs/archive/sessions/` with format `YYYY-MM-DD_brief-description.md`
- [ ] Move completed briefs to `docs/archive/briefs/`
- [ ] Add archive banner to moved files:
  ```markdown
  > **ARCHIVED**: This is a historical implementation brief. See [PROJECT_OVERVIEW.md](../../PROJECT_OVERVIEW.md) for current status.
  ```
- [ ] Mark completed items in briefs with "Completed [DD.MM.YY]"

---

## 4. Clean Up Code & Files

- [ ] Remove temporary files, test scripts, or helper files created during development
- [ ] Clean up any debugging code or console.logs
- [ ] Remove unused imports or commented-out code
- [ ] Delete any temporary configuration files
- [ ] Verify no conflicting documentation exists

---

## 5. Quality Verification

Before finishing, verify:

- [ ] All internal doc links work (use relative paths)
- [ ] No secrets or sensitive data committed
- [ ] No duplicate/conflicting documentation
- [ ] File naming follows conventions

---

## Summary

After completing these tasks, provide a summary of:

- Which docs were created/updated and why
- What files were archived or removed
- Which brief items were marked complete
- Any issues or incomplete items to note for next session
