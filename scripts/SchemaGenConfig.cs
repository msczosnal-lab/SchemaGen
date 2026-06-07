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
    public const double DriveMacroInsertY = 40.0;

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
