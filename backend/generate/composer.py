"""Generowanie schematu z blokow i konfiguracji."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from backend.models.schema import Component, Connection, SchemaMeta, SchemaModel, UserIntent
from backend.paths import BLOCKS, DRIVE_CONFIG


def _load_block(name: str) -> dict:
    path = BLOCKS / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Brak bloku: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_drive_xml(xml_path: Path) -> UserIntent:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    vars_map = {
        el.get("name", ""): (el.text or "").strip()
        for el in root.iter("ConfigurationVariable")
    }
    power = vars_map.get("SE_Drive_Type", "")
    power_kw = None
    if power:
        cleaned = power.replace("kW", "").replace(",", ".").strip()
        try:
            power_kw = float(cleaned)
        except ValueError:
            pass
    return UserIntent(
        drive_type=vars_map.get("SE_Drive_Control", ""),
        power_kw=power_kw,
        control=vars_map.get("SE_Drive_Control", ""),
    )


def _select_blocks(intent: UserIntent) -> list[str]:
    blocks = ["400vac_supply"]
    if "frequency" in intent.drive_type.lower():
        blocks.append("frequency_control")
    blocks.append("start_stop")
    return blocks


class BlockComposer:
    """Sklada SchemaModel z biblioteki blokow."""

    def compose_from_config(self, config_path: str | Path | None = None) -> SchemaModel:
        config_path = Path(config_path or DRIVE_CONFIG)
        intent = _parse_drive_xml(config_path)
        block_names = _select_blocks(intent)
        return self.compose_blocks(block_names, intent=intent)

    def compose_blocks(
        self,
        block_names: list[str],
        intent: UserIntent | None = None,
    ) -> SchemaModel:
        components: list[Component] = []
        connections: list[Connection] = []
        potentials: set[str] = set()
        x_offset = 0.0

        for name in block_names:
            block = _load_block(name)
            dx = x_offset
            for comp in block.get("components", []):
                bbox = comp.get("bbox", [0, 0, 0, 0])
                shifted = [bbox[0] + dx, bbox[1], bbox[2] + dx, bbox[3]]
                components.append(
                    Component(
                        id=comp["id"],
                        type=comp["type"],
                        tag=comp.get("tag", ""),
                        bbox=shifted,
                        source="block",
                    )
                )
            for conn in block.get("connections", []):
                connections.append(Connection.model_validate(conn))
            for p in block.get("potentials", []):
                potentials.add(p)
            x_offset += block.get("layout_width", 200)

        return SchemaModel(
            meta=SchemaMeta(source="blocks:" + ",".join(block_names)),
            components=components,
            connections=connections,
            potentials=sorted(potentials),
            blocks=block_names,
            user_intent=intent,
        )
