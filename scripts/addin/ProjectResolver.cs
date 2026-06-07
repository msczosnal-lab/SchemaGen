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
            try { oProject = pm.GetProject(projectPath); }
            catch { oProject = null; }
        }

        if (oProject == null)
            oProject = new SelectionSet().GetCurrentProject(false);

        return oProject;
    }
}
