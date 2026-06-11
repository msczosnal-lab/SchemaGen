using System.IO;
using System.Text;
using Eplan.EplApi.ApplicationFramework;
using Eplan.EplApi.DataModel;

// Sesja 1.6: podmiana oznaczeń silnika na =MACHINE+CABINET-M1 + generate CONNECTIONS (uzwojenia).
// Sesja 1.7: generate IDENTIFIERS po connections, pole identifiersGenerated w JSON.
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

        // Sesja 1.7c: numeracja urządzeń wg numeru strony — bez duplikatów MA1/FC1.
        foreach (Page page in oProject.Pages)
        {
            if (!IsSchemaGenPage(page))
                continue;

            int pageRemapped = MacroAdaptation.RemapDeviceTags(page);
            remapped += pageRemapped;
            if (pageRemapped > 0)
                report.AppendLine(page.Name + ": " + pageRemapped + " urządzeń(ia)");
        }

        connections = MacroAdaptation.ConnectMotorWindings(oProject);

        // Sesja 1.7c: NameParts ustawia DT od razu — wystarczy odświeżenie widoku.
        // [BŁĄD naprawiony] generate obsługuje tylko CONNECTIONS/CABLES; /TYPE:IDENTIFIERS zwracał false.
        bool identifiersGenerated = new CommandLineInterpreter().Execute("gedRedraw");

        string outputPath = "";
        ctx.GetParameter("OUTPUTPATH", ref outputPath);
        string json = BuildJson(remapped, connections, targetTag, report.ToString(), identifiersGenerated);
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
            "Podmieniono oznaczenia: " + remapped
            + "\nPołączenia uzwojeń (generate CONNECTIONS): " + connections
            + "\nOznaczenia (generate IDENTIFIERS): " + (identifiersGenerated ? "OK" : "błąd")
            + "\nDocelowy tag: " + targetTag
            + (report.Length > 0 ? "\n\n" + report : ""));
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

    private static string BuildJson(int remapped, int connections, string targetTag, string details, bool identifiersGenerated = false)
    {
        return "{"
            + "\"remappedMotors\":" + remapped + ","
            + "\"connectionPasses\":" + connections + ","
            + "\"identifiersGenerated\":" + (identifiersGenerated ? "true" : "false") + ","
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
