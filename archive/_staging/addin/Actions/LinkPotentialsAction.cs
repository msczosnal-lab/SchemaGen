using System.Collections.Generic;
using System.Text;
using Eplan.EplApi.ApplicationFramework;
using Eplan.EplApi.Base;
using Eplan.EplApi.DataModel;

// Normalizuje nazwy potencjałów między stronami (=GAA-2L1 → 2L1), generate CONNECTIONS, audyt odnośników.
public class SchemaGenLinkPotentialsAction : IEplAction
{
    public bool OnRegister(ref string Name, ref int Ordinal)
    {
        Name = "SchemaGenLinkPotentials";
        Ordinal = 22;
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

        int normalized = 0;
        foreach (Page page in oProject.Pages)
        {
            if (!IsSchemaGenPage(page))
                continue;
            normalized += MacroAdaptation.NormalizePotentialsOnPage(page);
        }

        new CommandLineInterpreter().Execute("generate /TYPE:CONNECTIONS");

        int interruptionCount = 0;
        int potentialDefCount = 0;
        int linkedGroups = 0;
        int unlinkedGroups = 0;
        var report = new StringBuilder();

        var interruptionByName = new Dictionary<string, List<InterruptionPoint>>();
        var potentialByName = new Dictionary<string, List<PotentialDefinition>>();

        foreach (Page page in oProject.Pages)
        {
            if (!IsSchemaGenPage(page))
                continue;

            foreach (Placement placement in page.AllFirstLevelPlacements)
            {
                InterruptionPoint ip = placement as InterruptionPoint;
                if (ip != null && !string.IsNullOrEmpty(ip.Name))
                {
                    interruptionCount++;
                    string key = MacroAdaptation.CanonicalPotentialName(ip.Name);
                    List<InterruptionPoint> list;
                    if (!interruptionByName.TryGetValue(key, out list))
                    {
                        list = new List<InterruptionPoint>();
                        interruptionByName[key] = list;
                    }
                    list.Add(ip);
                    continue;
                }

                PotentialDefinition pd = placement as PotentialDefinition;
                if (pd == null)
                    continue;

                string potName = MacroAdaptation.CanonicalPotentialName(pd.PotentialName);
                if (string.IsNullOrEmpty(potName))
                    continue;

                potentialDefCount++;
                List<PotentialDefinition> potList;
                if (!potentialByName.TryGetValue(potName, out potList))
                {
                    potList = new List<PotentialDefinition>();
                    potentialByName[potName] = potList;
                }
                potList.Add(pd);
            }
        }

        AuditGroups(interruptionByName, report, ref linkedGroups, ref unlinkedGroups, "Punkty przerwania");
        AuditPotentialGroups(potentialByName, report, ref linkedGroups, ref unlinkedGroups);

        string summary = "Znormalizowano potencjałów: " + normalized
            + "\nPunkty przerwania: " + interruptionCount
            + "\nDefinicje potencjału: " + potentialDefCount
            + "\nGrupy z odnośnikami: " + linkedGroups
            + "\nGrupy bez odnośników (wielostronne): " + unlinkedGroups;

        if (unlinkedGroups > 0)
        {
            SchemaGenUi.ShowError(
                "SchemaGen — odnośniki potencjałów (ostrzeżenie)",
                summary + "\n\nSzczegóły:\n" + report
                + "\n\nSchemat wygenerowany — sprawdź odnośniki ręcznie w GED.");
            return true;
        }

        SchemaGenUi.ShowSuccess(
            "SchemaGen — odnośniki potencjałów",
            summary + (report.Length > 0 ? "\n\n" + report : ""));
        return true;
    }

    private static bool IsSchemaGenPage(Page page)
    {
        string plant = page.Properties[Properties.Page.DESIGNATION_PLANT].ToString();
        return plant != null && plant.IndexOf(SchemaGenPaths.Plant, System.StringComparison.OrdinalIgnoreCase) >= 0;
    }

    private static void AuditGroups<T>(
        Dictionary<string, List<T>> groups,
        StringBuilder report,
        ref int linkedGroups,
        ref int unlinkedGroups,
        string label) where T : StorableObject
    {
        foreach (KeyValuePair<string, List<T>> entry in groups)
        {
            List<T> points = entry.Value;
            if (points.Count < 2)
                continue;

            var pages = new HashSet<string>();
            foreach (T pt in points)
            {
                Placement pl = pt as Placement;
                if (pl != null && pl.Page != null)
                    pages.Add(pl.Page.Name);
            }

            if (pages.Count < 2)
                continue;

            bool hasCrossRef = false;
            foreach (T pt in points)
            {
                StorableObject[] refs = pt.CrossReferencedObjectsAll;
                if (refs != null && refs.Length > 0)
                {
                    hasCrossRef = true;
                    break;
                }
            }

            if (hasCrossRef)
                linkedGroups++;
            else
            {
                unlinkedGroups++;
                report.AppendLine(label + " \"" + entry.Key + "\": brak odnośnika (" + pages.Count + " strony)");
            }
        }
    }

    private static void AuditPotentialGroups(
        Dictionary<string, List<PotentialDefinition>> groups,
        StringBuilder report,
        ref int linkedGroups,
        ref int unlinkedGroups)
    {
        foreach (KeyValuePair<string, List<PotentialDefinition>> entry in groups)
        {
            List<PotentialDefinition> points = entry.Value;
            if (points.Count < 2)
                continue;

            var pages = new HashSet<string>();
            foreach (PotentialDefinition pd in points)
            {
                if (pd.Page != null)
                    pages.Add(pd.Page.Name);
            }

            if (pages.Count < 2)
                continue;

            bool hasCrossRef = false;
            foreach (PotentialDefinition pd in points)
            {
                StorableObject[] refs = pd.CrossReferencedObjectsAll;
                if (refs != null && refs.Length > 0)
                {
                    hasCrossRef = true;
                    break;
                }
            }

            if (hasCrossRef)
                linkedGroups++;
            else
            {
                unlinkedGroups++;
                report.AppendLine("Potencjał \"" + entry.Key + "\": brak odnośnika (" + pages.Count + " strony)");
            }
        }
    }
}
