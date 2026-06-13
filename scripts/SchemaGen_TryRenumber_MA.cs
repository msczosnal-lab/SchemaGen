// Sesja 1.7f — PROBE: dual-pass renumber dla GLOBALNEGO MA przy FC per-lokalizacja.
// Cel: potwierdzić (a) że /IDENTIFIER i /CONFIGSCHEME działają, (b) nazwy schematów EPLAN,
//      które dają silniki +B2-MA1, +B4-MA2 (różne), a FC zostawiają per-lokalizacja.
// BEZ using System / Eplan.* — EPLAN wstrzykuje je automatycznie (CS0105).
// Uruchom: Narzędzia → Skrypty → SchemaGen_TryRenumber_MA.cs
// Wymóg: Hello_world po MVP otwarty i aktywny (są strony =SCHEMAGEN z FC i silnikami MA w +B2, +B4).
//
// JAK UŻYĆ (1 raz, żeby ustalić nazwy schematów):
// 1. EPLAN: Ustawienia → Projekty → <projekt> → Urządzenia → Numeracja (offline).
//    Przepisz DOKŁADNE nazwy dwóch schematów do stałych poniżej:
//      MaProjectWideScheme — schemat liczący w obrębie CAŁEGO projektu (ignoruje lokalizację)
//      FcPerLocationScheme — schemat liczący per lokalizacja ("" = domyślny projektu)
// 2. Uruchom skrypt, przeczytaj komunikat, sprawdź DT na schemacie.
// 3. Działające nazwy wpisz do config/numbering-rules.xml (atrybut configScheme).
public class SchemaGenTryRenumberMa
{
    // Schematy z Twojego EPLAN (1.7f). MA = globalny licznik co kolumnę; FC = domyślny per-lokalizacja.
    // Jeśli nazwa nie zadziała — sprawdź dokładną pisownię w Ustawienia → Numeracja offline.
    const string MaProjectWideScheme = "Identyfikator + Licznik techniki strumieniowej";
    const string FcPerLocationScheme = "";   // "" = domyślny schemat projektu (per lokalizacja)

    [Start]
    public void Run()
    {
        CommandLineInterpreter cli = new CommandLineInterpreter();

        // Pass 1: FC — per lokalizacja (bez zmian względem 1.7d)
        string fcCmd = BuildCmd("FC", FcPerLocationScheme);
        bool fcOk = cli.Execute(fcCmd);

        // Pass 2: MA — cały projekt → MA1, MA2 globalnie
        string maCmd = BuildCmd("MA", MaProjectWideScheme);
        bool maOk = cli.Execute(maCmd);

        cli.Execute("gedRedraw");

        string msg =
            "DUAL-PASS renumber (probe 1.7f):" + System.Environment.NewLine + System.Environment.NewLine
            + "FC: " + (fcOk ? "OK" : "BŁĄD") + System.Environment.NewLine + "  " + fcCmd + System.Environment.NewLine + System.Environment.NewLine
            + "MA: " + (maOk ? "OK" : "BŁĄD") + System.Environment.NewLine + "  " + maCmd + System.Environment.NewLine + System.Environment.NewLine
            + "SPRAWDŹ na schemacie:" + System.Environment.NewLine
            + "  - silniki: +B2-MA1, +B4-MA2 (RÓŻNE) → cel osiągnięty" + System.Environment.NewLine
            + "  - falowniki FC: licznik per lokalizacja bez zmian" + System.Environment.NewLine + System.Environment.NewLine
            + "DIAGNOSTYKA:" + System.Environment.NewLine
            + "  - MA nadal wszędzie -MA1 → zły/pusty CONFIGSCHEME dla MA; wpisz schemat 'cały projekt'." + System.Environment.NewLine
            + "  - Błąd S025019 / proces nieobsługiwany przy /IDENTIFIER lub /CONFIGSCHEME →" + System.Environment.NewLine
            + "    ten parametr NIE jest wspierany przez renumber. Napisz — zmienię podejście (FUNC_COUNTER w add-inie)." + System.Environment.NewLine + System.Environment.NewLine
            + "Po ustaleniu działających nazw → wpisz je do config/numbering-rules.xml (configScheme).";

        new Decider().Decide(
            EnumDecisionType.eOkDecision,
            msg,
            "SchemaGen — probe MA global (1.7f)",
            EnumDecisionReturn.eOK,
            EnumDecisionReturn.eOK);
    }

    static string BuildCmd(string identifier, string scheme)
    {
        string cmd = "renumber /TYPE:DEVICES /USESELECTION:0 /STARTVALUE:1 /STEPVALUE:1 /POSTNUMERATE:0"
            + " /IDENTIFIER:" + identifier;
        if (scheme != null && scheme.Length > 0)
            cmd += " /CONFIGSCHEME:\"" + scheme + "\"";
        return cmd;
    }
}
