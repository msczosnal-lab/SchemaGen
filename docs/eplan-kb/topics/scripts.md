# EPLAN API — scripts

*MVP — struktura skryptu .cs, [Start], parametry*

Dokumentów: 6

## Adding ribbon items by a script
*Źródło: `Adding ribbon items by a script.html`*
*Ścieżka: EPLAN API / User Guide / API Framework / Scripts / Adding ribbon items by a script*

Adding ribbon items by a script A script can add one or more items to the EPLAN ribbon. The convenient place to add these items is a function with [DeclareRegister] attribute, then the items are registered until the script is unloaded: 
- C# public
class
RegisterRibbonItems
{
string
m_newTabName =
"New API tab"
;
string
m_commandGroupName =
"New API command group"
;
string
m_commandName =
"New API command"
;

[DeclareRegister]
public
void
registerRibbonItems()
{ 
cleanItems();
var
newTab =
new
Eplan.EplApi.Gui.RibbonBar().AddTab(m_newTabName);
var
commandGroup = newTab.AddCommandGroup(m_commandGroupName);
var
command = commandGroup.AddCommand(m_commandName,
"XPartsManagementStart"
);
}

[DeclareUnregister]
public
void
unRegisterRibbonItems()
{ 
cleanItems();
}
void
cleanItems()
{
var
newTab =
new
Eplan.EplApi.Gui.RibbonBar().Tabs.FirstOrDefault(item => item.Name == m_newTabName);
if
(newTab !=
null
) 
newTab.Remove();
} 
}

