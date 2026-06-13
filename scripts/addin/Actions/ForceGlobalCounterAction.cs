using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using Eplan.EplApi.ApplicationFramework;
using Eplan.EplApi.DataModel;

// Sesja 1.7g — Plan B: globalny licznik DT dla identyfikatora (np. -MA1, -MA2 ...).
//
// Po renumber per-lokalizacja silniki w +B2 i +B4 dostają oba -MA1 (licznik resetowany
// per lokalizacja). Tu nadajemy licznik GLOBALNIE: kolejne funkcje główne z danym
// FUNC_CODE dostają counter = START, START+STEP, ...
//
// Mechanizm: NameParts → FUNC_COUNTER. DESIGNATION_PRODUCT (widoczne "MA1") jest
// składane z FUNC_CODE + FUNC_COUNTER (KB datamodel.md:454).
// [WAŻNE] NIE piszemy property <20010> wprost — to ślepa uliczka (S063113): albo się
// nie utrzymuje, albo rozjeżdża widoczny DT z modelem. Tu zmieniamy tylko licznik.
public class SchemaGenForceGlobalCounterAction : IEplAction
{
    public bool OnRegister(ref string Name, ref int Ordinal)
    {
        Name = "SchemaGenForceGlobalCounter";
        Ordinal = 27;
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

        string identifier = "";
        ctx.GetParameter("IDENTIFIER", ref identifier);
        identifier = (identifier ?? "").Trim();
        if (identifier.Length == 0)
        {
            SchemaGenUi.ShowError("SchemaGen — błąd",
                "SchemaGenForceGlobalCounter: brak parametru IDENTIFIER (np. MA).");
            return false;
        }

        int startValue = ParseIntOr(ctx, "STARTVALUE", 1);
        int stepValue = ParseIntOr(ctx, "STEPVALUE", 1);
        if (stepValue == 0)
            stepValue = 1;

        // Funkcje główne z FUNC_CODE == identifier, w kolejności stron SchemaGen.
        List<Function> targets = CollectMainFunctions(oProject, identifier);

        var log = new StringBuilder();
        int counter = startValue;
        int changed = 0;
        foreach (Function func in targets)
        {
            string oldName = "";
            try { oldName = func.Name ?? ""; } catch { }

            if (TrySetCounter(func, counter.ToString(), log, oldName))
                changed++;

            counter += stepValue;
        }

        new CommandLineInterpreter().Execute("gedRedraw");

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
                BuildJson(identifier, changed, targets.Count, log.ToString(), auditJson),
                Encoding.UTF8);
        }

        string silent = "";
        ctx.GetParameter("SILENT", ref silent);
        if (silent == "1")
            return changed == targets.Count;

        SchemaGenUi.ShowSuccess(
            "SchemaGen — globalny licznik",
            "Identyfikator -" + identifier + ": ustawiono " + changed + "/" + targets.Count
            + " liczników (start " + startValue + ", krok " + stepValue + ").\n\n" + log);
        return changed == targets.Count;
    }

    // Czytaj bieżący NameParts, zmień TYLKO FUNC_COUNTER, zapisz z powrotem —
    // plant/lokalizacja/FUNC_CODE zostają nietknięte (przekomponowanie DESIGNATION_PRODUCT).
    private static bool TrySetCounter(Function func, string newCounter, StringBuilder log, string oldName)
    {
        try
        {
            using (SafetyPoint sp = SafetyPoint.Create())
            {
                using (Transaction tx = new TransactionManager().CreateTransaction())
                {
                    FunctionBasePropertyList parts = func.NameParts;
                    parts.FUNC_COUNTER = newCounter;
                    func.NameParts = parts;
                    tx.Commit();
                }
                sp.Commit();
            }

            string newName = "";
            try { newName = func.Name ?? ""; } catch { }
            log.Append("OK: ").Append(oldName).Append(" -> ").AppendLine(newName);
            return true;
        }
        catch (Exception ex)
        {
            // [RYZYKO] jeśli NameParts getter/setter zachowa się inaczej w danej wersji API,
            // log pokaże komunikat — Filip weryfikuje w EPLAN, kod nie wywala pipeline.
            log.Append("ERR: ").Append(oldName).Append(" — ").AppendLine(ex.Message);
            return false;
        }
    }

    private static List<Function> CollectMainFunctions(Project project, string identifier)
    {
        var result = new List<Function>();
        foreach (Page page in project.Pages)
        {
            if (!IsSchemaGenPage(page))
                continue;

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

                string code = "";
                try { code = func.Properties.FUNC_CODE.ToString(); } catch { }

                if (string.Equals(code, identifier, StringComparison.OrdinalIgnoreCase))
                    result.Add(func);
            }
        }
        return result;
    }

    private static int ParseIntOr(ActionCallingContext ctx, string name, int def)
    {
        string v = "";
        ctx.GetParameter(name, ref v);
        int n;
        return int.TryParse((v ?? "").Trim(), out n) ? n : def;
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
                && plant.IndexOf(SchemaGenPaths.Plant, StringComparison.OrdinalIgnoreCase) >= 0;
        }
        catch
        {
            return false;
        }
    }

    private static string BuildJson(string identifier, int changed, int total, string log, string devicesJson)
    {
        return "{"
            + "\"action\":\"forceGlobalCounter\","
            + "\"identifier\":\"" + EscapeJson(identifier) + "\","
            + "\"changed\":" + changed + ","
            + "\"total\":" + total + ","
            + "\"log\":\"" + EscapeJson(log) + "\","
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
