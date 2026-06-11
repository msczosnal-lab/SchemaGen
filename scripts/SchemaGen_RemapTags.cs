using Eplan.EplApi.Scripting;
using Eplan.EplApi.ApplicationFramework;

// Sesja 1.7c — wyzwalacz akcji remap tagów + diagnostyka.
// Skrypt NIE używa typów DataModel (Page/Function) — te są tylko w add-in (DLL).
// Skrypt jedynie woła zarejestrowaną akcję przez CommandLineInterpreter.
// Bez SILENT -> okno z raportem (stary DT -> nowy DT, kod, numer strony).
// Wynik także w pliku scripts\remap-tags.json (do wklejenia).
// Wymóg: projekt Hello_world OTWARTY i aktywny.
public class SchemaGenRemapTagsScript
{
    [Start]
    public void Run()
    {
        ActionCallingContext ctx = new ActionCallingContext();
        ctx.AddParameter("OUTPUTPATH",
            @"C:\Users\Filip\Desktop\Cursor\SchemaGen\scripts\remap-tags.json");
        new CommandLineInterpreter().Execute("SchemaGenRemapTags", ctx);
    }
}
