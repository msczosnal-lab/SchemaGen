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
    public static int RemapDeviceTags(Page page, System.Text.StringBuilder diag)
    {
        if (page == null)
            return 0;

        int count = 0;
        int funcSeen = 0;
        foreach (Function func in page.Functions)
        {
            // Tylko funkcje GŁÓWNE urządzeń — pomijamy styki/zaciski/cewki (podfunkcje).
            try { if (!func.IsMainFunction) continue; } catch { }

            funcSeen++;
            string dt = "";
            try { dt = func.Name; } catch { }

            // <20010> = widoczny DT (override z makra). Gdy niepusty, przesłania wyliczone DT.
            // Czyścimy go, by edytor pokazał strukturalne oznaczenie (które EPLAN numeruje poprawnie).
            string visBefore = "";
            try { visBefore = func.Properties[20010, 0].ToString(); } catch { }

            string visAfter = visBefore;
            bool ok = false;
            try
            {
                using (SafetyPoint sp = SafetyPoint.Create())
                {
                    using (Transaction tx = new TransactionManager().CreateTransaction())
                    {
                        func.Properties[20010, 0] = "";
                        tx.Commit();
                    }
                    sp.Commit();
                }
                try { visAfter = func.Properties[20010, 0].ToString(); } catch { }
                ok = true;
                count++;
            }
            catch (System.Exception ex)
            {
                if (diag != null)
                    diag.AppendLine(page.Name + " | DT=" + dt + " | WYJATEK: " + ex.Message);
            }

            if (ok && diag != null)
                diag.AppendLine(page.Name + " | DT=" + dt
                    + " | vis20010: '" + visBefore + "' -> '" + visAfter + "'");
        }

        if (diag != null && funcSeen == 0)
            diag.AppendLine(page.Name + " | BRAK FUNKCJI na stronie");
        return count;
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
