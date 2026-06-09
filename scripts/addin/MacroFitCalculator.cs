using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Xml;
using Eplan.EplApi.Base;
using Eplan.EplApi.DataModel;

/// <summary>
/// Pozycjonuje makra tak, by ich wizualny lewy-górny róg lądował dokładnie
/// na zadanym (targetRy, targetRx), niezależnie od wewnętrznego origin .ema.
///
/// Przepływ:
///   1. Pierwsze wstawienie danego makra → insert na (0,0), pomiar BoundingBox
///      wstawionych obiektów, przesunięcie do celu, zapis offsetu do cache XML.
///   2. Kolejne wstawienia → odczyt cache, wyliczenie insertPoint = target - offset,
///      insert od razu na właściwej pozycji.
/// </summary>
public static class MacroFitCalculator
{
    // Cache trzymany w pamięci przez całą sesję EPLAN
    private static Dictionary<string, PointD> _cache;

    // Plik trwały — współdzielony z resztą config projektu
    public static readonly string CachePath =
        @"C:\Users\Public\EPLAN\Data\Makra\Schemagen\config\macro-offsets.xml";

    // ------------------------------------------------------------------ //
    // Główne API                                                           //
    // ------------------------------------------------------------------ //

    /// <summary>
    /// Wstawia makro na stronę i gwarantuje, że wizualny lewy-górny róg
    /// wyląduje na (targetRy, targetRx).
    ///
    /// Jeśli offset dla tego makra jest już w cache — insert bezpośrednio
    /// na właściwej pozycji (brak potrzeby przesuwania po fakcie).
    /// Jeśli nie — insert na (0,0), pomiar, przesunięcie, zapis do cache.
    /// </summary>
    public static StorableObject[] InsertAtTarget(
        Insert oInsert,
        string macroPath,
        Page oPage,
        double targetRy,
        double targetRx)
    {
        EnsureLoaded();

        PointD offset;
        bool hasCached = _cache.TryGetValue(macroPath, out offset);

        if (hasCached)
        {
            // Znamy offset: insert od razu w docelowym miejscu
            PointD insertPoint = new PointD(targetRy - offset.X, targetRx - offset.Y);
            return oInsert.WindowMacro(
                macroPath, 0, oPage, insertPoint, Insert.MoveKind.Relative);
        }
        else
        {
            // Nieznany offset: insert na (0,0), pomiar, przesunięcie do celu
            StorableObject[] inserted = oInsert.WindowMacro(
                macroPath, 0, oPage, new PointD(0.0, 0.0), Insert.MoveKind.Relative);

            PointD measuredMin = MeasureBoundingBoxMin(inserted);

            if (measuredMin.X < double.MaxValue / 2.0)
            {
                // Zapisz offset do cache
                _cache[macroPath] = measuredMin;
                SaveCache();

                // Przesuń wstawione obiekty do celu
                double dx = targetRy - measuredMin.X;
                double dy = targetRx - measuredMin.Y;
                MoveObjects(inserted, dx, dy);
            }

            return inserted;
        }
    }

    // ------------------------------------------------------------------ //
    // Helpers                                                              //
    // ------------------------------------------------------------------ //

    private static PointD MeasureBoundingBoxMin(StorableObject[] objects)
    {
        double minX = double.MaxValue;
        double minY = double.MaxValue;

        foreach (StorableObject obj in objects)
        {
            Function f = obj as Function;
            if (f != null)
            {
                try
                {
                    minX = Math.Min(minX, f.Location.X);
                    minY = Math.Min(minY, f.Location.Y);
                }
                catch { /* pomijamy obiekty bez Location */ }
            }
        }

        return new PointD(minX, minY);
    }

    private static void MoveObjects(StorableObject[] objects, double dx, double dy)
    {
        if (Math.Abs(dx) < 1e-9 && Math.Abs(dy) < 1e-9) return;

        using (UndoStep undo = new UndoManager().CreateUndoStep())
        {
            foreach (StorableObject obj in objects)
            {
                Function f = obj as Function;
                if (f == null) continue;
                try
                {
                    f.Location = new PointD(f.Location.X + dx, f.Location.Y + dy);
                }
                catch { /* obiekty tylko do odczytu pomijamy */ }
            }
        }
    }

    // ------------------------------------------------------------------ //
    // Trwały cache XML                                                     //
    // ------------------------------------------------------------------ //

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

        foreach (XmlNode node in doc.SelectNodes("//Macro"))
        {
            string path = node.Attributes["path"]?.Value;
            if (string.IsNullOrEmpty(path)) continue;

            double x, y;
            if (double.TryParse(node.Attributes["offsetX"]?.Value,
                    NumberStyles.Float, CultureInfo.InvariantCulture, out x)
                && double.TryParse(node.Attributes["offsetY"]?.Value,
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
