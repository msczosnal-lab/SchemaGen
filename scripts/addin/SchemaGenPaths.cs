// Stałe ścieżek i oznaczeń — bez logiki.
// Źródło ścieżek: docs/eplan-data-paths.txt
public static class SchemaGenPaths
{
    public const string Plant = "SCHEMAGEN";
    public const string Location = "MAIN";

    public const string PowerSupply400Vac =
        @"C:\Users\Public\EPLAN\Data\Makra\Schemagen\EPLAN_Macro\201_Power_Supply\101_01_Variant_1\400VAC_Power_Supply.ema";

    public const string PowerPageDescription = "Zasilanie 400VAC";
    public const string DrivePageDescription = "Sterowanie napędem";

    public const string FrequencyControl =
        @"C:\Users\Public\EPLAN\Data\Makra\Schemagen\EPLAN_Macro\203_Electrical_Engine\101_02_Variant_2\Frequency_Control.ema";

    public const double MacroInsertX = 16.0;
    public const double MacroInsertY = 0.0;

    public const double DriveMacroInsertX = 16.0;
    public const double DriveMacroInsertY = 40.0;
}
