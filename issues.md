# Issues Found

| Issue | Type | Line(s) | Description | Fix Approach |
|-------|------|---------|-------------|--------------|
| os.system with string concat (B605) | Security (High) | 68 | `printLabel` builds a shell command from the medicine name, so a name like `x; rm -rf /` runs arbitrary commands | Removed the shell; print the label directly |
| Weak MD5 hash (B324) | Security (High) | 51 | MD5 is broken and unsuitable for identifiers built from personal data | Switched to SHA-256 (with a `\|` separator between name and phone) |
| eval on doctor's note (B307 / W0123) | Security (Medium) | 48 | `eval(formula)` executes arbitrary code from input | Replaced with an AST-based evaluator allowing only numbers and + - * / |
| pickle load/dump (B301, B403) | Security (Medium) | 3, 64 | Unpickling a tampered stock file can execute code | Store stock as JSON |
| Hardcoded password (B105) | Security (Low) | 11 | `DB_PASSWORD` in source code and in version control | Read from `PHARMACY_PASSWORD` env var; `hmac.compare_digest` |
| `random` for Rx numbers (B311) | Security (Low) | 54 | Predictable numbers | `secrets.randbelow` |
| Bare except + pass (E722, W0702, B110) | Bug | 27 | `dispenseMedicine("Insulin")` fails silently, and any error is hidden | Validate and raise `ValueError` with a clear message |
| Mutable default `audit=[]` (W0102) | Bug | 13 | The list is shared across all calls, so audit logs leak between calls | Default `None`, create a new list inside |
| No input validation | Bug (logic) | 13-20 | Negative qty gave -10 units of stock; numeric name `404` accepted | Validate name, qty, price and expiry; raise `ValueError` |
| Over-dispensing and expired stock | Bug (logic) | 22-27, 40-43 | More units than in stock could be dispensed; expired medicine could be dispensed and billed | Check stock and expiry before dispensing/billing |
| File not closed on error (R1732) | Quality | 57-59, 62-65 | `open()` without `with` can leak file handles | Use `with open(..., encoding="utf-8")` |
| `global medicines` (W0603) | Quality | 63 | Rebinding a global makes code hard to follow | Mutate in place with `clear()` / `update()` |
| camelCase names, missing docstrings (C0103, C0116, C0114) | Style | many | Not PEP 8 / PEP 257 | snake_case names and docstrings |
| Unused imports `sys`, `logging` (F401, W0611) | Style | 2, 6 | Dead code | Removed |
| Blank lines, long lines, missing final newline (E302, E305, E501, W292) | Style | many | PEP 8 formatting | Reformatted with autopep8 |
| Code runs on import | Quality | 108 | `main()` was called at module level | Added `if __name__ == "__main__":` |

Line numbers refer to the original file.