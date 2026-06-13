using System.IO;
using System.Text;
using Eplan.EplApi.ApplicationFramework;
using Eplan.EplApi.DataModel;

// Sesja 1.7d cd.: natywna numeracja DT urządzeń (FC/MA) — wrapper CLI `renumber /TYPE:DEVICES`.
// Zastępuje ślepą uliczkę ręcznego remapu DT (func.Name/NameParts/<20010>, S063113 — usunięte w 1.7d).
// Składnia przechwycona z Action Monitor (Projekt → Numeruj): renumber /TYPE:DEVICES.
// Projekt aktywowany wcześniej przez SchemaGenEnsureProject; renumber działa na bieżącym projekcie.
public class SchemaGenRenumberDevicesAction : IEplAction
{
    public bool OnRegister(ref string Name, ref int Ordinal)
    {
        Name = "SchemaGenRenumberDevices";
        Ordinal = 26;
        return true;
    }

    public void GetActionProperties(ref ActionProperties actionProperties) { }

    public bool Execute(ActionCallingContext ctx)
    {
        Project oProject = ProjectResolver.Resolve(ctx);
        if (oProject == null)
        {
            SchemaGenUi.ShowError("SchemaGen — błąd", "SchemaGen: brak otwartego projektu.");
            return false;
        }

        bool renumbered = new CommandLineInterpreter().Execute("renumber /TYPE:DEVICES");
        bool viewRefreshed = new CommandLineInterpreter().Execute("gedRedraw");

        string outputPath = "";
        ctx.GetParameter("OUTPUTPATH", ref outputPath);
        if (!string.IsNullOrEmpty(outputPath))
        {
            string dir = Path.GetDirectoryName(outputPath);
            if (!string.IsNullOrEmpty(dir))
                Directory.CreateDirectory(dir);
            File.WriteAllText(outputPath, BuildJson(renumbered, viewRefreshed), Encoding.UTF8);
        }

        string silent = "";
        ctx.GetParameter("SILENT", ref silent);
        if (silent == "1")
            return renumbered;

        if (renumbered)
            SchemaGenUi.ShowSuccess(
                "SchemaGen — numeracja urządzeń",
                "Numeracja DT (renumber /TYPE:DEVICES): OK"
                + "\nOdświeżenie widoku (gedRedraw): " + (viewRefreshed ? "OK" : "błąd"));
        else
            SchemaGenUi.ShowError(
                "SchemaGen — błąd",
                "Akcja renumber /TYPE:DEVICES nie powiodła się.");
        return renumbered;
    }

    private static string BuildJson(bool renumbered, bool viewRefreshed)
    {
        return "{"
            + "\"renumbered\":" + (renumbered ? "true" : "false") + ","
            + "\"viewRefreshed\":" + (viewRefreshed ? "true" : "false")
            + "}";
    }
}