Removing a ribbon tab also removes its command groups and commands. Similarly, removing a command group also removes its commands. 
A ribbon command is always connected with an action, which is called when the command is clicked. This means that either the script registers an additional action, or the command is assigned to an already existing action. Remarks 
Please mind that users may start EPLAN in QUIET mode using W3u.exe /Quiet or the API could be initialized by an offline program . Because of this, it is not recommended to show .NET dialogs in the method marked by [DeclareRegister] . Please use Eplan.EplApi.Base.Decider class instead. If you encounter some problem during registering or initializing of a script, just create and throw a BaseException or use BaseException.FixMessage(...) to add the message to the system messages list. The following example shows a script, which registers an action and a ribbon command. 
- C# 
- VB public
class
ButtonWithAction
{
[DeclareAction(
"HelloWorldAction"
)]
public
void
MyFunctionAsAction()
{
new
Decider().Decide(EnumDecisionType.eOkDecision,
"Hello World!"
,
"HelloWorldAction title"
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
return
;
}

[DeclareRegister]
public
void
registerButtonWithAction()
{
var
ribbonBar=
new
Eplan.EplApi.Gui.RibbonBar();
ribbonBar.AddCommand(
"MyMenuText"
,
"HelloWorldAction"
, 2);
}

[DeclareUnregister]
public
void
unRegisterButtonWithAction()
{
var
ribbonBar=
new
Eplan.EplApi.Gui.RibbonBar();
ribbonBar.RemoveCommand(
"HelloWorldAction"
);
}

}
Public
Class
ButtonWithAction

<DeclareAction(
"HelloWorldAction"
)> _
Public
Sub
MyFunctionAsAction()
Dim
dec
As
Decider =
New
Decider
dec.Decide(EnumDecisionType.eOkDecision,
"Hello World!"
,
"HelloWorldAction title"
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)
Return
End Sub
'MyFunctionAsAction
<DeclareRegister()> _
Public
Sub
registerButtonWithAction()
Dim
ribbonBar
As
New
Eplan.EplApi.Gui.RibbonBar()
ribbonBar.AddCommand(
"MyMenuText"
,
"HelloWorldAction"
, 2)
End Sub
'registerButtonWithAction
<DeclareUnregister()> _
Public
Sub
unRegisterButtonWithAction()
Dim
ribbonBar
As
New
Eplan.EplApi.Gui.RibbonBar()
ribbonBar.RemoveCommand(
"HelloWorldAction"
)
End Sub
'unRegisterButtonWithAction
End Class
'ButtonWithAction

The [DeclareRegister] attribute calls the function buttonWithAction() when the script is loaded. The function creates a new ribbon command "MyMenuText" and binds the action "HelloWorldAction" to it. 

Possible problems with flickering and how to avoid them 
When loading or unloading a script in which many ribbon items (tabs, command groups and commands) are added, a temporary flickering of the page navigator and other parts of the GUI may occur. The following procedure reduces this flickering to a minimum: 
First, create a new RibbonBar object using the constructor that takes the boolean executeApplyAfterChanges parameter and set this parameter to "true". 
Then, add all of your custom tabs, command groups and commands to this RibbonBar object, as in the following example: 

- C# public
class
RegisterRibbonItems
{
// Create the RibbonBar object and set the "executeApplyAfterChanges" parameter in the constructor to "true"
Eplan.EplApi.Gui.RibbonBar myRibbonBar =
new
Eplan.EplApi.Gui.RibbonBar(
true
);
string
m_newTabName1 =
"New API tab 1"
;
string
m_newTabName2 =
"New API tab 2"
;
string
m_newTabName3 =
"New API tab 3"
;
string
m_commandGroupName1 =
"New API command group 1"
;
string
m_commandGroupName2 =
"New API command group 2"
;
string
m_commandGroupName3 =
"New API command group 3"
;
string
m_commandGroupName4 =
"New API command group 4"
;
string
m_commandName1 =
"New API command 1"
;
string
m_commandName2 =
"New API command 2"
;
string
m_commandName3 =
"New API command 3"
;
string
m_commandName4 =
"New API command 4"
;
string
m_commandName5 =
"New API command 5"
;
string
m_commandName6 =
"New API command 6"
;
string
m_commandName7 =
"New API command 7"
; 

[DeclareRegister]
public
void
registerRibbonItems()
{ 
cleanItems();
// Add all the tabs to the RibbonBar object defined above
var
newTab1 = myRibbonBar.AddTab(m_newTabName1);
var
newTab2 = myRibbonBar.AddTab(m_newTabName2);
var
newTab3 = myRibbonBar.AddTab(m_newTabName3);
// Add all the command groups and commands to these tabs
var
commandGroup1 = newTab1.AddCommandGroup(m_commandGroupName1);
var
commandGroup2 = newTab2.AddCommandGroup(m_commandGroupName2);
var
commandGroup3 = newTab3.AddCommandGroup(m_commandGroupName3);
var
commandGroup4 = newTab3.AddCommandGroup(m_commandGroupName4);
var
command1 = commandGroup1.AddCommand(m_commandName1,
"YourActionName1"
);
var
command2 = commandGroup1.AddCommand(m_commandName2,
"YourActionName2"
);
var
command3 = commandGroup2.AddCommand(m_commandName3,
"YourActionName3"
);
var
command4 = commandGroup3.AddCommand(m_commandName4,
"YourActionName4"
);
var
command5 = commandGroup4.AddCommand(m_commandName5,
"YourActionName5"
);
var
command6 = commandGroup4.AddCommand(m_commandName6,
"YourActionName6"
);
var
command7 = commandGroup4.AddCommand(m_commandName7,
"YourActionName7"
);
}

[DeclareUnregister]
public
void
unRegisterRibbonItems()
{ 
cleanItems();
}
void
cleanItems()
{
// Clean up ALL commands, command groups and tabs as shown in the topmost example
} 
}
See Also 
### Addins Adding ribbon commands 
### API Miscellaneous Ribbon bar 
### Reference RibbonBar Constructor

### Przykłady kodu (C#)
```csharp
public class RegisterRibbonItems
{   
    string m_newTabName         = "New API tab";
    string m_commandGroupName   = "New API command group";
    string m_commandName        = "New API command";
           
    [DeclareRegister]
    public void registerRibbonItems()
    {               
        cleanItems();
        var newTab = new Eplan.EplApi.Gui.RibbonBar().AddTab(m_newTabName);
        var commandGroup = newTab.AddCommandGroup(m_commandGroupName);                              
        var command = commandGroup.AddCommand(m_commandName, "XPartsManagementStart");
    }
       
    [DeclareUnregister]
    public void unRegisterRibbonItems()
    {   
        cleanItems();
    }
   
    void cleanItems()
    {
        var newTab = new Eplan.EplApi.Gui.RibbonBar().Tabs.FirstOrDefault(item => item.Name == m_newTabName);
        if(newTab != null)                      
            newTab.Remove();
    }   
}
```
```csharp
public class ButtonWithAction
{
    [DeclareAction("HelloWorldAction")]
    public void MyFunctionAsAction()
    {
       new Decider().Decide(EnumDecisionType.eOkDecision, "Hello World!", "HelloWorldAction title", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
       return;
    }

    [DeclareRegister]
    public void registerButtonWithAction()
    {
        var ribbonBar= new Eplan.EplApi.Gui.RibbonBar();
        ribbonBar.AddCommand("MyMenuText", "HelloWorldAction", 2);
    }

    [DeclareUnregister]
    public void unRegisterButtonWithAction()
    {
        var ribbonBar= new Eplan.EplApi.Gui.RibbonBar();
        ribbonBar.RemoveCommand("HelloWorldAction");
    }

}
```
```csharp
Public Class ButtonWithAction

   <DeclareAction("HelloWorldAction")>  _
   Public Sub MyFunctionAsAction()
      Dim dec As Decider = New Decider
      dec.Decide(EnumDecisionType.eOkDecision, "Hello World!", "HelloWorldAction title", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)
      Return
   End Sub 'MyFunctionAsAction

   <DeclareRegister()>  _
   Public Sub registerButtonWithAction()
      Dim ribbonBar As New Eplan.EplApi.Gui.RibbonBar()
      ribbonBar.AddCommand("MyMenuText", "HelloWorldAction", 2)
   End Sub 'registerButtonWithAction

   <DeclareUnregister()>  _
   Public Sub unRegisterButtonWithAction()
      Dim ribbonBar As New Eplan.EplApi.Gui.RibbonBar()
      ribbonBar.RemoveCommand("HelloWorldAction")
   End Sub 'unRegisterButtonWithAction


End Class 'ButtonWithAction
```
```csharp
public class RegisterRibbonItems
{   
    // Create the RibbonBar object and set the "executeApplyAfterChanges" parameter in the constructor to "true"
    Eplan.EplApi.Gui.RibbonBar myRibbonBar = new Eplan.EplApi.Gui.RibbonBar(true);
    string m_newTabName1        = "New API tab 1";
    string m_newTabName2        = "New API tab 2";
    string m_newTabName3        = "New API tab 3";
    string m_commandGroupName1  = "New API command group 1";
    string m_commandGroupName2  = "New API command group 2";
    string m_commandGroupName3  = "New API command group 3";
    string m_commandGroupName4  = "New API command group 4";
    string m_commandName1       = "New API command 1";
    string m_commandName2       = "New API command 2";
    string m_commandName3       = "New API command 3";
    string m_commandName4       = "New API command 4";
    string m_commandName5       = "New API command 5";
    string m_commandName6       = "New API command 6";
    string m_commandName7       = "New API command 7";      

    [DeclareRegister]
    public void registerRibbonItems()
    {              
        cleanItems();

        // Add all the tabs to the RibbonBar object defined above 
        var newTab1 = myRibbonBar.AddTab(m_newTabName1);
        var newTab2 = myRibbonBar.AddTab(m_newTabName2);
        var newTab3 = myRibbonBar.AddTab(m_newTabName3);

        // Add all the command groups and commands to these tabs
        var commandGroup1 = newTab1.AddCommandGroup(m_commandGroupName1);     
        var commandGroup2 = newTab2.AddCommandGroup(m_commandGroupName2);  
        var commandGroup3 = newTab3.AddCommandGroup(m_commandGroupName3);    
        var commandGroup4 = newTab3.AddCommandGroup(m_commandGroupName4);
        var command1 = commandGroup1.AddCommand(m_commandName1, "YourActionName1");                        
        var command2 = commandGroup1.AddCommand(m_commandName2, "YourActionName2");
        var command3 = commandGroup2.AddCommand(m_commandName3, "YourActionName3");                        
        var command4 = commandGroup3.AddCommand(m_commandName4, "YourActionName4");
        var command5 = commandGroup4.AddCommand(m_commandName5, "YourActionName5");                        
        var command6 = commandGroup4.AddCommand(m_commandName6, "YourActionName6");
        var command7 = commandGroup4.AddCommand(m_commandName7, "YourActionName7");
    }
        
    [DeclareUnregister]
    public void unRegisterRibbonItems()
    {   
        cleanItems();
    }
    
    void cleanItems()
    {
        // Clean up ALL commands, command groups and tabs as shown in the topmost example
    }  
}
```

---

## Development environment
*Źródło: `Development environment.html`*
*Ścieżka: EPLAN API / User Guide / Development environment*

Development environment The preferable way to develop EPLAN API applications is to reference the API assemblies directly in a .NET project using CLI programming languages like C# (C Sharp), Visual Basic.Net, C++/CLI.  You could do this by just using a text editor and calling the compiler from a DOS box – like described in the topics " Creating add-ins in CSharp " or " Creating add-ins in Visual Basic.Net ". 
The much more convenient way of developing involves the use of an Integrated Development Environment (IDE). We recommend the use of Microsoft Visual Studio, but there are also free development environments like SharpDevelop. How to start an API project in the Visual Studio is described in the topic " EPLAN .NET API ". 
The EPLAN API has explicitly been tested and released for Microsoft Windows 7, 8 and 10. 
It is not recommended to use EPLAN API in separate child threads. This could lead to problems because such configuration wasn't tested nor predicted by API designers. 
### Debugging applications 
Currently, when debugging applications, the w3u.exe process is detached at the beginning of the debug. This happens because w3u.exe from the "Electric P8" folder calls eplan.exe from the "Platform" folder. In order to continue debugging, please attach to the process eplan.exe from "Platform" folder. Another solution is to start debugging eplan.exe in the "Platform" folder, with the Variant argument, for example: 
/Variant:"Electric P8"

---

## Event handling in scripts
*Źródło: `Event handling in scripts.html`*
*Ścieżka: EPLAN API / User Guide / API Framework / Scripts / Event handling in scripts*

Event handling in scripts You can write a script to react on EPLAN events. To do this, you must declare at least one function of the script as an event handler using the [DeclareEventHandler()] attribute and load the script. 
It is even possible to handle event parameters. However, you need to know the event parameters in advance. 
The following two examples show scripts that respond to events when loaded. 
The script in the first example reacts to the onMainStart event. The function MyEventHandlerFunction in the class SimpleEventHandler is registered as event handler for the onMainStart event. When this event is raised in EPLAN, the function is called. 

The second example shows an event handler script that catches any onActionStart.String event. There is an event parameter for the name of the action. 

- C# 
- VB public
class
SimpleEventHandler
{
[DeclareEventHandler(
"onMainStart"
)]
public
void
MyEventHandlerFunction()
{
new
Decider().Decide(EnumDecisionType.eOkDecision,
"MyEventHandlerFunction was called!"
,
"SimpleEventHandler"
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
return
;
}
}
public
class
SimpleEventHandler
{
[DeclareEventHandler(
"onActionStart.String.*"
)]
public
long
MyEventHandlerFunction2(IEventParameter iEventParameter)
{
try
{
EventParameterString oEventParameterString=
new
EventParameterString(iEventParameter);
String strActionName= oEventParameterString.String;
new
Decider().Decide(EnumDecisionType.eOkDecision,
"Action "
+ strActionName +
" was started!"
,
"MyEventHandler"
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
}
catch
(System.InvalidCastException exc)
{
String strExc= exc.Message;
new
Decider().Decide(EnumDecisionType.eOkDecision,
"Parameter error: "
+ strExc,
"MyEventHandler"
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
}
return
0;
}
}
Public
Class
SimpleEventHandler

<DeclareEventHandler(
"onMainStart"
)> _
Public
Sub
MyEventHandlerFunction()
Dim
dec
As
Decider =
New
Decider
dec.Decide(EnumDecisionType.eOkDecision,
"MyEventHandlerFunction was called!"
,
"SimpleEventHandler"
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)
End Sub
'MyEventHandlerFunction
End Class
'SimpleEventHandler
Public
Class
SimpleEventHandler

<DeclareEventHandler(
"onActionStart.String.*"
)> _
Public
Function
MyEventHandlerFunction2(iEventParameter
As
IEventParameter)
As
Long
Dim
dec
As
Decider =
New
Decider
Try
Dim
oEventParameterString
As
New
EventParameterString(iEventParameter)
Dim
strActionName
As
[
String
] = oEventParameterString.String
dec.Decide(EnumDecisionType.eOkDecision,
"Action "
+ strActionName +
" was started!"
,
"MyEventHandler"
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)
Catch
exc
As
System.InvalidCastException
Dim
strExc
As
[
String
] = exc.Message
dec.Decide(EnumDecisionType.eOkDecision,
"Parameter error: "
+ strExc,
"MyEventHandler"
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)
End
Try
Return
0
End Function
'MyEventHandlerFunction2
End Class
'SimpleEventHandler

See Also 
### API Framework Events 
### Events Events

### Przykłady kodu (C#)
```csharp
public class SimpleEventHandler
{
    [DeclareEventHandler("onMainStart")]
     public void MyEventHandlerFunction()
     {
           new Decider().Decide(EnumDecisionType.eOkDecision, "MyEventHandlerFunction was called!","SimpleEventHandler", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
           return;
     }
} 

public class SimpleEventHandler
{
    [DeclareEventHandler("onActionStart.String.*")]
    public long MyEventHandlerFunction2(IEventParameter iEventParameter)
    {
        try
        {
            EventParameterString oEventParameterString= new EventParameterString(iEventParameter);
            String strActionName= oEventParameterString.String;
            new Decider().Decide(EnumDecisionType.eOkDecision, "Action " + strActionName + " was started!","MyEventHandler", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
        }
        catch (System.InvalidCastException exc)
        {
            String strExc= exc.Message;
            new Decider().Decide(EnumDecisionType.eOkDecision, "Parameter error: " + strExc, "MyEventHandler", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
        }
        return 0;
    }
}
```
```csharp
Public Class SimpleEventHandler

   <DeclareEventHandler("onMainStart")>  _
   Public Sub MyEventHandlerFunction()
      Dim dec As Decider = New Decider
      dec.Decide(EnumDecisionType.eOkDecision, "MyEventHandlerFunction was called!", "SimpleEventHandler", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)
   End Sub 'MyEventHandlerFunction
End Class 'SimpleEventHandler

 

Public Class SimpleEventHandler

   <DeclareEventHandler("onActionStart.String.*")>  _
   Public Function MyEventHandlerFunction2(iEventParameter As IEventParameter) As Long
   Dim dec As Decider = New Decider
      Try
         Dim oEventParameterString As New EventParameterString(iEventParameter)
         Dim strActionName As [String] = oEventParameterString.String
         dec.Decide(EnumDecisionType.eOkDecision, "Action " + strActionName + " was started!", "MyEventHandler", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)

      Catch exc As System.InvalidCastException
         Dim strExc As [String] = exc.Message
         dec.Decide(EnumDecisionType.eOkDecision, "Parameter error: " + strExc, "MyEventHandler", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)
      End Try

      Return 0
   End Function 'MyEventHandlerFunction2
End Class 'SimpleEventHandler
```

---

## Loading a script
*Źródło: `Loading a script.html`*
*Ścieżka: EPLAN API / User Guide / API Framework / Scripts / Loading a script*

Loading a script You can load and unload scripts in EPLAN. In this case, not the start function is executed, but special functions are registered in EPLAN. You can add a new action to EPLAN, add ribbon buttons to the Extension ribbon > API command group , and register functions to react on EPLAN events. The following example shows a script that registers a new action. Therefore, a function is marked by the attribute [DeclareAction] . The parameter of the attribute defines the name of the new action in EPLAN. 
- C# 
- VB public
class
SimpleScriptAction
{
[DeclareAction(
"MyScriptAction"
)]
public
void
MyFunctionAsAction()
{
new
Decider().Decide(EnumDecisionType.eOkDecision,
"MyFunctionAsAction was called!"
,
"RegisterScriptAction"
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
return
;
}
}
Public
Class
SimpleScriptAction

<DeclareAction(
"MyScriptAction"
)> _
Public
Sub
MyFunctionAsAction()
Dim
dec
As
Decider =
New
Decider
dec.Decide(EnumDecisionType.eOkDecision,
"MyFunctionAsAction was called!"
,
"RegisterScriptAction"
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)
End Sub
'MyFunctionAsAction
End Class
'SimpleScriptAction

When a script with the above code is loaded, the function "MyFunctionAsAction" is registered in EPLAN as action by the name "MyScriptAction". The new action can now be used like any other action in EPLAN. For example, it can be called from the command line or assigned to a button. 

Once the script has been loaded, it will be automatically loaded during the Startup of EPLAN and the action will be available again. 

To unload or unregister a script, you just call the ribbon File > Extras > Interfaces > Scripts > Unload and select the respective script in the dialog:

### Przykłady kodu (C#)
```csharp
public class SimpleScriptAction
{
     [DeclareAction("MyScriptAction")]
     public void MyFunctionAsAction()
     {
           new Decider().Decide(EnumDecisionType.eOkDecision, "MyFunctionAsAction was called!", "RegisterScriptAction", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
           return;
     }
}
```
```csharp
Public Class SimpleScriptAction

   <DeclareAction("MyScriptAction")>  _
   Public Sub MyFunctionAsAction()
      Dim dec As Decider = New Decider
      dec.Decide(EnumDecisionType.eOkDecision, "MyFunctionAsAction was called!", "RegisterScriptAction", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)
   End Sub 'MyFunctionAsAction
End Class 'SimpleScriptAction
```

---

## Simple script with parameters
*Źródło: `Simple script with parameters.html`*
*Ścieżka: EPLAN API / User Guide / API Framework / Scripts / Simple script with parameters*

Simple script with parameters The script functionality does also accept parameters. However, this only makes sense if a parameter can be passed to the script when it is started. This can be done by invoking EPLAN via the command line: 

W3u.exe ExecuteScript /ScriptFile:"C:\Program Files\EPLAN\EPLAN\Basic\Scripts\EPLAN\SimpleScriptWithParameters.cs" /Param1:"Hello" /Param2:"EPLAN" /Param3:"API developer!" 

When starting EPLAN via command line, in order to run a script, the first parameter is the name of the action to be executed. The action for executing scripts is called ExecuteScript . This action takes the /ScriptFile parameter which specifies the name of the script file to be run. Any further parameter ( <Param1> , <Param2> , <Param3> etc.) is optional and will be passed to the start function (i.e. the function marked with the [Start] attribute) of the script. You can name the further parameters as you wish. In the follwing example they are simply called "Param1", "Param2" and "Param3", but you can just as well give the parameters meaningful names like "Textmodule1", "projectName" or whatever makes sense in your use case. Example 
In the following example, the script (i.e. the script function) requires 3 string parameters "Param1", "Param2" and "Param3": 
- C# 
- VB public
class
SimpleScriptWithParameters
{
[Start]
public
bool
FunctionWithParameters(String Param1, String Param2, String Param3)
{
new
Decider().Decide(EnumDecisionType.eOkDecision, Param1 + Param2 + Param3 ,
"SimpleScriptWithParams"
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
return
true
;
}
}
Public
Class
SimpleScriptWithParameters

<Start> _
Public
Function
FunctionWithParameters(
ByVal
Param1
As
String
,
ByVal
Param2
As
String
, _
ByVal
Param3
As
String
)
as
Boolean
Dim
dec
As
Decider =
New
Decider
dec.Decide(EnumDecisionType.eOkDecision, Param1 + Param2 + Param3,
"SimpleScriptWithParams"
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)
Return
True
End Sub
'FunctionWithParameters
End Class
'SimpleScriptWithParameters

It is important, that the identifiers (in this example "Param1", "Param2", "Param3") are exactly matching in the command line and in the function! 
It is possible to use scripts with ActionCallingContext as a parameter. To do that, please look at the following example: 
- C# 
- VB public
class
ScriptWithActionCallingContext
{
[Start]
public
void
FunctionWithActionCallingContext(ActionCallingContext oActionCallingContext)
{
string
strFirstParam =
""
;
string
strSecondParam =
""
;
oActionCallingContext.GetParameter(
"strFirstParam"
,
ref
strFirstParam);
oActionCallingContext.GetParameter(
"strSecondParam"
,
ref
strSecondParam);
string
strNewParam =
""
;
oActionCallingContext.AddParameter(
"strNewParam"
, strFirstParam + strSecondParam);
oActionCallingContext.GetParameter(
"strNewParam"
,
ref
strNewParam);
if
(strNewParam.Equals(strFirstParam + strSecondParam))
{
// TODO: Add some functionality here
}
}
}
Public
Class
ScriptWithActionCallingContext

<Start> _
Public
Sub
FunctionWithActionCallingContext (
ByVal
oActionCallingContext
As
ActionCallingContext)
Dim
strFirstParam
As
[
String
] =
""
Dim
strSecondParam
As
[
String
] =
""
oActionCallingContext.GetParameter(
"strFirstParam"
, strFirstParam)
oActionCallingContext.GetParameter(
"strSecondParam"
, strSecondParam)
Dim
strNewParam
As
[
String
] =
""
oActionCallingContext.AddParameter(
"strNewParam"
, strFirstParam + strSecondParam)
oActionCallingContext.GetParameter(
"strNewParam"
, strNewParam)
If
strNewParam = strFirstParam + strSecondParam
Then
' TODO: Add some functionality here
End
If
End Sub
'FunctionWithActionCallingContext
End Class
'ScriptWithActionCallingContext

Using this feature, you can extend the scope of the EPLAN command line by your own parameters. If you need to call some API functionality via command line, just create a script. The start function of this script may take parameters and can call other functions with these parameters. See Also 
### Actions ExecuteScript

### Przykłady kodu (C#)
```csharp
public class SimpleScriptWithParameters
 {
    [Start]
     public bool FunctionWithParameters(String Param1, String Param2, String Param3)
     {
        new Decider().Decide(EnumDecisionType.eOkDecision,  Param1 + Param2 + Param3 , "SimpleScriptWithParams", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
        return true;
    }
 }
```
```csharp
Public Class SimpleScriptWithParameters

   <Start>  _
   Public Function FunctionWithParameters(ByVal Param1 As String, ByVal Param2 As String, _
                                            ByVal Param3 As String) as Boolean
      Dim dec As Decider = New Decider
      dec.Decide(EnumDecisionType.eOkDecision, Param1 + Param2 + Param3, "SimpleScriptWithParams", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)
      Return True
   End Sub 'FunctionWithParameters
End Class 'SimpleScriptWithParameters
```
```csharp
public class ScriptWithActionCallingContext
{
    [Start]
    public void FunctionWithActionCallingContext(ActionCallingContext oActionCallingContext)
    {
        string strFirstParam = "";
        string strSecondParam = "";
        oActionCallingContext.GetParameter("strFirstParam", ref strFirstParam);
        oActionCallingContext.GetParameter("strSecondParam", ref strSecondParam);
        string strNewParam = "";
        oActionCallingContext.AddParameter("strNewParam", strFirstParam + strSecondParam);
        oActionCallingContext.GetParameter("strNewParam", ref strNewParam);
        if (strNewParam.Equals(strFirstParam + strSecondParam))
        {
            // TODO: Add some functionality here
        }
    }
}
```
```csharp
Public Class ScriptWithActionCallingContext

<Start>  _
    Public Sub FunctionWithActionCallingContext (ByVal oActionCallingContext As ActionCallingContext)
        Dim strFirstParam As [String] = ""
        Dim strSecondParam As [String] = ""
        oActionCallingContext.GetParameter("strFirstParam", strFirstParam)
        oActionCallingContext.GetParameter("strSecondParam", strSecondParam)
        Dim strNewParam As [String] = ""
        oActionCallingContext.AddParameter("strNewParam", strFirstParam + strSecondParam)
        oActionCallingContext.GetParameter("strNewParam", strNewParam)
        If strNewParam = strFirstParam + strSecondParam Then       
            ' TODO: Add some functionality here
        End If
    End Sub 'FunctionWithActionCallingContext
End Class 'ScriptWithActionCallingContext
```

---

## Structure of a simple script
*Źródło: `Structure of a simple script.html`*
*Ścieżka: EPLAN API / User Guide / API Framework / Scripts / Structure of a simple script*

Structure of a simple script A script consists of at least one public class with at least one public function. This one required function needs to be marked with the attribute [Start] . 

The following example shows a very simple script. 
- CS 
- VB public
class
VerySimpleScript
{
[Start]
public
void
MyFunction()
{
new
Decider().Decide(EnumDecisionType.eOkDecision,
"MyFunction was called!"
,
"VerySimpleScript"
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
return
;
}
}
Public
Class
VerySimpleScript
<Start> _
Public
Sub
MyFunction()
Dim
dec
As
Decider =
New
Decider
dec.Decide(EnumDecisionType.eOkDecision,
"MyFunction was called!"
,
"VerySimpleScript"
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)
Return
End Sub
'MyFunction
End Class
'VerySimpleScript

In this example the class "VerySimpleScript" with a function "MyFunction" was created. The function was marked with the attribute [Start] . 
When this script is run using the ribbon File > Extras > Interfaces > Scripts > Run , the function "MyFunction" is executed and a message box appears: 

A script may contain more than one function. There even can be several classes in a script. However, there may only be exactly one function marked with the [Start] attribute!

### Przykłady kodu (C#)
```csharp
public class VerySimpleScript
{
     [Start]
     public void MyFunction()
     {
           new Decider().Decide(EnumDecisionType.eOkDecision, "MyFunction was called!", "VerySimpleScript", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
           return;
     }
}
```
```csharp
Public Class VerySimpleScript
   <Start> _
    Public Sub MyFunction()
      Dim dec As Decider = New Decider
      dec.Decide(EnumDecisionType.eOkDecision, "MyFunction was called!", "VerySimpleScript", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)
      Return
   End Sub 'MyFunction
 End Class 'VerySimpleScript
```

---
