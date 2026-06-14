// Sesja 1.7d — numeracja OZNACZEŃ URZĄDZEŃ (renumber /TYPE:DEVICES).
// Bare "renumber" → S025019 "Proces jest nieobsługiwany" (brak TYPE).
// Uruchom: Narzędzia → Skrypty → SchemaGen_TryRenumber.cs
// Wymóg: Hello_world otwarty i aktywny.
public class SchemaGenTryRenumber
{
    [Start]
    public void Run()
    {
        // CONFIGSCHEME pominięty — EPLAN użyje ostatniego/wbudowanego schematu projektu.
        // USESELECTION:0 = cały projekt; ustaw 1 jeśli wcześniej zaznaczysz strony =SCHEMAGEN*.
        string cmd =
            "renumber /TYPE:DEVICES /USESELECTION:0 /STARTVALUE:1 /STEPVALUE:1 /POSTNUMERATE:0";

        bool ok = new CommandLineInterpreter().Execute(cmd);

        string msg = ok
            ? "Numeracja urządzeń (TYPE:DEVICES) zakończona OK." + System.Environment.NewLine + System.Environment.NewLine
              + "Sprawdź na schemacie:" + System.Environment.NewLine
              + "- czy -FC1 duplikat na 2 stronach → -FC1, -FC2" + System.Environment.NewLine
              + "- czy silniki mają różne -MA1, -MA2, -MA3…" + System.Environment.NewLine + System.Environment.NewLine
              + "Wywołanie:" + System.Environment.NewLine + cmd
            : "Błąd numeracji. Sprawdź eplan_output\\ErrorLog_*.csv" + System.Environment.NewLine + System.Environment.NewLine
              + "Wywołanie:" + System.Environment.NewLine + cmd;

        new Decider().Decide(
            EnumDecisionType.eOkDecision,
            msg,
            "SchemaGen — renumber DEVICES",
            EnumDecisionReturn.eOK,
            EnumDecisionReturn.eOK);
    }
}
