using System.IO;
using Eplan.EplApi.ApplicationFramework;
using Eplan.EplApi.Base;
using Eplan.EplApi.DataModel;
using Eplan.EplApi.HEServices;

public static class ProjectResolver
{
    public static Project Resolve(ActionCallingContext ctx)
    {
        string projectPath = "";
        ctx.GetParameter("PROJECTPATH", ref projectPath);
        if (!string.IsNullOrEmpty(projectPath))
            projectPath = PathMap.SubstitutePath(projectPath);

        ProjectManager pm = new ProjectManager();
        Project oProject = null;

        if (!string.IsNullOrEmpty(projectPath))
        {
            oProject = TryGetProject(pm, projectPath);
            if (oProject == null)
            {
                try
                {
                    oProject = pm.OpenProject(projectPath);
                }
                catch
                {
                    oProject = null;
                }
            }

            if (oProject != null && !PathsMatch(oProject.ProjectLinkFilePath, projectPath))
                return null;
        }

        if (oProject == null)
            oProject = new SelectionSet().GetCurrentProject(false);

        return oProject;
    }

    public static bool EnsureProject(string projectPath, out string error)
    {
        error = null;
        projectPath = PathMap.SubstitutePath(projectPath);

        ProjectManager pm = new ProjectManager();
        Project oProject = TryGetProject(pm, projectPath);

        if (oProject == null)
        {
            try
            {
                oProject = pm.OpenProject(projectPath);
            }
            catch (System.Exception ex)
            {
                error = "Nie można otworzyć projektu:\n" + projectPath
                    + "\n\n" + ex.Message;
                return false;
            }
        }

        if (oProject == null)
        {
            error = "Projekt nie jest dostępny:\n" + projectPath
                + "\n\nZamknij inne projekty i uruchom skrypt ponownie.";
            return false;
        }

        if (!PathsMatch(oProject.ProjectLinkFilePath, projectPath))
        {
            error = "Aktywny jest inny projekt:\n" + oProject.ProjectLinkFilePath
                + "\n\nOczekiwano:\n" + projectPath
                + "\n\nZamknij inne projekty przed uruchomieniem SchemaGen.";
            return false;
        }

        return true;
    }

    private static Project TryGetProject(ProjectManager pm, string projectPath)
    {
        try
        {
            return pm.GetProject(projectPath);
        }
        catch
        {
            return null;
        }
    }

    private static bool PathsMatch(string actual, string expected)
    {
        if (string.IsNullOrEmpty(actual) || string.IsNullOrEmpty(expected))
            return false;
        return string.Equals(
            Path.GetFullPath(actual),
            Path.GetFullPath(expected),
            System.StringComparison.OrdinalIgnoreCase);
    }
}
