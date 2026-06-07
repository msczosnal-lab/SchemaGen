"""Build structured EPLAN API knowledge base from raw-extract.json."""
import json
import os
import re
from collections import defaultdict

ROOT = r"C:\Users\Filip\Desktop\Cursor\SchemaGen\docs\eplan-kb"
RAW = os.path.join(ROOT, "raw-extract.json")
TOPICS = os.path.join(ROOT, "topics")

# Topic routing: file pattern -> topic slug
TOPIC_MAP = {
    "scripts": [
        "Structure of a simple script",
        "Simple script with parameters",
        "Loading a script",
        "Event handling in scripts",
        "Adding ribbon items by a script",
        "Development environment",
    ],
    "datamodel": [
        "API DataModel",
        "Creating or opening projects",
        "Creating pages",
        "Navigating the project data",
        "DataModel navigation overview",
        "DataModel class diagram",
        "DMObjectsFinder overview",
        "EObjects overview",
        "Connections overview",
        "Graphics overview",
        "MasterData overview",
        "Filtering overview",
        "EPLAN properties",
        "Transactions",
        "Locking",
        "Project settings",
        "Working with parts",
        "Accessing selected objects",
    ],
    "heservices": [
        "API Higher Electrotechnical services",
        "Placing window macros",
        "Displaying a preview",
        "Pre-planning macro",
    ],
    "actions-cli": [
        "Calling actions",
        "Automatic actions",
        "Actions",
        "Command line parameters",
        "ExecuteScript",
    ],
    "addins": [
        "Add-ins",
        "Creating add-ins in CSharp",
        "Creating add-ins in Visual Basic.Net",
        "Creating an add-in in VisualStudio",
        "Registration",
        "Unregistration",
        "Assemblies",
        "Shadow Copying",
        "Shadow Copying API Assemblies",
        "Signing EPLAN assemblies",
    ],
    "pro-panel-3d": [
        "API Pro Panel",
        "InstallationSpace",
        "Component",
        "Cabinet",
        "MountingPanel",
        "MountingRail",
        "Plane",
        "Area",
        "Duct",
        "PlaceHolder3D",
        "Drilling",
        "RoutingSegment",
        "Connection3D",
        "3D macros",
        "Creating 3D objects",
        "Getting 3D objects",
        "Orientation of 3D objects",
        "Transformations in 3D space",
        "Mates",
        "Import_export 3D graphics",
        "ViewPlacement",
        "BusBarSystem",
    ],
    "parts-masterdata": [
        "API MasterData",
        "Working with parts database",
        "Basic operations on parts",
        "Filtering parts database items",
        "API Parts Selection Interface",
        "API Parts Management Extension",
    ],
    "misc": [
        "API Electrotechnical services",
        "API Miscellaneous",
        "Messages",
        "Verifications",
        "Ribbon bar",
        "Adding ribbon commands",
        "Working with settings",
        "Writing system messages",
        "Throwing and catching exceptions",
        "How to display a MessageBox",
        "Trace output",
        "Query user rights",
        "Events",
        "Interactions",
        "XML Converters",
        "XMLProcessor",
        "IdentityClient",
        "EPLAN API offline applications",
        "EPLAN Remoting",
        "Using EPLAN in other applications",
        "Using other applications",
        "API Pre-planning",
        "StructureSegment",
        "SegmentDefinition",
        "SegmentTemplate",
        "SegmentPlacement",
        "PCTLoop",
        "Structure",
        "Add-ons",
        "API Labeling Modification Interface",
        "API Reports Modification Interface",
        "Help structure",
        "API User Guide",
        "API Reference",
    ],
}

SCHEMAGEM_PRIORITY = {
    "scripts": "MVP — struktura skryptu .cs, [Start], parametry",
    "datamodel": "MVP — Project, Page, Function, właściwości, transakcje",
    "heservices": "MVP — wstawianie makr .ema, Insert, PlaceHolder",
    "actions-cli": "MVP — eksport CSV/PDF, CLI, CommandLineInterpreter",
    "addins": "Przyszłość — migracja z .cs do DLL",
    "pro-panel-3d": "Poza MVP — szafy 3D",
    "parts-masterdata": "Później — BOM, części",
    "misc": "Na żądanie",
}


