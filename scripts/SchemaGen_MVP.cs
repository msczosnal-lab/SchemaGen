//#################################################################################################################################################
// SchemaGen — SchemaGen_MVP
//#################################################################################################################################################
// Sesja 1.4: Wczytuje XML → dwie strony (400V + napęd) → generate CONNECTIONS
// Orkiestracja przez CLI; logika DataModel/HEServices w add-in DLL.
// Kod źródłowy: repo scripts/ → kopia do C:\Users\Public\EPLAN\Data\Skrypty\Schemagen\
// UWAGA EPLAN: tylko jeden plik .cs w Skrypty\Schemagen\ — helper SchemaGenConfig w tym samym pliku.
//#################################################################################################################################################
//[C#]
using System.Collections.Generic;
using System.IO;
using System.Xml;

public static class SchemaGenConfig
{
    private const string ConfigFileName = "901_Drive_Design.xml";
    private const string PrimaryConfigDir =
        @"C:\Users\Public\EPLAN\Data\Skrypty\Schemagen\config\";
    private const string FallbackConfigPath =
        @"C:\Users\Public\EPLAN\Data\Projekty\Schemagen\EPLAN_Sample_Macros.edb\DOC\901_Drive_Design.xml";

    public const string FrequencyControlMacro =
        @"C:\Users\Public\EPLAN\Data\Makra\Schemagen\EPLAN_Macro\203_Electrical_Engine\101_02_Variant_2\Frequency_Control.ema";

    public const double DriveMacroInsertX = 16.0;
    public const double DriveMacroInsertY = 8.35; // wycentrowane w ramce RY 0,2..70

    public static string ResolveConfigPath()
    {
        string primary = PrimaryConfigDir + ConfigFileName;
        if (File.Exists(primary))
            return primary;
        if (File.Exists(FallbackConfigPath))
            return FallbackConfigPath;
        return primary;
    }

    public static bool TryLoad(out Dictionary<string, string> config, out string error)
    {
        config = new Dictionary<string, string>();
        error = null;

        string path = ResolveConfigPath();
        if (!File.Exists(path))
        {
            error = "Nie znaleziono pliku konfiguracji XML:\n" + path
                + "\n\nSkopiuj config\\901_Drive_Design.xml do Skrypty\\Schemagen\\config\\";
            return false;
        }

        XmlDocument doc = new XmlDocument();
        doc.Load(path);

        XmlNodeList nodes = doc.SelectNodes("//ConfigurationVariable");
        if (nodes == null || nodes.Count == 0)
        {
            error = "Brak zmiennych ConfigurationVariable w pliku:\n" + path;
            return false;
        }

        foreach (XmlNode node in nodes)
        {
            XmlAttribute nameAttr = node.Attributes["name"];
            if (nameAttr == null || string.IsNullOrEmpty(nameAttr.Value))
                continue;
            config[nameAttr.Value] = node.InnerText.Trim();
        }

        return true;
    }

    public static bool TryGetDriveMacroPath(
        Dictionary<string, string> config,
        out string macroPath,
        out string error)
    {
        macroPath = null;
        error = null;

        string driveControl;
        if (!config.TryGetValue("SE_Drive_Control", out driveControl)
            || string.IsNullOrEmpty(driveControl))
        {
            error = "Brak zmiennej SE_Drive_Control w XML konfiguracji.";
            return false;
        }

        if (driveControl == "Frequency Converter")
        {
            macroPath = FrequencyControlMacro;
            return true;
        }

        error = "Nieobsługiwany typ sterowania napędu: " + driveControl;
        return false;
    }

    public static string GetDriveType(Dictionary<string, string> config)
    {
        string driveType;
        if (config.TryGetValue("SE_Drive_Type", out driveType))
            return driveType;
        return "";
    }
}

public class SchemaGen_MVP
{
    private const string AddInFileName = "SchemaGen.EplAddIn..dll";
    private const string AddInFolder =
        @"C:\Users\Public\EPLAN\Data\Skrypty\Schemagen\";

