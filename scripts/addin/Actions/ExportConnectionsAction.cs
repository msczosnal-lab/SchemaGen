using System.IO;
using Eplan.EplApi.ApplicationFramework;
using Eplan.EplApi.Base;

// Faza 2: eksport CSV połączeń — sprzężenie zwrotne walidacji agenta.
public class SchemaGenExportConnectionsAction : IEplAction
{
    public bool OnRegister(ref string Name, ref int Ordinal)
    {
        Name = "SchemaGenExportConnections";
        Ordinal = 25;
        return true;
    }

    public void GetActionProperties(ref ActionProperties actionProperties) { }

    public bool Execute(ActionCallingContext ctx)
    {
        string outputPath = "";
        ctx.GetParameter("OUTPUTPATH", ref outputPath);
        if (string.IsNullOrEmpty(outputPath))
            outputPath = SchemaGenPaths.DefaultConnectionsExportPath;

        outputPath = PathMap.SubstitutePath(outputPath);
        string dir = Path.GetDirectoryName(outputPath);
        if (!string.IsNullOrEmpty(dir))
            Directory.CreateDirectory(dir);

        string escaped = outputPath.Replace("\"", "\"\"");
        bool ok = new CommandLineInterpreter().Execute(
            "XExport /Format:CSV /Filename:\"" + escaped + "\"");

        string silent = "";
        ctx.GetParameter("SILENT", ref silent);
        if (silent == "1")
            return ok;

        if (ok)
            SchemaGenUi.ShowSuccess("SchemaGen — eksport CSV", "Zapisano:\n" + outputPath);
        else
            SchemaGenUi.ShowError("SchemaGen — błąd", "XExport CSV nie powiódł się:\n" + outputPath);
        return ok;
    }
}
