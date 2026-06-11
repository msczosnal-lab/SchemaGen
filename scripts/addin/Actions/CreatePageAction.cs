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

        string pageDescription = "";
        ctx.GetParameter("PAGEDESCRIPTION", ref pageDescription);

        PagePropertyList oPageProps = new PagePropertyList();
        oPageProps[Properties.Page.DESIGNATION_PLANT] = SchemaGenPaths.Plant;
        oPageProps[Properties.Page.DESIGNATION_LOCATION] = SchemaGenPaths.Location;

        Page oNewPage = new Page();
        oNewPage.Create(oProject, DocumentTypeManager.DocumentType.Circuit, oPageProps);

        // Format strony A4 landscape (sesja 1.7) — po Create, nie w PagePropertyList
        // [RYZYKO] DRAWING_DISPLAYEDWIDTH/HEIGHT — zweryfikuj po rebuild w EPLAN 2025
        try
        {
            oNewPage.Properties[Properties.Page.DRAWING_DISPLAYEDWIDTH]  = SchemaGenPaths.PageWidthMm;
            oNewPage.Properties[Properties.Page.DRAWING_DISPLAYEDHEIGHT] = SchemaGenPaths.PageHeightMm;
        }
        catch
        {
            // starsze API może nie mieć tej własności — ignoruj, strona zostaje z domyślnym formatem
        }

        // Opis strony (PAGE_NOMINATIOMN #11011) — widoczny w nawigatorze stron; ustawiany po Create
        // UWAGA: 11013 to PAGE_SUBCOUNTER, nie opis!
        if (!string.IsNullOrEmpty(pageDescription))
            oNewPage.Properties[Properties.Page.PAGE_NOMINATIOMN] = pageDescription;

        new CommandLineInterpreter().Execute("edit /Name:" + oNewPage.Name);
        ctx.AddParameter("PAGENAME", oNewPage.Name);

        string silent = "";
        ctx.GetParameter("SILENT", ref silent);
        if (silent != "1")
        {
            int pageCount = oProject.Pages.Length;
            SchemaGenUi.ShowSuccess(
                "SchemaGen — strona",
                "Projekt: " + oProject.ProjectLinkFilePath
                    + "\nUtworzono stronę: " + oNewPage.Name
                    + "\nStron w projekcie: " + pageCount);
        }
        return true;
    }
}
