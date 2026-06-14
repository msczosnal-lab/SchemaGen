"""CLI SchemaGen."""

from __future__ import annotations

import argparse
import json
import sys

from backend.db import init_db
from backend.generate.svg_renderer import generate_schematic
from backend.recognize.pipeline import recognize_file
from backend.validate.rules_engine import validate_model


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="schemagen", description="SchemaGen offline CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_rec = sub.add_parser("recognize", help="PDF/obraz -> SchemaModel JSON")
    p_rec.add_argument("input")
    p_rec.add_argument("-o", "--output", required=True)

    p_val = sub.add_parser("validate", help="Walidacja SchemaModel")
    p_val.add_argument("model")
    p_val.add_argument("--ground-truth")
    p_val.add_argument("-o", "--output")

    p_gen = sub.add_parser("generate", help="Config XML -> SVG schemat")
    p_gen.add_argument("-c", "--config")
    p_gen.add_argument("-o", "--output", required=True)

    p_init = sub.add_parser("init-db", help="Inicjalizacja SQLite")

    p_serve = sub.add_parser("serve", help="Uruchom FastAPI")
    p_serve.add_argument("--port", type=int, default=8780)

    args = parser.parse_args(argv)

    if args.command == "init-db":
        init_db()
        print("SQLite zainicjalizowane.")
        return 0

    if args.command == "recognize":
        model = recognize_file(args.input, args.output)
        print(json.dumps({"components": len(model.components)}, ensure_ascii=False))
        return 0

    if args.command == "validate":
        report = validate_model(args.model, args.ground_truth, args.output)
        print(json.dumps(report.model_dump(), ensure_ascii=False, indent=2))
        return 0 if report.approved else 1

    if args.command == "generate":
        model = generate_schematic(args.config, args.output)
        sidecar = args.output.rsplit(".", 1)[0] + ".json"
        with open(sidecar, "w", encoding="utf-8") as f:
            f.write(model.model_dump_json(by_alias=True, indent=2))
        print(json.dumps({"output": args.output, "model": sidecar}, ensure_ascii=False))
        return 0

    if args.command == "serve":
        import uvicorn

        uvicorn.run("backend.api.app:app", host="127.0.0.1", port=args.port, reload=False)
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
