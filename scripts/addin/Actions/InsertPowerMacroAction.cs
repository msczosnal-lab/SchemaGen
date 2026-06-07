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

        Insert oInsert = new Insert();
        oInsert.WindowMacro(
            macroPath,
            0,
            oPage,
            new PointD(SchemaGenPaths.MacroInsertX, SchemaGenPaths.MacroInsertY),
            Insert.MoveKind.Relative);

        new CommandLineInterpreter().Execute("edit /Name:" + pageName);

        int funcCount = oPage.Functions.Length;
        SchemaGenUi.ShowSuccess(
            "SchemaGen — makro",
            "Wstawiono makro:\n" + macroPath
                + "\nStrona: " + pageName
                + "\nFunkcji na stronie: " + funcCount);
        return true;
    }
}
