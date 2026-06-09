using System.Globalization;
using System.IO;
using System.Text;
using Eplan.EplApi.ApplicationFramework;
using Eplan.EplApi.DataModel;

// Zwraca bbox zawartości strony vs granice ramki — fundament MCP eplan_get_layout.
public class SchemaGenAuditLayoutAction : IEplAction
{
    public bool OnRegister(ref string Name, ref int Ordinal)
    {
        Name = "SchemaGenAuditLayout";
        Ordinal = 24;
        return true;
    }

    public void GetActionProperties(ref ActionProperties actionProperties) { }

    public bool Execute(ActionCallingContext ctx)
    {
        Project oProject = ProjectResolver.Resolve(ctx);
        if (oProject == null)
        {
            SchemaGenUi.ShowError("SchemaGen — błąd", "SchemaGen: brak otwartego projektu.");
            return false;
        }

        string pageName = "";
        ctx.GetParameter("PAGENAME", ref pageName);

        var results = new StringBuilder();
        results.Append("{\"pages\":[");

        bool first = true;
        foreach (Page page in oProject.Pages)
        {
            if (!IsSchemaGenPage(page))
                continue;
            if (!string.IsNullOrEmpty(pageName) && page.Name != pageName)
                continue;

            if (!first)
                results.Append(",");
            first = false;
            results.Append(SerializePage(page));
        }

        results.Append("]}");

        string outputPath = "";
        ctx.GetParameter("OUTPUTPATH", ref outputPath);
        string json = results.ToString();
        if (!string.IsNullOrEmpty(outputPath))
            File.WriteAllText(outputPath, json, Encoding.UTF8);

        string silent = "";
        ctx.GetParameter("SILENT", ref silent);
        if (silent == "1")
            return true;

        SchemaGenUi.ShowSuccess("SchemaGen — audyt layoutu", json);
        return true;
    }

    private static string SerializePage(Page page)
    {
        FrameLayoutCalculator.FrameRect frame = FrameLayoutCalculator.DefaultFrame();
        Bounds2D content = PlacementBounds.MeasurePageContent(page);
        FrameLayoutCalculator.FitReport fit = FrameLayoutCalculator.Evaluate(frame, content);
        FrameLayoutCalculator.InsertTarget target = FrameLayoutCalculator.ComputeInsertPoint(content, frame);

        return "{"
            + "\"pageName\":\"" + EscapeJson(page.Name) + "\","
            + "\"frame\":{"
            + "\"minRy\":" + F(frame.MinRy) + ",\"minRx\":" + F(frame.MinRx) + ","
            + "\"maxRy\":" + F(frame.MaxRy) + ",\"maxRx\":" + F(frame.MaxRx)
            + "},"
            + "\"content\":{"
            + ContentField("minRy", content.MinRy, content.IsValid) + ","
            + ContentField("minRx", content.MinRx, content.IsValid) + ","
            + ContentField("maxRy", content.MaxRy, content.IsValid) + ","
            + ContentField("maxRx", content.MaxRx, content.IsValid)
            + "},"
            + "\"fitsInFrame\":" + (fit.FitsInFrame ? "true" : "false") + ","
            + "\"overflow\":{"
            + "\"top\":" + Bool(fit.OverflowTop) + ","
            + "\"left\":" + Bool(fit.OverflowLeft) + ","
            + "\"right\":" + Bool(fit.OverflowRight) + ","
            + "\"bottom\":" + Bool(fit.OverflowBottom)
            + "},"
            + "\"suggestedInsert\":{"
            + "\"ry\":" + F(target.Ry) + ",\"rx\":" + F(target.Rx)
            + "}"
            + "}";
    }

    private static string ContentField(string name, double value, bool valid)
    {
        return "\"" + name + "\":" + (valid ? F(value) : "null");
    }

    private static string F(double value)
    {
        return value.ToString("G6", CultureInfo.InvariantCulture);
    }

    private static string Bool(bool value)
    {
        return value ? "true" : "false";
    }

    private static string EscapeJson(string value)
    {
        if (string.IsNullOrEmpty(value))
            return "";
        return value.Replace("\\", "\\\\").Replace("\"", "\\\"");
    }

    private static bool IsSchemaGenPage(Page page)
    {
        try
        {
            string plant = page.Properties[Properties.Page.DESIGNATION_PLANT].ToString();
            return plant != null && plant.IndexOf(SchemaGenPaths.Plant, System.StringComparison.OrdinalIgnoreCase) >= 0;
        }
        catch
        {
            return false;
        }
    }
}
