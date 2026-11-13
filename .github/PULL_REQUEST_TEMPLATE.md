## Summary of Changes

Provide a clear and concise description of what this PR introduces, fixes, or enhances.

---

## Invariants & Compliance Checklist

Please ensure all checks are satisfied before submitting:

- [ ] **Agent Skills Specification**: `SKILL.md` remains concise (< 500 lines) with proper YAML frontmatter.
- [ ] **Zero Cloud Dependencies**: No Notion, cloud database, or third-party drawing board requirements introduced.
- [ ] **Deterministic Tooling**: Python scripts use standard library only (no external pip dependencies).
- [ ] **Idempotent State**: `advance-cursor.py` and `import-curriculum.py` update state without corrupting `manifest.json`.
- [ ] **Verification**: Ran `python3 skills/system-design-studio/scripts/verify-instance.py` and passed with 0 errors.
- [ ] **Interactive HTML Pedagogy**: Any lesson changes preserve Tailwind styling, embedded simulator, and reality check accordions.

---

## Test Output

```text
Paste output of `python3 skills/system-design-studio/scripts/verify-instance.py` here.
```
