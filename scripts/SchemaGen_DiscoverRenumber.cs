// Sesja 1.7d — nasłuch akcji (wymaga WCZYTANIA skryptu, nie tylko Uruchom).
// BEZ using System / Eplan.* — EPLAN wstrzykuje je automatycznie (CS0105).
// Wczytaj: Plik → Dodatki → Interfejsy → Skrypty → Wczytaj (nie Uruchom!)
// Potem: numeracja URZĄDZEŃ (renumber), NIE stron (StartOfflineNumeration).
// Wynik: C:\Users\Public\EPLAN\Data\Skrypty\Schemagen\output\action-log.txt
// Prostsza ścieżka: SchemaGen_TryRenumber.cs — woła renumber bezpośrednio.
public class SchemaGenDiscoverRenumber
{
    static readonly string LogPath =
        @"C:\Users\Public\EPLAN\Data\Skrypty\Schemagen\output\action-log.txt";

    [DeclareEventHandler("onActionStart.String.*")]
    public long OnActionStart(IEventParameter iEventParameter)
    {
        try
        {
            EventParameterString ep = new EventParameterString(iEventParameter);
            string name = ep.String ?? "";
            string line = System.DateTime.Now.ToString("HH:mm:ss") + "  " + name + System.Environment.NewLine;
            string dir = System.IO.Path.GetDirectoryName(LogPath);
            if (!string.IsNullOrEmpty(dir))
                System.IO.Directory.CreateDirectory(dir);
            System.IO.File.AppendAllText(LogPath, line);
        }
        catch
        {
            // handler nie może blokować EPLAN
        }
        return 0;
    }

    [Start]
    public void Run()
    {
        string dir = System.IO.Path.GetDirectoryName(LogPath);
        if (!string.IsNullOrEmpty(dir))
            System.IO.Directory.CreateDirectory(dir);

        System.IO.File.WriteAllText(LogPath,
            "=== SchemaGen action-log " + System.DateTime.Now + " ===" + System.Environment.NewLine
            + "Poniżej pojawią się nazwy akcji po kliknięciu Projekt → Numeruj." + System.Environment.NewLine
            + System.Environment.NewLine);

        // Bez zmiennej typu Action — unikamy konfliktu System.Action vs Eplan.Action (CS0104).
        bool exists = new ActionManager().FindAction("renumber") != null;

        string msg =
            "UWAGA: Ten skrypt musi być WCZYTANY (Plik→Dodatki→Interfejsy→Skrypty→Wczytaj)," + System.Environment.NewLine
            + "nie tylko Uruchom — inaczej log będzie pusty." + System.Environment.NewLine + System.Environment.NewLine
            + "NIE używaj numeracji STRON (StartOfflineNumeration)!" + System.Environment.NewLine
            + "Potrzebna numeracja URZĄDZEŃ (akcja renumber)." + System.Environment.NewLine + System.Environment.NewLine
            + "Prościej: uruchom SchemaGen_TryRenumber.cs zamiast tego skryptu." + System.Environment.NewLine + System.Environment.NewLine
            + "Akcja 'renumber' w systemie: " + (exists ? "TAK" : "NIE") + System.Environment.NewLine
            + "Log: " + LogPath;

        new Decider().Decide(
            EnumDecisionType.eOkDecision,
            msg,
            "SchemaGen — odkryj renumber",
            EnumDecisionReturn.eOK,
            EnumDecisionReturn.eOK);
    }
}