    [Start]
    public void Run()
    {
        Dictionary<string, string> config;
        string configError;
        if (!SchemaGenConfig.TryLoad(out config, out configError))
        {
            ShowError(configError);
            return;
        }

        string driveMacroPath;
        string driveError;
        if (!SchemaGenConfig.TryGetDriveMacroPath(config, out driveMacroPath, out driveError))
        {
            ShowError(driveError);
            return;
        }

        string driveType = SchemaGenConfig.GetDriveType(config);
        string projectPath = PathMap.SubstitutePath(@"$(MD_PROJECTS)\Hello_world.elk");

        // EPLAN wymaga jednego otwartego projektu — zamknij inne przed uruchomieniem
        bool opened = OpenProject(projectPath);
        if (opened)
            System.Threading.Thread.Sleep(3000);

        if (!EnsureAddInLoaded())
        {
            ShowError("Nie wczytano add-in SchemaGen.");
            return;
        }

        // Strona 1: zasilanie 400VAC
        string powerPageName = "";
        if (!CreateSchematicPage(projectPath, ref powerPageName, "Zasilanie 400VAC"))
        {
            ShowError("Akcja SchemaGenCreatePage (zasilanie) nie powiodła się.");
            return;
        }

        if (!InsertPowerMacro(projectPath, powerPageName))
        {
            ShowError("Akcja SchemaGenInsertPowerMacro (400V) nie powiodła się.");
            return;
        }

        // Strona 2: sterowanie napędem
        string drivePageName = "";
        if (!CreateSchematicPage(projectPath, ref drivePageName, "Sterowanie napędem"))
        {
            ShowError("Akcja SchemaGenCreatePage (napęd) nie powiodła się.");
            return;
        }

        if (!InsertDriveMacro(projectPath, drivePageName, driveMacroPath, driveType))
        {
            ShowError("Akcja SchemaGenInsertPowerMacro (falownik) nie powiodła się.");
            return;
        }

        // Połączenia i odnośniki między punktami przerwania potencjałów (L1/L2/L3/PE) — weryfikacja w 1.5
        new CommandLineInterpreter().Execute("generate /TYPE:CONNECTIONS");
    }

    private static bool OpenProject(string projectPath)
    {
        CommandLineInterpreter cli = new CommandLineInterpreter();
        if (cli.Execute("ProjectOpen /Project:\"" + projectPath + "\""))
            return true;
        if (cli.Execute("XPrjActionProjectOpen /PROJECT:\"" + projectPath + "\""))
            return true;
        return cli.Execute("edit /PROJECTNAME:\"" + projectPath + "\"");
    }

    private static bool EnsureAddInLoaded()
    {
        ActionManager am = new ActionManager();
        if (am.FindAction("SchemaGenCreatePage") != null
            && am.FindAction("SchemaGenInsertPowerMacro") != null)
            return true;

        string addInPath = AddInFolder + AddInFileName;
        return new CommandLineInterpreter().Execute(
            "EplApiModuleAction /Filename:\"" + addInPath + "\"");
    }

    private static bool CreateSchematicPage(string projectPath, ref string pageName, string description = "")
    {
        ActionCallingContext ctx = new ActionCallingContext();
        ctx.AddParameter("PROJECTPATH", projectPath);
        if (!string.IsNullOrEmpty(description))
            ctx.AddParameter("PAGEDESCRIPTION", description);
        if (!new CommandLineInterpreter().Execute("SchemaGenCreatePage", ctx))
            return false;

        ctx.GetParameter("PAGENAME", ref pageName);
        return !string.IsNullOrEmpty(pageName);
    }

    private static bool InsertPowerMacro(string projectPath, string pageName)
    {
        ActionCallingContext ctx = new ActionCallingContext();
        ctx.AddParameter("PROJECTPATH", projectPath);
        ctx.AddParameter("PAGENAME", pageName);
        return new CommandLineInterpreter().Execute("SchemaGenInsertPowerMacro", ctx);
    }

    private static bool InsertDriveMacro(
        string projectPath,
        string pageName,
        string macroPath,
        string driveType)
    {
        ActionCallingContext ctx = new ActionCallingContext();
        ctx.AddParameter("PROJECTPATH", projectPath);
        ctx.AddParameter("PAGENAME", pageName);
        ctx.AddParameter("MACROPATH", macroPath);
        ctx.AddParameter("MACROX", SchemaGenConfig.DriveMacroInsertX.ToString(
            System.Globalization.CultureInfo.InvariantCulture));
        ctx.AddParameter("MACROY", SchemaGenConfig.DriveMacroInsertY.ToString(
            System.Globalization.CultureInfo.InvariantCulture));
        if (!string.IsNullOrEmpty(driveType))
            ctx.AddParameter("DRIVETYPE", driveType);
        return new CommandLineInterpreter().Execute("SchemaGenInsertPowerMacro", ctx);
    }

    private static void ShowError(string message)
    {
        new Decider().Decide(
            EnumDecisionType.eOkDecision,
            message,
            "SchemaGen MVP",
            EnumDecisionReturn.eOK,
            EnumDecisionReturn.eOK);
        new CommandLineInterpreter().Execute("SystemErrDialog");
    }
}

