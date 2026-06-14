using Eplan.EplApi.Base;

public static class SchemaGenUi
{
    public static void ShowError(string title, string message)
    {
        new Decider().Decide(
            EnumDecisionType.eOkDecision,
            message,
            title,
            EnumDecisionReturn.eOK,
            EnumDecisionReturn.eOK);
    }

    public static void ShowSuccess(string title, string message)
    {
        new Decider().Decide(
            EnumDecisionType.eOkDecision,
            message,
            title,
            EnumDecisionReturn.eOK,
            EnumDecisionReturn.eOK);
    }
}
