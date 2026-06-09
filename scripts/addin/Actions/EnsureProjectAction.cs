using Eplan.EplApi.ApplicationFramework;

public class SchemaGenEnsureProjectAction : IEplAction
{
    public bool OnRegister(ref string Name, ref int Ordinal)
    {
        Name = "SchemaGenEnsureProject";
        Ordinal = 19;
        return true;
    }

    public void GetActionProperties(ref ActionProperties actionProperties) { }

    public bool Execute(ActionCallingContext ctx)
    {
        string projectPath = "";
        ctx.GetParameter("PROJECTPATH", ref projectPath);
        if (string.IsNullOrEmpty(projectPath))
        {
            SchemaGenUi.ShowError("SchemaGen — błąd", "Brak parametru PROJECTPATH.");
            return false;
        }

        string error;
        if (!ProjectResolver.EnsureProject(projectPath, out error))
        {
            SchemaGenUi.ShowError("SchemaGen — projekt", error);
            return false;
        }

        return true;
    }
}
