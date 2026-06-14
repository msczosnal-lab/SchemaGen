using System.IO;
using System.Text;
using Eplan.EplApi.ApplicationFramework;
using Eplan.EplApi.DataModel;

// Sesja 1.6: połączenie uzwojeń silnika (U/V/W) + generate CONNECTIONS.
// Sesja 1.7d: usunięto remap DT silnika (ślepa uliczka) — akcja łączy tylko uzwojenia.
//             Numeracja DT urządzeń = osobny krok (natywny renumber EPLAN).
public class SchemaGenConnectMotorAction : IEplAction
{
    public bool OnRegister(ref string Name, ref int Ordinal)
    {
        Name = "SchemaGenConnectMotor";
        Ordinal = 23;
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

        int connections = MacroAdaptation.ConnectMotorWindings(oProject);

        bool viewRefreshed = new CommandLineInterpreter().Execute("gedRedraw");

        string outputPath = "";
        ctx.GetParameter("OUTPUTPATH", ref outputPath);
        string json = BuildJson(connections, viewRefreshed);
        if (!string.IsNullOrEmpty(outputPath))
        {
            string dir = Path.GetDirectoryName(outputPath);
            if (!string.IsNullOrEmpty(dir))
                Directory.CreateDirectory(dir);
            File.WriteAllText(outputPath, json, Encoding.UTF8);
        }

        string silent = "";
        ctx.GetParameter("SILENT", ref silent);
        if (silent == "1")
            return true;

        SchemaGenUi.ShowSuccess(
            "SchemaGen — uzwojenia silnika",
            "Połączenia uzwojeń (generate CONNECTIONS): " + connections
            + "\nOdświeżenie widoku (gedRedraw): " + (viewRefreshed ? "OK" : "błąd")
            + "\n\nNumeracja DT urządzeń (FC/MA): osobny krok — natywny renumber EPLAN.");
        return true;
    }

    private static string BuildJson(int connections, bool viewRefreshed)
    {
        return "{"
            + "\"connectionPasses\":" + connections + ","
            + "\"viewRefreshed\":" + (viewRefreshed ? "true" : "false")
            + "}";
    }
}
