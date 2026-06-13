//#################################################################################################################################################
// SchemaGen — SchemaGen_MVP
//#################################################################################################################################################
// Pipeline: 3 strony → makra (FrameLayout) → LinkPotentials → ConnectMotor → RenumberDevices → AuditLayout
// MACROX = RY (PointD.X), MACROY = RX (PointD.Y) — patrz SchemaGenPaths.cs
//#################################################################################################################################################
//[C#]
using System.Collections.Generic;
using System.IO;
using System.Xml;

public static class SchemaGenConfig
{
    private const string ConfigFileName = "901_Drive_Design.xml";
    private const string NumberingRulesFileName = "numbering-rules.xml";
    private const string PrimaryConfigDir =
        @"C:\Users\Public\EPLAN\Data\Skrypty\Schemagen\config\";
    private const string FallbackConfigPath =
        @"C:\Users\Public\EPLAN\Data\Projekty\Schemagen\EPLAN_Sample_Macros.edb\DOC\901_Drive_Design.xml";
    private const string FallbackNumberingRulesPath =
        @"C:\Users\Filip\Desktop\Cursor\SchemaGen\config\numbering-rules.xml";

    public const string FrequencyControlMacro =
        @"C:\Users\Public\EPLAN\Data\Makra\Schemagen\EPLAN_Macro\203_Electrical_Engine\101_02_Variant_2\Frequency_Control.ema";

    public const string StartStopRelayMacro =
        @"C:\Users\Public\EPLAN\Data\Makra\Schemagen\EPLAN_Macro\203_Electrical_Engine\202_PCT-Loop\Fan_motor_control_two_switches.ema";

    // Pozycje wstawienia — muszą być zgodne z SchemaGenPaths.cs (add-in). USE_FRAME_LAYOUT nadpisuje.
    public const double DriveMacroInsertRy = 37.0;
    public const double DriveMacroInsertRx = 37.0;
    public const double ControlMacroInsertRy = 37.0;
    public const double ControlMacroInsertRx = 37.0;

    public static string ResolveConfigPath()
    {
        string primary = PrimaryConfigDir + ConfigFileName;
        if (File.Exists(primary))
            return primary;
        if (File.Exists(FallbackConfigPath))
            return FallbackConfigPath;
        return primary;
    }

    public static string ResolveNumberingRulesPath()
    {
        string primary = PrimaryConfigDir + NumberingRulesFileName;
        if (File.Exists(primary))
            return primary;
        if (File.Exists(FallbackNumberingRulesPath))
            return FallbackNumberingRulesPath;
        return primary;
    }

    public struct NumberingRule
    {
        public string Identifier;
        public string ConfigScheme;
        public string StartValue;
        public string StepValue;
        public bool ForceGlobalCounter;
    }

