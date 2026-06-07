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

        double macroX = SchemaGenPaths.MacroInsertX;
        double macroY = SchemaGenPaths.MacroInsertY;
        string macroXStr = "";
        string macroYStr = "";
        ctx.GetParameter("MACROX", ref macroXStr);
        ctx.GetParameter("MACROY", ref macroYStr);
        if (!string.IsNullOrEmpty(macroXStr))
            double.TryParse(macroXStr, NumberStyles.Float, CultureInfo.InvariantCulture, out macroX);
        if (!string.IsNullOrEmpty(macroYStr))
            double.TryParse(macroYStr, NumberStyles.Float, CultureInfo.InvariantCulture, out macroY);

        Insert oInsert = new Insert();
        oInsert.WindowMacro(
            macroPath,
            0,
            oPage,
            new PointD(macroX, macroY),
            Insert.MoveKind.Relative);

        new CommandLineInterpreter().Execute("edit /Name:" + pageName);

        string driveType = "";
        ctx.GetParameter("DRIVETYPE", ref driveType);

        int funcCount = oPage.Functions.Length;
        string message = "Wstawiono makro:\n" + macroPath
            + "\nStrona: " + pageName
            + "\nFunkcji na stronie: " + funcCount;
        if (!string.IsNullOrEmpty(driveType))
            message += "\nTyp napędu (XML): " + driveType;

        SchemaGenUi.ShowSuccess("SchemaGen — makro", message);
        return true;
    }
}
