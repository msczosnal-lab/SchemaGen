#!/usr/bin/env python3
"""SchemaGen EPLAN MCP server — zamknięty obieg z EPLAN P8 2025."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT = REPO_ROOT / "scripts" / "build_addin.ps1"
MVP_SCRIPT = Path(r"C:\Users\Public\EPLAN\Data\Skrypty\Schemagen\SchemaGen_MVP.cs")
OUTPUT_DIR = Path(r"C:\Users\Public\EPLAN\Data\Skrypty\Schemagen\output")
LAYOUT_AUDIT = OUTPUT_DIR / "layout-audit.json"
CONNECTIONS_CSV = OUTPUT_DIR / "connections.csv"
VALIDATION_REPORT = OUTPUT_DIR / "validation-report.json"
VALIDATION_SCRIPT = REPO_ROOT / "scripts" / "validation" / "validate_connections.py"

EPLAN_CANDIDATES = [
    Path(r"C:\Program Files\EPLAN\Platform\2025.0.3\Bin\EPLAN.exe"),
    Path(r"C:\Program Files\EPLAN\Platform\2024.0.3\Bin\EPLAN.exe"),
    Path(r"C:\Program Files (x86)\EPLAN\Platform\2025.0.3\Bin\EPLAN.exe"),
]


def _find_eplan_exe() -> Path | None:
    env = os.environ.get("EPLAN_EXE")
    if env and Path(env).exists():
        return Path(env)
    for candidate in EPLAN_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


def _run_powershell(script: Path, *args: str) -> dict:
    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script),
        *args,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
    return {
        "ok": proc.returncode == 0,
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def _run_eplan_action(action_line: str, timeout: int = 600) -> dict:
    eplan = _find_eplan_exe()
    if eplan is None:
        return {"ok": False, "error": "Nie znaleziono EPLAN.exe. Ustaw EPLAN_EXE lub zainstaluj EPLAN P8."}

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(eplan),
        '/Variant:"Electric P8"',
        "/NoLoadWorkspace",
        "/Auto",
        "/Quiet",
        action_line,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return {
        "ok": proc.returncode == 0,
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "command": " ".join(cmd),
    }


def eplan_build_addin() -> str:
    result = _run_powershell(BUILD_SCRIPT)
    return json.dumps(result, ensure_ascii=False, indent=2)


def eplan_run_script() -> str:
    if not MVP_SCRIPT.exists():
        return json.dumps(
            {
                "ok": False,
                "error": f"Brak skryptu MVP: {MVP_SCRIPT}",
                "hint": "Skopiuj scripts/SchemaGen_MVP.cs do Skrypty\\Schemagen\\",
            },
            ensure_ascii=False,
            indent=2,
        )

    script_arg = f'/ScriptFile:"{MVP_SCRIPT}"'
    result = _run_eplan_action(f"ExecuteScript {script_arg}")
    result["mvp_script"] = str(MVP_SCRIPT)
    return json.dumps(result, ensure_ascii=False, indent=2)


def eplan_get_layout(page_name: str = "") -> str:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output = str(LAYOUT_AUDIT)
    action = (
        f'SchemaGenAuditLayout /SILENT:1 /OUTPUTPATH:"{output}"'
    )
    if page_name:
        action += f' /PAGENAME:"{page_name}"'

    run = _run_eplan_action(action)
    payload: dict = {"run": run, "output_path": output}
    if LAYOUT_AUDIT.exists():
        try:
            payload["layout"] = json.loads(LAYOUT_AUDIT.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            payload["parse_error"] = str(exc)
    else:
        payload["layout"] = None
    return json.dumps(payload, ensure_ascii=False, indent=2)


def eplan_export_connections() -> str:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output = str(CONNECTIONS_CSV)
    run = _run_eplan_action(f'SchemaGenExportConnections /SILENT:1 /OUTPUTPATH:"{output}"')
    payload: dict = {"run": run, "csv_path": output, "exists": CONNECTIONS_CSV.exists()}
    if CONNECTIONS_CSV.exists():
        payload["size_bytes"] = CONNECTIONS_CSV.stat().st_size
    return json.dumps(payload, ensure_ascii=False, indent=2)


def eplan_validate_and_report() -> str:
    """Faza 2: eksport CSV → reguły walidacji → raport JSON."""
    export = json.loads(eplan_export_connections())
    if not export.get("exists"):
        return json.dumps(
            {"ok": False, "stage": "export", "export": export},
            ensure_ascii=False,
            indent=2,
        )

    if not VALIDATION_SCRIPT.exists():
        return json.dumps(
            {
                "ok": False,
                "stage": "validate",
                "error": f"Brak skryptu walidacji: {VALIDATION_SCRIPT}",
                "export": export,
            },
            ensure_ascii=False,
            indent=2,
        )

    proc = subprocess.run(
        [sys.executable, str(VALIDATION_SCRIPT), str(CONNECTIONS_CSV), str(VALIDATION_REPORT)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    report = None
    if VALIDATION_REPORT.exists():
        try:
            report = json.loads(VALIDATION_REPORT.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            report = {"raw": VALIDATION_REPORT.read_text(encoding="utf-8")}

    return json.dumps(
        {
            "ok": proc.returncode == 0,
            "exit_code": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "report_path": str(VALIDATION_REPORT),
            "report": report,
            "export": export,
        },
        ensure_ascii=False,
        indent=2,
    )


def eplan_closed_loop() -> str:
    """Pełna pętla: build → run MVP → layout audit → walidacja CSV."""
    steps = {
        "build": json.loads(eplan_build_addin()),
        "run": json.loads(eplan_run_script()),
        "layout": json.loads(eplan_get_layout()),
        "validation": json.loads(eplan_validate_and_report()),
    }
    ok = (
        steps["build"].get("ok", False)
        and steps["run"].get("ok", False)
        and steps["validation"].get("ok", False)
    )
    return json.dumps({"ok": ok, "steps": steps}, ensure_ascii=False, indent=2)


TOOLS = {
    "eplan_build_addin": {
        "description": "Kompiluje i kopiuje SchemaGen.EplAddIn..dll do folderu EPLAN Skrypty\\Schemagen",
        "handler": lambda _args: eplan_build_addin(),
    },
    "eplan_run_script": {
        "description": "Uruchamia SchemaGen_MVP.cs w EPLAN (headless /Auto /Quiet)",
        "handler": lambda _args: eplan_run_script(),
    },
    "eplan_get_layout": {
        "description": "Wywołuje SchemaGenAuditLayout i zwraca JSON bbox vs ramka strony",
        "handler": lambda args: eplan_get_layout(args.get("page_name", "")),
    },
    "eplan_export_connections": {
        "description": "Eksportuje listę połączeń do CSV (XExport)",
        "handler": lambda _args: eplan_export_connections(),
    },
    "eplan_validate_and_report": {
        "description": "Eksport CSV + reguły walidacji → validation-report.json",
        "handler": lambda _args: eplan_validate_and_report(),
    },
    "eplan_closed_loop": {
        "description": "Build → run MVP → layout audit → walidacja CSV (pełna pętla Faza 2)",
        "handler": lambda _args: eplan_closed_loop(),
    },
}


def _handle_request(request: dict) -> dict:
    method = request.get("method")
    req_id = request.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "schemagen-eplan", "version": "0.1.0"},
            },
        }

    if method == "notifications/initialized":
        return None

    if method == "tools/list":
        tools = [
            {
                "name": name,
                "description": spec["description"],
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "page_name": {
                            "type": "string",
                            "description": "Opcjonalna nazwa strony dla eplan_get_layout",
                        }
                    },
                },
            }
            for name, spec in TOOLS.items()
        ]
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": tools}}

    if method == "tools/call":
        params = request.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments") or {}
        if tool_name not in TOOLS:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"},
            }
        try:
            content = TOOLS[tool_name]["handler"](arguments)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": content}]},
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32000, "message": str(exc)},
            }

    if method == "ping":
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue
        response = _handle_request(request)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
