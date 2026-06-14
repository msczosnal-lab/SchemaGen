using Eplan.EplApi.Scripting;
using Eplan.EplApi.ApplicationFramework;

// Sesja 1.7d — wyzwalacz akcji połączenia uzwojeń silnika + diagnostyka.
// Skrypt NIE używa typów DataModel (Page/Function) — te są tylko w add-in (DLL).
// Skrypt jedynie woła zarejestrowaną akcję przez CommandLineInterpreter.
// Bez SILENT -> okno z raportem (liczba przebiegów CONNECTIONS, gedRedraw).
// Wynik także w pliku Skrypty\Schemagen\output\connect-motor.json.
// Wymóg: projekt Hello_world OTWARTY i aktywny.
public class SchemaGenConnectMotorScript
{
    [Start]
    public void Run()
    {
        ActionCallingContext ctx = new ActionCallingContext();
        ctx.AddParameter("OUTPUTPATH",
            @"C:\Users\Public\EPLAN\Data\Skrypty\Schemagen\output\connect-motor.json");
        new CommandLineInterpreter().Execute("SchemaGenConnectMotor", ctx);
    }
}
