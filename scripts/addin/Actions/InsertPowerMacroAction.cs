using System.Globalization;
using System.IO;
using Eplan.EplApi.ApplicationFramework;
using Eplan.EplApi.Base;
using Eplan.EplApi.DataModel;
using Eplan.EplApi.HEServices;

public class SchemaGenInsertPowerMacroAction : IEplAction
{
    public bool OnRegister(ref string Name, ref int Ordinal)
    {
        Name = "SchemaGenInsertPowerMacro";
        Ordinal = 21;
        return true;
    }

    public void GetActionProperties(ref ActionProperties actionProperties) { }

    public bool Execute(ActionCallingContext ctx)
    {
        string pageName = "";
        ctx.GetParameter("PAGENAME", ref pageName);
        if (string.IsNullOrEmpty(pageName))
        {
            SchemaGenUi.ShowError("SchemaGen — błąd", "Brak parametru PAGENAME.");
            return false;
        }

        string macroPath = "";
        ctx.GetParameter("MACROPATH", ref macroPath);
        if (string.IsNullOrEmpty(macroPath))
            macroPath = SchemaGenPaths.PowerSupply400Vac;
        macroPath = PathMap.SubstitutePath(macroPath);

        if (!File.Exists(macroPath))
        {
            SchemaGenUi.ShowError("SchemaGen — błąd", "Nie znaleziono makra:\n" + macroPath);
            return false;
        }

        Project oProject = ProjectResolver.Resolve(ctx);
        if (oProject == null)
        {
            SchemaGenUi.ShowError("SchemaGen — błąd", "SchemaGen: brak otwartego projektu.");
            return false;
        }

        Page oPage = PageFinder.FindByName(oProject, pageName);
        if (oPage == null)
        {
            SchemaGenUi.ShowError("SchemaGen — błąd", "Nie znaleziono strony: " + pageName);
            return false;
        }

        // MACROX = RY (PointD.X), MACROY = RX (PointD.Y)
        double insertRy = SchemaGenPaths.MacroInsertRy;
        double insertRx = SchemaGenPaths.MacroInsertRx;
        string macroXStr = "";
        string macroYStr = "";
        ctx.GetParameter("MACROX", ref macroXStr);
        ctx.GetParameter("MACROY", ref macroYStr);
        if (!string.IsNullOrEmpty(macroXStr))
            double.TryParse(macroXStr, NumberStyles.Float, CultureInfo.InvariantCulture, out insertRy);
        if (!string.IsNullOrEmpty(macroYStr))
            double.TryParse(macroYStr, NumberStyles.Float, CultureInfo.InvariantCulture, out insertRx);

        Insert oInsert = new Insert();

        string useFrameLayout = "";
        ctx.GetParameter("USE_FRAME_LAYOUT", ref useFrameLayout);
        if (useFrameLayout == "1")
        {
            Bounds2D macroBounds = MacroFitCalculator.EnsureMacroBounds(oInsert, macroPath, oPage);
            FrameLayoutCalculator.FrameRect frame = FrameLayoutCalculator.DefaultFrame();
            FrameLayoutCalculator.InsertTarget target =
                FrameLayoutCalculator.ComputeInsertPoint(macroBounds, frame);
            insertRy = target.Ry;
            insertRx = target.Rx;
        }

        string driveType = "";
        ctx.GetParameter("DRIVETYPE", ref driveType);

        StorableObject[] inserted = MacroFitCalculator.InsertAtTarget(
            oInsert, macroPath, oPage, insertRy, insertRx);

        // Sesja 1.7c: korekta TYLKO w pionie (RY). offset z cache bywa ~0 (origin makra na 0,0),
        // przez co treść funkcyjna wychodzi górą ramki. Mierzymy realny dolny róg funkcji
        // i dosuwamy makro w pionie do FrameMinRy+margin. RX celowo nietknięty.
        if (useFrameLayout == "1")
        {
            Bounds2D content = PlacementBounds.MeasureContentObjects(inserted);
            if (content.IsValid)
            {
                double targetMinRy = SchemaGenPaths.FrameMinRy + SchemaGenPaths.FrameMarginRy;
                double deltaRy = targetMinRy - content.MinRy;
                if (System.Math.Abs(deltaRy) > 0.01)
                    ShiftPlacementsRy(inserted, deltaRy);
            }
        }

        // Tylko PlaceHolder z wyniku insert — bez RemapFunctionStructure (S063111)
        MacroAdaptation.AdaptInsertedObjects(inserted, driveType);

        new CommandLineInterpreter().Execute("edit /Name:" + pageName);

        string silent = "";
        ctx.GetParameter("SILENT", ref silent);
        if (silent == "1")
            return true;

        int funcCount = oPage.Functions.Length;
        string message = "Wstawiono makro:\n" + macroPath
            + "\nStrona: " + pageName
            + "\nPozycja: RY=" + insertRy.ToString("0.##", CultureInfo.InvariantCulture)
            + ", RX=" + insertRx.ToString("0.##", CultureInfo.InvariantCulture)
            + "\nFunkcji na stronie: " + funcCount;
        if (!string.IsNullOrEmpty(driveType))
            message += "\nTyp napędu (XML): " + driveType;

        SchemaGenUi.ShowSuccess("SchemaGen — makro", message);
        return true;
    }

    // Sesja 1.7c: translacja wstawionych obiektów makra wyłącznie w osi pionowej (RY = Location.Y).
    private static void ShiftPlacementsRy(StorableObject[] objects, double deltaRy)
    {
        if (objects == null)
            return;

        using (SafetyPoint sp = SafetyPoint.Create())
        {
            using (Transaction tx = new TransactionManager().CreateTransaction())
            {
                foreach (StorableObject obj in objects)
                {
                    Placement p = obj as Placement;
                    if (p == null)
                        continue;
                    try
                    {
                        PointD loc = p.Location;
                        p.Location = new PointD(loc.X, loc.Y + deltaRy);
                    }
                    catch
                    {
                        // obiekt bez modyfikowalnej pozycji — pomijamy
                    }
                }
                tx.Commit();
            }
            sp.Commit();
        }
    }
}
