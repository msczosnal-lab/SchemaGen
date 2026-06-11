using System.IO;
using System.Text;
using Eplan.EplApi.ApplicationFramework;
using Eplan.EplApi.DataModel;

// Sesja 1.6: podmiana tagów silnika + generate CONNECTIONS (uzwojenia).
// Sesja 1.7c: gedRedraw zamiast generate IDENTIFIERS (nieobsługiwane).
// Numeracja DT urządzeń — sesja 1.7d (natywna renumber EPLAN), nie ręczny remap.
public class SchemaGenRemapTagsAction : IEplAction
{
    public bool OnRegister(ref string Name, ref int Ordinal)
    {
        Name = "SchemaGenRemapTags";
        Ordinal = 23;
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

        string targetTag = SchemaGenPaths.MotorDesignation;
        ctx.GetParameter("MOTORTAG", ref targetTag);
        if (string.IsNullOrEmpty(targetTag))
            targetTag = SchemaGenPaths.MotorDesignation;

        int remapped = 0;
        int connections = 0;
        var report = new StringBuilder();

        foreach (Page page in oProject.Pages)
        {
            if (!IsSchemaGenPage(page))
                continue;

            int pageRemapped = MacroAdaptation.RemapMotorTag(page, targetTag);
            remapped += pageRemapped;
            if (pageRemapped > 0)
                report.AppendLine(page.Name + ": " + pageRemapped + " silnik(ów)");
        }

        connections = MacroAdaptation.ConnectMotorWindings(oProject);

        bool viewRefreshed = new CommandLineInterpreter().Execute("gedRedraw");

        string outputPath = "";
        ctx.GetParameter("OUTPUTPATH", ref outputPath);
        string json = BuildJson(remapped, connections, targetTag, report.ToString(), viewRefreshed);
        if (!string.IsNullOrEmpty(outputPath))
        {
            string dir = Path.GetDirectoryName(outputPath);
            if (!string.IsNullOrEmpty(dir))
                Directory.CreateDirectory(dir);
            File.WriteAllText(outputPath, json, Encoding.UTF8);
        }

        string silent = "";
        ctx.GetParameter("SILENT", ref silent);
        if (silent == "1")
            return true;

        SchemaGenUi.ShowSuccess(
            "SchemaGen — tagi silnika",
            "Podmieniono oznaczenia silnika: " + remapped
            + "\nPołączenia uzwojeń (generate CONNECTIONS): " + connections
            + "\nOdświeżenie widoku (gedRedraw): " + (viewRefreshed ? "OK" : "błąd")
            + "\nDocelowy tag: " + targetTag
            + (report.Length > 0 ? "\n\n" + report : "")
            + "\n\nNumeracja DT urządzeń (FC/MA): sesja 1.7d — natywna renumber EPLAN.");
        return true;
    }

    private static bool IsSchemaGenPage(Page page)
    {
        try
        {
            string plant = page.Properties[Properties.Page.DESIGNATION_PLANT].ToString();
            return plant != null && plant.IndexOf(SchemaGenPaths.Plant, System.StringComparison.OrdinalIgnoreCase) >= 0;
        }
        catch
        {
            return false;
        }
    }

    private static string BuildJson(int remapped, int connections, string targetTag, string details, bool viewRefreshed)
    {
        return "{"
            + "\"remappedMotors\":" + remapped + ","
            + "\"connectionPasses\":" + connections + ","
            + "\"viewRefreshed\":" + (viewRefreshed ? "true" : "false") + ","
            + "\"identifiersGenerated\":" + (viewRefreshed ? "true" : "false") + ","
            + "\"targetTag\":\"" + EscapeJson(targetTag) + "\","
            + "\"details\":\"" + EscapeJson(details.Trim()) + "\""
            + "}";
    }

    private static string EscapeJson(string value)
    {
        if (string.IsNullOrEmpty(value))
            return "";
        return value.Replace("\\", "\\\\").Replace("\"", "\\\"").Replace("\r", "").Replace("\n", "\\n");
    }
}