def clean_text(text: str) -> str:
    text = re.sub(r"In This Topic\s*", "", text)
    text = re.sub(r"See Also\s*### Reference.*", "", text, flags=re.S)
    text = re.sub(r"EPLAN API , 17\.02\.2025.*", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def format_doc(doc: dict) -> str:
    parts = [f"## {doc['title']}", f"*Źródło: `{doc['file']}`*"]
    if doc.get("breadcrumb"):
        parts.append(f"*Ścieżka: {doc['breadcrumb']}*")
    text = clean_text(doc.get("text", ""))
    if text:
        parts.append("")
        parts.append(text)
    codes = doc.get("code") or []
    if codes:
        parts.append("")
        parts.append("### Przykłady kodu (C#)")
        for i, code in enumerate(codes, 1):
            parts.append(f"```csharp\n{code}\n```")
    return "\n".join(parts)


def title_to_slug(title: str, filename: str) -> str:
    for slug, titles in TOPIC_MAP.items():
        for t in titles:
            if t in title or t in filename.replace(".html", ""):
                return slug
    return "misc"


def build_title_index(docs: list) -> dict:
    by_title = {}
    for d in docs:
        by_title[d["title"]] = d["file"]
    return by_title


def extract_actions(docs: list) -> str:
    actions_doc = next((d for d in docs if d["title"] == "Actions"), None)
    if not actions_doc:
        return ""
    rows = re.findall(
        r"\| ([^|\n]+) \| ([^\n]+)", actions_doc["text"]
    )
    lines = ["# EPLAN Actions — indeks skrócony", ""]
    lines.append("| Action | Opis |")
    lines.append("|--------|------|")
    for name, desc in rows:
        name = name.strip()
        desc = desc.strip()[:120]
        if name and desc and name != "Name":
            lines.append(f"| `{name}` | {desc} |")
    # SchemaGen-relevant subset
    keywords = ["export", "import", "print", "project", "script", "macro", "connection", "XMExport"]
    lines.append("")
    lines.append("## Akcje istotne dla SchemaGen")
    lines.append("")
    for name, desc in rows:
        name = name.strip()
        if any(k.lower() in name.lower() or k.lower() in desc.lower() for k in keywords):
            lines.append(f"- **{name}**: {desc.strip()[:150]}")
    return "\n".join(lines)


def main():
    with open(RAW, encoding="utf-8") as f:
        docs = json.load(f)

    os.makedirs(TOPICS, exist_ok=True)

    grouped = defaultdict(list)
    unassigned = []
    title_to_file = {}

    for doc in docs:
        title_to_file[doc["title"]] = doc["file"]
        assigned = False
        for slug, titles in TOPIC_MAP.items():
            for t in titles:
                if t in doc["title"] or t in doc["file"].replace(".html", ""):
                    grouped[slug].append(doc)
                    assigned = True
                    break
            if assigned:
                break
        if not assigned:
            unassigned.append(doc)
            grouped["misc"].append(doc)

    # Write topic files
    for slug, topic_docs in grouped.items():
        path = os.path.join(TOPICS, f"{slug}.md")
        header = [
            f"# EPLAN API — {slug}",
            "",
            f"*{SCHEMAGEM_PRIORITY.get(slug, '')}*",
            "",
            f"Dokumentów: {len(topic_docs)}",
            "",
        ]
        body = []
        for doc in sorted(topic_docs, key=lambda x: x["title"]):
            body.append(format_doc(doc))
            body.append("")
            body.append("---")
            body.append("")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(header + body))

    # Actions index
    actions_path = os.path.join(ROOT, "actions-index.md")
    with open(actions_path, "w", encoding="utf-8") as f:
        f.write(extract_actions(docs))

    # File manifest
    manifest_path = os.path.join(ROOT, "source-manifest.md")
    manifest = [
        "# Manifest źródeł EPLAN API",
        "",
        "Dokumentacja zaimportowana z:",
        "- Lokalnie: `C:\\Users\\Filip\\Desktop\\startUp\\AutoGen\\EPLAN API docs` (104 pliki HTML)",
        "- Online (mirror): https://www.eplan.help/en-us/Infoportal/Content/api/2025/index.html",
        "- Wersja API: EPLAN Platform 2025 (17.02.2025)",
        "",
        "## Mapowanie plik → temat",
        "",
        "| Plik HTML | Temat KB |",
        "|-----------|----------|",
    ]
    for doc in sorted(docs, key=lambda x: x["file"]):
        slug = "misc"
        for s, titles in TOPIC_MAP.items():
            if any(t in doc["title"] or t in doc["file"] for t in titles):
                slug = s
                break
        manifest.append(f"| `{doc['file']}` | `{slug}` |")
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write("\n".join(manifest))

    # INDEX
    index_path = os.path.join(ROOT, "INDEX.md")
    index = [
        "# EPLAN API Knowledge Base (SchemaGen)",
        "",
        "Lokalna baza wiedzy — **nie szukaj w internecie**, czytaj te pliki.",
        "",
        "## Jak korzystać (najtaniej)",
        "",
        "1. Zacznij od tego pliku (INDEX) — ~2 min kontekstu.",
        "2. Otwórz **jeden** plik z `topics/` pasujący do zadania.",
        "3. Szukaj w repo: `grep -r \"WindowMacro\" docs/eplan-kb/`",
        "4. Pełny surowy extract: `raw-extract.json` (grep, nie wczytuj całości).",
        "5. Notatki z testów: `docs/eplan-api-notes.md`",
        "",
        "## Tematy (topics/)",
        "",
    ]
    for slug in [
        "scripts",
        "datamodel",
        "heservices",
        "actions-cli",
        "addins",
        "pro-panel-3d",
        "parts-masterdata",
        "misc",
    ]:
        count = len(grouped.get(slug, []))
        index.append(
            f"- **[{slug}](topics/{slug}.md)** — {SCHEMAGEM_PRIORITY.get(slug, '')} ({count} doc)"
        )
    index.extend(
        [
            "",
            "## Szybkie odniesienia",
            "",
            "- [actions-index.md](actions-index.md) — lista akcji EPLAN",
            "- [source-manifest.md](source-manifest.md) — mapa 104 plików HTML",
            "- [schemagen-cheatsheet.md](schemagen-cheatsheet.md) — gotowe snippety pod MVP",
            "",
            "## Architektura API (skrót)",
            "",
            "| Namespace | Rola |",
            "|-----------|------|",
            "| `Eplan.EplApi.ApplicationFramework` | Actions, skrypty, add-iny |",
            "| `Eplan.EplApi.DataModel` | Project, Page, Function, właściwości |",
            "| `Eplan.EplApi.HEServices` | Makra, eksport, Search, SelectionSet |",
            "| `Eplan.EplApi.EServices` | Wiadomości, weryfikacje, GED interactions |",
            "| `Eplan.EplApi.MasterData` | Baza części, symbole |",
            "",
            "## SchemaGen MVP — typowy flow API",
            "",
            "```",
            "1. ProjectManager.OpenProject(\"...Hello_world.edb\")",
            "2. Page.Create(project, DocumentType.Circuit, PagePropertyList)",
            "3. Insert.WindowMacro(\"...400VAC_Power_Supply.ema\", variant, page, PointD, MoveKind)",
            "4. PlaceHolder.ApplyRecord(\"...\")  // jeśli makro ma PlaceHolder",
            "5. Function.Name = \"=MACHINE+CABINET-M1\"  // w Transaction + SafetyPoint",
            "6. CommandLineInterpreter.Execute(\"XMExportConnectionsAction ...\")  // walidacja CSV",
            "7. CommandLineInterpreter.Execute(\"XPrintPdf ...\")  // PDF dla człowieka",
            "```",
            "",
            "## Makra EPLAN",
            "",
            "| Rozszerzenie | Typ |",
            "|-------------|-----|",
            "| `.ema` | Window macro (na stronę) |",
            "| `.emp` | Page macro (cała strona) |",
            "| `.ems` | Symbol macro |",
            "",
            "Klasa: `Eplan.EplApi.HEServices.Insert` — `WindowMacro()`, `PageMacro()`, `SymbolMacro()`",
            "",
            "## Skrypt .cs — minimum",
            "",
            "```csharp",
            "public class SchemaGen_MVP {",
            "    [Start]",
            "    public void Run() { /* ... */ }",
            "}",
            "```",
            "",
            "Uruchomienie: EPLAN → Narzędzia → Skrypty → Uruchom",
            "Lokalizacja: `C:\\Users\\Public\\EPLAN\\Data\\Skrypty\\Schemagen\\`",
            "",
            "## Zmienne ścieżek EPLAN",
            "",
            "- `$(MD_PROJECTS)` — projekty",
            "- `$(MD_MACROS)` — makra",
            "- `$(MD_TEMPLATES)` — szablony projektów (.zw9)",
            "",
        ]
    )
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("\n".join(index))

    # SchemaGen cheatsheet
    cheatsheet_path = os.path.join(ROOT, "schemagen-cheatsheet.md")
    cheatsheet = """# SchemaGen — ściąga EPLAN API

Gotowe wzorce C# wyekstrahowane z dokumentacji EPLAN 2025.

## Otwórz projekt

```csharp
Project oProject = new ProjectManager().OpenProject(
    @"C:\\Users\\Public\\EPLAN\\Data\\Projekty\\Schemagen\\Hello_world.edb");
```

Alternatywnie ze zmienną EPLAN:
```csharp
Project oProject = new ProjectManager().OpenProject(@"$(MD_PROJECTS)\\Hello_world.edb");
```

## Utwórz stronę schematu

```csharp
PagePropertyList oPagePropList = new PagePropertyList();
oPagePropList[Properties.Page.DESIGNATION_PLANT] = "P1";
oPagePropList[Properties.Page.DESIGNATION_LOCATION] = "L1";
Page oNewPage = new Page();
oNewPage.Create(oProject, DocumentTypeManager.DocumentType.Circuit, oPagePropList);
// Właściwości opisowe — PO Create, przez Page.Properties
```

## Wstaw makro okna (.ema)

```csharp
Insert oInsert = new Insert();
oInsert.WindowMacro(
    @"C:\\Users\\Public\\EPLAN\\Data\\Makra\\Schemagen\\EPLAN_Macro\\201_Power_Supply\\101_01_Variant_1\\400VAC_Power_Supply.ema",
    0,
    oNewPage,
    new PointD(70.0, 0.0),
    Insert.MoveKind.Relative);
```

## PlaceHolder w makrze

```csharp
StorableObject[] inserted = oInsert.WindowMacro(path, 0, page, new PointD(70, 0), Insert.MoveKind.Relative);
foreach (StorableObject obj in inserted) {
    PlaceHolder ph = obj as Eplan.EplApi.DataModel.Graphics.PlaceHolder;
    if (ph != null && ph.Name == "Three-Phase")
        ph.ApplyRecord("Motor 0,75 KW");
}
```

## Transakcja + SafetyPoint

```csharp
using (SafetyPoint sp = SafetyPoint.Create()) {
    using (Transaction tx = new TransactionManager().CreateTransaction()) {
        oFunction.Name = "=MACHINE+CABINET-M1";
        tx.Commit();
    }
    sp.Commit(); // bez tego rollback
}
```

## Znajdź funkcję po nazwie (DT)

```csharp
DMObjectsFinder finder = new DMObjectsFinder(oProject);
FunctionsFilter filter = new FunctionsFilter();
filter.ExactNameMatching = true;
filter.Name = "=MACHINE+CABINET-M1";
Function[] funcs = finder.GetFunctions(filter);
```

## Pętla po funkcjach na stronie

```csharp
foreach (Function f in oPage.Functions) {
    string name = f.Name;
}
```

## Ustaw właściwość bool

```csharp
oFunction.Properties[Properties.Function.FUNC_ARTICLE_SUPPRESSINPARTSLIST] = true;
```

## Eksport połączeń (walidacja agenta)

```csharp
// Przez CommandLineInterpreter (wzorzec z project-context)
new CommandLineInterpreter().Execute("XMExportConnectionsAction /...");
// lub action framework:
ActionManager am = new ActionManager();
Action action = am.FindAction("XMExportConnectionsAction");
ActionCallingContext ctx = new ActionCallingContext();
action.Execute(ctx);
```

## PDF dla człowieka

```csharp
new CommandLineInterpreter().Execute("XPrintPdf /Filename:schemat.pdf");
```

## CLI uruchomienie EPLAN ze skryptem

```
EPLAN.EXE /Variant:"Electric P8" /NoLoadWorkspace /Auto /Quiet ExecuteScript /Script:SchemaGen_MVP.cs
```

## Locking w skrypcie

Skrypty: LockingStep tworzony automatycznie przez framework P8.
Offline: `using (LockingStep ls = new LockingStep()) { ... }`

## Ważne ograniczenia

- `PagePropertyList` przy Create — tylko części nazwy strony, nie właściwości opisowe
- Zagnieżdżone ustawianie właściwości (`oRect.Pen.ColorId = 5`) — NIE działa; pobierz obiekt, zmień, ustaw z powrotem
- `Function` to słowo kluczowe VB — w VB używaj pełnej nazwy `[Function]` lub `Eplan.EplApi.DataModel.Function`
- Długości w mm; współrzędne wg układu graficznego
- Po pętlach z wieloma obiektami: `GC.WaitForPendingFinalizers()`
"""
    with open(cheatsheet_path, "w", encoding="utf-8") as f:
        f.write(cheatsheet)

    print(f"Built KB: {len(docs)} docs -> {len(grouped)} topics")
    for slug, td in grouped.items():
        print(f"  {slug}: {len(td)} docs")


if __name__ == "__main__":
    main()
