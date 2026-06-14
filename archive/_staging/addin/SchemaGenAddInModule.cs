// SchemaGen — add-in EPLAN (DataModel + HEServices)
// Kompilacja: scripts/build_addin.ps1
// Mapa plików: scripts/addin/README.md
using Eplan.EplApi.ApplicationFramework;

public class SchemaGenAddInModule : IEplAddIn
{
    public bool OnRegister(ref bool bLoadOnStart)
    {
        bLoadOnStart = true;
        return true;
    }

    public bool OnUnregister() { return true; }
    public bool OnInit() { return true; }
    public bool OnInitGui() { return true; }
    public bool OnExit() { return true; }
}
