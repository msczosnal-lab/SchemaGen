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
    public const string ControlPageDescription = "Sterowanie Start/Stop";

    public const string FrequencyControl =
        @"C:\Users\Public\EPLAN\Data\Makra\Schemagen\EPLAN_Macro\203_Electrical_Engine\101_02_Variant_2\Frequency_Control.ema";

    public const string StartStopRelay =
        @"C:\Users\Public\EPLAN\Data\Makra\Schemagen\EPLAN_Macro\203_Electrical_Engine\202_PCT-Loop\Fan_motor_control_two_switches.ema";

    // Insert.WindowMacro PointD(X, Y): X → oś RY (pion strony), Y → oś RX (poziom).
    // Test 1.5: zmiana „MacroInsertY” przesuwała RX, nie RY.
    // Pozycja wklejania: RY=1, RX=1 (góra-lewo strony).
    public const double MacroInsertRy = -1.0;
    public const double MacroInsertRx = 18.0;

    public const double DriveMacroInsertRy = -1.0;
    public const double DriveMacroInsertRx = 18.0;

    public const double ControlMacroInsertRy = -1.0;
    public const double ControlMacroInsertRx = 18.0;

    // Aliasy dla kompatybilności parametrów CLI MACROX/MACROY (X=RY, Y=RX)
    public const double MacroInsertX = MacroInsertRy;
    public const double MacroInsertY = MacroInsertRx;
    public const double DriveMacroInsertX = DriveMacroInsertRy;
    public const double DriveMacroInsertY = DriveMacroInsertRx;
    public const double ControlMacroInsertX = ControlMacroInsertRy;
    public const double ControlMacroInsertY = ControlMacroInsertRx;
}
