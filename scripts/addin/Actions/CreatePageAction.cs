using Eplan.EplApi.ApplicationFramework;
using Eplan.EplApi.Base;
using Eplan.EplApi.DataModel;

public class SchemaGenCreatePageAction : IEplAction
{
    public bool OnRegister(ref string Name, ref int Ordinal)
    {
        Name = "SchemaGenCreatePage";
        Ordinal = 20;
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

        PagePropertyList oPageProps = new PagePropertyList();
        oPageProps[Properties.Page.DESIGNATION_PLANT] = SchemaGenPaths.Plant;
        oPageProps[Properties.Page.DESIGNATION_LOCATION] = SchemaGenPaths.Location;
        oPageProps[Properties.Page.DESCRIPTION] = SchemaGenPaths.PowerPageDescription;

        Page oNewPage = new Page();
        oNewPage.Create(oProject, DocumentTypeManager.DocumentType.Circuit, oPageProps);

        new CommandLineInterpreter().Execute("edit /Name:" + oNewPage.Name);
        ctx.AddParameter("PAGENAME", oNewPage.Name);

        int pageCount = oProject.Pages.Length;
        SchemaGenUi.ShowSuccess(
            "SchemaGen — strona",
            "Projekt: " + oProject.ProjectLinkFilePath
                + "\nUtworzono stronę: " + oNewPage.Name
                + "\nStron w projekcie: " + pageCount);
        return true;
    }
}
