using Eplan.EplApi.DataModel;

public static class PageFinder
{
    public static Page FindByName(Project project, string pageName)
    {
        if (project == null || string.IsNullOrEmpty(pageName))
            return null;

        foreach (Page page in project.Pages)
        {
            if (page.Name == pageName)
                return page;
        }

        return null;
    }
}
