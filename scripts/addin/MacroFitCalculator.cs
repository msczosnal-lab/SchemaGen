using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Xml;
using Eplan.EplApi.Base;
using Eplan.EplApi.DataModel;
using Eplan.EplApi.HEServices;

/// <summary>
/// Pozycjonuje makra tak, by ich wizualny lewy-górny róg lądował dokładnie
/// na zadanym (targetRy, targetRx), niezależnie od wewnętrznego origin .ema.
/// </summary>
public static class MacroFitCalculator
{
    private const int CacheSchemaVersion = 4; // v4: pełny bbox makra (min+max) dla FrameLayout

    private static Dictionary<string, PointD> _offsetCache;
    private static Dictionary<string, Bounds2D> _boundsCache;

    public static readonly string CachePath =
        @"C:\Users\Public\EPLAN\Data\Makra\Schemagen\config\macro-offsets.xml";

    /// <summary>
    /// Pełny bbox makra z cache lub probe insert na (0,0). Wymagane przed FrameLayout.
    /// </summary>
    public static Bounds2D EnsureMacroBounds(Insert oInsert, string macroPath, Page oPage)
    {
        EnsureLoaded();

        Bounds2D bounds;
        if (_boundsCache.TryGetValue(macroPath, out bounds))
            return bounds;

        StorableObject[] probe = oInsert.WindowMacro(
            macroPath, 0, oPage, new PointD(0.0, 0.0), Insert.MoveKind.Relative);

        bounds = PlacementBounds.MeasureObjects(probe);
        PointD minCorner = PlacementBounds.MeasureMinCorner(probe);

        if (bounds.IsValid)
        {
            _boundsCache[macroPath] = bounds;
            if (minCorner.X < double.MaxValue / 2.0)
                _offsetCache[macroPath] = minCorner;
            SaveCache();
        }

        DeleteObjects(probe);
        return bounds;
    }

    public static StorableObject[] InsertAtTarget(
        Insert oInsert,
        string macroPath,
        Page oPage,
        double targetRy,
        double targetRx)
    {
        EnsureLoaded();

        PointD offset;
        if (!_offsetCache.TryGetValue(macroPath, out offset))
        {
            EnsureMacroBounds(oInsert, macroPath, oPage);
            _offsetCache.TryGetValue(macroPath, out offset);
        }

        if (offset.X >= double.MaxValue / 2.0)
        {
            return oInsert.WindowMacro(
                macroPath, 0, oPage, new PointD(targetRy, targetRx), Insert.MoveKind.Relative);
        }

        PointD insertPoint = new PointD(targetRy - offset.X, targetRx - offset.Y);
        return oInsert.WindowMacro(
            macroPath, 0, oPage, insertPoint, Insert.MoveKind.Relative);
    }

    private static void DeleteObjects(StorableObject[] objects)
    {
        if (objects == null || objects.Length == 0)
            return;

        using (UndoStep undo = new UndoManager().CreateUndoStep())
        {
            foreach (StorableObject obj in objects)
            {
                Placement placement = obj as Placement;
                if (placement == null)
                    continue;

                try
                {
                    placement.Remove();
                }
                catch { /* obiekt już usunięty lub tylko do odczytu */ }
            }
        }
    }

    private static void EnsureLoaded()
    {
        if (_offsetCache != null)
            return;

        _offsetCache = new Dictionary<string, PointD>(StringComparer.OrdinalIgnoreCase);
        _boundsCache = new Dictionary<string, Bounds2D>(StringComparer.OrdinalIgnoreCase);
        try { LoadCache(); } catch { /* brak pliku przy pierwszym uruchomieniu */ }
    }

    private static void LoadCache()
    {
        if (!File.Exists(CachePath))
            return;

        XmlDocument doc = new XmlDocument();
        doc.Load(CachePath);

        XmlElement root = doc.DocumentElement;
        if (root == null)
            return;

        XmlAttribute versionAttr = root.Attributes["schemaVersion"];
        int version;
        if (versionAttr == null
            || !int.TryParse(versionAttr.Value, NumberStyles.Integer, CultureInfo.InvariantCulture, out version)
            || version != CacheSchemaVersion)
        {
            return;
        }

        foreach (XmlNode node in doc.SelectNodes("//Macro"))
        {
            XmlAttribute pathAttr = node.Attributes["path"];
            string path = pathAttr != null ? pathAttr.Value : null;
            if (string.IsNullOrEmpty(path))
                continue;

            double minRy, minRx, maxRy, maxRx;
            if (!TryParseAttr(node, "minRy", out minRy)
                || !TryParseAttr(node, "minRx", out minRx)
                || !TryParseAttr(node, "maxRy", out maxRy)
                || !TryParseAttr(node, "maxRx", out maxRx))
                continue;

            _boundsCache[path] = new Bounds2D
            {
                MinRy = minRy,
                MinRx = minRx,
                MaxRy = maxRy,
                MaxRx = maxRx
            };
            _offsetCache[path] = new PointD(minRy, minRx);
        }
    }

    private static bool TryParseAttr(XmlNode node, string name, out double value)
    {
        value = 0;
        XmlAttribute attr = node.Attributes[name];
        if (attr == null)
            return false;
        return double.TryParse(attr.Value, NumberStyles.Float, CultureInfo.InvariantCulture, out value);
    }

    private static void SaveCache()
    {
        string dir = Path.GetDirectoryName(CachePath);
        if (!string.IsNullOrEmpty(dir))
            Directory.CreateDirectory(dir);

        XmlDocument doc = new XmlDocument();
        XmlElement root = doc.CreateElement("MacroOffsets");
        root.SetAttribute("schemaVersion",
            CacheSchemaVersion.ToString(CultureInfo.InvariantCulture));
        doc.AppendChild(root);

        foreach (KeyValuePair<string, Bounds2D> kv in _boundsCache)
        {
            Bounds2D b = kv.Value;
            if (!b.IsValid)
                continue;

            XmlElement el = doc.CreateElement("Macro");
            el.SetAttribute("path", kv.Key);
            el.SetAttribute("minRy", b.MinRy.ToString("G6", CultureInfo.InvariantCulture));
            el.SetAttribute("minRx", b.MinRx.ToString("G6", CultureInfo.InvariantCulture));
            el.SetAttribute("maxRy", b.MaxRy.ToString("G6", CultureInfo.InvariantCulture));
            el.SetAttribute("maxRx", b.MaxRx.ToString("G6", CultureInfo.InvariantCulture));
            root.AppendChild(el);
        }

        doc.Save(CachePath);
    }
}
