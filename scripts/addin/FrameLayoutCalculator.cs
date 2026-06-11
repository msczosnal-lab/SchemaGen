using Eplan.EplApi.Base;

/// <summary>
/// Oblicza docelowy punkt wstawienia makra w obszarze ramki strony.
/// Granice ramki: SchemaGenPaths.Frame* (kalibruj przez SchemaGenAuditLayout).
/// </summary>
public static class FrameLayoutCalculator
{
    public struct FrameRect
    {
        public double MinRy;
        public double MinRx;
        public double MaxRy;
        public double MaxRx;
    }

    public struct InsertTarget
    {
        public double Ry;
        public double Rx;
        public bool FitsKnownContent;
        public bool MacroTooLarge;
    }

    public struct FitReport
    {
        public FrameRect Frame;
        public Bounds2D Content;
        public bool FitsInFrame;
        public bool MacroTooLarge;
        public bool OverflowTop;
        public bool OverflowLeft;
        public bool OverflowRight;
        public bool OverflowBottom;
    }

    public static FrameRect DefaultFrame()
    {
        return new FrameRect
        {
            MinRy = SchemaGenPaths.FrameMinRy,
            MinRx = SchemaGenPaths.FrameMinRx,
            MaxRy = SchemaGenPaths.FrameMaxRy,
            MaxRx = SchemaGenPaths.FrameMaxRx
        };
    }

    /// <summary>
    /// Docelowy lewy-górny róg makra (RY/RX) — MacroFitCalculator wstawia na target − offset.
    /// </summary>
    public static InsertTarget ComputeInsertPoint(Bounds2D macroBounds, FrameRect frame)
    {
        double marginRy = SchemaGenPaths.FrameMarginRy;
        double marginRx = SchemaGenPaths.FrameMarginRx;
        double targetRy = frame.MinRy + marginRy;
        double targetRx = frame.MinRx + marginRx;

        if (!macroBounds.IsValid)
        {
            return new InsertTarget
            {
                Ry = targetRy,
                Rx = targetRx,
                FitsKnownContent = false,
                MacroTooLarge = false
            };
        }

        double macroHeight = macroBounds.HeightRy;
        double macroWidth = macroBounds.WidthRx;
        double innerHeight = frame.MaxRy - frame.MinRy - 2 * marginRy;
        double innerWidth = frame.MaxRx - frame.MinRx - 2 * marginRx;

        bool tooLarge = macroHeight > innerHeight || macroWidth > innerWidth;

        // Wyrównaj lewą-górą do ramki; jeśli nie mieści się — przesuń w górę / w lewo
        if (macroHeight <= innerHeight && targetRy + macroHeight > frame.MaxRy - marginRy)
            targetRy = frame.MaxRy - marginRy - macroHeight;

        if (macroWidth <= innerWidth && targetRx + macroWidth > frame.MaxRx - marginRx)
            targetRx = frame.MaxRx - marginRx - macroWidth;

        if (targetRy < frame.MinRy + marginRy)
            targetRy = frame.MinRy + marginRy;
        if (targetRx < frame.MinRx + marginRx)
            targetRx = frame.MinRx + marginRx;

        return new InsertTarget
        {
            Ry = targetRy,
            Rx = targetRx,
            FitsKnownContent = true,
            MacroTooLarge = tooLarge
        };
    }

    public static FitReport Evaluate(FrameRect frame, Bounds2D content)
    {
        FitReport report = new FitReport
        {
            Frame = frame,
            Content = content,
            FitsInFrame = true,
            MacroTooLarge = false
        };

        if (!content.IsValid)
            return report;

        double innerHeight = frame.MaxRy - frame.MinRy;
        double innerWidth = frame.MaxRx - frame.MinRx;
        report.MacroTooLarge = content.HeightRy > innerHeight || content.WidthRx > innerWidth;

        report.OverflowTop = content.MinRy < frame.MinRy;
        report.OverflowLeft = content.MinRx < frame.MinRx;
        report.OverflowRight = content.MaxRx > frame.MaxRx;
        report.OverflowBottom = content.MaxRy > frame.MaxRy;
        report.FitsInFrame = !report.OverflowTop && !report.OverflowLeft
            && !report.OverflowRight && !report.OverflowBottom;
        return report;
    }
}
