using System;
using Eplan.EplApi.ApplicationFramework;
using Eplan.EplApi.Base;
using Eplan.EplApi.DataModel;
using Eplan.EplApi.DataModel.Graphics;

// Etap 2: bezpieczna adaptacja po Insert.WindowMacro.
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
            // PotentialDefinition — bezpośrednia zmiana nazwy
            PotentialDefinition pd = placement as PotentialDefinition;
            if (pd != null)
            {
                try
                {
                    string canonical = CanonicalPotentialName(pd.PotentialName);
                    if (!string.IsNullOrEmpty(canonical) && canonical != pd.PotentialName)
                    {
                        pd.PotentialName = canonical;
                        changes++;
                    }
                }
                catch
                {
                    // pojedynczy punkt — nie przerywaj insertu
                }
                continue;
            }

            // InterruptionPoint (sesja 1.7) — nosi pełną ścieżkę potencjału np. =GAA-2L1
            InterruptionPoint ip = placement as InterruptionPoint;
            if (ip != null)
            {
                try
                {
                    string canonical = CanonicalPotentialName(ip.Name);
                    if (!string.IsNullOrEmpty(canonical) && canonical != ip.Name)
                    {
                        using (SafetyPoint sp = SafetyPoint.Create())
                        {
                            using (Transaction tx = new TransactionManager().CreateTransaction())
                            {
                                ip.Name = canonical;
                                tx.Commit();
                            }
                            sp.Commit();
                        }
                        changes++;
                    }
                }
                catch
                {
                    // ip.Name może być tylko do odczytu w starszych API — ignoruj
                }
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

    // Sesja 1.7c: numeracja urządzeń wg NUMERU STRONY (tymczasowy system tagowania).
    // Każde urządzenie zachowuje swój kod (MA, FC, ...), licznik = numer strony:
    // strona 1 → MA1/FC1, strona 2 → MA2/FC2. Eliminuje duplikaty z powielanych makr.
    // Struktura DT przez NameParts (KB: datamodel), nie func.Name.
    public static int RemapDeviceTags(Page page)
    {
        if (page == null)
            return 0;

        int pageNo = PageNumber(page);
        int count = 0;
        foreach (Function func in page.Functions)
        {
            string code;
            try
            {
                code = func.Properties.FUNC_CODE.ToString();
            }
            catch
            {
                continue; // funkcja bez kodu (np. potencjał) — pomijamy
            }
            if (string.IsNullOrEmpty(code))
                continue;

            try
            {
                using (SafetyPoint sp = SafetyPoint.Create())
                {
                    using (Transaction tx = new TransactionManager().CreateTransaction())
                    {
                        var np = new FunctionBasePropertyList();
                        np.DESIGNATION_PLANT    = SchemaGenPaths.MotorPlant;
                        np.DESIGNATION_LOCATION = SchemaGenPaths.MotorLocation;
                        np.FUNC_CODE    = code;      // zachowaj istniejący kod (MA, FC, ...)
                        np.FUNC_COUNTER = pageNo;    // licznik = numer strony
                        func.NameParts = np;
                        tx.Commit();
                    }
                    sp.Commit();
                }
                count++;
            }
            catch
            {
                // pojedyncza funkcja — nie przerywaj
            }
        }
        return count;
    }

    // Numer strony z nazwy: "=SCHEMAGEN+MAIN/1" → 1. Bierze cyfry po ostatnim '/'.
    private static int PageNumber(Page page)
    {
        try
        {
            string n = page.Name ?? "";
            int slash = n.LastIndexOf('/');
            if (slash >= 0 && slash < n.Length - 1)
            {
                string tail = n.Substring(slash + 1);
                var digits = new System.Text.StringBuilder();
                foreach (char c in tail)
                {
                    if (char.IsDigit(c))
                        digits.Append(c);
                    else
                        break;
                }
                int v;
                if (digits.Length > 0 && int.TryParse(digits.ToString(), out v))
                    return v;
            }
        }
        catch { }

        return 1;
    }

    public static int ConnectMotorWindings(Project project)
    {
        if (project == null)
            return 0;

        int normalized = 0;
        foreach (Page page in project.Pages)
        {
            if (!IsSchemaGenPage(page))
                continue;
            normalized += NormalizeMotorConnectionsOnPage(page);
        }

        new CommandLineInterpreter().Execute("generate /TYPE:CONNECTIONS");
        return normalized;
    }

    private static int NormalizeMotorConnectionsOnPage(Page page)
    {
        int changes = 0;
        foreach (Function func in page.Functions)
        {
            if (!IsMotorFunction(func) && !IsDriveOutputFunction(func))
                continue;

            for (int i = 1; i <= 3; i++)
            {
                try
                {
                    string conn = func.Properties[Properties.Function.FUNC_CONNECTIONDESIGNATION, i].ToString();
                    if (string.IsNullOrEmpty(conn))
                        continue;

                    string canonical = CanonicalMotorWindingName(conn);
                    if (canonical == conn)
                        continue;

                    using (SafetyPoint sp = SafetyPoint.Create())
                    {
                        using (Transaction tx = new TransactionManager().CreateTransaction())
                        {
                            func.Properties[Properties.Function.FUNC_CONNECTIONDESIGNATION, i] = canonical;
                            tx.Commit();
                        }
                        sp.Commit();
                    }
                    changes++;
                }
                catch
                {
                    // brak indeksu połączenia — pomijamy
                }
            }
        }
        return changes;
    }

    private static bool IsMotorFunction(Function func)
    {
        if (func == null)
            return false;

        try
        {
            if (func.FunctionCategory == Eplan.EplApi.Base.Enums.FunctionCategory.Motor)
                return true;
        }
        catch { /* brak kategorii */ }

        string name = func.Name ?? "";
        if (name.IndexOf("MOTOR", StringComparison.OrdinalIgnoreCase) >= 0)
            return true;
        if (name.IndexOf("-M1", StringComparison.OrdinalIgnoreCase) >= 0)
            return true;
        if (name.IndexOf("+M1", StringComparison.OrdinalIgnoreCase) >= 0)
            return true;
        return false;
    }

    private static bool IsDriveOutputFunction(Function func)
    {
        if (func == null)
            return false;

        string name = func.Name ?? "";
        return name.IndexOf("FREQUENCY", StringComparison.OrdinalIgnoreCase) >= 0
            || name.IndexOf("CONVERTER", StringComparison.OrdinalIgnoreCase) >= 0
            || name.IndexOf("INVERTER", StringComparison.OrdinalIgnoreCase) >= 0
            || name.IndexOf("U1", StringComparison.OrdinalIgnoreCase) >= 0;
    }

    private static string CanonicalMotorWindingName(string conn)
    {
        string trimmed = (conn ?? "").Trim().ToUpperInvariant();
        if (trimmed == "U" || trimmed == "U1" || trimmed.EndsWith("-U"))
            return "U";
        if (trimmed == "V" || trimmed == "V1" || trimmed.EndsWith("-V"))
            return "V";
        if (trimmed == "W" || trimmed == "W1" || trimmed.EndsWith("-W"))
            return "W";
        return conn;
    }

    private static bool IsSchemaGenPage(Page page)
    {
        try
        {
            string plant = page.Properties[Properties.Page.DESIGNATION_PLANT].ToString();
            return plant != null && plant.IndexOf(SchemaGenPaths.Plant, StringComparison.OrdinalIgnoreCase) >= 0;
        }
        catch
        {
            return false;
        }
    }
}
