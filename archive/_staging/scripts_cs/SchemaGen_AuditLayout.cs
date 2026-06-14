using Eplan.EplApi.Scripting;
using Eplan.EplApi.ApplicationFramework;

// Sesja 1.7c — pomocniczy skrypt do ręcznego uruchomienia audytu layoutu.
// Bez SILENT  -> wynik JSON pokazuje się w oknie dialogowym (skopiuj treść).
// Bez PAGENAME-> audytuje wszystkie strony SchemaGen aktywnego projektu.
// Wymóg: projekt Hello_world musi być OTWARTY i aktywny przed uruchomieniem.
public class SchemaGenAuditLayoutScript
{
    [Start]
    public void Run()
    {
        ActionCallingContext ctx = new ActionCallingContext();
        // Zapis JSON do Skrypty\Schemagen\output\layout-audit.json.
        ctx.AddParameter("OUTPUTPATH",
            @"C:\Users\Public\EPLAN\Data\Skrypty\Schemagen\output\layout-audit.json");
        new CommandLineInterpreter().Execute("SchemaGenAuditLayout", ctx);
    }
}