    public static bool TryLoadNumberingRules(string path, out NumberingRule[] rules, out string error)
    {
        rules = null;
        error = null;

        if (!File.Exists(path))
        {
            error = "Brak pliku reguł numeracji:\n" + path;
            return false;
        }

        XmlDocument doc = new XmlDocument();
        doc.Load(path);

        XmlNodeList ruleNodes = doc.SelectNodes("//NumberingRules/rule");
        if (ruleNodes == null || ruleNodes.Count == 0)
        {
            error = "Brak elementów <rule> w pliku:\n" + path;
            return false;
        }

        var list = new List<NumberingRule>();
        foreach (XmlNode node in ruleNodes)
        {
            XmlAttribute idAttr = node.Attributes["identifier"];
            if (idAttr == null || string.IsNullOrEmpty(idAttr.Value))
                continue;

            string configScheme = "";
            XmlAttribute schemeAttr = node.Attributes["configScheme"];
            if (schemeAttr != null)
                configScheme = schemeAttr.Value ?? "";

            string startValue = "1";
            XmlAttribute startAttr = node.Attributes["startValue"];
            if (startAttr != null && !string.IsNullOrEmpty(startAttr.Value))
                startValue = startAttr.Value.Trim();

            string stepValue = "1";
            XmlAttribute stepAttr = node.Attributes["step"];
            if (stepAttr != null && !string.IsNullOrEmpty(stepAttr.Value))
                stepValue = stepAttr.Value.Trim();

            bool forceGlobalCounter = false;
            XmlAttribute forceAttr = node.Attributes["forceGlobalCounter"];
            if (forceAttr != null)
            {
                string fv = (forceAttr.Value ?? "").Trim().ToLowerInvariant();
                forceGlobalCounter = (fv == "true" || fv == "1");
            }

            list.Add(new NumberingRule
            {
                Identifier = idAttr.Value.Trim(),
                ConfigScheme = configScheme.Trim(),
                StartValue = startValue,
                StepValue = stepValue,
                ForceGlobalCounter = forceGlobalCounter
            });
        }

        if (list.Count == 0)
        {
            error = "Brak poprawnych reguł (atrybut identifier) w:\n" + path;
            return false;
        }

        rules = list.ToArray();
        return true;
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

        // 1. Add-in (DataModel) musi być załadowany przed otwarciem projektu przez API
        if (!EnsureAddInLoaded())
        {
            ShowError("Nie wczytano add-in SchemaGen.\n\nEPLAN → Plik → Dodatki → Interfejsy → API → Zarządzaj → Wczytaj");
            return;
        }

        // Sesja 1.6+: ConnectMotor, AuditLayout, ExportConnections

        // 2. Otwórz / aktywuj Hello_world (GetProject lub OpenProject — działa też gdy już otwarty)
        if (!EnsureProject(projectPath))
        {
            ShowError("Nie przygotowano projektu Hello_world.\nZamknij inne projekty i spróbuj ponownie.");
            return;
        }

        System.Threading.Thread.Sleep(1000);

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
        string controlPageName = "";
        if (!CreateSchematicPage(projectPath, ref controlPageName, "Sterowanie Start/Stop"))
        {
            ShowError("Akcja SchemaGenCreatePage (Start/Stop) nie powiodła się.");
            return;
        }

        if (!InsertControlMacro(projectPath, controlPageName))
        {
            ShowError("Akcja SchemaGenInsertPowerMacro (Start/Stop) nie powiodła się.");
            return;
        }

        LinkPotentials(projectPath);

        if (!ConnectMotor(projectPath))
        {
            ShowError("Akcja SchemaGenConnectMotor nie powiodła się.");
            return;
        }

        if (!RenumberDevices(projectPath))
        {
            ShowError("Akcja SchemaGenRenumberDevices nie powiodła się.");
            return;
        }

        AuditLayout(projectPath);

        new Decider().Decide(
            EnumDecisionType.eOkDecision,
            "Wygenerowano schemat SchemaGen:\n"
                + powerPageName + " (400V)\n"
                + drivePageName + " (napęd)\n"
                + controlPageName + " (Start/Stop)",
            "SchemaGen MVP — gotowe",
            EnumDecisionReturn.eOK,
            EnumDecisionReturn.eOK);
    }

    private static bool EnsureAddInLoaded()
    {
        ActionManager am = new ActionManager();
        if (am.FindAction("SchemaGenEnsureProject") != null
            && am.FindAction("SchemaGenCreatePage") != null
            && am.FindAction("SchemaGenInsertPowerMacro") != null
            && am.FindAction("SchemaGenConnectMotor") != null
            && am.FindAction("SchemaGenRenumberDevices") != null
            && am.FindAction("SchemaGenAuditLayout") != null)
            return true;

        string addInPath = AddInFolder + AddInFileName;
        if (!new CommandLineInterpreter().Execute(
            "EplApiModuleAction /Filename:\"" + addInPath + "\""))
            return false;

        System.Threading.Thread.Sleep(1500);
        am = new ActionManager();
        return am.FindAction("SchemaGenEnsureProject") != null
            && am.FindAction("SchemaGenCreatePage") != null
            && am.FindAction("SchemaGenInsertPowerMacro") != null
            && am.FindAction("SchemaGenConnectMotor") != null
            && am.FindAction("SchemaGenRenumberDevices") != null
            && am.FindAction("SchemaGenAuditLayout") != null;
    }

    private static bool EnsureProject(string projectPath)
    {
        ActionCallingContext ctx = new ActionCallingContext();
        ctx.AddParameter("PROJECTPATH", projectPath);
        return new CommandLineInterpreter().Execute("SchemaGenEnsureProject", ctx);
    }

    private static bool CreateSchematicPage(string projectPath, ref string pageName, string description = "")
    {
        ActionCallingContext ctx = new ActionCallingContext();
        ctx.AddParameter("PROJECTPATH", projectPath);
        ctx.AddParameter("SILENT", "1");
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
        ctx.AddParameter("SILENT", "1");
        ctx.AddParameter("USE_FRAME_LAYOUT", "1");
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
        ctx.AddParameter("SILENT", "1");
        ctx.AddParameter("MACROX", SchemaGenConfig.DriveMacroInsertRy.ToString(
            System.Globalization.CultureInfo.InvariantCulture));
        ctx.AddParameter("MACROY", SchemaGenConfig.DriveMacroInsertRx.ToString(
            System.Globalization.CultureInfo.InvariantCulture));
        if (!string.IsNullOrEmpty(driveType))
            ctx.AddParameter("DRIVETYPE", driveType);
        ctx.AddParameter("USE_FRAME_LAYOUT", "1");
        return new CommandLineInterpreter().Execute("SchemaGenInsertPowerMacro", ctx);
    }

