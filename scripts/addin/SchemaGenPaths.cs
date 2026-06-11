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
    // Sesja 1.7b: FrameMin + FrameMargin (domyślnie gdy USE_FRAME_LAYOUT=0)
    public const double MacroInsertRy = 37.0;
    public const double MacroInsertRx = 37.0;

    public const double DriveMacroInsertRy = 37.0;
    public const double DriveMacroInsertRx = 37.0;

    public const double ControlMacroInsertRy = 37.0;
    public const double ControlMacroInsertRx = 37.0;

    // Aliasy dla kompatybilności parametrów CLI MACROX/MACROY (X=RY, Y=RX)
    public const double MacroInsertX = MacroInsertRy;
    public const double MacroInsertY = MacroInsertRx;
    public const double DriveMacroInsertX = DriveMacroInsertRy;
    public const double DriveMacroInsertY = DriveMacroInsertRx;
    public const double ControlMacroInsertX = ControlMacroInsertRy;
    public const double ControlMacroInsertY = ControlMacroInsertRx;

    // Oznaczenie silnika (sesja 1.6)
    public const string MotorDesignation = "=MACHINE+CABINET-M1";

    // Sesja 1.7c: struktura DT silnika rozbita na NameParts (=PLANT +LOCATION -CODE+COUNTER).
    // func.Name = "=...-M1" nie ustawia struktury — wymagane NameParts (KB: datamodel).
    public const string MotorPlant    = "MACHINE";  // =
    public const string MotorLocation = "CABINET";  // +
    public const string MotorCode     = "MA";       // -MA (napęd) — licznik nadawany rosnąco: MA1, MA2, ...

    // Obszar rysunkowy ramki strony (mm, oś RY/RX) — kalibruj przez SchemaGenAuditLayout
    // Hello_world / IEC_bas003: A3 landscape; MinRy/MinRx poniżej nagłówka strony (layout-audit)
    public const double FrameMinRy = 35.0;
    public const double FrameMinRx = 35.0;
    public const double PageWidthMm  = 420.0;   // A3 landscape — poziom (RX)
    public const double PageHeightMm = 297.0;   // A3 landscape — pion (RY)
    public const double FrameMaxRy = 287.0;     // PageHeightMm − 10mm margines
    public const double FrameMaxRx = 415.0;     // PageWidthMm  − 5mm margines
    public const double FrameMarginRy = 2.0;
    public const double FrameMarginRx = 2.0;

    // Domyślne ścieżki wyjścia MCP / walidacji
    public const string DefaultLayoutAuditPath =
        @"C:\Users\Public\EPLAN\Data\Skrypty\Schemagen\output\layout-audit.json";
    public const string DefaultConnectionsExportPath =
        @"C:\Users\Public\EPLAN\Data\Skrypty\Schemagen\output\connections.csv";
    public const string DefaultValidationReportPath =
        @"C:\Users\Public\EPLAN\Data\Skrypty\Schemagen\output\validation-report.json";
}
