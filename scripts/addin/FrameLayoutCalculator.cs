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
    }

    public struct FitReport
    {
        public FrameRect Frame;
        public Bounds2D Content;
        public bool FitsInFrame;
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

    public static InsertTarget ComputeInsertPoint(Bounds2D macroSize, FrameRect frame)
    {
        double targetRy = frame.MinRy + SchemaGenPaths.FrameMarginRy;
        double targetRx = frame.MinRx + SchemaGenPaths.FrameMarginRx;

        if (macroSize.IsValid)
        {
            double macroHeight = macroSize.HeightRy;
            double macroWidth = macroSize.WidthRx;
            double frameHeight = frame.MaxRy - frame.MinRy;
            double frameWidth = frame.MaxRx - frame.MinRx;

            if (macroHeight <= frameHeight - 2 * SchemaGenPaths.FrameMarginRy
                && macroWidth <= frameWidth - 2 * SchemaGenPaths.FrameMarginRx)
            {
                targetRy = frame.MinRy + SchemaGenPaths.FrameMarginRy;
                targetRx = frame.MinRx + SchemaGenPaths.FrameMarginRx;
            }
        }

        return new InsertTarget
        {
            Ry = targetRy,
            Rx = targetRx,
            FitsKnownContent = macroSize.IsValid
        };
    }

    public static FitReport Evaluate(FrameRect frame, Bounds2D content)
    {
        FitReport report = new FitReport
        {
            Frame = frame,
            Content = content,
            FitsInFrame = true
        };

        if (!content.IsValid)
            return report;

        report.OverflowTop = content.MinRy < frame.MinRy;
        report.OverflowLeft = content.MinRx < frame.MinRx;
        report.OverflowRight = content.MaxRx > frame.MaxRx;
        report.OverflowBottom = content.MaxRy > frame.MaxRy;
        report.FitsInFrame = !report.OverflowTop && !report.OverflowLeft
            && !report.OverflowRight && !report.OverflowBottom;
        return report;
    }
}
