using Eplan.EplApi.DataModel;
using Eplan.EplApi.DataModel.Graphics;

// Etap 2: bezpieczna adaptacja po Insert.WindowMacro.
// UWAGA: RemapFunctionStructure (GAA→SCHEMAGEN via NameParts) powoduje S063111 — wyłączone do sesji 1.6.
public static class MacroAdaptation
{
    public static string CanonicalPotentialName(string name)
    {
        if (string.IsNullOrEmpty(name))
            return name;

        string trimmed = name.Trim();
        // =GAA-2L1 → 2L1 (zgodnie z makrem zasilania 400V)
        if (trimmed.StartsWith("="))
        {
            int dash = trimmed.LastIndexOf('-');
            if (dash > 0 && dash < trimmed.Length - 1)
                return trimmed.Substring(dash + 1);
        }
        return trimmed;
    }

    public static int NormalizePotentialsOnPage(Page page)
    {
        int changes = 0;
        foreach (Placement placement in page.AllFirstLevelPlacements)
        {
            PotentialDefinition pd = placement as PotentialDefinition;
            if (pd == null)
                continue;

            try
            {
                string canonical = CanonicalPotentialName(pd.PotentialName);
                if (string.IsNullOrEmpty(canonical) || canonical == pd.PotentialName)
                    continue;

                pd.PotentialName = canonical;
                changes++;
            }
            catch
            {
                // pojedynczy punkt — nie przerywaj insertu
            }
        }
        return changes;
    }

    public static void AdaptInsertedObjects(StorableObject[] inserted, string driveTypeRecord)
    {
        if (inserted == null || string.IsNullOrEmpty(driveTypeRecord))
            return;

        foreach (StorableObject obj in inserted)
        {
            PlaceHolder ph = obj as PlaceHolder;
            if (ph == null)
                continue;

            try
            {
                ph.ApplyRecord(driveTypeRecord);
            }
            catch
            {
                // brak rekordu PlaceHolder — ignoruj
            }
        }
    }
}
