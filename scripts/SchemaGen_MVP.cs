//#################################################################################################################################################
// SchemaGen — SchemaGen_MVP
//#################################################################################################################################################
// Sesja 1.3: Otwiera Hello_world.elk → tworzy stronę → wstawia makro 400VAC_Power_Supply.ema
// Orkiestracja przez CLI; logika DataModel/HEServices w add-in DLL.
// Kod źródłowy: repo scripts/ → kopia do C:\Users\Public\EPLAN\Data\Skrypty\Schemagen\
//#################################################################################################################################################
//[C#]
public class SchemaGen_MVP
{
    private const string AddInFileName = "SchemaGen.EplAddIn..dll";
    private const string AddInFolder =
        @"C:\Users\Public\EPLAN\Data\Skrypty\Schemagen\";

    [Start]
    public void Run()
    {
        string projectPath = PathMap.SubstitutePath(@"$(MD_PROJECTS)\Hello_world.elk");

        // EPLAN wymaga jednego otwartego projektu — zamknij inne przed uruchomieniem
        bool opened = OpenProject(projectPath);
        if (opened)
            System.Threading.Thread.Sleep(3000);

        if (!EnsureAddInLoaded())
        {
            ShowError("Nie wczytano add-in SchemaGen.");
            return;
        }

        string pageName = "";
        if (!CreateSchematicPage(projectPath, ref pageName))
        {
            ShowError("Akcja SchemaGenCreatePage nie powiodła się.");
            return;
        }

        if (!InsertPowerMacro(projectPath, pageName))
            ShowError("Akcja SchemaGenInsertPowerMacro nie powiodła się.");
    }

    private static bool OpenProject(string projectPath)
    {
        CommandLineInterpreter cli = new CommandLineInterpreter();
        if (cli.Execute("ProjectOpen /Project:\"" + projectPath + "\""))
            return true;
        if (cli.Execute("XPrjActionProjectOpen /PROJECT:\"" + projectPath + "\""))
            return true;
        return cli.Execute("edit /PROJECTNAME:\"" + projectPath + "\"");
    }

    private static bool EnsureAddInLoaded()
    {
        ActionManager am = new ActionManager();
        if (am.FindAction("SchemaGenCreatePage") != null
            && am.FindAction("SchemaGenInsertPowerMacro") != null)
            return true;

        string addInPath = AddInFolder + AddInFileName;
        return new CommandLineInterpreter().Execute(
            "EplApiModuleAction /Filename:\"" + addInPath + "\"");
    }

    private static bool CreateSchematicPage(string projectPath, ref string pageName)
    {
        ActionCallingContext ctx = new ActionCallingContext();
        ctx.AddParameter("PROJECTPATH", projectPath);
        if (!new CommandLineInterpreter().Execute("SchemaGenCreatePage", ctx))
            return false;

        ctx.GetParameter("PAGENAME", ref pageName);
        return !string.IsNullOrEmpty(pageName);
    }

    private static bool InsertPowerMacro(string projectPath, string pageName)
    {
        ActionCallingContext ctx = new ActionCallingContext();
        ctx.AddParameter("PROJECTPATH", projectPath);
        ctx.AddParameter("PAGENAME", pageName);
        return new CommandLineInterpreter().Execute("SchemaGenInsertPowerMacro", ctx);
    }

    private static void ShowError(string message)
    {
        new Decider().Decide(
            EnumDecisionType.eOkDecision,
            message,
            "SchemaGen MVP",
            EnumDecisionReturn.eOK,
            EnumDecisionReturn.eOK);
        new CommandLineInterpreter().Execute("SystemErrDialog");
    }
}