    private static bool InsertControlMacro(string projectPath, string pageName)
    {
        ActionCallingContext ctx = new ActionCallingContext();
        ctx.AddParameter("PROJECTPATH", projectPath);
        ctx.AddParameter("PAGENAME", pageName);
        ctx.AddParameter("MACROPATH", SchemaGenConfig.StartStopRelayMacro);
        ctx.AddParameter("SILENT", "1");
        ctx.AddParameter("MACROX", SchemaGenConfig.ControlMacroInsertRy.ToString(
            System.Globalization.CultureInfo.InvariantCulture));
        ctx.AddParameter("MACROY", SchemaGenConfig.ControlMacroInsertRx.ToString(
            System.Globalization.CultureInfo.InvariantCulture));
        ctx.AddParameter("USE_FRAME_LAYOUT", "1");
        return new CommandLineInterpreter().Execute("SchemaGenInsertPowerMacro", ctx);
    }

    private static void LinkPotentials(string projectPath)
    {
        ActionCallingContext ctx = new ActionCallingContext();
        ctx.AddParameter("PROJECTPATH", projectPath);
        new CommandLineInterpreter().Execute("SchemaGenLinkPotentials", ctx);
    }

    private static bool ConnectMotor(string projectPath)
    {
        ActionCallingContext ctx = new ActionCallingContext();
        ctx.AddParameter("PROJECTPATH", projectPath);
        ctx.AddParameter("SILENT", "1");
        ctx.AddParameter("OUTPUTPATH",
            @"C:\Users\Public\EPLAN\Data\Skrypty\Schemagen\output\connect-motor.json");
        return new CommandLineInterpreter().Execute("SchemaGenConnectMotor", ctx);
    }

    private static bool RenumberDevices(string projectPath)
    {
        const string outputPath =
            @"C:\Users\Public\EPLAN\Data\Skrypty\Schemagen\output\renumber-devices.json";

        string rulesPath = SchemaGenConfig.ResolveNumberingRulesPath();
        SchemaGenConfig.NumberingRule[] rules;
        string rulesError;
        if (File.Exists(rulesPath)
            && SchemaGenConfig.TryLoadNumberingRules(rulesPath, out rules, out rulesError))
        {
            for (int i = 0; i < rules.Length; i++)
            {
                SchemaGenConfig.NumberingRule rule = rules[i];
                ActionCallingContext ctx = new ActionCallingContext();
                ctx.AddParameter("PROJECTPATH", projectPath);
                ctx.AddParameter("SILENT", "1");
                ctx.AddParameter("IDENTIFIER", rule.Identifier);
                if (!string.IsNullOrEmpty(rule.ConfigScheme))
                    ctx.AddParameter("CONFIGSCHEME", rule.ConfigScheme);
                ctx.AddParameter("STARTVALUE", rule.StartValue);
                ctx.AddParameter("STEPVALUE", rule.StepValue);
                if (i == rules.Length - 1)
                    ctx.AddParameter("OUTPUTPATH", outputPath);

                if (!new CommandLineInterpreter().Execute("SchemaGenRenumberDevices", ctx))
                    return false;
            }
            return true;
        }

        ActionCallingContext fallbackCtx = new ActionCallingContext();
        fallbackCtx.AddParameter("PROJECTPATH", projectPath);
        fallbackCtx.AddParameter("SILENT", "1");
        fallbackCtx.AddParameter("OUTPUTPATH", outputPath);
        return new CommandLineInterpreter().Execute("SchemaGenRenumberDevices", fallbackCtx);
    }

    private static void AuditLayout(string projectPath)
    {
        ActionCallingContext ctx = new ActionCallingContext();
        ctx.AddParameter("PROJECTPATH", projectPath);
        ctx.AddParameter("SILENT", "1");
        ctx.AddParameter("OUTPUTPATH",
            @"C:\Users\Public\EPLAN\Data\Skrypty\Schemagen\output\layout-audit.json");
        new CommandLineInterpreter().Execute("SchemaGenAuditLayout", ctx);
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
