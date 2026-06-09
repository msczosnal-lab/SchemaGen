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
///
/// Makro musi trafić na stronę jako całość (WindowMacro) — nigdy nie przesuwaj
/// tylko części obiektów (Function bez linii = urwane połączenia graficzne).
///
/// Przepływ:
///   1. Brak offsetu w cache → probe insert na (0,0), pomiar bbox Placement,
///      usunięcie probe, zapis offsetu, final insert na target - offset.
///   2. Z cache → insert od razu na target - offset.
/// </summary>
public static class MacroFitCalculator
{
    private const int CacheSchemaVersion = 2;

    private static Dictionary<string, PointD> _cache;

    public static readonly string CachePath =
        @"C:\Users\Public\EPLAN\Data\Makra\Schemagen\config\macro-offsets.xml";

    public static StorableObject[] InsertAtTarget(
        Insert oInsert,
        string macroPath,
        Page oPage,
        double targetRy,
        double targetRx)
    {
        EnsureLoaded();

        PointD offset;
        if (!_cache.TryGetValue(macroPath, out offset))
        {
            StorableObject[] probe = oInsert.WindowMacro(
                macroPath, 0, oPage, new PointD(0.0, 0.0), Insert.MoveKind.Relative);

            offset = MeasureBoundingBoxMin(probe);
            if (offset.X < double.MaxValue / 2.0)
            {
                _cache[macroPath] = offset;
                SaveCache();
            }

            DeleteObjects(probe);
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

    private static PointD MeasureBoundingBoxMin(StorableObject[] objects)
    {
        double minX = double.MaxValue;
        double minY = double.MaxValue;

        foreach (StorableObject obj in objects)
        {
            Placement placement = obj as Placement;
            if (placement == null)
                continue;

            try
            {
                PointD loc = placement.Location;
                minX = Math.Min(minX, loc.X);
                minY = Math.Min(minY, loc.Y);
            }
            catch { /* pomijamy obiekty bez Location */ }
        }

        return new PointD(minX, minY);
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
        if (_cache != null) return;
        _cache = new Dictionary<string, PointD>(StringComparer.OrdinalIgnoreCase);
        try { LoadCache(); } catch { /* brak pliku przy pierwszym uruchomieniu */ }
    }

    private static void LoadCache()
    {
        if (!File.Exists(CachePath)) return;

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
            if (string.IsNullOrEmpty(path)) continue;

            XmlAttribute offsetXAttr = node.Attributes["offsetX"];
            XmlAttribute offsetYAttr = node.Attributes["offsetY"];
            if (offsetXAttr == null || offsetYAttr == null) continue;

            double x, y;
            if (double.TryParse(offsetXAttr.Value,
                    NumberStyles.Float, CultureInfo.InvariantCulture, out x)
                && double.TryParse(offsetYAttr.Value,
                    NumberStyles.Float, CultureInfo.InvariantCulture, out y))
            {
                _cache[path] = new PointD(x, y);
            }
        }
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

        foreach (KeyValuePair<string, PointD> kv in _cache)
        {
            XmlElement el = doc.CreateElement("Macro");
            el.SetAttribute("path", kv.Key);
            el.SetAttribute("offsetX",
                kv.Value.X.ToString("G6", CultureInfo.InvariantCulture));
            el.SetAttribute("offsetY",
                kv.Value.Y.ToString("G6", CultureInfo.InvariantCulture));
            root.AppendChild(el);
        }

        doc.Save(CachePath);
    }
}
