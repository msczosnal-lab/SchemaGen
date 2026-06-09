using System;
using Eplan.EplApi.Base;
using Eplan.EplApi.DataModel;

/// <summary>
/// Pomiar bbox Placement na stronie — wspólna logika dla MacroFitCalculator,
/// FrameLayoutCalculator i SchemaGenAuditLayout.
/// Oś: minRy/maxRy = pion (PointD.X / Location.Y), minRx/maxRx = poziom (PointD.Y / Location.X).
/// </summary>
public struct Bounds2D
{
    public double MinRy;
    public double MinRx;
    public double MaxRy;
    public double MaxRx;

    public bool IsValid
    {
        get { return MinRy < double.MaxValue / 2.0; }
    }

    public double WidthRx
    {
        get { return MaxRx - MinRx; }
    }

    public double HeightRy
    {
        get { return MaxRy - MinRy; }
    }
}

public static class PlacementBounds
{
    public static Bounds2D MeasurePageContent(Page page)
    {
        Bounds2D bounds = Empty();
        foreach (Placement placement in page.AllFirstLevelPlacements)
            IncludePlacement(ref bounds, placement);
        return bounds;
    }

    public static Bounds2D MeasureObjects(StorableObject[] objects)
    {
        Bounds2D bounds = Empty();
        if (objects == null)
            return bounds;

        foreach (StorableObject obj in objects)
        {
            Placement placement = obj as Placement;
            if (placement != null)
                IncludePlacement(ref bounds, placement);
        }
        return bounds;
    }

    public static Bounds2D Empty()
    {
        return new Bounds2D
        {
            MinRy = double.MaxValue,
            MinRx = double.MaxValue,
            MaxRy = double.MinValue,
            MaxRx = double.MinValue
        };
    }

    public static void IncludePlacement(ref Bounds2D bounds, Placement placement)
    {
        if (placement == null)
            return;

        try
        {
            PointD loc = placement.Location;
            double ry = loc.Y;
            double rx = loc.X;
            bounds.MinRy = Math.Min(bounds.MinRy, ry);
            bounds.MinRx = Math.Min(bounds.MinRx, rx);
            bounds.MaxRy = Math.Max(bounds.MaxRy, ry);
            bounds.MaxRx = Math.Max(bounds.MaxRx, rx);
        }
        catch
        {
            // obiekt bez Location — pomijamy
        }
    }

    public static PointD MeasureMinCorner(StorableObject[] objects)
    {
        Bounds2D b = MeasureObjects(objects);
        if (!b.IsValid)
            return new PointD(double.MaxValue, double.MaxValue);
        return new PointD(b.MinRy, b.MinRx);
    }
}
