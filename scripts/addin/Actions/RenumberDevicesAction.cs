using System.Collections.Generic;
using System.IO;
using System.Text;
using Eplan.EplApi.ApplicationFramework;
using Eplan.EplApi.DataModel;

// Sesja 1.7d cd.: natywna numeracja DT urządzeń — wrapper CLI `renumber /TYPE:DEVICES`.
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

        string configScheme = "";
        ctx.GetParameter("CONFIGSCHEME", ref configScheme);

        string identifier = "";
        ctx.GetParameter("IDENTIFIER", ref identifier);

        string useSelection = SchemaGenPaths.RenumberUseSelection;
        ctx.GetParameter("USESELECTION", ref useSelection);

        var commands = new List<string>();
        if (!string.IsNullOrEmpty(identifier))
        {
            foreach (string id in identifier.Split(new[] { ';', ',' }, System.StringSplitOptions.RemoveEmptyEntries))
            {
                string trimmed = id.Trim();
                if (trimmed.Length > 0)
                    commands.Add(BuildRenumberCommand(trimmed, configScheme, useSelection));
            }
        }
        else
            commands.Add(BuildRenumberCommand("", configScheme, useSelection));

        var cli = new CommandLineInterpreter();
        bool renumbered = true;
        var commandLog = new StringBuilder();
        foreach (string cmd in commands)
        {
            bool ok = cli.Execute(cmd);
            renumbered = renumbered && ok;
            if (commandLog.Length > 0)
                commandLog.AppendLine();
            commandLog.Append(ok ? "OK: " : "ERR: ");
            commandLog.Append(cmd);
        }

        bool viewRefreshed = cli.Execute("gedRedraw");
        string auditJson = AuditMainDeviceTags(oProject);

        string outputPath = "";
        ctx.GetParameter("OUTPUTPATH", ref outputPath);
        if (!string.IsNullOrEmpty(outputPath))
        {
            string dir = Path.GetDirectoryName(outputPath);
            if (!string.IsNullOrEmpty(dir))
                Directory.CreateDirectory(dir);
            File.WriteAllText(
                outputPath,
                BuildJson(renumbered, viewRefreshed, commandLog.ToString(), auditJson),
                Encoding.UTF8);
        }

        string silent = "";
        ctx.GetParameter("SILENT", ref silent);
        if (silent == "1")
            return renumbered;

        if (renumbered)
            SchemaGenUi.ShowSuccess(
                "SchemaGen — numeracja urządzeń",
                "Numeracja DT (renumber /TYPE:DEVICES): OK"
                + "\nOdświeżenie widoku (gedRedraw): " + (viewRefreshed ? "OK" : "błąd")
                + "\n\nJeśli -FC1/-MA1 powtarza się na różnych stronach: to numeracja per lokalizacja"
                + " w schemacie projektu (lokalizacja w nagłówku strony). Pełne DT w output/renumber-devices.json."
                + "\nGlobalne FC1,FC2,FC3 / MA1,MA2,MA3: ustaw parametr CONFIGSCHEME (schemat „cały projekt” z EPLAN).");
        else
            SchemaGenUi.ShowError(
                "SchemaGen — błąd",
                "Akcja renumber nie powiodła się.\n" + commandLog);
        return renumbered;
    }

    private static string BuildRenumberCommand(string identifier, string configScheme, string useSelection)
    {
        var sb = new StringBuilder();
        sb.Append("renumber /TYPE:DEVICES");
        sb.Append(" /USESELECTION:").Append(string.IsNullOrEmpty(useSelection) ? "0" : useSelection);
        sb.Append(" /STARTVALUE:").Append(SchemaGenPaths.RenumberStartValue);
        sb.Append(" /STEPVALUE:").Append(SchemaGenPaths.RenumberStepValue);
        sb.Append(" /POSTNUMERATE:").Append(SchemaGenPaths.RenumberPostnumerate);
        if (!string.IsNullOrEmpty(identifier))
            sb.Append(" /IDENTIFIER:").Append(identifier);
        if (!string.IsNullOrEmpty(configScheme))
            sb.Append(" /CONFIGSCHEME:\"").Append(configScheme.Replace("\"", "\\\"")).Append("\"");
        return sb.ToString();
    }

    private static string AuditMainDeviceTags(Project project)
    {
        var items = new List<string>();
        foreach (Page page in project.Pages)
        {
            if (!IsSchemaGenPage(page))
                continue;

            string pageName = "";
            string pageLocation = "";
            try
            {
                pageName = page.Name;
                pageLocation = page.Properties[Properties.Page.DESIGNATION_LOCATION].ToString();
            }
            catch { /* ignore */ }

            foreach (Function func in page.Functions)
            {
                try
                {
                    if (!func.IsMainFunction)
                        continue;
                }
                catch
                {
                    continue;
                }

                string funcCode = "";
                string funcCounter = "";
                string visibleName = "";
                try { funcCode = func.Properties.FUNC_CODE.ToString(); } catch { }
                try { funcCounter = func.Properties.FUNC_COUNTER.ToString(); } catch { }
                try { visibleName = func.Name ?? ""; } catch { }

                if (string.IsNullOrEmpty(funcCode) && string.IsNullOrEmpty(visibleName))
                    continue;

                string product = "-" + funcCode + funcCounter;
                string fullTag = "=SCHEMAGEN" + pageLocation + product;

                items.Add("{"
                    + "\"page\":\"" + EscapeJson(pageName) + "\","
                    + "\"location\":\"" + EscapeJson(pageLocation) + "\","
                    + "\"funcCode\":\"" + EscapeJson(funcCode) + "\","
                    + "\"funcCounter\":\"" + EscapeJson(funcCounter) + "\","
                    + "\"visibleName\":\"" + EscapeJson(visibleName) + "\","
                    + "\"fullTag\":\"" + EscapeJson(fullTag) + "\""
                    + "}");
            }
        }
        return "[" + string.Join(",", items.ToArray()) + "]";
    }

    private static bool IsSchemaGenPage(Page page)
    {
        try
        {
            string plant = page.Properties[Properties.Page.DESIGNATION_PLANT].ToString();
            return plant != null
                && plant.IndexOf(SchemaGenPaths.Plant, System.StringComparison.OrdinalIgnoreCase) >= 0;
        }
        catch
        {
            return false;
        }
    }

    private static string BuildJson(bool renumbered, bool viewRefreshed, string commands, string devicesJson)
    {
        return "{"
            + "\"renumbered\":" + (renumbered ? "true" : "false") + ","
            + "\"viewRefreshed\":" + (viewRefreshed ? "true" : "false") + ","
            + "\"commands\":\"" + EscapeJson(commands) + "\","
            + "\"devices\":" + devicesJson
            + "}";
    }

    private static string EscapeJson(string value)
    {
        if (string.IsNullOrEmpty(value))
            return "";
        return value.Replace("\\", "\\\\").Replace("\"", "\\\"").Replace("\r", "").Replace("\n", "\\n");
    }
}
