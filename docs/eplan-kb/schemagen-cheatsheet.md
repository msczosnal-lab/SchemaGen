# SchemaGen — ściąga EPLAN API

Gotowe wzorce C# wyekstrahowane z dokumentacji EPLAN 2025.

## Otwórz projekt

**Skrypt .cs** — brak `Eplan.EplApi.DataModel` w kompilatorze skryptów; użyj akcji `edit`:

```csharp
bool ok = new CommandLineInterpreter().Execute(
    @"ProjectOpen /Project:""C:\Users\Public\EPLAN\Data\Projekty\Schemagen\Hello_world.elk""");
// Uwaga: ścieżka w cudzysłowie — bez tego C: obcina parametr akcji
```

**Add-in / offline** — `ProjectManager.OpenProject` (plik **.elk**, nie katalog .edb):

```csharp
Project oProject = new ProjectManager().OpenProject(
    @"C:\Users\Public\EPLAN\Data\Projekty\Schemagen\Hello_world.elk");
```

Alternatywnie ze zmienną EPLAN:
```csharp
Project oProject = new ProjectManager().OpenProject(@"$(MD_PROJECTS)\Schemagen\Hello_world.elk");
```

## Utwórz stronę schematu

**Skrypt .cs** — brak `DataModel` w kompilatorze; użyj add-in + akcja `SchemaGenCreatePage`:

```csharp
// Jednorazowo: zarejestruj SchemaGen.EplAddin.dll w EPLAN API → Zarządzaj
new CommandLineInterpreter().Execute("SchemaGenCreatePage");
```

**Add-in / offline** — `Page.Create` (pełny DataModel):

```csharp
PagePropertyList oPagePropList = new PagePropertyList();
oPagePropList[Properties.Page.DESIGNATION_PLANT] = "=SCHEMAGEN";
oPagePropList[Properties.Page.DESIGNATION_LOCATION] = "+MAIN";
Page oNewPage = new Page();
oNewPage.Create(oProject, DocumentTypeManager.DocumentType.Circuit, oPagePropList);
// Właściwości opisowe — PO Create, przez Page.Properties
```

## Wstaw makro okna (.ema)

```csharp
Insert oInsert = new Insert();
oInsert.WindowMacro(
    @"C:\Users\Public\EPLAN\Data\Makra\Schemagen\EPLAN_Macro\201_Power_Supply\101_01_Variant_1\400VAC_Power_Supply.ema",
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
