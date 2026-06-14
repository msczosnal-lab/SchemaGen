# EPLAN API — actions-cli

*MVP — eksport CSV/PDF, CLI, CommandLineInterpreter*

Dokumentów: 4

## Actions
*Źródło: `Actions.html`*
*Ścieżka: EPLAN API / API Reference / Actions*

Actions This is the list of all official EPLAN API actions available for the user 

### Name 
### Description 
| backup | Action class for backup functions. Backs up a project and master data (forms, symbols, ...) to disk 
| changelayer | Changes graphical layer properties. 
| check | Action class for checking functions: check a project and check pages. 
| CleanWorkspaceAction | Cleans an existing workspace. 
| compress | Action class to compress projects. 
| devicelist | Action class for device list functions: import, export, and delete device lists. 
| edit | Action class for edit functions: open a project, open a page with a name, open a page with a device name and open a page with name and set the cursor at x y coordinates. 
| EplApiModuleAction | Loads and registers an API Add-in. 
| EsCorrectConnections | Merges graphical properties (color, line type, layer...) of connection definition points into one signal definition point for each signal, if these graphical properties are equal on the whole signal. 
| ExecuteScript | Runs the given script. 
| export | Action to export pages and projects in graphical, DXF, DWG, PXF format. 
| export3d | Action to export installation spaces into 3d formats. 
| ExportNCData | Action exports NC Data for machines. 
| ExportProductionWiring | Action to export Production Wiring Data for machines according to calling parameters. 
| ExportSegmentsTemplate | Action to export segment templates to file. 
| exportToGraphics | Action to export pages and projects to graphical (TIF, GIF, PNG, JPG) format. 
| gedRedraw | Action class for GED redraw. 
| generate | Action class for generate functions: generate connections and generate cables. 
| generatemacros | Action for generating macros from project. 
| graphicallayertable | Action class for graphical layer table functions: import, export. 
| import | Action for importing projects, macros, and drawings. 
| import3d | Action for importing 3d data. 
| ImportPrePlanningData | Action to import pre-planning data. 
| ImportSegmentsTemplate | Action to import segment templates from file to project. 
| InsertModelViewAction | Action to insert model view object on a page. 
| label | Action class to create labels for projects. 
| masterdata | Action class for operations related to EPLAN master data. 
| MfExportRibbonBarAction | Exports main ribbon bar customizing to XML file. 
| MfImportRibbonBarAction | Imports main ribbon bar customizing from XML file. 
| MfToggleMainMenuAction | Toggles the visibility of the classic menu 
| navigateToEEC | Action class to navigate to an object in the EPLAN Engineering Configuration. 
| OpenWorkspaceAction | Opens an existing workspace. 
| partslist | Action class for exporting and importing parts and other parts management items like addresses, constructions, terminals, accessory lists and accessory placements. Allows also to delete stored properties. 
| partsmanagementapi | Action class for exporting and importing parts and other parts management items like addresses, constructions, terminals, accessory lists and accessory placements. 
| plcservice | Exports/imports PLC data using the specified converter. 
| preparemacros | Action for preparing project for macro generation. 
| print | Action class to print projects and pages. 
| ProjectAction | Runs an action upon a given project and closes project afterwards. 
| projectmanagement | Action class for project management. 
| ProjectOpen | Opens given project. 
| RegisterCustomPropertyEditorAction | Registers/Unregisters a custom editor dialog for a property ID or identifying name of a user-defined property. 
| RegisterScript | Register a script. 
| renumber | Action corresponds to numbering functionality. 
| reports | Action class to update all project evaluations. 
| restore | Action class for restore functions: restore projects and restore master data (forms, symbols, ...) 
| SaveWorkspaceAction | Saves the actual workspace. 
| search | Action class for search operations. Searchs items in a project. 
| selectionset | Action class for selection set functions: get current project, get selected projects, get selected pages. 
| SetProjectLanguage | Sets project languages for read-write and read-only projects. 
| subprojects | Action class to export and import subprojects. 
| SwitchProjectType | Action to change type of project. 
| synchronize | Action class to synchronize project data. 
| Topology | Action for topology-related operations. 
| translate | Action class for translate functions: translate a project, export missing translation list, and remove languages from a project. 
| UnregisterScript | Unregisters a script. 
| UpdateSegmentsFilling | Calculates and sets value of property CABLINGSEGMENT_FILLING for all segments in project. 
| XAfActionSetting | Sets the value of a setting. 
| XAfActionSettingProject | Sets the value of a project setting. 
| XAMlExportProductionData2RASCenterAction | Export of the construction spaces of the selected project in AutomationML format. The generated AutomationML file is intended for import into the Rittal - RiPanel Processing Center, which controls the machines for creating the openings or cutting the mounting rails and wiring channels. 
| XAMlExportProductionData2SmartMountingAction | Export of the construction spaces of the selected project in AutomationML format. The generated AutomationML file is intended for import into the Rittal - RiPanel Processing Center, which controls the machines for creating the openings or cutting the mounting rails and wiring channels. 
| XCabCalculateEnclosureTotalWeightAction | Calculates the total weight of a cabinet and writes it to the "Total weight" property (#36108 - FUNCTION3D_CABINET_TOTALWEIGHT) 
| XCCreateGravingtextAction | Generates an engraving text from the DTs of the source and target of the cable. By default, the designation is abbreviated in accordance with the VASS standard (Volkswagen Audi Seat Skoda), i.e., structure identifiers having the same name of source and target are removed - starting from the left. 
| XCMRemoveUnnecessaryNDPsAction | Removes unnecessary net definition points of active project. 
| XCMUniteNetDefinitionPointsAction | Unites net definition points placed on the same net in active project. 
| XDLInsertDeviceAction | Starts interaction for inserting a device. 
| XEGActionInsertSymRef | Standard action to find symbol references for inserting. 
| XEsGetPagePropertyAction | Gets a special property of first selected page. 
| XEsGetProjectPropertyAction | Gets a special property of the current project. 
| XEsGetPropertyAction | Gets selected objects and gets the property. 
| XEsSetPagePropertyAction | Sets a special property of selected pages. 
| XEsSetProjectPropertyAction | Sets a special property of a current project. 
| XEsSetPropertyAction | Gets selected objects and sets the property. 
| XEsUserPropertiesExportAction | Exports user properties to file. 
| XEsUserPropertiesImportAction | Imports user properties to project from file. 
| XGedClosePage | Closes all selected pages. 
| XGedStartInteractionAction | Starts an interaction of the graphical editor. 
| XGedUpdateMacroAction | Updates macros. It can be passed the full path of a project. When project is not opened, this action opens it and closes it automatically. 
| XMActionDCCommonExport | Starts the export for the external editing. 
| XMActionDCImport | Imports a data configuration file into an existing EPLAN project. 
| XMDeleteReprTypeAction | Removes a representation type from selected macros and what is stored in a selected directory. 
| XMExportConnectionsAction | Action class to export connections of a project. 
| XMExportDCArticleDataAction | Starts the export for the external editing. 
| XMExportFunctionAction | Action class to export functions of a project. 
| XMExportLocationBoxesAction | Action class to export location boxes of a project. 
| XMExportPagesAction | Action class to export pages of a project. 
| XMExportPipeLineDefsAction | Action class to export pipeline definitions of a project. 
| XMExportPotentialDefsAction | Action class to export potential definitions of a project. 
| XMImportDCArticleDataAction | Imports a data configuration file into an existing EPLAN article database. 
| XPamArticlesSyncAction | Synchronization of articles/parts databases from V2022 to SQL Server V2.9. 
| XPamConvertPartDatabaseToArticleDatabaseAction | Converts parts databases from EPLAN Version V2.9 to Version V2022. 
| XPamsDeviceSelectionAction | Selects device or updates device information. This object can be a project/function/connection. 
| XPamSelectPart | Starts the part selection (using the configured database). 
| XPartsSetDataSourceAction | Changes the setting responsible for parts management database type. 
| XPlaUpdateDetailAction | The detail engineering is updated for the selected planning objects 
| XPrjActionUpgradeProjects | This action upgrades one ore more projects to the actual database scheme version. 
| XPrjConvertBaseProjectsAction | This action converts one ore more old basic projects (*.ept and *.epb files) to new basic projects (*.zw9). All basic projects in a folder are upgraded (recursively). 
| XSDPreviewAction | Opens or closes the preview of a project page or macro 
| XSettingsExport | Exports settings to an XML file. 
| XSettingsImport | Imports project-, station-, company- or user settings from an XML file. 
| XSettingsRegisterAction | Registers Add-ons. 
| XSettingsUnregisterAction | Unregistration of Add-ons.

---

## Automatic actions
*Źródło: `Automatic actions.html`*
*Ścieżka: EPLAN API / User Guide / API Framework / Add-ins / Actions / Automatic actions*

Automatic actions This topic describes the automatic actions for the EPLAN command line – we also call them " command line actions ". In contrast to a normal ribbon action, an automatic action does a complete task without any user interaction. It will show no dialogs. 
### How do automatic actions work? 
A command line action first checks, whether all parameters passed to it are valid. It checks if a given parameter exists or if the given project is available, etc. It then processes the parameter values so that they can be passed to the parameters of the corresponding API HEServices class. Now, the HEServices function is called and performs the actual task. This approach ensures that command line actions and HEServices functions conduct exactly the same internal functionality. 
A command line action has either the complete or a subset of the functionality of the respective HEServices class. The following figure shows the principle: 

These are some of the available command line actions: 
- Backup projects and master data 
- Restore projects and master data 
- Compress projects 
- Import 
- Export 
- Device list 
- Parts list 
- Connections and cable generation 
- Search 
- Edit 
- Print 
- Translate 
- Check 
- Labeling 
- Getting the selected project or page 
- ... 

### General remarks 
- If the project name parameter is not specified, the currently selected project is used. When calling the action from the Windows command line the PROJECTNAME parameter must be set. 
- Boolean values need to be set as 0 for "false" and 1 for "true". 
- You may not pass an empty string as parameter value (e.g. /PARAMETER:"" ). If you do not want to set a specific parameter, just skip it. 
- For most parameters that specify a scheme name, the last used scheme will be used, if the respective parameter is not set. You can easily check in GUI which scheme is last used. 
- In general, parameter names are not case sensitive, while parameter values may be case sensitive depending on their purpose.

---

## Calling actions
*Źródło: `Calling actions.html`*
*Ścieżka: EPLAN API / User Guide / API Framework / Add-ins / Actions / Calling actions*

Calling actions All ribbon buttons in P8 are linked to an action. This means that when a ribbon button is called, the corresponding action is executed. In order to execute an action via EPLAN API, you have to create an Action object and execute the action with the Execute method. 
In order to create an Action object, you need to know the action by its name. You have to create a new ActionManager object and call the FindAction function, which takes the name of the action as parameter. 
To pass and evaluate action parameters, you need the ActionCallingContext class: 
- C# 
- VB String strAction =
"TestAction"
;
ActionManager oAMnr=
new
ActionManager();
Action oAction= oAMnr.FindAction(strAction);
if
(oAction !=
null
)
{
ActionCallingContext ctx =
new
ActionCallingContext();
bool
bRet=oAction.Execute(ctx);
if
(bRet)
{
new
Decider().Decide(EnumDecisionType.eOkDecision,
"The Action "
+ strAction +
" ended successfully!"
,
""
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
}
else
{
new
Decider().Decide(EnumDecisionType.eOkDecision,
"The Action "
+ strAction +
" ended with errors!"
,
""
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
}
}
Dim
strAction
As
String
=
"TestAction"
Dim
oAMnr
As
New
ActionManager()
Dim
oAction
As
Action = oAMnr.FindAction(strAction)
Dim
dec
As
Decider =
New
Decider
If
Not
(oAction
Is
Nothing
)
Then
Dim
ctx
As
New
ActionCallingContext()
Dim
bRet
As
Boolean
= oAction.Execute(ctx)
If
bRet
Then
dec.Decide(EnumDecisionType.eOkDecision,
"The Action "
+ strAction +
" ended successfully!"
,
""
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)
Else
dec.Decide(EnumDecisionType.eOkDecision,
"The Action "
+ strAction +
" ended with errors!"
,
""
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)
End
If
End
If

To find out which action is linked to which ribbon button, you can evaluate the onActionStart.String.* event. Alternatively, after clicking the ribbon button, press [Ctrl] + [VK_OEM_5] to show the Diagnostics Dialog . [VK_OEM_5] corresponds to the [^] key on a German keyboard or to the [\] on a United States 101 keyboard. 
For a list of automatic actions, refer to the topic " Automatic Actions ". 

Important: 
Please mind that an action may modify the ActionCallingContext during its execution. For example, sometimes project IDs are added to the context and are passed to an inner action. Reusing the same ActionCallingContext for another action call may lead to unexpected results. So in most cases it is advisable to create a new ActionCallingContext for a new action call. 

### Command line call 
To extend the EPLAN command line with new commands and parameters, you need to implement an action. The action can have its own parameters and can call other API functions. 
In this way an action is executed just after starting EPLAN, for example: 

EPLAN.EXE /Variant:"Electric P8" /NoLoadWorkspace action /Param1:value1 /Param2:value2 /Param3:value3 

The parameter without a flag ( / or - ) is interpreted as the name of an action to be executed. All following parameters are passed to the action. Only one action is allowed per command line call. 
A script can also contain and register an action. This means that it can also evaluate action parameters. 

It is necessary to pass more general command line parameters before the action name. 

List of general command line parameters evaluated by EPLAN: 
| Parameter | Description 
| /Variant | Select the product variant you want to start. E.g. "Electric P8" or "Fluid" 
| /NoLoadWorkspace | No workspace is loaded or restored. 
| /NoSplash | No splash screen is shown on system start. 
| /Language:en_us | EPLAN is started with GUI language "English". The language predefined in the settings of EPLAN will not be changed. 
| /Auto | EPLAN is shut down after executing the command line. 
| /Quiet | No dialogs are shown while a command line is being executed. 
| /Frame:0 | 
- /Frame:0 ➔ The EPLAN main frame is invisible 
- /Frame:1 ➔ The EPLAN main frame is restored to its original size and position 
- /Frame:2 ➔ The EPLAN main frame is started minimized 
- /Frame:3 ➔ The EPLAN main frame is started maximized 
| /Setup | All Settings are restored to their installation default 
| <action name> | The action will be executed, all following parameters (starting with / or – ) are passed to the action as parameters. 
Any command line parameter after the action name is passed as parameter to the action. The parameters are wrapped into an ActionCallingContext as string parameters and can be extracted by the action. Please note that the parameter names on the command line and in the ActionCallingContext must be spelled in the exactly the same: 

EPLAN.EXE /Variant:"Electric P8" action /Param1:value1 /Param2:value2 /Param3:value3 
- C# 
- VB public
bool
Execute(ActionCallingContext ctx )
{
String strParamValue1=
null
;
ctx.GetParameter(
"Param1"
,
ref
strParamValue1);
String strParamValue2=
null
;
ctx.GetParameter(
"Param2"
,
ref
strParamValue2);
String strParamValue3=
null
;
ctx.GetParameter(
"Param3"
,
ref
strParamValue3);
return
true
;
}
Public
Function
Execute(ctx
As
ActionCallingContext)
As
Boolean
Implements
IEplAction
Dim
strParamValue1
As
String
=
Nothing
ctx.GetParameter(
"Param1"
, strParamValue1)
Dim
strParamValue2
As
String
=
Nothing
ctx.GetParameter(
"Param2"
, strParamValue2)
Dim
strParamValue3
As
String
=
Nothing
ctx.GetParameter(
"Param3"
, strParamValue3)
Return
True
End Function
'Execute

Warning: When starting EPLAN from the command line with an action, then no previously opened projects are opened at the beginning of the session. See Also 
### API Miscellaneous Command line parameters

### Przykłady kodu (C#)
```csharp
String strAction = "TestAction";
ActionManager oAMnr= new ActionManager();
Action oAction= oAMnr.FindAction(strAction);
if (oAction != null)
{
    ActionCallingContext ctx = new ActionCallingContext();
    bool bRet=oAction.Execute(ctx);
    if (bRet)
    {               
    new Decider().Decide(EnumDecisionType.eOkDecision, "The Action " + strAction + " ended successfully!", "", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
    }
    else
    {
    new Decider().Decide(EnumDecisionType.eOkDecision, "The Action " + strAction + " ended with errors!", "", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
    }
}
```
```csharp
Dim strAction As String = "TestAction"
Dim oAMnr As New ActionManager()
Dim oAction As Action = oAMnr.FindAction(strAction)
Dim dec As Decider = New Decider
If Not (oAction Is Nothing) Then
   Dim ctx As New ActionCallingContext()
   Dim bRet As Boolean = oAction.Execute(ctx)
   If bRet Then
      dec.Decide(EnumDecisionType.eOkDecision, "The Action " + strAction + " ended successfully!", "", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)              
   Else
      dec.Decide(EnumDecisionType.eOkDecision, "The Action " + strAction + " ended with errors!", "", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)
   End If
End If
```
```csharp
public bool Execute(ActionCallingContext ctx )
{
   String strParamValue1=null;
   ctx.GetParameter("Param1", ref strParamValue1);
   String strParamValue2=null;
   ctx.GetParameter("Param2", ref strParamValue2);
   String strParamValue3=null;
   ctx.GetParameter("Param3", ref strParamValue3);
   return true;
}
```
```csharp
Public Function Execute(ctx As ActionCallingContext) As Boolean Implements IEplAction
   Dim strParamValue1 As String = Nothing
   ctx.GetParameter("Param1", strParamValue1)
   Dim strParamValue2 As String = Nothing
   ctx.GetParameter("Param2", strParamValue2)
   Dim strParamValue3 As String = Nothing
   ctx.GetParameter("Param3", strParamValue3)
   Return True
End Function 'Execute
```

---

## Command line parameters
*Źródło: `Command line parameters.html`*
*Ścieżka: EPLAN API / User Guide / API Miscellaneous / Command line parameters*

Command line parameters Here is a full list of parameters of the EPLAN.exe application. 
By default, it is installed in the C:\Program Files\EPLAN\Platform\<version>\Bin directory. 

### Parameter 
### Description 
| 
Auto | EPLAN is shut down after executing the command line; it has no effects on showing dialogs or the mainframe.

| 
Quiet | Determines if dialogs are shown while a command line is executed:
* 0: all dialogs will be shown
* 1: no dialog will be shown (default)
* 2: only some special dialogs will be shown, e.g. progress bars

| 
NoLicenseDialog | Turn off calling license dialog.

| 
NoUserRightsDialog | Turn off calling user rights dialog. If user rights check fails, EPLAN application will terminate. This dialog will be shown per default if it is needed.

| 
Frame | Determines how the EPLAN mainframe should be shown: 
* 0: Hides this window and passes activation to another window.
* 1: Activates and displays the window. If the window is minimized or maximized, Windows restores it to its original size and position.
* 2: Activates the window and displays it as an icon.
* 3: Activates the window and displays it as a maximized window.
* 4: Displays the window as an icon. The window that is currently active remains active.
* 5: Activates the window and displays it in its current size and position.
* 6: Minimizes the window and activates the top-level window in the system's list.
* 7: Displays the window as an icon. The window that is currently active remains active.
* 8: Displays the window in its current state. The window that is currently active remains active.
* 9: Activates and displays the window. If the window is minimized or maximized, Windows restores it to its original size and position.

| 
Setup | Determines if default settings should be used:
* 0: USER, STATION, COMPANY settings are restored to their installation default (on file level) and databases are backed (default)
* 8: the actual adjusted settings will be used (on file level) ONLY FOR INTERNAL USE!
* category (USER or STATION or COMPANY) is denoted: settings of that category are restored to their installation default (on file level) and the database is backed
* path: all settings below this location will be deleted and then reloaded from the reference database, but only when more than the category is denoted
* nobackup: same as setup:0, but no backup of the databases.

| 
SetupRestore | Determines if settings should be restored from last database backup (default: 0): 
* 0: USER, STATION, COMPANY settings are restored from their last backup (on file level)
* category (USER or STATION or COMPANY) is denoted: settings of that category are restored from their last backup (on file level)

| 
User | Eplan login user. Settings will be used from this user.
As value for this parameter please enter the user name.

| 
Password | Eplan login password used for user rights.
As value for this parameter please enter the user password.

| 
Station | Settings will be used from another station.
As value for this parameter please enter the station name

| 
Company | Settings will be used from another company.
As value for this parameter please enter the company name.

| 
NoLoadWorkspace | No workspace is loaded or restored.

| 
NoSplash | No splash screen is shown on system start.

| 
NoRemoting | No Eplan Remoting functionalities are available.

| 
EplanServerPort | Set the gRPC server on a given port number. The port should be in the range: 49152 - 65535.

| 
Language | EPLAN will be started with chosen GUI language. The language predefined in the settings of EPLAN will not be changed.
As value for this parameter please enter the chosen language (e.g. "de_DE" or "en_US").

| 
PathsScheme | Sets scheme of directories' paths, e.g. "/PathsScheme:PredefinedPathScheme". If a chosen scheme does not exist, the default scheme is used.

| 
autoRegAddon | New installed add-ons will be registered at startup.
Possible values: "true" or "false"

| 
License | Name of the file containing the license to use or to borrow ("*.lis")
As value for this parameter please enter the filename of the "*.lis" file.

| 
ReturnLicense | Return the borrowed license. The parameter is the name of the file containing the borrowed license. This same file used by "/license"
As value for this parameter please enter the filename of the "*.lis" file.

| 
RequestOfflineLicense | Create the request file to borrow license offline ("*.egr"). The parameter is the name of the file containing the license to borrow ("*.lis")
As value for this parameter please enter the filename of the "*.lis" file.

| 
OfflineLicense | Use the file containing the borrowed license which is converted from a confirmation file. The parameter is the name of the file containing the license to borrow ("*.lis")
As value for this parameter please enter the filename of the "*.lis" file.

| 
SystemConfiguration | Set system configuration scheme.
As value for this parameter please enter the scheme name of system configuration.

| 
Variant | Product name. It is used to call an EPLAN platform-based product:
* "Electric P8" 
* Fluid
* FluidMan
* ProPanel
* PPE
* View
* CPM
* FHC
* Education
* Trial

| 
VariantSharedEplDir | Product name directory. This is an alternative way of setting product name to "Variant" parameter, for example "C:\\Program Files\\EPLAN\\Preplanning\\2024.0.3"

| 
AttachDebugger | Attach debugger to execution of eplan.

| 
BatchServer | Use eplan as a batch server.
As value for this parameter please enter the batch server port (default:50000).

| 
WebService | Starts a webservice on the specific URL.
As value for this parameter please enter the URL for the service

| 
RestartOnCrash | Restart EPLAN after a crash occurred.

| 
UseLastOpenedProjects | Determines if last opened projects should be opened on start:
* 0: No projects will be opened.
* 1: Last used projects will be opened.
* 2: Last used projects will be opened if no action is passed. Otherwise (i.e. with action parameter), no projects are opened (default).

| 
<action name> | Action that should be executed, all following parameters (starting with "/" or "–") are passed to the action as parameters.

Remarks By default, when starting P8 from command line with an action, no previously opened projects are opened at the beginning of the session.
If your installation path is different from the default ("C:\Program Files\EPLAN\Platform\<version>\Bin"), you must modify the code samples below accordingly.

Example "C:\\Program Files\\EPLAN\\Platform\\2024.0.3\\Bin\\EPLAN.exe" /variant:"Electric P8"

"C:\\Program Files\\EPLAN\\Platform\\2024.0.3\\Bin\\EPLAN.exe" action /Param1:wert1 /Param2:wert2 /Param3

"C:\\Program Files\\EPLAN\\Platform\\2024.0.3\\Bin\\EPLAN.exe" /Setup:SS_USER_WORKSPACE_NAMED_PATH

"C:\\Program Files\\EPLAN\\Platform\\2024.0.3\\Bin\\EPLAN.exe" /User:UserXYZ

"C:\\Program Files\\EPLAN\\Platform\\2024.0.3\\Bin\\EPLAN.exe" /NoLoadWorkspace action /Param1:wert1

"C:\\Program Files\\EPLAN\\Platform\\2024.0.3\\Bin\\EPLAN.exe" /Language:en_us

"C:\\Program Files\\EPLAN\\Platform\\2024.0.3\\Bin\\EPLAN.exe" /Auto /Quiet /Frame:2 AnotherAction /ActionPar

If the license dialog is needed, the flag "NoLicenseDialog" disables calling it.

"C:\\Program Files\\EPLAN\\Platform\\2024.0.3\\Bin\\EPLAN.exe" /NoLicenseDialog action /Param1:wert1 /Param2:wert2

If no user rights dialog is needed, the flag "NoUserRightsDialog" disables calling it. If user rights check fails, EPLAN application will terminate.

"C:\\Program Files\\EPLAN\\Platform\\2024.0.3\\Bin\\EPLAN.exe" /NoUserRightsDialog action /Param1:wert1 /Param2:wert2

Use or borrow a License defined in "myLicense.lis". In "myLicense.lis" you can define a product variant and License modules to use or to borrow for a period of time.

"C:\\Program Files\\EPLAN\\Platform\\2024.0.3\\Bin\\EPLAN.exe" /License:"D:\\myLicense.lis"

Return a license

"C:\\Program Files\\EPLAN\\Platform\\2024.0.3\\Bin\\EPLAN.exe" /ReturnLicense:"D:\\myLicense.lis"

Request a license file

"C:\\Program Files\\EPLAN\\Platform\\2024.0.3\\Bin\\EPLAN.exe" /RequestOfflineLicense:"D:\\myLicense.lis"

Use a license offline

"C:\\Program Files\\EPLAN\\Platform\\2024.0.3\\Bin\\EPLAN.exe" /OfflineLicense:"D:\\myLicense.lis"

Use a specific port for the Grpc server (API remoting). The port should be in the range : 49152 - 65535.
If not explicitly set, it is automatically determined from this range.

"C:\\Program Files\\EPLAN\\Platform\\2026.0.0\\Bin\\EPLAN.exe" /EplanServerPort:portNr

### Przykłady kodu (C#)
```csharp
EPLAN is shut down after executing the command line; it has no effects on showing dialogs or the mainframe.
```
```csharp
Determines if dialogs are shown while a command line is executed:
 * 0: all dialogs will be shown
 * 1: no dialog will be shown (default)
 * 2: only some special dialogs will be shown, e.g. progress bars
```
```csharp
Turn off calling license dialog.
```
```csharp
Turn off calling user rights dialog. If user rights check fails, EPLAN application will terminate. This dialog will be shown per default if it is needed.
```
```csharp
Determines how the EPLAN mainframe should be shown: 
 * 0: Hides this window and passes activation to another window.
 * 1: Activates and displays the window. If the window is minimized or maximized, Windows restores it to its original size and position.
 * 2: Activates the window and displays it as an icon.
 * 3: Activates the window and displays it as a maximized window.
 * 4: Displays the window as an icon. The window that is currently active remains active.
 * 5: Activates the window and displays it in its current size and position.
 * 6: Minimizes the window and activates the top-level window in the system's list.
 * 7: Displays the window as an icon. The window that is currently active remains active.
 * 8: Displays the window in its current state. The window that is currently active remains active.
 * 9: Activates and displays the window. If the window is minimized or maximized, Windows restores it to its original size and position.
```
```csharp
Determines if default settings should be used:
 * 0: USER, STATION, COMPANY settings are restored to their installation default (on file level) and databases are backed (default)
 * 8: the actual adjusted settings will be used (on file level) ONLY FOR INTERNAL USE!
 * category (USER or STATION or COMPANY) is denoted: settings of that category are restored to their installation default (on file level) and the database is backed
 * path: all settings below this location will be deleted and then reloaded from the reference database, but only when more than the category is denoted
 * nobackup: same as setup:0, but no backup of the databases.
```
```csharp
Determines if settings should be restored from last database backup (default: 0): 
 * 0: USER, STATION, COMPANY settings are restored from their last backup (on file level)
 * category (USER or STATION or COMPANY) is denoted: settings of that category are restored from their last backup (on file level)
```
```csharp
Eplan login user. Settings will be used from this user.
 As value for this parameter please enter the user name.
```
```csharp
Eplan login password used for user rights.
 As value for this parameter please enter the user password.
```
```csharp
Settings will be used from another station.
 As value for this parameter please enter the station name
```
```csharp
Settings will be used from another company.
 As value for this parameter please enter the company name.
```
```csharp
No workspace is loaded or restored.
```
```csharp
No splash screen is shown on system start.
```
```csharp
No Eplan Remoting functionalities are available.
```
```csharp
Set the gRPC server on a given port number. The port should be in the range: 49152 - 65535.
```
```csharp
EPLAN will be started with chosen GUI language. The language predefined in the settings of EPLAN will not be changed.
 As value for this parameter please enter the chosen language (e.g. "de_DE" or "en_US").
```
```csharp
Sets scheme of directories' paths, e.g. "/PathsScheme:PredefinedPathScheme". If a chosen scheme does not exist, the default scheme is used.
```
```csharp
New installed add-ons will be registered at startup.
 Possible values: "true" or "false"
```
```csharp
Name of the file containing the license to use or to borrow ("*.lis")
 As value for this parameter please enter the filename  of the "*.lis" file.
```
```csharp
Return the borrowed license. The parameter is the name of the file containing the borrowed license. This same file used by "/license"
 As value for this parameter please enter the filename  of the "*.lis" file.
```
```csharp
Create the request file to borrow license offline ("*.egr"). The parameter is the name of the file containing the license to borrow ("*.lis")
 As value for this parameter please enter the filename  of the "*.lis" file.
```
```csharp
Use the file containing the borrowed license which is converted from a confirmation file. The parameter is the name of the file containing the license to borrow ("*.lis")
 As value for this parameter please enter the filename  of the "*.lis" file.
```
```csharp
Set system configuration scheme.
 As value for this parameter please enter the scheme name of system configuration.
```
```csharp
Product name. It is used to call an EPLAN platform-based product:
 * "Electric P8" 
 * Fluid
 * FluidMan
 * ProPanel
 * PPE
 * View
 * CPM
 * FHC
 * Education
 * Trial
```
```csharp
Product name directory. This is an alternative way of setting product name to "Variant" parameter, for example "C:\\Program Files\\EPLAN\\Preplanning\\2024.0.3"
```
```csharp
Attach debugger to execution of eplan.
```
```csharp
Use eplan as a batch server.
 As value for this parameter please enter the batch server port (default:50000).
```
```csharp
Starts a webservice on the specific URL.
 As value for this parameter please enter the URL for the service
```
```csharp
Restart EPLAN after a crash occurred.
```
```csharp
Determines if last opened projects should be opened on start:
 * 0: No projects will be opened.
 * 1: Last used projects will be opened.
 * 2: Last used projects will be opened if no action is passed. Otherwise (i.e. with action parameter), no projects are opened (default).
```
```csharp
Action that should be executed, all following parameters (starting with "/" or "–") are passed to the action as parameters.
```
```csharp
By default, when starting P8 from command line with an action, no previously opened projects are opened at the beginning of the session.
 If your installation path is different from the default ("C:\Program Files\EPLAN\Platform\<version>\Bin"), you must modify the code samples below accordingly.
```
```csharp
"C:\\Program Files\\EPLAN\\Platform\\2024.0.3\\Bin\\EPLAN.exe" /variant:"Electric P8"
```
```csharp
"C:\\Program Files\\EPLAN\\Platform\\2024.0.3\\Bin\\EPLAN.exe" action /Param1:wert1 /Param2:wert2 /Param3
```
```csharp
"C:\\Program Files\\EPLAN\\Platform\\2024.0.3\\Bin\\EPLAN.exe" /Setup:SS_USER_WORKSPACE_NAMED_PATH
```
```csharp
"C:\\Program Files\\EPLAN\\Platform\\2024.0.3\\Bin\\EPLAN.exe" /User:UserXYZ
```
```csharp
"C:\\Program Files\\EPLAN\\Platform\\2024.0.3\\Bin\\EPLAN.exe" /NoLoadWorkspace action /Param1:wert1
```
```csharp
"C:\\Program Files\\EPLAN\\Platform\\2024.0.3\\Bin\\EPLAN.exe" /Language:en_us
```
```csharp
"C:\\Program Files\\EPLAN\\Platform\\2024.0.3\\Bin\\EPLAN.exe" /Auto /Quiet /Frame:2 AnotherAction /ActionPar
```
```csharp
If the license dialog is needed, the flag "NoLicenseDialog" disables calling it.
 
 "C:\\Program Files\\EPLAN\\Platform\\2024.0.3\\Bin\\EPLAN.exe" /NoLicenseDialog action /Param1:wert1 /Param2:wert2
```
```csharp
If no user rights dialog is needed, the flag "NoUserRightsDialog" disables calling it. If user rights check fails, EPLAN application will terminate.
 
 "C:\\Program Files\\EPLAN\\Platform\\2024.0.3\\Bin\\EPLAN.exe" /NoUserRightsDialog action /Param1:wert1 /Param2:wert2
```
```csharp
Use or borrow a License defined in "myLicense.lis". In "myLicense.lis" you can define a product variant and License modules to use or to borrow for a period of time.
 
 "C:\\Program Files\\EPLAN\\Platform\\2024.0.3\\Bin\\EPLAN.exe" /License:"D:\\myLicense.lis"
```
```csharp
Return a license
 
 "C:\\Program Files\\EPLAN\\Platform\\2024.0.3\\Bin\\EPLAN.exe" /ReturnLicense:"D:\\myLicense.lis"
```
```csharp
Request a license file
 
 "C:\\Program Files\\EPLAN\\Platform\\2024.0.3\\Bin\\EPLAN.exe" /RequestOfflineLicense:"D:\\myLicense.lis"
```
```csharp
Use a license offline
 
 "C:\\Program Files\\EPLAN\\Platform\\2024.0.3\\Bin\\EPLAN.exe" /OfflineLicense:"D:\\myLicense.lis"
```
```csharp
Use a specific port for the Grpc server (API remoting). The port should be in the range : 49152 - 65535.
 If not explicitly set, it is automatically determined from this range.
 
 "C:\\Program Files\\EPLAN\\Platform\\2026.0.0\\Bin\\EPLAN.exe" /EplanServerPort:portNr
```

---
