
# Bundle to a Single EXE (Windows)

## Benefits
- No Python install on operator PCs
- One file to double‑click (simpler training)
- Frozen dependencies (fewer environment issues)
- Mild code obfuscation (not true security)

## Trade‑offs
- Larger file size (40–100+ MB)
- Occasional antivirus false positives
- First launch can be slower
- Must rebuild EXE after updates

## Steps
1) Put `build_exe.ps1` next to `app.py` (and `templates/`, `static/` if used).
2) Right‑click **build_exe.ps1** → Run with PowerShell.
3) EXE appears in `dist/TelegramAdminApp.exe`.
4) Place a `.env` next to the EXE (copy from `.env.example`).
5) Double‑click the EXE, open http://127.0.0.1:8000

## Tips
- Change the port via `PORT` in `.env`.
- If templates or static aren’t found, ensure they’re included (see the script/spec).
- If DB driver errors appear, `psycopg2-binary` is recommended and is covered by `--collect-all psycopg2`.
