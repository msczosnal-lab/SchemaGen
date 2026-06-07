# EPLAN API — misc

*Na żądanie*

Dokumentów: 34

## API Electrotechnical services
*Źródło: `API Electrotechnical services.html`*
*Ścieżka: EPLAN API / User Guide / API Electrotechnical services*

API Electrotechnical services The namespace Eplan.EplApi.EServices provides the following functionality: 
- Getting registered messages, verifications 
- Retrieving project messages 
- Interfaces for registering custom messages / verifications 

The namespace Eplan.EplApi.EServices.Ged provides functionality for creating custom interactions.

---

## API Labeling Modification Interface
*Źródło: `API Labeling Modification Interface.html`*
*Ścieżka: EPLAN API / User Guide / API Miscellaneous / API Labeling Modification Interface*

API Labeling Modification Interface The API Labeling Modification Interface allows you to modify the result of label generation via API. 
The following steps must be perfomed to use it in an API program: 

### a) Create labeling scheme settings Action 
Each labeling scheme now contains a property, where you can set an action name: 

If an action with this name is registered in EPLAN, it is called during label generation. 
You can use the action to influence the objects that are reported and the order in which they appear. 

The action is called from the template with the following parameters: 

Parameters: 
project – Input parameter; value: ID of a project 
mode – Input parameter; value: "ModifyObjectList" 
objects – Input / output parameter; value: IDs of objects that will be evaluated separated by semicolon 

This list can be modified (but not the objects themselves!). You can add or remove object IDs from the list or change their order in the list. 

### b) Create label texts processing action 
You can now add an action to a label: 

This action will be called, when the label is created. The action is called with the following parameters: 

objects – Input parameter; value: main object for the line (can be more than one). 
ActionCallingContext.SetStrings() – Output parameter; call SetStrings() of the calling context to set the result text. More than one result text will generate new lines. 

Please set only one string in the string array you pass to SetStrings() . 
Line breaks are always written to the output file as they are in the string. If necessary, remove line breaks from the strings.

---

## API Miscellaneous
*Źródło: `API Miscellaneous.html`*
*Ścieżka: EPLAN API / User Guide / API Miscellaneous*

API Miscellaneous Other programming interface functionality

---

## API Pre-planning
*Źródło: `API Pre-planning.html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / API Pre-planning*

API Pre-planning The EPLAN API now provides full access to pre-planning data. The following extensions were created for this purpose: 
- Project-related classes from Eplan.EplApi.DataModel.Planning namespace 
- The PrePlanningMacro class and Insert::PrePlanning for the macro access 
- PrePlanningService for more complex operations 
- New enum values 
### Eplan.EplApi.DataModel.Planning namespace 
Pre-Planning related objects are stored in the Eplan.EplApi.DataModel.Planning namespace. Here is an UML class diagram that shows their inheritance hierarchy: 

### Migration of PPE API to Preplanning 
Since EPLAN 2.4, there is a new product for the pre-planning and basic engineering of plant and machinery: 
EPLAN Preplanning Professional 

The product was developed on the basis of the EPLAN Platform and in parallel to the EPLAN PPE solution. Now it is the replacement of the EPLAN PPE. 
Because of this, EPLAN PPE is no longer supported nor described in API Help since version 2.7. So please migrate your applications using PPE API to Preplanning API. 
As a replacement, use classes from Eplan.EplApi.DataModel.Planning namespace and PrePlanningService. 
Please note also, there will be no further development of the EPLAN PPE system.

---

## API Reference
*Źródło: `API Reference.html`*
*Ścieżka: EPLAN API / API Reference*

API Reference API Reference stores detail description of classes and other API items (actions, events, interactions and converters)

---

## API Reports Modification Interface
*Źródło: `API Reports Modification Interface.html`*
*Ścieżka: EPLAN API / User Guide / API Miscellaneous / API Reports Modification Interface*

API Reports Modification Interface The API Reports Modification Interface makes it possible to take influence on the result of report generation via an API action. 
In this way, it is possible to filter or change the order of objects for a report. Warning: When a report action is used, please don't set a filter or sort settings because it can be inconsistent with the action! 
The following steps need to be done to in order to use the interface: 

### a) Create a report processing action 
Each report template now contains a property that allows you to set an action name: 

If an action with this name is registered in EPLAN, it is called on several occasions during report generation. 
During these steps, you can influence the texts that appear in the report as well as the objects that are reported and the order in which they appear. 
The steps are distinguished by the mode parameter of the called action. 

The action from the template is called with the following parameters: 

Step 1. 
Parameters: 
project – Input parameter; value: ID of a project 
mode – Input parameter; value: "Start" 
objects – Input parameter; value: IDs of objects that will be updated (only if you UPDATE a report) 

Prepare project data for this report if necessary, fill caches etc. 

Step 2. 
Parameters: 
project – Input parameter; value: ID of a project 
mode – Input parameter; value: "ModifyObjectList" 
objects – Input / output parameter; value: IDs of objects that will be evaluated separated with semicolon 

This list can be modified (but not the objects themselves!). You can add or remove object IDs from the list or change their order in the list. 
The objects parameter can be set only in "ModifyObjectList" mode! 

Step 3. 
Parameters: 
project – Input parameter; value: ID of a project 
mode – Input parameter; value: "ModifyPages" 
pages – Input parameter; value: IDs of created pages separated by semicolon 

The created pages and their properties can be modified. 

Step 4 . 
Parameters: 
project – Input parameter; value: ID of a project 
mode – Input parameter; value: "Finish" 

Clean up caches or undo changes made in step 1. 

### b) Prepare a form to be processed 
It is recommended to use a custom form that will be processed by the action described above. 
This will ensure that reports can be created either in the "standard" way or in the new one. 
The easiest way is to use a copy of an existing form. Such a form should be set in the Form field of the project template: 

The form can have a custom actions assigned to the placeholder text. This can be set in the Form editor: 

Now it is necessary to create the text processing action (see below). 

### c) Create a placeholder text processing action 

This action is called when the placeholder text is evaluated during the report generation. The action is called with the following parameters: 

objects – Input parameter; value: main object for the line (can be more than one). 
ActionCallingContext.SetStrings() – Output parameter; call SetStrings() of the calling context to set the result text. More than one result text will generate new lines. 
color – Input / output parameter; value: "ColorId". Set this parameter to change the color of the placeholder text. It works with one result text only. 
Possible values are from 0 to 256. Please use "-16002" as "From layer" value. 
Predefined values for line color index are: 

0 = black 
1 = red 
2 = yellow 
3 = green 
4 = cyan 
5 = blue 
6 = magenta 
7 = white 
... 
252 = dark gray 
253 = gray 
... 

### d) Make sure that the new form is included in the project master data pool 

This can be done using the Eplan::EplApi::HEServices::Masterdata class. 

The following example shows how to create an embedded report with report a processing action: 

### C# 
### Copy Code 
| // Copy a form with placeholder text processing action to the master data directory
File.Copy(
"c:\\temp\\PlugDiagramReportActionFormular.f22"
,
new
ProjectManager().Paths.Forms +
"\\PlugDiagramReportActionFormular.f22"
,
true
);
//... and add it to project master data
StringCollection oProjectNewEntries =
new
StringCollection();
oProjectNewEntries.Add(
@"PlugDiagramReportActionFormular.f22"
);
System.Collections.Hashtable oResult =
new
Masterdata().AddToProjectEx(m_oReportActionProject, oProjectNewEntries);
// Prepare the ReportBlock object
ReportBlock oReportBlock =
new
ReportBlock();
oReportBlock.Create(m_oReportActionProject);
// Set a form with a placeholder text processing action
oReportBlock.FormName =
"PlugDiagramReportActionFormular"
;
oReportBlock.Type = DocumentTypeManager.DocumentType.PlugDiagram;
// Set the report processing action
oReportBlock.Action =
"PlugDiagramReportAction"
;
// Generate the embedded report
ReportBlockReference oReportBlockReference =
new
Reports().CreateEmbeddedReport(oReportBlock, oPage,
new
PointD(10.0, 300.0));

### Przykłady kodu (C#)
```csharp
// Copy a form with placeholder text processing action to the master data directory
File.Copy("c:\\temp\\PlugDiagramReportActionFormular.f22", new ProjectManager().Paths.Forms + "\\PlugDiagramReportActionFormular.f22", true);
//... and add it to project master data
StringCollection oProjectNewEntries = new StringCollection();
oProjectNewEntries.Add(@"PlugDiagramReportActionFormular.f22");
System.Collections.Hashtable oResult = new Masterdata().AddToProjectEx(m_oReportActionProject, oProjectNewEntries);
// Prepare the ReportBlock object
ReportBlock oReportBlock = new ReportBlock();
oReportBlock.Create(m_oReportActionProject);
// Set a form with a placeholder text processing action
oReportBlock.FormName = "PlugDiagramReportActionFormular";
oReportBlock.Type = DocumentTypeManager.DocumentType.PlugDiagram;
// Set the report processing action
oReportBlock.Action = "PlugDiagramReportAction";
// Generate the embedded report
ReportBlockReference oReportBlockReference = new Reports().CreateEmbeddedReport(oReportBlock, oPage, new PointD(10.0, 300.0));
```

---

## API User Guide
*Źródło: `API User Guide.html`*
*Ścieżka: EPLAN API / API User Guide*

API User Guide The user guide is a compilation of How-To-Dos, which describe, how you can use the EPLAN API. It shows, how you can manage to write your own API applications, like add-ins or using EPLAN in other applications . 
The user guide contains examples for some typical tasks, you perhaps want to automate in EPLAN using the API. There are examples for creating or opening EPLAN projects , for creating pages an placing macros , etc. 

In contrast to the API Reference the user guide does not store detail description of every API class.

---

## Add-ons
*Źródło: `Add-ons.html`*
*Ścieżka: EPLAN API / User Guide / API Framework / Add-ons*

Add-ons EPLAN has a modular architecture. This architecture system provides the possibility to expand the standard scope of EPLAN by including additional functionality and changing existing functionality. 
Add-ons enable the user to extend an installed version of EPLAN. Using an add-on, you can basically distribute and centrally administer the following kind of data: 
- Master data 
- Settings 
- API add-ins 
- Scripts 
When the EPLAN version is started for the first time after an add-on has been installed, the new add-on is registered automatically to this EPLAN version (if the add-on is set to autoregister ). 
Add-ons can be installed and updated automatically or manually, locally or from a server. 
Each add-on can be automatically registered as an API DLL. It is also possible to register a script when the add-on is registered.

---

## Adding ribbon commands
*Źródło: `Adding ribbon commands.html`*
*Ścieżka: EPLAN API / User Guide / API Framework / Add-ins / Adding ribbon commands*

Adding ribbon commands An add-in can add one or more ribbon commands to the Extensions > API command gropup. Therefore the class Eplan.EplApi.Gui.RibbonBar provides a function AddCommand which should be called in the OnRegister() method of the add-in class: 

- C# 
- VB ///
<summary>
/// The function is called once during registration add-in.
///
</summary>
///
<param name="bLoadOnStart">
true: In the next Eplan session, add-in will be loaded during initialization
</param>
///
<returns></returns>
public
bool
OnRegister(
ref
System.Boolean bLoadOnStart)
{
var
ribbonBar=
new
Eplan.EplApi.Gui.RibbonBar();
ribbonBar.AddCommand(
"CSharpAction"
,
"CSharpAction"
);
return
true
;
}
///
<summary>
/// The function is called during unregistration the add-in.
///
</summary>
///
<returns></returns>
public
bool
OnUnregister()
{
var
ribbonBar =
new
Eplan.EplApi.Gui.RibbonBar();
return
ribbonBar.RemoveCommand(
"CSharpAction"
);
}
'''
<summary>
''' This function is called once the Add-ins through the Framework in the registering. 
'''
</summary>
'''
<param name="bLoadOnStart">
True: The Add-in is loaded in the future in system start and the function
<seealso cref="OnInit"/>
is called.
</param>
'''
<returns></returns>
Public
Function
OnRegister(
ByRef
bLoadOnStart
As
System.Boolean)
As
Boolean
Implements
IEplAddIn.OnRegister
Dim
ribbonBar
As
Eplan.EplApi.Gui.RibbonBar=
New
Eplan.EplApi.Gui.RibbonBar
ribbonBar.AddCommand(
"CSharpAction"
,
"CSharpAction"
)
Return
True
End Function
'OnInitGui
'''
<summary>
''' This function will remove from called once the Add-ins through the Framework in that the system.
'''
</summary>
'''
<returns></returns>
Public
Function
OnUnregister()
As
Boolean
Implements
IEplAddIn.OnUnregister
Dim
ribbonBar
As
New
RibbonBar()
Return
ribbonBar.RemoveCommand(
"CSharpAction"
)
End Function

The function AddCommand(text, command line) adds a button (i.e ribbon command) with the text "CSharpAction" and assigns the action "CSharpAction" to it. The button is then visible in Extensions > API command group. It is also possible to add it to a custom command group that exists in either persistent or a custom tab. 
Ribbon commands are always assigned to an action. This can be either a custom action (created using the API) or an already existing action. See Also 
### Scripts Adding ribbon items by a script 
### API Miscellaneous Ribbon bar

### Przykłady kodu (C#)
```csharp
/// <summary>
/// The function is called once during registration add-in.
/// </summary>
/// <param name="bLoadOnStart"> true: In the next Eplan session, add-in will be loaded during initialization</param>
/// <returns></returns>
public bool OnRegister(ref System.Boolean bLoadOnStart)
{
   var ribbonBar= new Eplan.EplApi.Gui.RibbonBar();
   ribbonBar.AddCommand("CSharpAction", "CSharpAction");
   return true;
}

/// <summary>
/// The function is called during unregistration the add-in.
/// </summary>
/// <returns></returns>
public bool OnUnregister()
{
    var ribbonBar = new Eplan.EplApi.Gui.RibbonBar();
    return ribbonBar.RemoveCommand("CSharpAction");
}
```
```csharp
''' <summary>
''' This function is called once the Add-ins through the Framework in the registering.  
''' </summary>
''' <param name="bLoadOnStart"> True:  The Add-in is loaded in the future in system start and the function <seealso cref="OnInit"/> is called. </param>
''' <returns></returns>
Public Function OnRegister(ByRef bLoadOnStart As System.Boolean) As Boolean Implements IEplAddIn.OnRegister
   Dim ribbonBar As Eplan.EplApi.Gui.RibbonBar= New Eplan.EplApi.Gui.RibbonBar
   ribbonBar.AddCommand("CSharpAction", "CSharpAction")
   Return True
End Function 'OnInitGui

''' <summary>
''' This function will remove from called once the Add-ins through the Framework in that the system.
''' </summary>
''' <returns></returns>
Public Function OnUnregister() As Boolean Implements IEplAddIn.OnUnregister
    Dim ribbonBar As New RibbonBar()
    Return ribbonBar.RemoveCommand("CSharpAction")
End Function
```

---

## EPLAN API offline applications
*Źródło: `EPLAN API offline applications.html`*
*Ścieżka: EPLAN API / User Guide / API Framework / Using EPLAN in other applications / EPLAN API offline applications*

EPLAN API offline applications The easiest way to use EPLAN API objects in your program is to directly use the functionally of the API DLLs in your code. It is even easier, if your program is a .NET application: You just reference the managed EPLAN API assemblies in your project. This type of application, we call an " offline application ". 

Then – in the appropriate place (e.g. in the main form) – you create an instance of the Eplan.EplApi.System.EplApplication class and initialize it: 
- C# 
- VB private
Eplan.EplApi.System.EplApplication m_oEplApp;
public
MainForm()
{
//
// Required for Windows Form Designer support
//
InitializeComponent();
m_oEplApp =
new
Eplan.EplApi.System.EplApplication();
System.String strAppModifier=
""
;
m_oEplApp.Init(strAppModifier);
}
Private
m_oEplApp
As
Eplan.EplApi.System.EplApplication
Public
Sub
New
()
'
' Required for Windows Form Designer support
'
InitializeComponent()
m_oEplApp =
New
Eplan.EplApi.System.EplApplication()
Dim
strAppModifier
As
System.String =
""
m_oEplApp.Init(strAppModifier)
End Sub
'New MainForm

The string parameter strAppModifier determines, which configuration file is used and thus which modules will be loaded. If you pass an empty string like in the above example, the eplset.xml of the standard version of the current user will be loaded. 
After executing the Init() function, all functions / objects of the EPLAN API are available, with the exception of those that expose GUI functionality such as modal dialogs, docked dialogs or MDI windows. The API classes and methods, etc. are then used in the same way as if programming a normal EPLAN add-in. A few selected modal dialogs of EPLAN are provided by special methods of classes in Eplan.EplApi.System.EplApplication . 
When you no longer need the EPLAN API in your program, you should call the Exit() function of your EplApplication object to unload the API. 
### Usage with Windows Forms 
In case of an offline application using Windows Forms, it is possible that the application changes its size after EplApplication::Init . It happens if the font size in OS is set to other than 100%, which happens quite often in case of large monitors. Because of this, please set DPI awarness in .config file of the application, in order to avoid rescaling: 

### 
### Copy Code 
| <
System.Windows.Forms.ApplicationConfigurationSection
>
<
add
key
="DpiAwareness"
value
="PerMonitorV2"
/>
</
System.Windows.Forms.ApplicationConfigurationSection
>

Also, please assure your .manifest file is Windows 10 compatible: 

### 
### Copy Code 
| <
compatibility
xmlns
="urn:schemas-microsoft-com:compatibility.v1"
>
<
application
>
<!-- Windows 10 compatibility -->
<
supportedOS
Id
="{8e0f7a12-bfb3-4fe8-b9a5-48fd50a15a9a}"
/>
</
application
>
</
compatibility
>

### How to make sure, that the API assemblies are directly loaded from the EPLAN platform BIN folder? 
As briefly mentioned in the topic " EPLAN .NET API ", a path must be set to the <eplan main path>\Platform\<version>\BIN folder. More precisely, you need to make sure to load the EPLAN API assemblies from exactly this folder. The reason for this is, that the API assemblies have statically linked unmanaged dependencies, which need to be loaded directly from the current directory. 
This is also the reason why it generally does not work to register the EPLAN API DLLs in GAC . The directory from which the references of your Visual Studio project are added has no influence on where the DLLs are actually loaded from. 

You can make sure, the API assemblies are loaded from the correct BIN directory by different means: 
- This is the easiest way: You can just copy the executable of your offline application to the <eplan main path>\Platform\<version>\BIN folder. 
- Use EPLAN API offline wizard. Then your assemblies will be bound to the correct EPLAN variant by means of the Eplan.EplApi.Starter library: 

### C# 
### Copy Code 
| // Use the finder to find the correct EPLAN version if not yet known
EplanFinder oEplanFinder =
new
EplanFinder();
String strBinPath = oEplanFinder.SelectEplanVersion(
true
);
// Check if the user has selected any EPLAN variant (Electric P8, etc.)
if
(String.IsNullOrEmpty(strBinPath))
return
;
// Use the AssemblyResolver to let the program know where all EPLAN variants can be found.
AssemblyResolver oResolver =
new
AssemblyResolver();
oResolver.SetEplanBinPath(strBinPath);
// Now pin to EPLAN. This way all referenced EPLAN assemblies are loaded from the platform BIN path.
oResolver.PinToEplan();
// Use a separate class to initialize EplApplication. Pass the path to the EPLAN product variant BIN directory in order to set the EplApplication.EplanBinFolder property
Form1 oForm =
new
Form1();
oForm.EplanBinFolder = oResolver.GetEplanBinPath();
Application.Run(oForm);

3. Publish the codebases of all needed API assemblies in the application config file. (An XML file, which is named like your executable with an additional extension .config , e.g. "MyApplication.exe.config"). The following code shows an example for the contents of such a config file. 

### XML 
### Copy Code 
| <?
xml version="1.0"
?>
<
configuration
>
<
runtime
>
<
assemblyBinding
xmlns
="urn:schemas-microsoft-com:asm.v1"
>
<
dependentAssembly
>
<
assemblyIdentity
name
="Eplan.EplApi.Systemu"
publicKeyToken
="57aaa27e22f7b107"
/>
<
publisherPolicy
apply
="yes"
/>
<
codeBase
version
="1.0.0.0"
href
="file:///C:\Program Files\EPLAN\Platform\2.2.0\Bin\Eplan.EplApi.Systemu.dll"
/>
</
dependentAssembly
>
<
dependentAssembly
>
<
assemblyIdentity
name
="Eplan.EplApi.AFu"
publicKeyToken
="57aaa27e22f7b107"
/>
<
publisherPolicy
apply
="yes"
/>
<
codeBase
version
="1.0.0.0"
href
="file:///C:\Program Files\EPLAN\Platform\2.2.0\Bin\Eplan.EplApi.AFu.dll"
/>
</
dependentAssembly
>
<
dependentAssembly
>
<
assemblyIdentity
name
="Eplan.EplApi.Baseu"
publicKeyToken
="57aaa27e22f7b107"
/>
<
publisherPolicy
apply
="yes"
/>
<
codeBase
version
="1.0.0.0"
href
="file:///C:\Program Files\EPLAN\Platform\2.2.0\Bin\Eplan.EplApi.Baseu.dll"
/>
</
dependentAssembly
>
<
dependentAssembly
>
<
assemblyIdentity
name
="Eplan.EplApi.DataModelu"
publicKeyToken
="57aaa27e22f7b107"
/>
<
publisherPolicy
apply
="yes"
/>
<
codeBase
version
="1.0.0.0"
href
="file:///C:\Program Files\EPLAN\Platform\2.2.0\Bin\Eplan.EplApi.DataModelu.dll"
/>
</
dependentAssembly
>
<
dependentAssembly
>
<
assemblyIdentity
name
="Eplan.EplApi.HEServicesu"
publicKeyToken
="57aaa27e22f7b107"
/>
<
publisherPolicy
apply
="yes"
/>
<
codeBase
version
="1.0.0.0"
href
="file:///C:\Program Files\EPLAN\Platform\2.2.0\Bin\Eplan.EplApi.HEServicesu.dll"
/>
</
dependentAssembly
>
<
dependentAssembly
>
<
assemblyIdentity
name
="Eplan.EplApi.EServicesu"
publicKeyToken
="57aaa27e22f7b107"
/>
<
publisherPolicy
apply
="yes"
/>
<
codeBase
version
="1.0.0.0"
href
="file:///C:\Program Files\EPLAN\Platform\2.2.0\Bin\Eplan.EplApi.EServicesu.dll"
/>
</
dependentAssembly
>
</
assemblyBinding
>
</
runtime
>
</
configuration
>

4. Last but not least, you can implement an AssemblyResolve event handler in your offline application, where you explicitly load the assemblies you are looking for. You will also need to set the current directory of the application to the respective BIN directory. The following code shows an example for this: 

### C# 
### Copy Code 
| [STAThread]
static
void
Main()
{
Application.EnableVisualStyles();
Application.SetCompatibleTextRenderingDefault(
false
);
Environment.CurrentDirectory =
@"C:\program files\EPLAN\platform\x.x.x\BIN\"
;
// x.x.x = your desired EPLAN version
AppDomain appDomain = AppDomain.CurrentDomain;
appDomain.AssemblyResolve +=
new
ResolveEventHandler(MyResolveEventHandler);

Application.Run(
new
Form1());
}
static
Assembly MyResolveEventHandler(
object
sender, ResolveEventArgs args)
{
Console.WriteLine(
"Resolving..."
);
string
sAssemblyName = args.Name.Split(
','
)[0];
Assembly ass = Assembly.LoadFile(
@"C:\program files\EPLAN\platform\x.x.x\BIN\"
+ sAssemblyName +
".dll"
);
return
ass ;
}
}

In Visual Studio Tools for Office ( VSTO ) projects, the assembly resolver or the application config file is not working. Office still tries to copy the EPLAN API assemblies to a temporary folder before loading. VSTO applications will only work, if you set the codebases of the API assemblies in the machine.config file, which is usually located in the C:\WINDOWS\Microsoft.NET\Framework\v4.0.30319\CONFIG directory. 
### Remarks 
If you want to use any object from the namespaces beginning with Eplan.EplApi.DataModel , you need to open a LockingStep, before you e.g. open an EPLAN project. 

Make sure to call Exit() only one time in your application. It is currently not possible to use Init("") after Exit() , while the application is still running. 
The EplApplication instance should be explicitly de-initialized by the main thread. If the <c>Exit</c> method is called by the garbage collector thread or after leaving the main function of the application, it will cause the application to crash.

### Przykłady kodu (C#)
```csharp
private Eplan.EplApi.System.EplApplication m_oEplApp;
public MainForm()
{
   //
   // Required for Windows Form Designer support
   //
   InitializeComponent();
   m_oEplApp = new Eplan.EplApi.System.EplApplication();
   System.String strAppModifier="";
   m_oEplApp.Init(strAppModifier);
}
```
```csharp
Private m_oEplApp As Eplan.EplApi.System.EplApplication
Public Sub New()
   '
   ' Required for Windows Form Designer support
   '
   InitializeComponent()
   m_oEplApp = New Eplan.EplApi.System.EplApplication()
   Dim strAppModifier As System.String = ""
   m_oEplApp.Init(strAppModifier)
End Sub 'New MainForm
```
```csharp
<System.Windows.Forms.ApplicationConfigurationSection>
     <add key="DpiAwareness" value="PerMonitorV2" />
</System.Windows.Forms.ApplicationConfigurationSection>
```
```csharp
<compatibility xmlns="urn:schemas-microsoft-com:compatibility.v1">
  <application>
    <!-- Windows 10 compatibility -->
    <supportedOS Id="{8e0f7a12-bfb3-4fe8-b9a5-48fd50a15a9a}" />
  </application>
</compatibility>
```
```csharp
// Use the finder to find the correct EPLAN version if not yet known
EplanFinder oEplanFinder = new EplanFinder();
String strBinPath = oEplanFinder.SelectEplanVersion(true);

// Check if the user has selected any EPLAN variant (Electric P8, etc.)
if (String.IsNullOrEmpty(strBinPath))
    return;

// Use the AssemblyResolver to let the program know where all EPLAN variants can be found.
AssemblyResolver oResolver = new AssemblyResolver();
oResolver.SetEplanBinPath(strBinPath);

// Now pin to EPLAN. This way all referenced EPLAN assemblies are loaded from the platform BIN path.
oResolver.PinToEplan();

// Use a separate class to initialize EplApplication. Pass the path to the EPLAN product variant BIN directory in order to set the EplApplication.EplanBinFolder property
Form1 oForm = new Form1();
oForm.EplanBinFolder = oResolver.GetEplanBinPath();
Application.Run(oForm);
```
```csharp
<?xml version="1.0"?>
<configuration>
  <runtime>
    <assemblyBinding xmlns="urn:schemas-microsoft-com:asm.v1">
      <dependentAssembly>
        <assemblyIdentity name="Eplan.EplApi.Systemu" publicKeyToken="57aaa27e22f7b107" />
        <publisherPolicy apply="yes" />
        <codeBase version="1.0.0.0" href="file:///C:\Program Files\EPLAN\Platform\2.2.0\Bin\Eplan.EplApi.Systemu.dll" />
      </dependentAssembly>
      <dependentAssembly>
        <assemblyIdentity name="Eplan.EplApi.AFu" publicKeyToken="57aaa27e22f7b107" />
        <publisherPolicy apply="yes" />
        <codeBase version="1.0.0.0" href="file:///C:\Program Files\EPLAN\Platform\2.2.0\Bin\Eplan.EplApi.AFu.dll" />
      </dependentAssembly>
      <dependentAssembly>
        <assemblyIdentity name="Eplan.EplApi.Baseu" publicKeyToken="57aaa27e22f7b107" />
        <publisherPolicy apply="yes" />
        <codeBase version="1.0.0.0" href="file:///C:\Program Files\EPLAN\Platform\2.2.0\Bin\Eplan.EplApi.Baseu.dll" />
      </dependentAssembly>
      <dependentAssembly>
        <assemblyIdentity name="Eplan.EplApi.DataModelu" publicKeyToken="57aaa27e22f7b107" />
        <publisherPolicy apply="yes" />
        <codeBase version="1.0.0.0" href="file:///C:\Program Files\EPLAN\Platform\2.2.0\Bin\Eplan.EplApi.DataModelu.dll" />
      </dependentAssembly>
      <dependentAssembly>
        <assemblyIdentity name="Eplan.EplApi.HEServicesu" publicKeyToken="57aaa27e22f7b107" />
        <publisherPolicy apply="yes" />
        <codeBase version="1.0.0.0" href="file:///C:\Program Files\EPLAN\Platform\2.2.0\Bin\Eplan.EplApi.HEServicesu.dll" />
      </dependentAssembly>
      <dependentAssembly>
        <assemblyIdentity name="Eplan.EplApi.EServicesu" publicKeyToken="57aaa27e22f7b107" />
        <publisherPolicy apply="yes" />
        <codeBase version="1.0.0.0" href="file:///C:\Program Files\EPLAN\Platform\2.2.0\Bin\Eplan.EplApi.EServicesu.dll" />
      </dependentAssembly>
    </assemblyBinding>
  </runtime>
</configuration>
```
```csharp
[STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Environment.CurrentDirectory = @"C:\program files\EPLAN\platform\x.x.x\BIN\"; // x.x.x = your desired EPLAN version
            AppDomain appDomain = AppDomain.CurrentDomain;
            appDomain.AssemblyResolve += new ResolveEventHandler(MyResolveEventHandler);

            Application.Run(new Form1());
        }
        static Assembly MyResolveEventHandler(object sender, ResolveEventArgs args)
        {
            Console.WriteLine("Resolving...");
            string sAssemblyName = args.Name.Split(',')[0];
            Assembly ass = Assembly.LoadFile(@"C:\program files\EPLAN\platform\x.x.x\BIN\" + sAssemblyName + ".dll");
            return ass ;
        }
    }
```

---

## EPLAN Remoting
*Źródło: `EPLAN Remoting.html`*
*Ścieżka: EPLAN API / User Guide / API Framework / Using EPLAN in other applications / EPLAN Remoting*

EPLAN Remoting ### Introduction 
### EPLAN Remoting 
EPLAN Remoting is a part of API which enables user to connect to an EPLAN Platform variant and control it in remote way. 
Internally it uses gRPC and protocol buffers (protobuf) technology. 
### How to connect 
The connection is established form client application (a .NET program written by API user) to existing EPLAN instance which is available in network. 
### Condition of use 
The condition is that the EPLAN variant is started as a remoting server (without the /NoRemoting parameter). 

### Libraries 
EPLAN Remoting consist of following internal libraries: 
- Eplan.EplApi.RemoteClientu.dll (namespace Eplan.EplApi.RemoteClient ) 
- Eplan.EplApi.Remotingu.dll (namespace Eplan.EplApi.Remoting ) 
external libraries: 
- Google.Protobuf.dll 
- Grpc.Core.Api.dll 
- Grpc.Core.dll 
- Grpc_csharp_ext.x64.dll 
and .NET System libraries 
- System.Runtime.CompilerServices.Unsafe 
- System.Runtime.Remoting Warning! 
It is possible to compile a program without the System.Runtime.CompilerServices.Unsafe library, but it will not work at all. 

The – Grpc_csharp_ext.x64.dll – is a runtime dll that is used by the Grpc.Core and it is necessary to integrate it to the project. 
There are two ways to integrate it correctly. Either you copy it into the build folder or it is added to the project as an "existing item". 
Add -> Existing item… (Shift + Alt + A) Notice: 
The name of the dll must be entered explicitly in the search field. 

When added, please set the property “Copy to Output Directory” to “Copy always”: 

All the dlls are stored in  EPLAN Platform BIN folder. Below are examples how to use it. 

### EPLAN Remoting overview 

EPLAN Remoting allows you to execute actions and some P8 operations in the remote way. 
To open a new session, you have to connect your client to one of the existing P8 instance (the gRPC server that is embedded inside it). 
The server could run locally or remotely. 

After that, you can run P8 actions synchronously or asynchronously. 
You can also pass or get parameters using action contex. 
Finally, to close your remote session, you have to disconnect. 
Below examples show how to use EPLAN Remoting: 
### Getting installed local servers: 

### C# 
### Copy Code 
| List<EplanServerData> oInstalledEplanVersions =
new
List<EplanServerData>();
oClient.GetInstalledEplanVersionsOnLocalMachine(
out
oInstalledEplanVersions);
foreach
(EplanServerData oVersion
in
oInstalledEplanVersions)
Console.WriteLine(oVersion.EplanVariant +
","
+ oVersion.EplanVersion +
","
+ (oVersion.Is64Bit ?
"64"
:
"32"
);

### Listing servers on a local machine: 

### C# 
### Copy Code 
| List<EplanServerData> oActiveEplanVersions =
new
List<EplanServerData>();
oClient.GetActiveEplanServersOnLocalMachine(
out
oActiveEplanVersions);
foreach
(EplanServerData oVersion
in
oActiveEplanVersions)
Console.WriteLine(oVersion.EplanVariant +
","
+ oVersion.EplanVersion +
","
+ oVersion.ServerPort);

### Start an EPLAN instance locally from a client: 

### C# 
### Copy Code 
| List<EplanServerData> oInstalledEplanVersions =
new
List<EplanServerData>();
oClient.GetInstalledEplanVersionsOnLocalMachine(
out
oInstalledEplanVersions);
EplanServerData oConnected = oClient.StartEplan(oInstalledEplanVersions[0].EplanPath);

To make sure that the EPLAN server was started, please check the registry key HKEY_CURRENT_USER\Software\EPLAN\RemoteServer\<port_number> . 

### Establishing a connection with the localhost: 

### C# 
### Copy Code 
| EplanRemoteClient oClient =
new
EplanRemoteClient();
bool
bConnected = oClient.Connect(
"localhost"
,
"49155"
);
// Default port for EPLAN instance is 49155

### Establishing a connection with a remote server: 

### C# 
### Copy Code 
| EplanRemoteClient oClient =
new
EplanRemoteClient();
bool
bConnected = oClient.Connect(
"remote_server"
,
"49155"
,
new
TimeSpan(0, 0, 0, 5));
// Wait 5 seconds

### Calling an action: 

### C# 
### Copy Code 
| bool
oResp = oClient.ExecuteAction(
"XPartsManagementStart"
);

### Calling an action in an asynchronous mode: 

### C# 
### Copy Code 
| oClient.SynchronousMode =
false
;
oClient.ResponseArrivedFromEplanServer += onCallbackArrivedFromEplan;
oClient.ExecuteAction(
"XPartsManagementStart"
);

In this case, the program starts an action and continues running. onCallbackArrivedFromEplan method is called after action finished. 

### Calling an action in synchronous mode: 
This example shows how to get input from a user using context: 

### C# 
### Copy Code 
| oClient.SynchronousMode =
true
;
CallingContext oCallingContext =
new
CallingContext();
oClient.ExecuteAction(
"XPamSelectPart"
,
ref
oCallingContext);

In this case, the program waits until the action execution is finished. 

### Making a selection: 

### C# 
### Copy Code 
| StringCollection oObjects =
new
StringCollection();
oObjects.Add(
@"17/688"
);
EplanResponse oResponse = oClient.SelectEplanObjects(
@"$(MD_PROJECTS)\EPLAN_Sample_Project.elk"
, oObjects,
true
);

### Disconnection: 

### C# 
### Copy Code 
| oClient.Disconnect();

It is important to close the connection when operations are finished.

### Przykłady kodu (C#)
```csharp
List<EplanServerData> oInstalledEplanVersions = new List<EplanServerData>();
oClient.GetInstalledEplanVersionsOnLocalMachine(out oInstalledEplanVersions);
foreach (EplanServerData oVersion in oInstalledEplanVersions)
   Console.WriteLine(oVersion.EplanVariant + "," + oVersion.EplanVersion + "," + (oVersion.Is64Bit ? "64" : "32");
```
```csharp
List<EplanServerData> oActiveEplanVersions = new List<EplanServerData>();
oClient.GetActiveEplanServersOnLocalMachine(out oActiveEplanVersions);
foreach (EplanServerData oVersion in oActiveEplanVersions)
   Console.WriteLine(oVersion.EplanVariant + "," + oVersion.EplanVersion + "," + oVersion.ServerPort);
```
```csharp
List<EplanServerData> oInstalledEplanVersions = new List<EplanServerData>();
oClient.GetInstalledEplanVersionsOnLocalMachine(out oInstalledEplanVersions);
EplanServerData oConnected = oClient.StartEplan(oInstalledEplanVersions[0].EplanPath);
```
```csharp
EplanRemoteClient oClient = new EplanRemoteClient();
bool bConnected = oClient.Connect("localhost", "49155");   // Default port for EPLAN instance is 49155
```
```csharp
EplanRemoteClient oClient = new EplanRemoteClient();
bool bConnected = oClient.Connect("remote_server", "49155", new TimeSpan(0, 0, 0, 5));   // Wait 5 seconds
```
```csharp
bool oResp = oClient.ExecuteAction("XPartsManagementStart");
```
```csharp
oClient.SynchronousMode = false;
oClient.ResponseArrivedFromEplanServer += onCallbackArrivedFromEplan;
oClient.ExecuteAction("XPartsManagementStart");
```
```csharp
oClient.SynchronousMode = true;
CallingContext oCallingContext = new CallingContext();
oClient.ExecuteAction("XPamSelectPart", ref oCallingContext);
```
```csharp
StringCollection oObjects = new StringCollection();
oObjects.Add(@"17/688");
EplanResponse oResponse = oClient.SelectEplanObjects(@"$(MD_PROJECTS)\EPLAN_Sample_Project.elk", oObjects, true);
```
```csharp
oClient.Disconnect();
```

---

## Events
*Źródło: `Events.html`*
*Ścieżka: EPLAN API / API Reference / Events*

Events This is the list of the system notifications from EPLAN on which an API add-in can react. 
- Eplan.EplApi.OnMainEnd 
- Eplan.EplApi.OnMainStart 
- Eplan.EplApi.OnPostOpenProject 
- Eplan.EplApi.OnResetRibbon 
- Eplan.EplApi.OnUserPreCloseProject 
- onActionEnd.String.* 
- onActionStart.String.* 
- Ged.Redraw 
- NCSettingsMachineTools.Redraw 
- Page.ConnectionDirty 
- Project.CablingDirty 
- RefreshPageFilter

---

## Help structure
*Źródło: `Help structure.html`*
*Ścieżka: EPLAN API / Help structure*

Help structure The documentation you are reading is divided into two sections: 1. User Guide 
The User Guide section introduces you into how to set up a development environment and start developing or use more advanced functionality. 
2. API Reference 
The API Reference section lists and describes in detail all the namespaces, classes, methods, etc. of the EPLAN API. API Support setup installs the API Help in HTML and Microsoft Help Viewer format. In this way, it can be accessed online or locally from a disk (i.e. in offline mode). 
### API Help formats In offline mode, API Help can be accessed by the shortcut on a desktop (HTML format) or from Visual Studio (Microsoft Help Viewer). The later one is the standard help system format used by Visual Studio. It can thus be accessed as another VS help installed locally, i.e. by pressing the [F1] key. 
Sometimes the setup cannot correctly register the help correctly in Visual Studio. In this case it can be done manually using the following steps: 
a) Start the Microsoft Help Viewer using Help > Add and Remove Help Content from Visual Studio. 

b) In the Manage Content tab, please select Disk installation source , then browse for the helpcontentsetup.msha file in the directory where the API Help was installed. 
By default it should be in %ProgramData%\EPLAN\O_Data\API-Support\<Eplan version>\doc . 
c) Select the Add link and press the Update button. 
d) Make sure that the help is registered by browsing the EPLAN API content in the Microsoft Help Viewer. 
e) In order to use the help integrated with Visual Studio, please set the preferred help to the Help Viewer: 

Please note that as of Visual Studio 2017, Microsoft Help Viewer is an optional installation component, so it must be additionally added by the Visual Studio Installer.

---

## How to display a MessageBox with the EPLAN window as owner
*Źródło: `How to display a MessageBox with the EPLAN window as owner.html`*
*Ścieżka: EPLAN API / User Guide / API Miscellaneous / How to display a MessageBox with the EPLAN window as owner*

How to display a MessageBox with the EPLAN window as owner How to display a MessageBox with the EPLAN window as owner 
If you would like to display a message box or a modal dialog that uses the EPLAN window as owner window, you can do this as in the following example: 

### C# 
### Copy Code 
| Process oCurrent = Process.GetCurrentProcess();
var
ww =
new
WindowWrapper(oCurrent.MainWindowHandle);
MessageBox.Show(ww,
"dialog with owner"
);
MessageBox.Show(
"dialog without owner"
);
public
class
WindowWrapper : System.Windows.Forms.IWin32Window
{
public
WindowWrapper(IntPtr handle)
{
_hwnd = handle;
}
public
IntPtr Handle
{
get
{
return
_hwnd; }
}
private
IntPtr _hwnd;
}

### Przykłady kodu (C#)
```csharp
Process oCurrent = Process.GetCurrentProcess();
var ww = new WindowWrapper(oCurrent.MainWindowHandle);
MessageBox.Show(ww, "dialog with owner");
MessageBox.Show("dialog without owner");
public class WindowWrapper : System.Windows.Forms.IWin32Window
{
 public WindowWrapper(IntPtr handle)
 {
 _hwnd = handle;
 }
 public IntPtr Handle
 {
 get { return _hwnd; }
 }
 private IntPtr _hwnd;
}
```

---

## IdentityClient
*Źródło: `IdentityClient.html`*
*Ścieżka: EPLAN API / User Guide / API Miscellaneous / IdentityClient*

IdentityClient This chapter shows how to work with the Eplan.IdentityClient.Authentification and Eplan.IdentityClient.Types namespaces. 

First create an IEIdentityClient object and make sure you are signed in to the EPLAN Cloud: 
- C# // Create IdentityClient instance
IEIdentityClient IdentityClient = EIdentityClient.Instance;
// Make sure you are signed in to EPLAN Cloud
Task<AuthenticationData> signInData = IdentityClient.Signin();
AuthenticationData signInResult = signInData.Result;
// Check if success
if
(signInResult.IsSuccess)
new
Decider().Decide(EnumDecisionType.eOkDecision,
"Sign in success"
,
"Result"
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);

Get example information from the user cloud profile: 
- C# // User profile information
Task<IdentityClientResponse> userProfile = IdentityClient.GetUserProfile();
IdentityClientResponse getUserProfileResult = userProfile.Result;
// Show exmaple information
if
(getUserProfileResult.IsSuccess)
{
string
message =
$"Organization Name:
{getUserProfileResult.OrganizationName}
,\nEmail:
{getUserProfileResult.Email}
"
;
new
Decider().Decide(EnumDecisionType.eOkDecision, message,
"UserProfile success"
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
}

Set the ClientId name to work with a specific API service in the EPLAN Cloud: 
- C# // ClientId of specific EPLAN Cloud API application
string
ClientId =
"Proper_Client_Id_Name"
;

Notice: 
ClientId is case-sensitive and can be found on EPLAN Cloud Developer Portal inside tooltip of product tag: 

Use the GetHttpClient() method to work with EPLAN Cloud API endpoints: 
- C# // Initialize httpClient object
var
url =
"https://api.eplan.com/estockservice/v2.0/"
;
HttpClient httpClient =
null
;
IdentityClientResponse httpClientRespone = IdentityClient.GetHttpClient(strClientId, url,
ref
httpClient);
// Get collections
if
(httpClientRespone.IsSuccess)
{
HttpResponseMessage GetAsyncResult = httpClient.GetAsync(
"collections"
).Result;
string
message =
$"Status:
{GetAsyncResult.StatusCode.ToString()}
,\nResult:
{GetAsyncResult.Content.ReadAsStringAsync().Result}
"
;
new
Decider().Decide(EnumDecisionType.eOkDecision, message,
"Get result"
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
}

The GetAccessToken() is called internally by GetHttpClient() , but it is still possible to use this method directly: 
- C# // Get access Token
IdentityClientResponse tokenResponse = IdentityClient.GetAccessToken(strClientId);

Sign out and exit: 
- C# // Sign out
Task<IdentityClientResponse> response = IdentityClient.Signout();
IdentityClientResponse signOutResult = response.Result;
if
(signOutResult.IsSuccess)
new
Decider().Decide(EnumDecisionType.eOkDecision,
"Sign out success"
,
"Result"
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
// Exit IdentityClient
IdentityClientResponse exitResponse = IdentityClient.Exit();
if
(exitResponse.IsSuccess)
new
Decider().Decide(EnumDecisionType.eOkDecision,
"Exit success"
,
"Result"
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);

### Warning about deprecated endpoints 
To receive a warning when a deprecated URL is addressed, the EplanCloudResourceDeprecationEvent must be subscribed to. In the following example, a message box will pop up as soon as a deprecated endpoint is addressed: 

For this purpose, an event handler is registered for the EplanCloudResourceDeprecationEvent . 

- C# // Create an IdentityClient instance
IEIdentityClient IdentityClient = EIdentityClient.Instance;
// Create an endpoint deprecation event handling
EventHandler<EplanCloudResourceDeprecationArgs> DeprecationHandler = (sender, args) =>
{
// Show a message box that displays the deprecated URL as well as the deprecation timestamp and sunset timestamp
string
message =
$"The Eplan URL '
{args.Uri}
' is depreacted. Deprecation:
{args.Deprecation}
. Sunset:
{args.Sunset}
."
;
MessageBox.Show(message);
};
try
{
// Register an event handler for the EplanCloudResourceDeprecationEvent
IdentityClient.EplanCloudResourceDeprecationEvent += DeprecationHandler;
// Call an Eplan Cloud deprecated endpoint
string
deprecatedURL =
"yourDeprecatedEndpointURL"
;
HttpClient httpClient =
null
;
var
result =
IdentityClient.GetHttpClient(strClientId, deprecatedURL,
ref
httpClient);
if
(result.IsSuccess)
{
var
response = httpClient.GetAsync(deprecatedURL).Result;
// Handle response
if
(!response.IsSuccessStatusCode)
{
MessageBox.Show(
$"Eplan Cloud call failed. Error =
{response.ReasonPhrase}
"
);
}
// Give the deprecation message some time to pop up
MessageBox.Show(
"Waiting for event..."
);
}
else
{
MessageBox.Show(result.Error);
}
}
catch
(Exception e)
{
MessageBox.Show(e.Message);
}
finally
{
// Unregister the event handler for EplanCloudResourceDeprecationEvent
IdentityClient.EplanCloudResourceDeprecationEvent -= DeprecationHandler;
}

### Przykłady kodu (C#)
```csharp
// Create IdentityClient instance
IEIdentityClient IdentityClient = EIdentityClient.Instance;

// Make sure you are signed in to EPLAN Cloud
Task<AuthenticationData> signInData = IdentityClient.Signin();
AuthenticationData signInResult = signInData.Result;

// Check if success
if (signInResult.IsSuccess)
    new Decider().Decide(EnumDecisionType.eOkDecision, "Sign in success", "Result", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
```
```csharp
// User profile information
Task<IdentityClientResponse> userProfile = IdentityClient.GetUserProfile();
IdentityClientResponse getUserProfileResult = userProfile.Result;

// Show exmaple information
if (getUserProfileResult.IsSuccess)
{
    string message = $"Organization Name: {getUserProfileResult.OrganizationName},\nEmail: {getUserProfileResult.Email}";
    new Decider().Decide(EnumDecisionType.eOkDecision, message, "UserProfile success", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
}
```
```csharp
// ClientId of specific EPLAN Cloud API application
string ClientId = "Proper_Client_Id_Name";
```
```csharp
// Initialize httpClient object
var url = "https://api.eplan.com/estockservice/v2.0/";
HttpClient httpClient = null;
IdentityClientResponse httpClientRespone = IdentityClient.GetHttpClient(strClientId, url, ref httpClient);

// Get collections
if (httpClientRespone.IsSuccess)
{
     HttpResponseMessage GetAsyncResult = httpClient.GetAsync("collections").Result;
     string message = $"Status: {GetAsyncResult.StatusCode.ToString()},\nResult: {GetAsyncResult.Content.ReadAsStringAsync().Result}";
     new Decider().Decide(EnumDecisionType.eOkDecision, message, "Get result", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
}
```
```csharp
// Get access Token
IdentityClientResponse tokenResponse = IdentityClient.GetAccessToken(strClientId);
```
```csharp
// Sign out
Task<IdentityClientResponse> response = IdentityClient.Signout();
IdentityClientResponse signOutResult = response.Result;

if (signOutResult.IsSuccess)
    new Decider().Decide(EnumDecisionType.eOkDecision, "Sign out success", "Result", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);


// Exit IdentityClient
IdentityClientResponse exitResponse = IdentityClient.Exit();

if (exitResponse.IsSuccess)
    new Decider().Decide(EnumDecisionType.eOkDecision, "Exit success", "Result", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
```
```csharp
// Create an IdentityClient instance
IEIdentityClient IdentityClient = EIdentityClient.Instance;

// Create an endpoint deprecation event handling
EventHandler<EplanCloudResourceDeprecationArgs> DeprecationHandler = (sender, args) =>
{
    // Show a message box that displays the deprecated URL as well as the deprecation timestamp and sunset timestamp
    string message = $"The Eplan URL '{args.Uri}' is depreacted. Deprecation: {args.Deprecation}. Sunset: {args.Sunset}.";
    MessageBox.Show(message);
};

try
{
    // Register an event handler for the EplanCloudResourceDeprecationEvent
    IdentityClient.EplanCloudResourceDeprecationEvent += DeprecationHandler;

    // Call an Eplan Cloud deprecated endpoint
    string deprecatedURL = "yourDeprecatedEndpointURL";
    HttpClient httpClient = null;
    var result =
        IdentityClient.GetHttpClient(strClientId, deprecatedURL, ref httpClient);

    if (result.IsSuccess)
    {
        var response = httpClient.GetAsync(deprecatedURL).Result;

        // Handle response
        if (!response.IsSuccessStatusCode)
        {
            MessageBox.Show($"Eplan Cloud call failed. Error = {response.ReasonPhrase}");
        }

        // Give the deprecation message some time to pop up
        MessageBox.Show("Waiting for event...");
    }
    else
    {
        MessageBox.Show(result.Error);
    }
}
catch (Exception e)
{
    MessageBox.Show(e.Message);
}
finally
{
    // Unregister the event handler for EplanCloudResourceDeprecationEvent
    IdentityClient.EplanCloudResourceDeprecationEvent -= DeprecationHandler;
}
```

---

## Interactions
*Źródło: `Interactions.html`*
*Ścieżka: EPLAN API / API Reference / Interactions*

Interactions This is the list of the available GED interactions. 
- XGedIaFormatDefPoints 
- XGedIaFormatGraphic 
- XGedIaFormatSymbol 
- XGedIaFormatText 
- XMIaInsertMacro

---

## Messages
*Źródło: `Messages.html`*
*Ścieżka: EPLAN API / User Guide / API Electrotechnical services / Messages*

Messages As an API developer, you can add new electrotechnical messages to EPLAN and write them to the message management. 
In order to create a new message, add a class to your project that inherits from the Eplan.EplApi.EServices.Message class. 

The Eplan.EplApi.EServices.Message class declares 3 functions: 
- The parameters of the OnRegister() function define the properties of the message and how it is registered in EPLAN. 
- The GetMessageText() function returns the message text that is displayed in dialogs if requested by EPLAN. 
- The DoHelp() function is called by the system if EPLAN requests help on the message. 
- C# 
- VB public
class
Message1 : Eplan.EplApi.EServices.Message
{
public
override
void
OnRegister(
ref
string
creator,
ref
IMessage.Region eRegionId,
ref
int
iMessageId,
ref
IMessage.Classification eClassification,
ref
int
iOrdinal)
{
creator =
"Creator name"
;
eRegionId = IMessage.Region.Externals;
iMessageId = 25;
eClassification = IMessage.Classification.Error;
iOrdinal = 20;
return
;
}
public
override
System.String GetMessageText()
{
// TODO: Provide text from resource in active GUI language
return
"Message text for %1!s! from Eplan.EplAddIn.Demo.Messages"
;
}
public
override
void
DoHelp()
{
new
Decider().Decide(EnumDecisionType.eOkDecision,
"DoHelp was called!"
,
"Eplan.EplAddIn.Demo.Messages"
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
// TODO: activate help for this message
}
}
Public
Class
Message1
Implements
Eplan.EplApi.EServices.Message
Public
Sub
OnRegister(
ByRef
creator
As
System.String,
ByRef
eRegionId
As
IMessage.Region,
ByRef
iMessageId
As
Integer
, _
ByRef
eClassification
As
IMessage.Classification,
ByRef
iOrdinal
As
Integer
) _
Implements
Eplan.EplApi.EServices.IMessage.OnRegister
creator =
"Creator name"
eRegionId = IMessage.Region.Externals
iMessageId = 25
eClassification = IMessage.Classification.Error
iOrdinal = 20
Return
End Sub
'OnRegister
Public
Function
GetMessageText()
As
System.String
Implements
Eplan.EplApi.EServices.IMessage.GetMessageText
' TODO: Provide text from resource in active GUI language
Return
"Message text for %1!s! from Eplan.EplAddIn.Demo.Messages"
End Function
'GetMessageText
Public
Sub
DoHelp() Eplan.EplApi.EServices.IMessage.DoHelp
Dim
dec
As
Decider =
New
Decider
dec.Decide(EnumDecisionType.eOkDecision,
"DoHelp was called!"
,
"Eplan.EplAddIn.Demo.Messages"
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)
End Sub
'DoHelp ' TODO: activate help for this message
End Class
'Message

It is also possible to create such classes automatically using the EPLAN API Add-in Wizard. 

### Adding a new message 
A registered message can be now added to the message management of EPLAN using the PrjMessagesCollection class. 
- C# 
- VB var
projectMessageCollection =
new
PrjMessagesCollection(myProject);

IMessage.Region region = IMessage.Region.Externals;
int
messageId = 25;
var
storableObject1 = myProjectPage.Functions[0]
as
StorableObject;
var
storableObject2 = myProjectPage.Functions[1]
as
StorableObject;
//Add new message using AddMessage method
projectMessageCollection.AddMessage(
region,
messageId,
"param text 1"
,
storableObject1,
true
,
storableObject2,
"additional info 2"
);
//or using BaseProjectMessage class
var
newMessage =
new
BaseProjectMessage(region, messageId,
"param text 2"
,
"BECK.BK3100"
,
"additional info 2"
);
projectMessageCollection.Add(newMessage);
Dim
projectMessageCollection =
New
PrjMessagesCollection(myProject)
Dim
region
As
IMessage.Region = IMessage.Region.Externals
Dim
messageId
As
Integer
= 25
Dim
storableObject1 = TryCast(myProjectPage.Functions(0), StorableObject)
Dim
storableObject2 = TryCast(myProjectPage.Functions(1), StorableObject)

projectMessageCollection.AddMessage(region, messageId,
"param text 1"
, storableObject1,
True
, storableObject2,
"additional info 2"
)
Dim
newMessage =
New
BaseProjectMessage(region, messageId,
"param text 2"
,
"BECK.BK3100"
,
"additional info 2"
)
projectMessageCollection.Add(newMessage)

### Overriding the text of an existing message 
It is not possible to change an existing verification by overriding it via API (by setting the same name and a higher Ordinal number). However, you can override an existing message and change the default message text to your own text. You need to implement a message with the same iMessageId and eRegion, but use a higher iOrdinal , e.g. 50. Other properties of the message will not be affected. 
The following example shows how to override the existing message 007005 "Device without main function.": 

### C# 
### Copy Code 
| /// This function returns the message text.
/// One verification needs always exactly one message text
public
string
GetMessageText()
{
return
"This device has absolutely no main function!!!!"
;
}
/// This is the registration function of the message belonging to the verification.
/// Parameters:
/// message region
/// message number
/// classification: error, message or info.
/// overload priority
public
void
OnRegister(
ref
String strCreator,
ref
Eplan.EplApi.EServices.IMessage.Region eRegion,
ref
int
iMessageId,
ref
Eplan.EplApi.EServices.IMessage.Classification eClassification,
ref
int
iOrdinal)
{
strCreator =
"de.Eplan.Demo"
;
eRegion = IMessage.Region.Devices;
iMessageId = 5;
eClassification = IMessage.Classification.Error;
iOrdinal = 50;
// Higher than 20
}

### Przykłady kodu (C#)
```csharp
public class Message1 : Eplan.EplApi.EServices.Message
{
    public override void OnRegister(ref string creator, ref IMessage.Region eRegionId, ref int iMessageId,
      ref IMessage.Classification eClassification, ref int iOrdinal)
    {
        creator = "Creator name";
        eRegionId = IMessage.Region.Externals;
        iMessageId = 25;
        eClassification = IMessage.Classification.Error;
        iOrdinal = 20;
        return;
    }
    public override System.String GetMessageText()
    {
        // TODO: Provide text from resource in active GUI language
        return "Message text for %1!s! from Eplan.EplAddIn.Demo.Messages";
    }
    public override void DoHelp()
    {
        new Decider().Decide(EnumDecisionType.eOkDecision, "DoHelp was called!", "Eplan.EplAddIn.Demo.Messages", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
        // TODO: activate help for this message
    }
}
```
```csharp
Public Class Message1
   Implements Eplan.EplApi.EServices.Message
   Public Sub OnRegister(ByRef creator As System.String, ByRef eRegionId As IMessage.Region, ByRef iMessageId As Integer, _
                          ByRef eClassification As IMessage.Classification, ByRef iOrdinal As Integer) _
                          Implements Eplan.EplApi.EServices.IMessage.OnRegister
      creator = "Creator name"
      eRegionId = IMessage.Region.Externals
      iMessageId = 25
      eClassification = IMessage.Classification.Error
      iOrdinal = 20
      Return
   End Sub 'OnRegister

   Public Function GetMessageText() As System.String Implements Eplan.EplApi.EServices.IMessage.GetMessageText
      ' TODO: Provide text from resource in active GUI language
      Return "Message text for %1!s! from Eplan.EplAddIn.Demo.Messages"
   End Function 'GetMessageText

   Public Sub DoHelp() Eplan.EplApi.EServices.IMessage.DoHelp
      Dim dec As Decider = New Decider
      dec.Decide(EnumDecisionType.eOkDecision, "DoHelp was called!", "Eplan.EplAddIn.Demo.Messages", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)
   End Sub 'DoHelp ' TODO: activate help for this message
End Class 'Message
```
```csharp
var projectMessageCollection = new PrjMessagesCollection(myProject);

IMessage.Region region = IMessage.Region.Externals;
int messageId = 25;

var storableObject1 = myProjectPage.Functions[0] as StorableObject;
var storableObject2 = myProjectPage.Functions[1] as StorableObject;

//Add new message using AddMessage method
projectMessageCollection.AddMessage(
    region,
    messageId,
    "param text 1",
    storableObject1,
    true,
    storableObject2,
    "additional info 2");

//or using BaseProjectMessage class
var newMessage = new BaseProjectMessage(region, messageId, "param text 2", "BECK.BK3100", "additional info 2");
projectMessageCollection.Add(newMessage);
```
```csharp
Dim projectMessageCollection = New PrjMessagesCollection(myProject)

Dim region As IMessage.Region = IMessage.Region.Externals
Dim messageId As Integer = 25

Dim storableObject1 = TryCast(myProjectPage.Functions(0), StorableObject)
Dim storableObject2 = TryCast(myProjectPage.Functions(1), StorableObject)

projectMessageCollection.AddMessage(region, messageId, "param text 1", storableObject1, True, storableObject2, "additional info 2")

Dim newMessage = New BaseProjectMessage(region, messageId, "param text 2", "BECK.BK3100", "additional info 2")
projectMessageCollection.Add(newMessage)
```
```csharp
/// This function returns the message text.
/// One verification needs always exactly one message text
public string GetMessageText()
{
   return "This device has absolutely no main function!!!!";
}

/// This is the registration function of the message belonging to the verification.
/// Parameters:
///   message region
///   message number
///   classification: error, message or info.
///   overload priority
public void OnRegister(ref String strCreator, ref Eplan.EplApi.EServices.IMessage.Region eRegion, ref int iMessageId, ref Eplan.EplApi.EServices.IMessage.Classification eClassification, ref int iOrdinal)
{
   strCreator = "de.Eplan.Demo";
   eRegion = IMessage.Region.Devices;
   iMessageId = 5;
   eClassification = IMessage.Classification.Error;
   iOrdinal = 50; // Higher than 20
}
```

---

## PCTLoop
*Źródło: `PCTLoop.html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / API Pre-planning / PCTLoop*

PCTLoop The PCTLoop class represents the PCT loops in a project. They are logical units to measure or control. 

### C# 
### Copy Code 
| SegmentDefinition oSegmentDefinition = m_oTestProject.GetSegmentDefinition(
"Eplan.PCT.Loop"
);
PCTLoop oPCTLoop = PCTLoop.Create(oSegmentDefinition)
as
PCTLoop;

In the GUI, they are visible in Pre-planning navigator:

### Przykłady kodu (C#)
```csharp
SegmentDefinition oSegmentDefinition = m_oTestProject.GetSegmentDefinition("Eplan.PCT.Loop");
PCTLoop oPCTLoop  = PCTLoop.Create(oSegmentDefinition) as PCTLoop;
```

---

## Query user rights
*Źródło: `Query user rights.html`*
*Ścieżka: EPLAN API / User Guide / API Miscellaneous / Query user rights*

Query user rights EPLAN can link user interactions with specific rights. This is done by the EPLAN r ights management module. If this module is not available or not licensed, the r ights management is not active in EPLAN. The following screenshot shows the Rights management dialog with a list of rights. 

In your API application, you can find out, whether the rights management module is active and you can query the status of a given user right. The following example checks the user right for "XPLEditorStart", using the checkUserRights and the checkRightFor method. 
- C# 
- VB UserRights oUserRights =
new
UserRights();
bool
bRights = oUserRights.CheckUserRights();
if
(bRights)
{
bool
bAnRight= oUserRights.CheckRightFor(
"XPLEditorStart"
);
if
(bAnRight)
{
new
Decider().Decide(EnumDecisionType.eOkDecision,
"You have the right to call XPLEditorStart!"
,
""
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
}
else
{
new
Decider().Decide(EnumDecisionType.eOkDecision,
"You don't have the right to call XPLEditorStart!"
,
""
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
}
}
else
{
new
Decider().Decide(EnumDecisionType.eOkDecision,
"This application works without rights management!"
,
""
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
}
Dim
oUserRights
As
New
UserRights()
Dim
bRights
As
Boolean
= oUserRights.CheckUserRights()
Dim
dec
As
Decider =
New
Decider
If
bRights
Then
Dim
bAnRight
As
Boolean
= oUserRights.CheckRightFor(
"XPLEditorStart"
)
If
bAnRight
Then
dec.Decide(EnumDecisionType.eOkDecision,
"You have the right to call XPLEditorStart!"
,
""
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)
Else
dec.Decide(EnumDecisionType.eOkDecision,
"You don't have the right to call XPLEditorStart!"
,
""
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)
End
If
Else
dec.Decide(EnumDecisionType.eOkDecision,
"This application works without rights management!"
,
""
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)
End
If

For information about the rights available in EPLAN and about their assignment to the users, please refer to the Rights management dialog. You cannot add new user rights via API.

### Przykłady kodu (C#)
```csharp
UserRights oUserRights = new UserRights();
bool bRights = oUserRights.CheckUserRights();
if (bRights)
{
     bool bAnRight= oUserRights.CheckRightFor("XPLEditorStart");
     if (bAnRight)
     {
       new Decider().Decide(EnumDecisionType.eOkDecision, "You have the right to call XPLEditorStart!", "", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
     }
     else
     {
       new Decider().Decide(EnumDecisionType.eOkDecision, "You don't have the right to call XPLEditorStart!", "", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
     }
}
else
{
    new Decider().Decide(EnumDecisionType.eOkDecision, "This application works without rights management!", "", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
}
```
```csharp
Dim oUserRights As New UserRights()
Dim bRights As Boolean = oUserRights.CheckUserRights()
Dim dec As Decider = New Decider
If bRights Then
   Dim bAnRight As Boolean = oUserRights.CheckRightFor("XPLEditorStart")
   If bAnRight Then
      dec.Decide(EnumDecisionType.eOkDecision, "You have the right to call XPLEditorStart!", "", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)               
   Else
      dec.Decide(EnumDecisionType.eOkDecision, "You don't have the right to call XPLEditorStart!", "", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)             
   End If
Else
   dec.Decide(EnumDecisionType.eOkDecision, "This application works without rights management!", "", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)
End If
```

---

## Ribbon bar
*Źródło: `Ribbon bar.html`*
*Ścieżka: EPLAN API / User Guide / API Miscellaneous / Ribbon bar*

Ribbon bar Since version 2022, the EPLAN GUI items are accessible through a ribbon. In the API this control is represented by the following classes: 
- Eplan.EplApi.Gui.RibbonBar 
- Eplan.EplApi.Gui.RibbonTab 
- Eplan.EplApi.Gui.RibbonCommandGroup 
- Eplan.EplApi.Gui.RibbonCommand 
The ribbon is divided into tabs and these tabs into c ommand groups and commands. 
All ribbon related classes are stored in the Eplan.EplApi.Gui namespace. They correspond to the types of ribbon items from the GUI: 

Here is an example of listing ribbon items (tabs, command groups and commands): 
- C# RibbonBar ribbonBar =
new
RibbonBar();
foreach
(RibbonTab tab
in
ribbonBar.Tabs)
{
Debug.WriteLine(
$"\tTab Name:
{tab.Name}
------------"
);
foreach
(
var
commandGroup
in
tab.CommandGroups)
{
Debug.WriteLine(
$"\t\tCommand group:
{commandGroup.Name}
------"
);
foreach
(
var
command
in
commandGroup.Commands)
{
RibbonCommand ribbonCommand = command.Value;
uint
commandId = ribbonCommand.ID;
string
strText = ribbonCommand.Text;
string
strDescription = ribbonCommand.Description;
string
strTooltipText = ribbonCommand.TooltipText;
string
strActionCommandLine = ribbonCommand.ActionCommandLine;
Debug.WriteLine(
$"\t\t\tCommand Id:
{commandId}
---.Text:
{strText}
---.ActionCommandLine:
{strActionCommandLine}
---.TooltipText:
{strTooltipText}
---.Description:
{strDescription}
"
);
}
Debug.WriteLine(
$"\t\t-----------------------"
);
}
Debug.WriteLine(
$"\t-----------------------------"
);
}

Please keep it in mind that some tabs are context sensitive, i.e they are open only when the editor is visible. 
The old menu and toolbars are no longer accessible. The equivalent of the old menu point / toolbar button is now the ribbon command: 

In the API, commands can be created in following places: 
- Extensions > API command group 
- A custom command group that is placed in a persistient or custom tab 
### Menu and toolbar migration 
The classes corresponding to the old GUI items i.e. Toolbar and Menu are currently deprecated, so it is highly recommended to migrate relevant code. 
The following table shows how to create new ribbon items and provides example code: 

### Old GUI item 
### Old API method 
### New GUI equivalent 
### New API method 
### Example old code 
### Example new code 
| Main menu | Menu.AddMainMenu | RibbonTab | RibbonBar.AddTab | menu.AddMainMenu("API Tests A-N", Menu.MainMenuName.eMainMenuHelp,"AddingMessageAction", "AddingMessageAction", "First menu element", 1); | var ribbonTab = ribbonBar.AddTab("API Tests A-N"); 
| Popup menu | Menu.AddPopupMenuItem | RibbonCommandGroup | RibbonTab.AddCommandGroup | menu.AddPopupMenuItem("ActionExample - test2","ActionExample - test2 submenupoint1", "ActionExample", "status text", mainID, 0, false, false); | var commandGroup = ribbonTab.AddCommandGroup("ActionExample - test2"); 
| Toolbar | toolbar.CreateCustomToolbar | RibbonCommandGroup | RibbonTab.AddCommandGroup | toolbar.CreateCustomToolbar("SelectionSet", Toolbar.ToolBarDockPos.eToolbarLeft, 4, 1, true); | var commandGroup = ribbonTab.AddCommandGroup("SelectionSet"); 
| Menu item | menu.AddMenuItem( | RibbonCommand | RibbonBar.AddCommand , RibbonCommandGroup.AddCommand | 
menu.AddMenuItem("UndoAction", "UndoAction"); 
menu.AddMenuItem("SelectionRecursive", "SelectionRecursiveAction", "", selectionSetID, 1,false, false); | 
ribbonBar.AddCommand("UndoAction", "UndoAction"); 
commandGroup.AddCommand("SelectionRecursive", "SelectionRecursiveAction"); 
| Toolbar button | toolbar.AddButton( | RibbonCommand | RibbonCommandGroup.AddCommand(…,index) | toolbar.AddButton("SelectionSet", Int32.MaxValue, "SelectionOneItemAction","C:\\myicons\\0.ico", "SelectionOneItemAction"); | commandGroup.AddCommand("SelectionOneItemAction", "SelectionOneItemAction", 0); 
Here is also a list of other old methods and their new counterparts: 
| 

### Old method 
### New method 
| Toolbar.ExistsToolbar | RibbonBar.Tabs.Any(by LINQ) 
RibbonBar.GetTab 
RibbonBar.GetDefaultTab 
| Toolbar.GetButtonAction | RibbonCommand.ActionCommandLine 
| Toolbar.GetButtonToolTip | RibbonCommand.TooltipText 
| Toolbar.GetCountOfButtons | RibbonCommandGroup.Commands.Count 
| Toolbar.GetPersistentButtonId 
Menu.GetCustomMenuId 
GetPersistentMenuId | RibbonCommand.ID 
| Toolbar.RemoveButton | RibbonCommand.Remove 
| Toolbar.RemoveCustomToolbar | RibbonCommandGroup.Remove 
| Menu.IsActionChecked | RibbonCommand.IsChecked 
| Menu.IsActionEnabled | RibbonCommand.IsEnabled 
| Menu.RemoveMenuItem | RibbonTab.Remove 
RibbonCommandGroup.Remove 
RibbonCommand.Remove 
The ContextMenu class is not affected by this change, i.e everything should work as before version 2022. 
For more information, please refer to chapter "The New Ribbon" of the EPLAN Help. 

### RibbonIcons 
Ribbon command actions can now be created with .svg icons. There is a list of standard CommandIcons , accessible by name or index number. 
Furthermore, below examples present also how to use custom icons, which can be added by specifying path to .svg file or providing icon content in string format. 

Adding standard icons 
- C# var
ribbonBar =
new
RibbonBar();
var
tab = ribbonBar.AddTab(
"RibbonIcons"
);
// Adding standard icons to a command action using enum names
var
commandGroup = tab.AddCommandGroup(
"enum names"
);
commandGroup.AddCommand(
"Button1"
,
"action1"
,
new
RibbonIcon(CommandIcon.Generator));
commandGroup.AddCommand(
"Button2"
,
"action2"
,
new
RibbonIcon(CommandIcon.Amplifier));
commandGroup.AddCommand(
"Button3"
,
"action3"
,
new
RibbonIcon(CommandIcon.Octagon_3));
// Adding standard icons to a command action using index numbers
commandGroup = tab.AddCommandGroup(
"index numbers"
);
commandGroup.AddCommand(
"Button4"
,
"action4"
,
new
RibbonIcon(75));
commandGroup.AddCommand(
"Button5"
,
"action5"
,
new
RibbonIcon(123));
commandGroup.AddCommand(
"Button6"
,
"action6"
,
new
RibbonIcon(181));

Adding custom icons 
- C# // Adding new custom icons to a command action using the path to the file
commandGroup = tab.AddCommandGroup(
"custom icons path to file"
);
commandGroup.AddCommand(
"Button7"
,
"action7"
,
new
RibbonIcon(
"D:\\Icon2.svg"
));
commandGroup.AddCommand(
"Button8"
,
"action8"
,
new
RibbonIcon(
"D:\\Icon3.svg"
));
// Adding new custom icons to a RibbonBar using the path to the file
RibbonIcon ribbonIcon = ribbonBar.AddIcon(
"D:\\CarIco.svg"
);
commandGroup = tab.AddCommandGroup(
"AddIcon using path"
);
commandGroup.AddCommand(
"Button10"
,
"action10"
, ribbonIcon);
// Adding new custom icons to a RibbonBar using the string source
var
svgContent =
"<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"16\" height=\"16\" viewBox=\"0 0 16 16\">"
+
"<title>Clock_1</title>"
+
"<g id=\"GUIicons\">"
+
"<g id=\"Clock\">"
+
"<g>"
+
"<circle cx=\"8\" cy=\"8\" r=\"7.5\" style=\"fill: #fff\"/>"
+
"<path d=\"M8,1A7,7,0,1,1,1,8,7,7,0,0,1,8,1M8,0a8,8,0,1,0,8,8A8,8,0,0,0,8,0Z\" style=\"fill: #4a7db1\"/>"
+
"<g>"
+
"<path d=\"M12,8.5H8v-1h4ZM7.5,4V7h1V4Z\" style=\"fill:#9e0b0f\"/>"
+
"<g>"
+
"<rect x=\"13.5\" y=\"7\" width=\"1\" height=\"2\"transform=\"translate(22 -6) rotate(90)\" style=\"fill: #505050\"/>"
+
"<rect x=\"7.5\" y=\"13\" width=\"1\" height=\"2\"transform=\"translate(16 28) rotate(-180)\" style=\"fill: #505050\"/>"
+
"<rect x=\"1.5\" y=\"7\" width=\"1\" height=\"2\"transform=\"translate(-6 10) rotate(-90)\" style=\"fill: #505050\"/>"
+
"<rect x=\"7.5\" y=\"1\" width=\"1\" height=\"2\"style=\"fill: #505050\"/>"
+
"</g>"
+
"<circle cx=\"8\" cy=\"8\" r=\"1\" style=\"fill:#4a7db1;stroke: #9e0b0f;stroke-miterlimit: 10;stroke-width: 0.5px\"/>"
+
"</g>"
+
"</g>"
+
"</svg>"
;

commandGroup = tab.AddCommandGroup(
"AddIcon using source"
);
ribbonIcon = ribbonBar.AddIcon(svgContent);
commandGroup.AddCommand(
"Button13"
,
"action13"
, ribbonIcon);

The above examples result in this RibbonBar: 

RibbonCommandInfo 
Ribbon command actions can now be created using a RibbonCommandInfo object. This object contains all required and optional properties. 
The optional properties are Description , Tooltip , Icon , IndexButtonPosition , MultiLangButtonText , MultiLangDescription and MultiLangTooltip . 
The multilanguage properties are used over the non-multilanguage properties if they are not empty. 
The IndexButtonPosition is used to specify the position in a RibbonCommandGroup . 
- C# // Adding new commands using the RibbonCommandInfo
commandGroup = tab.AddCommandGroup(
"commands with RibbonCommandInfo"
);
RibbonCommandInfo ribbonCommandInfo =
new
RibbonCommandInfo(
"buttonText"
,
"actionCommandLine"
);
commandGroup.AddCommand(ribbonCommandInfo);

Add existing EPLAN actions to a custom CommandGroup 
It is possible to add existing EPLAN ribbon command actions to a custom CommandGroup via their Command.ID . 
The corresponding internal icon is automatically added to the action. 
- C# // Adding an existing EPLAN command action by its ID
const
int
commandId = 35089;
var
tab = ribbonBar.AddTab(
"CustomTab"
);
var
commandGroup = tab.AddCommandGroup(
"Group1"
);
var
commandAction = commandGroup.AddCommandWithId(commandId);

To find the correct Command.ID value for the command, you can check the description log in the EPLAN Diagnostics dialog after calling this action from the ribbon (to show the Diagnostics Dialog press [Ctrl] + [VK_OEM_5] . [VK_OEM_5] corresponds to the [^] key on a German keyboard or to the [\] on a United States 101 keyboard.): 

SVG Icons limitations 
Our UI libraries provide SVG support with the following limitations: 
• Scripts, interactions and external objects are not implemented for security reasons. 
• Animations, videos, sounds and internal images are not implemented. 
• Since SVG icons should be small and fast to render, we disabled the following SVG elements that can significantly affect drawing performance: 

- <pattern> 

- <color-profile> 

- <hkern> 

- <hatch> 

- <hatchpath> 

-  all effects, blend mode and filters 
-  compressed SVG files ( SVGz ) 
It is strongly recommended to use only simplified ("optimized") SVG : All elements such as text or shapes should be converted to paths and all paths should be combined. 
The simplified SVG is small and fast-drawing. In addition, it will be very difficult to "reverse engineer" your media in this case. 

See Also 
### Scripts Adding ribbon items by a script 
### Addins Adding ribbon commands

### Przykłady kodu (C#)
```csharp
RibbonBar ribbonBar = new RibbonBar();
foreach (RibbonTab tab in ribbonBar.Tabs)
{
    Debug.WriteLine($"\tTab Name:{tab.Name}------------");
    foreach (var commandGroup in tab.CommandGroups)
    {
        Debug.WriteLine($"\t\tCommand group:{commandGroup.Name}------");
        foreach (var command in commandGroup.Commands)
        {
            RibbonCommand ribbonCommand = command.Value;
            uint commandId          = ribbonCommand.ID;
            string strText          = ribbonCommand.Text;
            string strDescription   = ribbonCommand.Description;
            string strTooltipText   = ribbonCommand.TooltipText;
            string strActionCommandLine = ribbonCommand.ActionCommandLine;
            Debug.WriteLine($"\t\t\tCommand Id:{commandId}---.Text:{strText}---.ActionCommandLine:{strActionCommandLine}---.TooltipText:{strTooltipText}---.Description:{strDescription}");
        }
        Debug.WriteLine($"\t\t-----------------------");
    }
    Debug.WriteLine($"\t-----------------------------");
}
```
```csharp
var ribbonBar = new RibbonBar();
var tab = ribbonBar.AddTab("RibbonIcons");


// Adding standard icons to a command action using enum names
var commandGroup = tab.AddCommandGroup("enum names");
commandGroup.AddCommand("Button1", "action1", new RibbonIcon(CommandIcon.Generator));
commandGroup.AddCommand("Button2", "action2", new RibbonIcon(CommandIcon.Amplifier));
commandGroup.AddCommand("Button3", "action3", new RibbonIcon(CommandIcon.Octagon_3));


// Adding standard icons to a command action using index numbers
commandGroup = tab.AddCommandGroup("index numbers");
commandGroup.AddCommand("Button4", "action4", new RibbonIcon(75));
commandGroup.AddCommand("Button5", "action5", new RibbonIcon(123));
commandGroup.AddCommand("Button6", "action6", new RibbonIcon(181));
```
```csharp
// Adding new custom icons to a command action using the path to the file
commandGroup = tab.AddCommandGroup("custom icons path to file");
commandGroup.AddCommand("Button7", "action7", new RibbonIcon("D:\\Icon2.svg"));
commandGroup.AddCommand("Button8", "action8", new RibbonIcon("D:\\Icon3.svg"));

// Adding new custom icons to a RibbonBar using the path to the file
RibbonIcon ribbonIcon = ribbonBar.AddIcon("D:\\CarIco.svg");
commandGroup = tab.AddCommandGroup("AddIcon using path");
commandGroup.AddCommand("Button10", "action10", ribbonIcon);

// Adding new custom icons to a RibbonBar using the string source
var svgContent = "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"16\" height=\"16\" viewBox=\"0 0 16 16\">" +
 "<title>Clock_1</title>" +
 "<g id=\"GUIicons\">" +
 "<g id=\"Clock\">" +
 "<g>" +
   "<circle cx=\"8\" cy=\"8\" r=\"7.5\" style=\"fill: #fff\"/>" +
   "<path d=\"M8,1A7,7,0,1,1,1,8,7,7,0,0,1,8,1M8,0a8,8,0,1,0,8,8A8,8,0,0,0,8,0Z\" style=\"fill: #4a7db1\"/>" +
 "<g>" +
   "<path d=\"M12,8.5H8v-1h4ZM7.5,4V7h1V4Z\" style=\"fill:#9e0b0f\"/>" +
 "<g>" +
   "<rect x=\"13.5\" y=\"7\" width=\"1\" height=\"2\"transform=\"translate(22 -6) rotate(90)\" style=\"fill: #505050\"/>" +
   "<rect x=\"7.5\" y=\"13\" width=\"1\" height=\"2\"transform=\"translate(16 28) rotate(-180)\" style=\"fill: #505050\"/>" +
   "<rect x=\"1.5\" y=\"7\" width=\"1\" height=\"2\"transform=\"translate(-6 10) rotate(-90)\" style=\"fill: #505050\"/>" +
   "<rect x=\"7.5\" y=\"1\" width=\"1\" height=\"2\"style=\"fill: #505050\"/>" +
 "</g>" +
   "<circle cx=\"8\" cy=\"8\" r=\"1\" style=\"fill:#4a7db1;stroke: #9e0b0f;stroke-miterlimit: 10;stroke-width: 0.5px\"/>" +
 "</g>" +
 "</g>" +
 "</svg>";

commandGroup = tab.AddCommandGroup("AddIcon using source");
ribbonIcon = ribbonBar.AddIcon(svgContent);
commandGroup.AddCommand("Button13", "action13", ribbonIcon);
```
```csharp
// Adding new commands using the RibbonCommandInfo
commandGroup = tab.AddCommandGroup("commands with RibbonCommandInfo");
RibbonCommandInfo ribbonCommandInfo = new RibbonCommandInfo("buttonText", "actionCommandLine");
commandGroup.AddCommand(ribbonCommandInfo);
```
```csharp
// Adding an existing EPLAN command action by its ID
const int commandId = 35089;
var tab = ribbonBar.AddTab("CustomTab");
var commandGroup = tab.AddCommandGroup("Group1");
var commandAction = commandGroup.AddCommandWithId(commandId);
```

---

## SegmentDefinition
*Źródło: `SegmentDefinition.html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / API Pre-planning / SegmentDefinition*

SegmentDefinition The SegmentDefinition class represents segment definition objects. 
They define the behavior and properties of a segment. 

### C# 
### Copy Code 
| SegmentDefinition oSegmentDefinition =
new
SegmentDefinition();
oSegmentDefinition.Create(
"test_001"
, m_oTestProject.SegmentDefinitions[0]);

In the GUI, they are visible in the Segment templates navigator:

### Przykłady kodu (C#)
```csharp
SegmentDefinition oSegmentDefinition = new SegmentDefinition();
oSegmentDefinition.Create("test_001", m_oTestProject.SegmentDefinitions[0]);
```

---

## SegmentPlacement
*Źródło: `SegmentPlacement.html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / API Pre-planning / SegmentPlacement*

SegmentPlacement The SegmentPlacement class represents segment objects on a 2D page. Because of this, the class inherits from SymbolReference . 

### C# 
### Copy Code 
| // Prepare a segment
StructureSegment oStructureSegment = StructureSegment.Create(m_oTestProject.SegmentDefinitions[0])
as
StructureSegment;
oStructureSegment.Name =
"test1c"
;
// Prepare a page
Page oNewPage =
new
Page(m_oTestProject, DocumentTypeManager.DocumentType.Planning,
new
PagePropertyList());
oNewPage.Name =
"SegmentPlacement_Test001c"
;
// Create SegmentPlacement
SegmentPlacement oSegmentPlacement =
new
SegmentPlacement();
oSegmentPlacement.Create(oStructureSegment, oNewPage);

SegmentPlacements are visible in the GED, for example:

### Przykłady kodu (C#)
```csharp
// Prepare a segment
StructureSegment oStructureSegment = StructureSegment.Create(m_oTestProject.SegmentDefinitions[0]) as StructureSegment;
oStructureSegment.Name = "test1c";

// Prepare a page
Page oNewPage = new Page(m_oTestProject, DocumentTypeManager.DocumentType.Planning, new PagePropertyList());
oNewPage.Name = "SegmentPlacement_Test001c";
          
// Create SegmentPlacement
SegmentPlacement oSegmentPlacement = new SegmentPlacement();
oSegmentPlacement.Create(oStructureSegment, oNewPage);
```

---

## SegmentTemplate
*Źródło: `SegmentTemplate.html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / API Pre-planning / SegmentTemplate*

SegmentTemplate The SegmentTemplate class represents segment template objects. They contain common values of some properties. 
The Segment inherits these values from a template. 

### C# 
### Copy Code 
| SegmentTemplate oSegmentTemplate =
new
SegmentTemplate();
oSegmentTemplate.Create(oSegmentDefinition);
oSegmentTemplate.Name =
"SegmentTemplate_006"
;

In the GUI, they are visible in the Segment templates navigator:

### Przykłady kodu (C#)
```csharp
SegmentTemplate oSegmentTemplate = new SegmentTemplate();
oSegmentTemplate.Create(oSegmentDefinition);
oSegmentTemplate.Name = "SegmentTemplate_006";
```

---

## Structure
*Źródło: `Structure.html`*
*Ścieżka: EPLAN API / User Guide / API Framework / Add-ons / Structure*

Structure ### The folder structure 
Every add-on has the same folder structure. The folder names are marked with <> when names are optional and can be changed by the add-on developer. 
Note: 
This add-on folder can exist anywhere on the disk! 
An add-on always consists of the same folder structure, which basically looks like this: 
<Add-on> 
<Add-on version> 
BIN Here, all binaries of the add-on are installed. 
CFG Here, all XML files and the install.xml are installed. The install.xml file is the base data. 
The names of the folders are listed in the install.xml for copying the data to the EPLAN base data. 
<Images> 
<Scripts> 
<XML> 
<…> 
### The files 
The most important file is the install.xml . It contains all the information about the add-on and the EPLAN version. 
This paragraph shows an install.xml file example, which is created with the EplAddonUtility.exe . 
Tip: 
For further information, about how to create an add-on with the EplAddonUtility.exe and which terms and conditions you should follow, see the " EplAddonUtility" documentation. 

### XML 
### Copy Code 
| <
Settings
format
="2"
>
<
CAT
name
="INSTALL"
>
<
MOD
name
="AF"
>
<!
—The application modifier is the unique identifier for this add-on. Either spaces or dots are allowed. Otherwise, the registration is not possible then. --
>
<
Setting
name
="ApplicationModifier"
type
="string"
info
="Name modification for specific application configuration"
>
<
Val
>
MyAddon
</
Val
>
</
Setting
>
</
MOD
>
</
CAT
>
<
CAT
name
="STATION"
>
<
MOD
name
="SYSTEM"
>
<
LEV1
name
="MyAddon"
>
<!
—This is the path to the xml file. This setting is patched by the installer --
>
<
Setting
name
="XMLPath"
type
="string"
info
="patched path to install.xml"
>
<
Val
>
C:\Users\ Username \Desktop\MyAddon\CFG\
</
Val
>
</
Setting
>
<!
—This is the version of the add-on this setting is patched by the installer. --
>
<
Setting
name
="Version"
type
="string"
info
="version nr of this addon"
>
<
Val
>
1.0.0
</
Val
>
</
Setting
>
<!
—This node describe the main versions, this add-on belongsto.. --
>
<
LEV2
name
="MainVersion"
>
<
LEV3
name
="Basic"
>
<!
—This setting is the license identifier for the main version. All these licences MUST be available, only then this add-on will be registered --
>
<
Setting
name
="Licences"
type
="string"
info
="Licence of Main Product to identify it"
>
<
Val
>
700
</
Val
>
</
Setting
>
<!
—This setting is the version identifier for the main version. By multiple versions, ONE of this licenc-es MUST be identical to the main version number, then this add-on is registered. --
>
<
Setting
name
="Versions"
type
="string"
info
="Version of Main Product to identify it"
>
<
Val
>
2.9.0
</
Val
>
</
Setting
>
</
LEV3
>
<
LEV3
name
="FLUID"
>
<
Setting
name
="Licences"
type
="string"
info
="Licence of Main Product to identify it"
>
<
Val
>
703
</
Val
>
</
Setting
>
<
Setting
name
="Versions"
type
="string"
info
="Version of Main Product to identify it"
>
<
Val
>
2.9.0
</
Val
>
</
Setting
>
</
LEV3
>
<
LEV3
name
="VIEWER"
>
<
Setting
name
="Licences"
type
="string"
info
="Licence of Main Product to identify it"
>
<
Val
>
701
</
Val
>
</
Setting
>
<
Setting
name
="Versions"
type
="string"
info
="Version of Main Product to identify it"
>
<
Val
>
2.9.0
</
Val
>
</
Setting
>
</
LEV3
>
<
LEV3
name
="EDUCATION"
>
<
Setting
name
="Licences"
type
="string"
info
="Licence of Main Product to identify it"
>
<
Val
>
790
</
Val
>
</
Setting
>
<
Setting
name
="Versions"
type
="string"
info
="Version of Main Product to identify it"
>
<
Val
>
2.9.0
</
Val
>
</
Setting
>
</
LEV3
>
<
LEV3
name
="CPM"
>
<
Setting
name
="Licences"
type
="string"
info
="Licence of Main Product to identify it"
>
<
Val
>
786
</
Val
>
</
Setting
>
<
Setting
name
="Versions"
type
="string"
info
="Version of Main Product to identify it"
>
<
Val
>
2.9.0
</
Val
>
</
Setting
>
</
LEV3
>
<
LEV3
name
="TRIAL"
>
<
Setting
name
="Licences"
type
="string"
info
="Licence of Main Product to identify it"
>
<
Val
>
702
</
Val
>
</
Setting
>
<
Setting
name
="Versions"
type
="string"
info
="Version of Main Product to identify it"
>
<
Val
>
2.9.0
</
Val
>
</
Setting
>
</
LEV3
>
<
LEV3
name
="Preplanning"
>
<
Setting
name
="Licences"
type
="string"
info
="Licence of Main Product to identify it"
>
<
Val
>
1132
</
Val
>
</
Setting
>
<
Setting
name
="Versions"
type
="string"
info
="Version of Main Product to identify it"
>
<
Val
>
2.9.0
</
Val
>
</
Setting
>
</
LEV3
>
<
LEV3
name
="FluidHoseConfigurator"
>
<
Setting
name
="Licences"
type
="string"
info
="Licence of Main Product to identify it"
>
<
Val
>
1192
</
Val
>
</
Setting
>
<
Setting
name
="Versions"
type
="string"
info
="Version of Main Product to identify it"
>
<
Val
>
2.9.0
</
Val
>
</
Setting
>
</
LEV3
>
<
LEV3
name
="ProPanel"
>
<
Setting
name
="Licences"
type
="string"
info
="Licence of Main Product to identify it"
>
<
Val
>
565
</
Val
>
</
Setting
>
<
Setting
name
="Versions"
type
="string"
info
="Version of Main Product to identify it"
>
<
Val
>
2.9.0
</
Val
>
</
Setting
>
</
LEV3
>
</
LEV2
>
</
LEV1
>
<!
—Now the base data the add-on has will be copied to the EPLAN base data. Define as many pathes as possible. --
>
<
LEV1
name
="Basedata"
>
<
LEV2
name
="MyAddon"
>
<!
—Copy all files behind this setting pathes to pathes for master data… --
>
<
Setting
name
="CopyTo"
type
="string"
info
="copy-to pathes for masterData"
>
<
Val
>
USER.TrDMProject.Masterdata.Pathnames..Projects
</
Val
>
<
Val
>
USER.TrDMProject.Masterdata.Pathnames..Templates
</
Val
>
<
Val
>
USER.TrDMProject.Masterdata.Pathnames..Symbols
</
Val
>
<
Val
>
USER.TrDMProject.Masterdata.Pathnames..Forms
</
Val
>
<
Val
>
USER.TrDMProject.Masterdata.Pathnames..Frames
</
Val
>
<
Val
>
USER.TrDMProject.Masterdata.Pathnames..FctDefs
</
Val
>
<
Val
>
USER.TrDMProject.Masterdata.Pathnames..Revisions
</
Val
>
<
Val
>
USER.TrDMProject.Masterdata.Pathnames..Images
</
Val
>
<
Val
>
USER.TrDMProject.Masterdata.Pathnames..DXFDWG
</
Val
>
<
Val
>
USER.TrDMProject.Masterdata.Pathnames..MechanicalModels
</
Val
>
<
Val
>
USER.SYSTEM.Pathnames..ExternalDocuments
</
Val
>
<
Val
>
USER.SYSTEM.Pathnames..Scheme
</
Val
>
</
Setting
>
</
LEV2
>
<!
—…from pathes for master data. The count of the settings of “CopyTo” and “CopyFrom” has to be identical. --
>
<
Setting
name
="CopyFrom"
type
="string"
info
="copy-from pathes for masterData"
>
<
Val
>
USER.TrDMProject.Masterdata.Pathnames.MyAddon.Projects
</
Val
>
<
Val
>
USER.TrDMProject.Masterdata.Pathnames.MyAddon.Templates
</
Val
>
<
Val
>
USER.TrDMProject.Masterdata.Pathnames.MyAddon.Symbols
</
Val
>
<
Val
>
USER.TrDMProject.Masterdata.Pathnames.MyAddon.Forms
</
Val
>
<
Val
>
USER.TrDMProject.Masterdata.Pathnames.MyAddon.Frames
</
Val
>
<
Val
>
USER.TrDMProject.Masterdata.Pathnames.MyAddon.FctDefs
</
Val
>
<
Val
>
USER.TrDMProject.Masterdata.Pathnames.MyAddon.Macros
</
Val
>
<
Val
>
USER.TrDMProject.Masterdata.Pathnames.MyAddon.Images
</
Val
>
<
Val
>
USER.TrDMProject.Masterdata.Pathnames.MyAddon.DXFDWG
</
Val
>
<
Val
>
USER.TrDMProject.Masterdata.Pathnames.MyAddon.MechanicalModels
</
Val
>
<
Val
>
USER.SYSTEM.Pathnames.MyAddon.ExternalDocuments
</
Val
>
<
Val
>
USER.SYSTEM.Pathnames.MyAddon.Scheme
</
Val
>
</
Setting
>
</
LEV1
>
</
MOD
>
</
CAT
>
<
CAT
name
="USER"
>
<
MOD
name
="TrDMProject"
>
<
LEV1
name
="Masterdata"
>
<
LEV2
name
="Pathnames"
>
<
LEV3
name
="MyAddon"
>
<
Setting
name
="Projects"
type
="string"
info
="file path to masterData"
>
<
Val
>
C:\Users\ Username \Desktop\MyAddon\CFG\MyAddon\Projects
</
Val
>
</
Setting
>
<
Setting
name
="Templates"
type
="string"
info
="file path to masterData"
>
<
Val
>
C:\Users\ Username \Desktop\MyAddon\CFG\MyAddon\Templates
</
Val
>
</
Setting
>
<
Setting
name
="Symbols"
type
="string"
info
="file path to masterData"
>
<
Val
>
C:\Users\ Username \Desktop\MyAddon\CFG\MyAddon\Symbols
</
Val
>
</
Setting
>
<
Setting
name
="Forms"
type
="string"
info
="file path to masterData"
>
<
Val
>
C:\Users\ Username \Desktop\MyAddon\CFG\MyAddon\Forms
</
Val
>
</
Setting
>
<
Setting
name
="Frames"
type
="string"
info
="file path to masterData"
>
<
Val
>
C:\Users\ Username \Desktop\MyAddon\CFG\MyAddon\PlotFrames
</
Val
>
</
Setting
>
<
Setting
name
="FctDefs"
type
="string"
info
="file path to masterData"
>
<
Val
>
C:\Users\ Username \Desktop\MyAddon\CFG\MyAddon\FunctionDefinition
</
Val
>
</
Setting
>
<
Setting
name
="Macros"
type
="string"
info
="file path to masterData"
>
<
Val
>
C:\Users\ Username \Desktop\MyAddon\CFG\MyAddon\Macros
</
Val
>
</
Setting
>
<
Setting
name
="Images"
type
="string"
info
="file path to masterData"
>
<
Val
>
C:\Users\ Username \Desktop\MyAddon\CFG\MyAddon\Images
</
Val
>
</
Setting
>
<
Setting
name
="DXFDWG"
type
="string"
info
="file path to masterData"
>
<
Val
>
C:\Users\ Username \Desktop\MyAddon\CFG\MyAddon\DXF_DWG
</
Val
>
</
Setting
>
<
Setting
name
="MechanicalModels"
type
="string"
info
="file path to masterData"
>
<
Val
>
C:\Users\ Username \Desktop\MyAddon\CFG\MyAddon\Mechanical models
</
Val
>
</
Setting
>
<
Setting
name
="Scripts"
type
="string"
info
="file path to masterData"
>
<
Val
>
C:\Users\ Username \Desktop\MyAddon\CFG\MyAddon\Documents
</
Val
>
</
Setting
>
<
Setting
name
="Scheme"
type
="string"
info
="file path to masterData"
>
<
Val
>
C:\Users\Username\Desktop\MyAddon\CFG\MyAddon\Schemes
</
Val
>
</
Setting
>
</
LEV3
>
</
LEV2
>
</
LEV1
>
</
MOD
>
<
MOD
name
="System"
>
<
LEV1
name
="Pathnames"
>
<
LEV2
name
="MyAddon"
/>
</
LEV1
>
</
MOD
>
</
CAT
>
</
Settings
>

### Information about the settings 
ApplicationModifier : 
The identifier for this add-on. This has to be a unique name without blanks and dots. 
XMLPath : 
Location of CFG folder of add-on 
Version : 
This is the version number of the add-on. 
MainVersion : 
One sub-node belongs to one EPLAN version. The Basic node contains the licence information and version information for EPLAN Electric P8. 
Licences : 
Add-on program validity. All of the licences must be available, so this add-on can be registered for this main version. 
Versions : 
Add-on version validity. One of the version numbers must match the EPLAN version number, so this add-on can be registered. The version number can contain a * as a wildcard. This is interpreted as "any". 
### The API add-ins 
It is possible to list the API add-ins in an XML file with any name. 

### XML 
### Copy Code 
| <
Settings
format
="2"
>
<
CAT
name
="STATION"
>
<
MOD
name
="AF"
>
<
LEV1
name
="ApiModules"
>
<
Setting
name
="MyAddon"
type
="string"
info
=""
>
<
Val
>
Eplan.EplAddin.Addin_2_8
</
Val
>
</
Setting
>
</
LEV1
>
</
MOD
>
</
CAT
>
</
Settings
>

All API modules in the setting ApiModules are registered and loaded. 
When an API add-in has a linked DLL in the add-on binary path, the DLL should be registered as a reference. This is the list in " API Reference ". Then EPLAN will always be able to resolve this API add-in. 
### The Scripts 
If a script is to be registered when the add-on is registered, an XML file must have a content similar to this: 

### XML 
### Copy Code 
| <
Settings
format
="2"
>
<
CAT
name
="STATION"
>
<
MOD
name
="AF"
>
<
LEV1
name
="Scripts"
>
<
Setting
name
="MyAddon"
type
="string"
info
=""
>
<
Val
>
BIN\myScript.cs
</
Val
>
</
Setting
>
</
LEV1
>
</
MOD
>
</
CAT
>
</
Settings
>

The script file location is either an absolute path or a relative one. The relative path is calculated from the add-on path, where the BIN folder and the CFG folder is in. 
### Ribbons 
With the version 2022, it is possible to import a ribbon bar or rather ribbon tabs with their children (see: EPLAN API / User Guide / API Miscellaneous / Ribbon Bar for more information) when the add-on is registered. 

### XML 
### Copy Code 
| <
Settings
format
="2"
>
<
CAT
name
="USER"
>
<
MOD
name
="AF"
>
<
LEV1
name
="Ribbon"
>
<
Setting
name
="Ribbonbartest"
type
="string"
info
=""
>
<
Val
>
CFG\myRibbonTab.xml
</
Val
>
</
Setting
>
</
LEV1
>
</
MOD
>
</
CAT
>
</
Settings
>

The custom ribbon tab is imported from the XML file when the add-on is registered. The user can remove the ribbon tab by customizing the ribbon (i.e. when the user changes his workspace). Unregistering the add-on will also remove the ribbon tab.

### Przykłady kodu (C#)
```csharp
<Settings format="2">
  <CAT name="INSTALL">
    <MOD name="AF">
<!—The application modifier is the unique identifier for this add-on. Either spaces or dots are allowed. Otherwise, the registration is not possible then. -->
      <Setting name="ApplicationModifier" type="string" info="Name modification for specific application configuration">
        <Val>MyAddon</Val>
      </Setting>
    </MOD>
  </CAT>
  <CAT name="STATION">
    <MOD name="SYSTEM">
      <LEV1 name="MyAddon">
<!—This is the path to the xml file. This setting is patched by the installer -->
        <Setting name="XMLPath" type="string" info="patched path to install.xml">
          <Val>C:\Users\ Username \Desktop\MyAddon\CFG\</Val>
        </Setting>
<!—This is the version of the add-on this setting is patched by the installer. -->
        <Setting name="Version" type="string" info="version nr of this addon">
          <Val>1.0.0</Val>
        </Setting>
<!—This node describe the main versions, this add-on belongsto.. -->
        <LEV2 name="MainVersion">
          <LEV3 name="Basic">
<!—This setting is the license identifier for the main version. All these licences MUST be available, only then this add-on will be registered -->
            <Setting name="Licences" type="string" info="Licence of Main Product to identify it">
              <Val>700</Val>
            </Setting>
<!—This setting is the version identifier for the main version. By multiple versions, ONE of this licenc-es MUST be identical to the main version number, then this add-on is registered. -->
            <Setting name="Versions" type="string" info="Version of Main Product to identify it">
              <Val>2.9.0</Val>
            </Setting>
          </LEV3>
          <LEV3 name="FLUID">
            <Setting name="Licences" type="string" info="Licence of Main Product to identify it">
              <Val>703</Val>
            </Setting>
            <Setting name="Versions" type="string" info="Version of Main Product to identify it">
              <Val>2.9.0</Val>
            </Setting>
          </LEV3>
          <LEV3 name="VIEWER">
            <Setting name="Licences" type="string" info="Licence of Main Product to identify it">
              <Val>701</Val>
            </Setting>
            <Setting name="Versions" type="string" info="Version of Main Product to identify it">
              <Val>2.9.0</Val>
            </Setting>
          </LEV3>
          <LEV3 name="EDUCATION">
            <Setting name="Licences" type="string" info="Licence of Main Product to identify it">
              <Val>790</Val>
            </Setting>
            <Setting name="Versions" type="string" info="Version of Main Product to identify it">
              <Val>2.9.0</Val>
            </Setting>
          </LEV3>
          <LEV3 name="CPM">
            <Setting name="Licences" type="string" info="Licence of Main Product to identify it">
              <Val>786</Val>
            </Setting>
            <Setting name="Versions" type="string" info="Version of Main Product to identify it">
              <Val>2.9.0</Val>
            </Setting>
          </LEV3>
          <LEV3 name="TRIAL">
            <Setting name="Licences" type="string" info="Licence of Main Product to identify it">
              <Val>702</Val>
            </Setting>
            <Setting name="Versions" type="string" info="Version of Main Product to identify it">
              <Val>2.9.0</Val>
            </Setting>
          </LEV3>
          <LEV3 name="Preplanning">
            <Setting name="Licences" type="string" info="Licence of Main Product to identify it">
              <Val>1132</Val>
            </Setting>
            <Setting name="Versions" type="string" info="Version of Main Product to identify it">
              <Val>2.9.0</Val>
            </Setting>
          </LEV3>
          <LEV3 name="FluidHoseConfigurator">
            <Setting name="Licences" type="string" info="Licence of Main Product to identify it">
              <Val>1192</Val>
            </Setting>
            <Setting name="Versions" type="string" info="Version of Main Product to identify it">
              <Val>2.9.0</Val>
            </Setting>
          </LEV3>
          <LEV3 name="ProPanel">
            <Setting name="Licences" type="string" info="Licence of Main Product to identify it">
              <Val>565</Val>
            </Setting>
            <Setting name="Versions" type="string" info="Version of Main Product to identify it">
              <Val>2.9.0</Val>
            </Setting>
          </LEV3>
        </LEV2>
      </LEV1>
<!—Now the base data the add-on has will be copied to the EPLAN base data. Define as many pathes as possible. -->
      <LEV1 name="Basedata">
        <LEV2 name="MyAddon">
<!—Copy all files behind this setting pathes to pathes for master data… -->
          <Setting name="CopyTo" type="string" info="copy-to pathes for masterData">
            <Val>USER.TrDMProject.Masterdata.Pathnames..Projects</Val>
            <Val>USER.TrDMProject.Masterdata.Pathnames..Templates</Val>
            <Val>USER.TrDMProject.Masterdata.Pathnames..Symbols</Val>
            <Val>USER.TrDMProject.Masterdata.Pathnames..Forms</Val>
            <Val>USER.TrDMProject.Masterdata.Pathnames..Frames</Val>
            <Val>USER.TrDMProject.Masterdata.Pathnames..FctDefs</Val>
            <Val>USER.TrDMProject.Masterdata.Pathnames..Revisions</Val>
            <Val>USER.TrDMProject.Masterdata.Pathnames..Images</Val>
            <Val>USER.TrDMProject.Masterdata.Pathnames..DXFDWG</Val>
            <Val>USER.TrDMProject.Masterdata.Pathnames..MechanicalModels</Val>
            <Val>USER.SYSTEM.Pathnames..ExternalDocuments</Val>
            <Val>USER.SYSTEM.Pathnames..Scheme</Val>
          </Setting>
        </LEV2>
<!—…from pathes for master data. The count of the settings of “CopyTo” and “CopyFrom” has to be identical. -->
        <Setting name="CopyFrom" type="string" info="copy-from pathes for masterData">
          <Val>USER.TrDMProject.Masterdata.Pathnames.MyAddon.Projects</Val>
          <Val>USER.TrDMProject.Masterdata.Pathnames.MyAddon.Templates</Val>
          <Val>USER.TrDMProject.Masterdata.Pathnames.MyAddon.Symbols</Val>
          <Val>USER.TrDMProject.Masterdata.Pathnames.MyAddon.Forms</Val>
          <Val>USER.TrDMProject.Masterdata.Pathnames.MyAddon.Frames</Val>
          <Val>USER.TrDMProject.Masterdata.Pathnames.MyAddon.FctDefs</Val>
          <Val>USER.TrDMProject.Masterdata.Pathnames.MyAddon.Macros</Val>
          <Val>USER.TrDMProject.Masterdata.Pathnames.MyAddon.Images</Val>
          <Val>USER.TrDMProject.Masterdata.Pathnames.MyAddon.DXFDWG</Val>
          <Val>USER.TrDMProject.Masterdata.Pathnames.MyAddon.MechanicalModels</Val>
          <Val>USER.SYSTEM.Pathnames.MyAddon.ExternalDocuments</Val>
          <Val>USER.SYSTEM.Pathnames.MyAddon.Scheme</Val>
        </Setting>
      </LEV1>
    </MOD>
  </CAT>
  <CAT name="USER">
    <MOD name="TrDMProject">
      <LEV1 name="Masterdata">
        <LEV2 name="Pathnames">
          <LEV3 name="MyAddon">
            <Setting name="Projects" type="string" info="file path to masterData">
              <Val>C:\Users\ Username \Desktop\MyAddon\CFG\MyAddon\Projects</Val>
            </Setting>
            <Setting name="Templates" type="string" info="file path to masterData">
              <Val>C:\Users\ Username \Desktop\MyAddon\CFG\MyAddon\Templates</Val>
            </Setting>
            <Setting name="Symbols" type="string" info="file path to masterData">
              <Val>C:\Users\ Username \Desktop\MyAddon\CFG\MyAddon\Symbols</Val>
            </Setting>
            <Setting name="Forms" type="string" info="file path to masterData">
              <Val>C:\Users\ Username \Desktop\MyAddon\CFG\MyAddon\Forms</Val>
            </Setting>
            <Setting name="Frames" type="string" info="file path to masterData">
              <Val>C:\Users\ Username \Desktop\MyAddon\CFG\MyAddon\PlotFrames</Val>
            </Setting>
            <Setting name="FctDefs" type="string" info="file path to masterData">
              <Val>C:\Users\ Username \Desktop\MyAddon\CFG\MyAddon\FunctionDefinition</Val>
            </Setting>
            <Setting name="Macros" type="string" info="file path to masterData">
              <Val>C:\Users\ Username \Desktop\MyAddon\CFG\MyAddon\Macros</Val>
            </Setting>
            <Setting name="Images" type="string" info="file path to masterData">
              <Val>C:\Users\ Username \Desktop\MyAddon\CFG\MyAddon\Images</Val>
            </Setting>
            <Setting name="DXFDWG" type="string" info="file path to masterData">
              <Val>C:\Users\ Username \Desktop\MyAddon\CFG\MyAddon\DXF_DWG</Val>
            </Setting>
            <Setting name="MechanicalModels" type="string" info="file path to masterData">
              <Val>C:\Users\ Username \Desktop\MyAddon\CFG\MyAddon\Mechanical models</Val>
            </Setting>
            <Setting name="Scripts" type="string" info="file path to masterData">
              <Val>C:\Users\ Username \Desktop\MyAddon\CFG\MyAddon\Documents</Val>
            </Setting>
            <Setting name="Scheme" type="string" info="file path to masterData">
              <Val>C:\Users\Username\Desktop\MyAddon\CFG\MyAddon\Schemes</Val>
            </Setting>
          </LEV3>
        </LEV2>
      </LEV1>
    </MOD>
    <MOD name="System">
      <LEV1 name="Pathnames">
        <LEV2 name="MyAddon" />
      </LEV1>
    </MOD>
  </CAT>
</Settings>
```
```csharp
<Settings format="2">
  <CAT name="STATION">
    <MOD name="AF">
      <LEV1 name="ApiModules">
        <Setting name="MyAddon" type="string" info="">
          <Val>Eplan.EplAddin.Addin_2_8</Val>
        </Setting>
      </LEV1>
    </MOD>
  </CAT>
</Settings>
```
```csharp
<Settings format="2">
  <CAT name="STATION">
    <MOD name="AF">
      <LEV1 name="Scripts">
        <Setting name="MyAddon" type="string" info="">
          <Val>BIN\myScript.cs</Val>
        </Setting>
      </LEV1>
    </MOD>
  </CAT>
</Settings>
```
```csharp
<Settings format="2">
  <CAT name="USER">
    <MOD name="AF">
      <LEV1 name="Ribbon">
        <Setting name="Ribbonbartest" type="string" info="">
          <Val>CFG\myRibbonTab.xml</Val>
        </Setting>
      </LEV1>
    </MOD>
  </CAT>
</Settings>
```

---

## StructureSegment
*Źródło: `StructureSegment.html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / API Pre-planning / StructureSegment*

StructureSegment The StructureSegment class represents structure segment objects. They are used to represent a part of the project structure. 

### C# 
### Copy Code 
| SegmentDefinition oSegmentDefinition = m_oTestProject.GetSegmentDefinition(
"Eplan.Base.StructureNode"
);
StructureSegment oStructureSegment = StructureSegment.Create(m_oTestProject.SegmentDefinitions[0])
as
StructureSegment;
oStructureSegment.Name =
"test1b"
;

In the GUI, they are visible in Pre-planning navigator:

### Przykłady kodu (C#)
```csharp
SegmentDefinition oSegmentDefinition = m_oTestProject.GetSegmentDefinition("Eplan.Base.StructureNode");
StructureSegment oStructureSegment = StructureSegment.Create(m_oTestProject.SegmentDefinitions[0]) as StructureSegment;
oStructureSegment.Name = "test1b";
```

---

## Throwing and catching exceptions
*Źródło: `Throwing and catching exceptions.html`*
*Ścieżka: EPLAN API / User Guide / API Miscellaneous / Throwing and catching exceptions*

Throwing and catching exceptions Error handling in EPLAN is preferably done using exceptions. The API framework provides the BaseException base class that provides you access to the error handling of EPLAN. 
If an e xception object of this type is thrown, the EPLAN framework catches the exception and writes the data to the system error management or shows the error message in the EPLAN error dialog. 
- C# 
- VB Eplan.EplApi.Base.BaseException exc2=
new
Eplan.EplApi.Base.BaseException(
"Error from CSharpAction thrown as exception"
,
Eplan.EplApi.Base.MessageLevel.Error);
throw
exc2;
Dim
exc2
As
New
Eplan.EplApi.Base.BaseException(
"Error from VBAction thrown as exception"
, _
Eplan.EplApi.Base.MessageLevel.Error)
Throw
exc2

Of course, you can also catch exceptions in your API application and evaluate them, e.g. to display your own error message. 
- C# 
- VB // Test wrong settings name (throws BaseException that is handled here)
try
{
String strGuiLanguage= Settings.GetStringSetting(
"USER.SYSEM.GUI.LANGUAGE"
, 0);
new
Decider().Decide(EnumDecisionType.eOkDecision,
"The current GUI language is: "
+ strGuiLanguage,
""
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
}
catch
(BaseException exc)
{
String strMessage= exc.Message;
new
Decider().Decide(EnumDecisionType.eOkDecision,
"Exception: "
+ strMessage,
""
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
}
' Test wrong settings name (throws BaseException that is handled here)
Dim
dec
As
Decider =
New
Decider
Try
Dim
strGuiLanguage
As
String
= Settings.GetStringSetting(
"USER.SYSEM.GUI.LANGUAGE"
, 0)
dec.Decide(EnumDecisionType.eOkDecision,
"The current GUI language is: "
+ strGuiLanguage,
""
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)
Catch
exc
As
BaseException
Dim
strMessage
As
String
= exc.Message
dec.Decide(EnumDecisionType.eOkDecision,
"Exception: "
+ strMessage,
""
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)
End
Try

### Przykłady kodu (C#)
```csharp
Eplan.EplApi.Base.BaseException exc2= new Eplan.EplApi.Base.BaseException(
                                                "Error from CSharpAction thrown as exception",
                                                Eplan.EplApi.Base.MessageLevel.Error);

throw exc2;
```
```csharp
Dim exc2 As New Eplan.EplApi.Base.BaseException("Error from VBAction thrown as exception", _
                                                  Eplan.EplApi.Base.MessageLevel.Error)
Throw exc2
```
```csharp
// Test wrong settings name (throws BaseException that is handled here)
try
{
    String strGuiLanguage= Settings.GetStringSetting("USER.SYSEM.GUI.LANGUAGE", 0);
    new Decider().Decide(EnumDecisionType.eOkDecision, "The current GUI language is: "+ strGuiLanguage, "", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
}
catch (BaseException exc)
{
    String strMessage= exc.Message;
    new Decider().Decide(EnumDecisionType.eOkDecision, "Exception: " + strMessage, "", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
}
```
```csharp
' Test wrong settings name (throws BaseException that is handled here)
Dim dec As Decider = New Decider
Try
   Dim strGuiLanguage As String = Settings.GetStringSetting("USER.SYSEM.GUI.LANGUAGE", 0)
   dec.Decide(EnumDecisionType.eOkDecision, "The current GUI language is: "+  strGuiLanguage, "", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)
Catch exc As BaseException
   Dim strMessage As String = exc.Message
   dec.Decide(EnumDecisionType.eOkDecision, "Exception: " + strMessage, "", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)
End Try
```

---

## Trace output
*Źródło: `Trace output.html`*
*Ścieżka: EPLAN API / User Guide / API Miscellaneous / Trace output*

Trace output For debugging purposes (or program logging in the release version) it is useful to log messages to a trace listener. The API framework provides a TraceListener class for this purpose. 
In your API program, you simply add your own trace listener to the System.Diagnostics.Trace.Listeners : 
- C# 
- VB private
Eplan.EplApi.Base.TraceListener m_oTrace;
//.
//.
//.
m_oTrace=
new
Eplan.EplApi.Base.TraceListener();
//.
//.
//.
public
bool
Execute(ActionCallingContext ctx )
{
System.Diagnostics.Trace.Listeners.Add(m_oTrace);
System.Diagnostics.Trace.WriteLine(
" Begin Execute "
);
//.
//.
}
Dim
m_oTrace
As
Eplan.EplApi.Base.TraceListener
'...
m_oTrace=
New
Eplan.EplApi.Base.TraceListener()
Public
Function
Execute(
ByVal
ctx
as
ActionCallingContext)
as
Boolean
Implements
IEplAction.Execute
System.Diagnostics.Trace.Listeners.Add(m_oTrace)
System.Diagnostics.Trace.WriteLine(
" Begin Execute "
)
'...
'...

As a result, all further trace outputs are visible in the Windows trace management and – as the case may be – written to the EPLAN log database at the end of the program. 
TRACE: .\Actions\AfCommandLineInterpreter.cpp(18) : AfCommandLineInterpreter::execute: CSharpAction
TRACE: .\Actions\AfAction.cpp(123) : Execute Action: URCheckRightsForAction
TRACE: .\Actions\AfAction.cpp(123) : Execute Action: CSharpAction
TRACE: u:\eplanw3_1.0_vc7.1\eplan\extensions\api_demosfue\v_1.0\eplan.w3addin.demo1\csharpaction.cs(24) : Begin Execute

### Przykłady kodu (C#)
```csharp
private Eplan.EplApi.Base.TraceListener m_oTrace;
//.
//.
//.
    m_oTrace= new Eplan.EplApi.Base.TraceListener();
//.
//.
//.
public bool Execute(ActionCallingContext ctx )
{
    System.Diagnostics.Trace.Listeners.Add(m_oTrace);
    System.Diagnostics.Trace.WriteLine(" Begin Execute ");
//.
//.
}
```
```csharp
Dim m_oTrace As Eplan.EplApi.Base.TraceListener
'...
   m_oTrace= New Eplan.EplApi.Base.TraceListener()
Public Function Execute(ByVal ctx as ActionCallingContext)as Boolean Implements IEplAction.Execute
    System.Diagnostics.Trace.Listeners.Add(m_oTrace)
    System.Diagnostics.Trace.WriteLine(" Begin Execute ")
'...
'...
```
```csharp
TRACE: .\Actions\AfCommandLineInterpreter.cpp(18) : AfCommandLineInterpreter::execute: CSharpAction
TRACE: .\Actions\AfAction.cpp(123) : Execute Action: URCheckRightsForAction
TRACE: .\Actions\AfAction.cpp(123) : Execute Action: CSharpAction
TRACE: u:\eplanw3_1.0_vc7.1\eplan\extensions\api_demosfue\v_1.0\eplan.w3addin.demo1\csharpaction.cs(24) : Begin Execute
```

---

## Using EPLAN in other applications
*Źródło: `Using EPLAN in other applications.html`*
*Ścieżka: EPLAN API / User Guide / API Framework / Using EPLAN in other applications*

Using EPLAN in other applications This topic describes various options for using EPLAN functions outside of  a script or an EPLAN add-in. 

Basically, there are three options to use EPLAN functionality in other applications: 

- Calling EPLAN with command line parameters 
- Using parts of EPLAN (modules/DLLs) in other processes. Only the functionality of EPLAN is used; no main frame and - with some exceptions - no dialogs of EPLAN will be shown. 
- EPLAN runs as a separate process and functions, objects in this process are called by another process. (ActiveX automation, out-of-process server, EXE server) In this case, EPLAN can be visible or invisible. 

If you want to use the EPLAN API together with office applications (e.g. Excel), you should consider the following order of choice when planning your code architecture: 

- Create an EPLAN add-in and use the other application as managed code via COM interop. 
- Use Visual Studio Tools for Office (VSTO) together with managed EPLAN API assemblies. (EPLAN is in-process server or remoting client).

---

## Using other applications
*Źródło: `Using other applications.html`*
*Ścieżka: EPLAN API / User Guide / API Framework / Using EPLAN in other applications / Using other applications*

Using other applications The current topic describes, how you can use other applications, like for example Microsoft Excel in your EPLAN API add-in. 
If you want to access data of an other program, the application needs to have a suitable interface. Because an EPLAN add-in is written in managed code (C# or VB.NET), you need to be able to set a reference to the other program. Either the other application already exposes its interface as .NET assembly, or the .NET Framework creates an interop assembly from a COM type library. 

The following example shows the use of Microsoft Excel 2003. Excel exposes its functions as COM interface. In your EPLAN add-in, you can add a reference to the registered type library of Excel: 

After you added the reference, the development environment creates an interop assembly. The types of this assembly then can be used in managed code (C#, etc.): 

In your application code, the use of Excel would look like in the following example: 
- C# 
- VB Excel.ApplicationClass oExcel=
new
Excel.ApplicationClass();
oExcel.Visible=
true
;
new
Decider().Decide(EnumDecisionType.eOkDecision,
"Now Excel should be visible!"
,
""
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
Excel.Workbooks iWorkBooks=oExcel.Workbooks;
Excel.Workbook iWorkBook= iWorkBooks.Add(Excel.XlWBATemplate.xlWBATWorksheet);
Excel.Worksheet iSheet = (Excel.Worksheet)oExcel.ActiveSheet;
new
Decider().Decide(EnumDecisionType.eOkDecision,
"All project messages are now written into an Excel worksheet!"
,
""
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
Check oCheck =
new
Check();
oCheck.VerifyProject(oProject);
PrjMessagesCollection colPrjMsg =
new
PrjMessagesCollection(oProject);
PrjMessagesEnumerator itPrjMsg = colPrjMsg.GetPrjMsgEnumerator();
itPrjMsg.MoveNext();
int
nNr=1;
do
{
ProjectMessage oPrjMsg = itPrjMsg.Current
as
ProjectMessage;
if
(oPrjMsg !=
null
)
{
nNr++;
iSheet.Cells[nNr, 1] = oPrjMsg.GetGroup().ToString() + GetId().ToString();
iSheet.Cells[nNr, 2] = oPrjMsg.GetText();
}
}
while
(itPrjMsg.MoveNext());
new
Decider().Decide(EnumDecisionType.eOkDecision,
"Action completed!"
,
""
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
oExcel.Quit();
Dim
oExcel
As
New
Excel.ApplicationClass()
oExcel.Visible =
True
Dim
dec
As
Decider =
New
Decider
dec.Decide(EnumDecisionType.eOkDecision,
"Now Excel should be visible!"
,
""
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)
Dim
iWorkBooks
As
Excel.Workbooks = oExcel.Workbooks
Dim
iWorkBook
As
Excel.Workbook = iWorkBooks.Add(Excel.XlWBATemplate.xlWBATWorksheet)
Dim
iSheet
As
Excel.Worksheet =
CType
(oExcel.ActiveSheet, Excel.Worksheet)
dec.Decide(EnumDecisionType.eOkDecision,
"All project messages are now written into an Excel worksheet!"
,
""
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)
Dim
oCheck
As
New
Check()
oCheck.VerifyProject(oProject)
Dim
colPrjMsg
As
New
PrjMessagesCollection(oProject)
Dim
itPrjMsg
As
PrjMessagesEnumerator = colPrjMsg.GetPrjMsgEnumerator()
itPrjMsg.MoveNext()
Dim
nNr
As
Integer
= 1
Do
Dim
oPrjMsg
As
ProjectMessage = itPrjMsg.Current
If
Not
(oPrjMsg
Is
Nothing
)
Then
nNr += 1
iSheet.Cells(nNr, 1) = oPrjMsg.GetGroup().ToString() + GetId().ToString()
iSheet.Cells(nNr, 2) = oPrjMsg.GetText()
End
If
Loop
While
itPrjMsg.MoveNext()
dec.Decide(EnumDecisionType.eOkDecision,
"Action completed!"
,
""
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)
oExcel.Quit()

Excel is started as a separate process. The only object, you create with new is the Excel.ApplicationClass . All other objects like Excel.Workbook , are created – or queried from Excel – through functions of the Application object. 
Each call of Excel functions is a communication between processes!

### Przykłady kodu (C#)
```csharp
Excel.ApplicationClass oExcel= new Excel.ApplicationClass();
oExcel.Visible=true;
new Decider().Decide(EnumDecisionType.eOkDecision, "Now Excel should be visible!" ,"", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
Excel.Workbooks iWorkBooks=oExcel.Workbooks;
Excel.Workbook  iWorkBook= iWorkBooks.Add(Excel.XlWBATemplate.xlWBATWorksheet);
Excel.Worksheet iSheet = (Excel.Worksheet)oExcel.ActiveSheet;
new Decider().Decide(EnumDecisionType.eOkDecision, "All project messages are now written into an Excel worksheet!", "", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
Check oCheck = new Check();
oCheck.VerifyProject(oProject);
PrjMessagesCollection colPrjMsg = new PrjMessagesCollection(oProject);
PrjMessagesEnumerator itPrjMsg = colPrjMsg.GetPrjMsgEnumerator();
itPrjMsg.MoveNext();
int nNr=1;
do
{
   ProjectMessage oPrjMsg = itPrjMsg.Current as ProjectMessage;
   if (oPrjMsg != null)
   {
       nNr++;
       iSheet.Cells[nNr, 1] = oPrjMsg.GetGroup().ToString() + GetId().ToString();
       iSheet.Cells[nNr, 2] = oPrjMsg.GetText();
   }
} while(itPrjMsg.MoveNext());

new Decider().Decide(EnumDecisionType.eOkDecision, "Action completed!", "", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
oExcel.Quit();
```
```csharp
Dim oExcel As New Excel.ApplicationClass()
oExcel.Visible = True
Dim dec As Decider = New Decider
dec.Decide(EnumDecisionType.eOkDecision, "Now Excel should be visible!", "", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)
Dim iWorkBooks As Excel.Workbooks = oExcel.Workbooks
Dim iWorkBook As Excel.Workbook = iWorkBooks.Add(Excel.XlWBATemplate.xlWBATWorksheet)
Dim iSheet As Excel.Worksheet = CType(oExcel.ActiveSheet, Excel.Worksheet)
dec.Decide(EnumDecisionType.eOkDecision, "All project messages are now written into an Excel worksheet!", "", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)
Dim oCheck As New Check()
oCheck.VerifyProject(oProject)
Dim colPrjMsg As New PrjMessagesCollection(oProject)
Dim itPrjMsg As PrjMessagesEnumerator = colPrjMsg.GetPrjMsgEnumerator()
itPrjMsg.MoveNext()
Dim nNr As Integer = 1
Do
   Dim oPrjMsg As ProjectMessage = itPrjMsg.Current
   If Not (oPrjMsg Is Nothing) Then
      nNr += 1
      iSheet.Cells(nNr, 1) = oPrjMsg.GetGroup().ToString() + GetId().ToString()
      iSheet.Cells(nNr, 2) = oPrjMsg.GetText()
   End If
Loop While itPrjMsg.MoveNext()
dec.Decide(EnumDecisionType.eOkDecision, "Action completed!", "", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)
oExcel.Quit()
```

---

## Verifications
*Źródło: `Verifications.html`*
*Ścieżka: EPLAN API / User Guide / API Electrotechnical services / Verifications*

Verifications You can use an EPLAN API add-in to add new verifications. EPLAN will use them in the same way as already existing internal verifications. 
For a new verification, the add-in must  implement the IVerification interface. 

### C# 
### Copy Code 
| public
class
NewVerification : Eplan.EplApi.EServices.Verification
{
private
int
m_iMessageId = 30;
///
<summary>
/// Default constructor.
///
</summary>
public
NewVerification()
{
}
///
<summary>
/// In this function, the test logic will implement. 
///
</summary>
///
<param name="oObject1">
/// This object is tested. One can be certain that here only
/// function objects of the desired category arrive
///
</param>
public
override
void
Execute(Eplan.EplApi.DataModel.StorableObject oObject1)
{
DoErrorMessage(oObject1, oObject1.Project,
"Verification dynamic text"
);
}
///
<summary>
/// This function is called after end of all verifications run.
///
</summary>
public
override
void
OnEndInspection()
{
// TODO: Add NewVerification.OnEndInspection implementation
}
///
<summary>
/// Registration function of the verification.
///
</summary>
///
<param name="strName">
/// Under this name, the new verification registered in the system.
///
</param>
///
<param name="iOrdinal">
/// Overload priority. 
///
</param>
public
override
void
OnRegister(
ref
string
strName,
ref
int
iOrdinal)
{
strName =
"NewVerification"
;
iOrdinal = 30;
this
.VerificationPermission = IVerification.Permission.OnlineOfflinePermitted;
this
.VerificationState = IVerification.VerificationState.OnlineOfflineState;
}
///
<summary>
/// This function is called before start of all verifications run.
///
</summary>
///
<param name="bOnline">
/// true: online verification
/// false: offline verification
///
</param>
public
override
void
OnStartInspection(
bool
bOnline)
{
// TODO: Add NewVerification.OnStartInspection implementation
}
///
<summary>
/// This function must deliver the accompanying message text. 
/// A test has always exactly an accompanying message text. 
///
</summary>
///
<returns>
Der Meldungstext
</returns>
public
override
string
GetMessageText()
{
return
"Verification static text . %1!s!"
;
}
///
<summary>
///This function is called if to a message the aid text is supposed to be indicated. 
///It lies in the responsibility of the Implementation of the function to call
///the suitable aid system in the correct language.
///In the simplest case, for example only a simple dialog can be called. 
///
</summary>
public
override
void
DoHelp()
{
// TODO: NewVerification.DoHelp implementation
}
///
<summary>
/// This function is called of the system if the message of this test
/// is supposed to be registered in the system. 
///
</summary>
///
<param name="strCreator">
Creator of the message
</param>
///
<param name="eRegion">
Message region
</param>
///
<param name="iMessageId">
Number of the message
</param>
///
<param name="eClassification">
Default classification.
</param>
///
<param name="iOrdinal">
Overload priority.
</param>
public
override
void
OnRegister(
ref
String strCreator,
ref
Eplan.EplApi.EServices.IMessage.Region eRegion,
ref
int
iMessageId,
ref
Eplan.EplApi.EServices.IMessage.Classification eClassification,
ref
int
iOrdinal)
{
strCreator =
"Author"
;
eRegion = IMessage.Region.Externals;
iMessageId = m_iMessageId;
eClassification = IMessage.Classification.Error;
iOrdinal = 20;
}
}

In order to simplify the creation of a verification, the EPLAN API has some base classes that provide some service functions. 
These base classes are: 
- FunctionVerification 
- PotentialVerification 
- InterruptionPointVerification 

In your add-in, simply have your verification class inherit from one of these base classes and implement the necessary interface functions. For outputting messages, several variations of the AddMessage() function are available. In addition, the classes contain some functions for finding cross-referenced objects. 
If you want to implement a verification that cheks something about potentials, then you implement a new verification derived from PotentialVerification . In the Execute function of your new verification, you can use the GetAllPotentialsWithSameName() function to get the potential from the verification cache. It makes no sense to call this function in any other context than in the Execute() verification. 
All registered verifications are called by the system using Check project... . If you want to execute only your verification, you have to configure the check settings (create new scheme, disable other verifications ( Type of check : "No")). 
Please take into account that compared to 1.9 version, verifications inheriting from the Verification class must have the override keyword in the base methods definitions. This is required since the API extension has been migrated to C++/CLI . 

### How to start a verification 
Verifications can be invoked from API or GUI in 3 modes: 
- Online mode – This is called when a change was done and the UndoStep was disposed: 

### C# 
### Copy Code 
| using
(UndoStep oUndo =
new
UndoManager().CreateUndoStep())
{
oFunction.Location =
new
PointD(oFunction.Location.X + 10.0, oFunction.Location.Y + 10.0);
}

- Prevent errors mode (restrictive mode) – This is similar to the online mode, but if DoErrorMessage() is called, the last UndoStep is automatically undone, so the last changes are reverted. For the "Prevent errors mode" you should set the following options in the OnRegister method of the verification: 

### C# 
### Copy Code 
| this
.VerificationPermission = IVerification.Permission.RestrictivePermitted;
this
.VerificationState = IVerification.VerificationState.RestrictiveState;

- Offline mode – This can be done using: 
- the check action 
- the Check class ( VerifyProject and VerifyPages methods) 
- the Check project dialog

### Przykłady kodu (C#)
```csharp
public class NewVerification : Eplan.EplApi.EServices.Verification
{
    private int m_iMessageId = 30;
    /// <summary>
    /// Default constructor.
    /// </summary>
    public NewVerification()
    {
    }

    /// <summary>
    /// In this function, the test logic will implement. 
    /// </summary>
    /// <param name="oObject1">
    /// This object is tested.  One can be certain that here only
    /// function objects of the desired category arrive
    /// </param>
    public override void Execute(Eplan.EplApi.DataModel.StorableObject oObject1)
    {
        DoErrorMessage(oObject1, oObject1.Project, "Verification dynamic text");
    }

    /// <summary>
    /// This function is called after end of all verifications run.
    /// </summary>
    public override void OnEndInspection()
    {
        // TODO:  Add NewVerification.OnEndInspection implementation
    }

    /// <summary>
    /// Registration function of the verification.
    /// </summary>
    /// <param name="strName">
    /// Under this name, the new verification registered  in the system.
    /// </param>
    /// <param name="iOrdinal">
    /// Overload priority. 
    /// </param>
    public override void OnRegister(ref string strName, ref int iOrdinal)
    {
        strName = "NewVerification";
        iOrdinal = 30;
        this.VerificationPermission = IVerification.Permission.OnlineOfflinePermitted;
        this.VerificationState = IVerification.VerificationState.OnlineOfflineState;
    }

    /// <summary>
    /// This function is called before start of all verifications run.
    /// </summary>
    /// <param name="bOnline">
    /// true: online verification
    /// false: offline verification
    /// </param>
    public override void OnStartInspection(bool bOnline)
    {
        // TODO:  Add NewVerification.OnStartInspection implementation
    }

    /// <summary>
    /// This function must deliver the accompanying message text. 
    /// A test has always exactly an accompanying message text. 
    /// </summary>
    /// <returns>Der Meldungstext</returns>
    public override string GetMessageText()
    {
        return "Verification static text . %1!s!";
    }

    ///<summary>
    ///This function is called if to a message the aid text is supposed to be indicated. 
    ///It lies in the responsibility of the Implementation of the function to call
    ///the suitable aid system in the correct language.
    ///In the simplest case, for example only a simple dialog can be called. 
    ///</summary>
    public override void DoHelp()
    {
        // TODO:  NewVerification.DoHelp implementation
    }

    /// <summary>
    /// This function is called of the system if the message of this test
    ///  is supposed to be registered in the system. 
    /// </summary>
    /// <param name="strCreator">Creator of the message</param>
    /// <param name="eRegion">Message region</param>
    /// <param name="iMessageId">Number of the message</param>
    /// <param name="eClassification">Default classification.  </param>
    /// <param name="iOrdinal">Overload priority.</param>
    public override void OnRegister(ref String strCreator, ref Eplan.EplApi.EServices.IMessage.Region eRegion, ref int iMessageId, ref Eplan.EplApi.EServices.IMessage.Classification eClassification, ref int iOrdinal)
    {
        strCreator = "Author";
        eRegion = IMessage.Region.Externals;
        iMessageId = m_iMessageId;
        eClassification = IMessage.Classification.Error;
        iOrdinal = 20;
    }
}
```
```csharp
using (UndoStep oUndo = new UndoManager().CreateUndoStep())
{
oFunction.Location = new PointD(oFunction.Location.X + 10.0, oFunction.Location.Y + 10.0);
}
```
```csharp
this.VerificationPermission = IVerification.Permission.RestrictivePermitted;
this.VerificationState = IVerification.VerificationState.RestrictiveState;
```

---

## Working with settings
*Źródło: `Working with settings.html`*
*Ścieżka: EPLAN API / User Guide / API Miscellaneous / Working with settings*

Working with settings EPLAN has a settings database in which user preferences such as used fonts, colors, etc. are stored. 
In the GUI it is visible under the ribbon item File > Settings... . 
Using the API, we can modify the database and also create custom values for use in API applications. 

We can distinguish the following categories of settings: 
- Company settings : These settings should be located on a server and should be the same for the entire company. 
- Workstation settings : These settings apply to a single computer and should be stored on a local hard drive. 
- User settings : These settings, such as dimensions and positions of toolbars and dialogs, also need to be stored on a central server so that a user can use his own settings on another workstation. 
- Project-related settings : These settings are independent of a user or a workstation. They are stored in a project. See the "Project Settings" chapter. 

For more details, please refer to the "Settings: Operation" chapter of the EPLAN Help. 

### Format of settings 
The settings database is organized in a tree structure: Particular branches refer to similar settings and leaves store relevant values. 
Using the export functionality we can access their values, even those that are not visible in the Options > Settings dialog. The format of the file is XML , and here is its XML schema definition: 

### 
### Copy Code 
| <?
xml version="1.0" encoding="utf-8"
?>
<
xs:schema
attributeFormDefault
="unqualified"
elementFormDefault
="qualified"
xmlns:xs
="http://www.w3.org/2001/XMLSchema"
>
<
xs:group
name
="levlSettingGroup"
>
<
xs:sequence
>
<
xs:element
name
="Setting"
>
<
xs:complexType
>
<
xs:sequence
>
<
xs:element
minOccurs
="0"
maxOccurs
="unbounded"
name
="Val"
type
="xs:anyType"
/>
</
xs:sequence
>
<
xs:attribute
name
="name"
use
="required"
>
<
xs:simpleType
>
<
xs:restriction
base
="xs:string"
>
<
xs:pattern
value
="[a-zA-ZäöüÄÖÜ0-9_\s\+\-#\[\]]*"
/>
</
xs:restriction
>
</
xs:simpleType
>
</
xs:attribute
>
<
xs:attribute
name
="type"
use
="required"
>
<
xs:simpleType
>
<
xs:restriction
base
="xs:string"
>
<
xs:enumeration
value
="bool"
/>
<
xs:enumeration
value
="int"
/>
<
xs:enumeration
value
="unsigned int"
/>
<
xs:enumeration
value
="long"
/>
<
xs:enumeration
value
="unsigned long"
/>
<
xs:enumeration
value
="double"
/>
<
xs:enumeration
value
="string"
/>
<
xs:enumeration
value
="mlstring"
/>
</
xs:restriction
>
</
xs:simpleType
>
</
xs:attribute
>
<
xs:attribute
name
="info"
type
="xs:string"
use
="optional"
/>
<
xs:attribute
name
="desc"
type
="xs:string"
use
="optional"
/>
<
xs:attribute
name
="range"
type
="xs:string"
use
="optional"
/>
</
xs:complexType
>
</
xs:element
>
</
xs:sequence
>
</
xs:group
>
<
xs:attributeGroup
name
="levlAttrGroup"
>
<
xs:attribute
name
="name"
use
="required"
>
<
xs:simpleType
>
<
xs:restriction
base
="xs:string"
>
<
xs:pattern
value
="[a-zA-ZäöüÄÖÜß0-9_\s\+\-#\[\](),\/@:;\*&amp;]*"
/>
</
xs:restriction
>
</
xs:simpleType
>
</
xs:attribute
>
<
xs:attribute
name
="info"
type
="xs:string"
use
="optional"
/>
<
xs:attribute
name
="nodekind"
type
="xs:string"
use
="optional"
/>
</
xs:attributeGroup
>
<
xs:element
name
="Settings"
>
<
xs:complexType
>
<
xs:sequence
>
<
xs:element
minOccurs
="0"
maxOccurs
="5"
name
="CAT"
>
<
xs:complexType
>
<
xs:sequence
>
<
xs:element
minOccurs
="0"
maxOccurs
="unbounded"
name
="MOD"
>
<
xs:complexType
>
<
xs:sequence
>
<
xs:choice
minOccurs
="0"
maxOccurs
="unbounded"
>
<
xs:element
name
="LEV1"
>
<
xs:complexType
mixed
="true"
>
<
xs:sequence
>
<
xs:choice
minOccurs
="0"
maxOccurs
="unbounded"
>
<
xs:element
name
="LEV2"
>
<
xs:complexType
>
<
xs:sequence
>
<
xs:choice
minOccurs
="0"
maxOccurs
="unbounded"
>
<
xs:element
name
="LEV3"
>
<
xs:complexType
>
<
xs:sequence
>
<
xs:choice
minOccurs
="0"
maxOccurs
="unbounded"
>
<
xs:element
name
="LEV4"
>
<
xs:complexType
>
<
xs:sequence
>
<
xs:choice
minOccurs
="0"
maxOccurs
="unbounded"
>
<
xs:element
name
="LEV5"
>
<
xs:complexType
>
<
xs:sequence
>
<
xs:choice
minOccurs
="0"
maxOccurs
="unbounded"
>
<
xs:element
name
="LEV6"
>
<
xs:complexType
>
<
xs:sequence
>
<
xs:choice
minOccurs
="0"
maxOccurs
="unbounded"
>
<
xs:element
name
="LEV7"
>
<
xs:complexType
>
<
xs:sequence
>
<
xs:choice
minOccurs
="0"
maxOccurs
="unbounded"
>
<
xs:element
name
="LEV8"
>
<
xs:complexType
>
<
xs:sequence
>
<
xs:choice
minOccurs
="0"
maxOccurs
="unbounded"
>
<
xs:element
name
="LEV9"
>
<
xs:complexType
>
<
xs:sequence
>
<
xs:choice
minOccurs
="0"
maxOccurs
="unbounded"
>
<
xs:element
name
="LEV10"
>
<
xs:complexType
>
<
xs:group
ref
="levlSettingGroup"
/>
<
xs:attributeGroup
ref
="levlAttrGroup"
/>
</
xs:complexType
>
</
xs:element
>
<
xs:group
ref
="levlSettingGroup"
/>
</
xs:choice
>
</
xs:sequence
>
<
xs:attributeGroup
ref
="levlAttrGroup"
/>
</
xs:complexType
>
</
xs:element
>
<
xs:group
ref
="levlSettingGroup"
/>
</
xs:choice
>
</
xs:sequence
>
<
xs:attributeGroup
ref
="levlAttrGroup"
/>
</
xs:complexType
>
</
xs:element
>
<
xs:group
ref
="levlSettingGroup"
/>
</
xs:choice
>
</
xs:sequence
>
<
xs:attributeGroup
ref
="levlAttrGroup"
/>
</
xs:complexType
>
</
xs:element
>
<
xs:group
ref
="levlSettingGroup"
/>
</
xs:choice
>
</
xs:sequence
>
<
xs:attributeGroup
ref
="levlAttrGroup"
/>
</
xs:complexType
>
</
xs:element
>
<
xs:group
ref
="levlSettingGroup"
/>
</
xs:choice
>
</
xs:sequence
>
<
xs:attributeGroup
ref
="levlAttrGroup"
/>
</
xs:complexType
>
</
xs:element
>
<
xs:group
ref
="levlSettingGroup"
/>
</
xs:choice
>
</
xs:sequence
>
<
xs:attributeGroup
ref
="levlAttrGroup"
/>
</
xs:complexType
>
</
xs:element
>
<
xs:group
ref
="levlSettingGroup"
/>
</
xs:choice
>
</
xs:sequence
>
<
xs:attributeGroup
ref
="levlAttrGroup"
/>
</
xs:complexType
>
</
xs:element
>
<
xs:group
ref
="levlSettingGroup"
/>
</
xs:choice
>
</
xs:sequence
>
<
xs:attributeGroup
ref
="levlAttrGroup"
/>
</
xs:complexType
>
</
xs:element
>
<
xs:group
ref
="levlSettingGroup"
/>
</
xs:choice
>
</
xs:sequence
>
<
xs:attributeGroup
ref
="levlAttrGroup"
/>
</
xs:complexType
>
</
xs:element
>
<
xs:group
ref
="levlSettingGroup"
/>
</
xs:choice
>
</
xs:sequence
>
<
xs:attributeGroup
ref
="levlAttrGroup"
/>
</
xs:complexType
>
</
xs:element
>
</
xs:sequence
>
<
xs:attribute
name
="name"
use
="required"
>
<
xs:simpleType
>
<
xs:restriction
base
="xs:string"
>
<
xs:enumeration
value
="COMPANY"
/>
<
xs:enumeration
value
="INSTALL"
/>
<
xs:enumeration
value
="PROJECT"
/>
<
xs:enumeration
value
="STATION"
/>
<
xs:enumeration
value
="USER"
/>
</
xs:restriction
>
</
xs:simpleType
>
</
xs:attribute
>
</
xs:complexType
>
</
xs:element
>
</
xs:sequence
>
<
xs:attribute
name
="format"
type
="xs:unsignedByte"
use
="required"
/>
</
xs:complexType
>
</
xs:element
>
</
xs:schema
>

Here is a simplified description of the settings file: 
- name – The name of a setting that must be always unique within a setting node. 
- Settings – This is the root node. 
- CAT – Then there are 0-5 possible CAT nodes with the name attribute one of the following: COMPANY , PROJECT , STATION , USER , INSTALL . 
- MOD – Then there is a subnode MOD , which is a kind of namespace for a setting. 
- LEV – Then there are subnodes LEV1 up to LEV10 that specify a path to a leaf node. 
- Setting – Next there is a leaf node Setting which stores the following data: 
- Val – The setting value in the Val node. There can be more such nodes, each of them is accessible by individual index parameter. 
- type – Defines the expected settings type. 
- range – The range of values 
- ... does not concern Boolean data types 
- ... can consist of a token list for strings: (for example "arial/courier/tahoma") 
- ... can have a upper and lower bound for numbers in the format "from/to" (separated by slash): "1/10;20/100" 
### 
### Example of settings in XML format 
Here is an example of a simple user setting from the User > Display > Identifier branch: 

### 
### Copy Code 
| <?
xml version="1.0" encoding="utf-8"
?>
<
Settings
ver
="2.4.1"
format
="2"
>
<
CAT
name
="USER"
>
<
MOD
name
="PLEditorGui"
>
<
Setting
name
="SortMode"
type
="int"
>
<
Val
>
1
</
Val
>
</
Setting
>
</
MOD
>
</
CAT
>
</
Settings
>

Below is another example of workstation settings ( Workstation > Graphical editing > Print ): 

### 
### Copy Code 
| <?
xml version="1.0" encoding="utf-8"
?>
<
Settings
ver
="2.4.1"
format
="2"
>
<
CAT
name
="STATION"
>
<
MOD
name
="Print"
>
<
Setting
name
="BlackWhite"
type
="bool"
>
<
Val
>
1
</
Val
>
</
Setting
>
<
Setting
name
="BottomMargin"
type
="double"
range
="0/1000"
>
<
Val
>
0
</
Val
>
</
Setting
>
<
Setting
name
="ConsiderPageScale"
type
="bool"
>
<
Val
>
1
</
Val
>
</
Setting
>
<
Setting
name
="FitToPage"
type
="bool"
>
<
Val
>
1
</
Val
>
</
Setting
>
<
Setting
name
="KeepAspectRatio"
type
="bool"
>
<
Val
>
1
</
Val
>
</
Setting
>
<
Setting
name
="LeftMargin"
type
="double"
range
="0/1000"
>
<
Val
>
0
</
Val
>
</
Setting
>
<
Setting
name
="Position"
type
="unsigned long"
range
="0/8"
>
<
Val
>
0
</
Val
>
</
Setting
>
<
Setting
name
="RightMargin"
type
="double"
range
="0/1000"
>
<
Val
>
0
</
Val
>
</
Setting
>
<
Setting
name
="ScaleHorizontal"
type
="double"
range
="0.001/1000"
>
<
Val
>
1.0
</
Val
>
</
Setting
>
<
Setting
name
="ScaleVertical"
type
="double"
range
="0.001/1000"
>
<
Val
>
1.0
</
Val
>
</
Setting
>
<
Setting
name
="TopMargin"
type
="double"
range
="0/1000"
>
<
Val
>
0
</
Val
>
</
Setting
>
</
MOD
>
</
CAT
>
</
Settings
>

Here is example of indexed settings from Company > Graphical editing > Fonts . 

### 
### Copy Code 
| <?
xml version="1.0" encoding="utf-8"
?>
<
Settings
ver
="2.4.3"
format
="2"
>
<
CAT
name
="COMPANY"
>
<
MOD
name
="GedViewer"
>
<
Setting
name
="Fonts"
type
="mlstring"
>
<
Val
>
??_??@Arial;
</
Val
>
<
Val
>
??_??@Verdana;
</
Val
>
<
Val
>
??_??@Georgia;
</
Val
>
<
Val
>
??_??@Tahoma;zh_CN@??;
</
Val
>
<
Val
>
??_??@Tahoma;zh_CN@??;
</
Val
>
<
Val
>
??_??@Tahoma;zh_CN@??;
</
Val
>
<
Val
>
??_??@Tahoma;zh_CN@??;
</
Val
>
<
Val
>
??_??@Tahoma;zh_CN@??;
</
Val
>
<
Val
>
??_??@Tahoma;zh_CN@??;
</
Val
>
<
Val
>
??_??@Tahoma;zh_CN@??;
</
Val
>
</
Setting
>
</
MOD
>
</
CAT
>
</
Settings
>

### API classes for working with settings 
Settings – functions for reading, writing and creating User, Company or Workstation settings. 
ProjectSettings – functions for reading, writing and creating project dependant settings. Refer to the "See Also" section. 
SettingNode – functions for managing the settings hierarchy (only User, Company or Workstation settings). 
SchemeSetting – functions for managing a settings group (scheme). Only for User, Company or Workstation settings. 
ProjectSchemeSetting – the same as SchemeSetting but for project settings. 
ProjectSettingNode – the same as SettingNode but for project settings. 
### Examples 
Adding, setting and getting settings: 
- C# 
- VB Eplan.EplApi.Base.Settings oSettings =
new
Eplan.EplApi.Base.Settings();
oSettings.AddStringSetting(
"USER.DEMOSETTINGS.TEST1"
,
new
string
[] { },
new
string
[] { }, ISettings.CreationFlag.Insert);
oSettings.SetStringSetting(
"USER.DEMOSETTINGS.TEST1"
,
"Testwert1"
, 0);
String strTest1 = oSettings.GetStringSetting(
"USER.DEMOSETTINGS.TEST1"
, 0);
if
(strTest1 ==
"Testwert1"
)
Console.Out.WriteLine(
"SetGetAddSetting OK!"
);
else
Console.Out.WriteLine(
"SetGetAddSetting not OK!"
);
Dim
oSettings
As
New
Settings()
oSettings.AddStringSetting(
"USER.DEMOSETTINGS.TEST1"
,
New
String
() {},
New
String
() {}, ISettings.CreationFlag.Insert)
oSettings.SetStringSetting(
"USER.DEMOSETTINGS.TEST1"
,
"Testwert1"
, 0)
Dim
strTest1
As
[
String
] = oSettings.GetStringSetting(
"USER.DEMOSETTINGS.TEST1"
, 0)
Dim
dec
As
Decider =
New
Decider
If
strTest1 =
"Testwert1"
Then
dec.Decide(EnumDecisionType.eOkDecision,
"SetGetAddSetting OK!"
,
""
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)
Else
dec.Decide(EnumDecisionType.eOkDecision,
"SetGetAddSetting not OK!"
,
""
,EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
End
If

Example of merging nodes using SettingNode : 
- C# 
- VB Eplan.EplApi.Base.SettingNode oSettingNode =
new
Eplan.EplApi.Base.SettingNode(
"STATION.AF.Interfaces"
);
uint
uiCountOfSettings = oSettingNode.GetCountOfSettings();
uint
uiCountOfNodes = oSettingNode.GetCountOfNodes();
System.Collections.Specialized.StringCollection
strColl1 =
new
System.Collections.Specialized.StringCollection();
oSettingNode.GetListOfAllSettings(
ref
strColl1,
false
);
System.Collections.Specialized.StringCollection
strColl2 =
new
System.Collections.Specialized.StringCollection();
oSettingNode.GetListOfNodes(
ref
strColl2,
false
);
System.Collections.Specialized.StringCollection
strColl3 =
new
System.Collections.Specialized.StringCollection();
oSettingNode.GetListOfSettings(
ref
strColl3,
false
);
Eplan.EplApi.Base.SettingNode oMuster =
new
Eplan.EplApi.Base.SettingNode(
"STATION.AF.DefaultSetting.ActionInterface"
);
Eplan.EplApi.Base.SettingNode ownSetting =
new
Eplan.EplApi.Base.SettingNode(
"STATION.AF.ActionTestInterfaces"
);
Eplan.EplApi.Base.SettingNode oNew = ownSetting.GetSubNode(
"TestNode1"
);
oNew.MergeWithNode(oMuster);
oNew.SetStringSetting(
"ModuleName"
,
"Test1Value1"
, 0);
oNew.SetBoolSetting(
"IsAddIn"
,
true
, 0);
oNew.SetStringSetting(
"ActionName"
,
"TestAction1"
, 0);
Dim
oSettingNode
As
New
SettingNode(
"STATION.AF.Interfaces"
)
Dim
uiCountOfSettings
As
UInteger
= oSettingNode.GetCountOfSettings()
Dim
uiCountOfNodes
As
UInteger
= oSettingNode.GetCountOfNodes()
Dim
strColl1
As
New
StringCollection()
oSettingNode.GetListOfAllSettings(strColl1,
False
)
Dim
strColl2
As
New
StringCollection()
oSettingNode.GetListOfNodes(strColl2,
False
)
Dim
strColl3
As
New
StringCollection()
oSettingNode.GetListOfSettings(strColl3,
False
)
Dim
oMuster
As
New
SettingNode(
"STATION.AF.DefaultSetting.ActionInterface"
)
Dim
ownSetting
As
New
SettingNode(
"STATION.AF.ActionTestInterfaces"
)
Dim
oNew
As
SettingNode = ownSetting.GetSubNode(
"TestNode1"
)
oNew.MergeWithNode(oMuster)
oNew.SetStringSetting(
"ModuleName"
,
"Test1Value1"
, 0)
oNew.SetBoolSetting(
"IsAddIn"
,
True
, 0)
oNew.SetStringSetting(
"ActionName"
,
"TestAction1"
, 0)

You can also combine settings into a group under a specific name – it is called a "schema". It is possible to have multiple groups under different names, but with the same settings structure. One of the groups is an active scheme. 

- C# 
- VB SchemeSetting oSchemeSetting =
new
SchemeSetting();
oSchemeSetting.Init(
"USER.DXF.SCHEMES"
);
int
iCount = oSchemeSetting.GetCount();
String strName = oSchemeSetting.GetName();
int
iExportFormatVersion = oSchemeSetting.GetNumericSetting(
"EXPORT.FORMAT_VERSION"
, 0);
Dim
oSchemeSetting
As
New
SchemeSetting()
oSchemeSetting.Init(
"USER.DXF.SCHEMES"
)
Dim
iCount
As
Integer
= oSchemeSetting.GetCount()
Dim
strName
As
[
String
] = oSchemeSetting.GetName()
Dim
iExportFormatVersion
As
Integer
= oSchemeSetting.GetNumericSetting(
"EXPORT.FORMAT_VERSION"
, 0)

As mentioned above, each setting has a default value. To return a setting to its default value, you must get the setting's default value and set it to the setting: 
- C# 
- VB Eplan.EplApi.Base.Settings oSettings =
new
Eplan.EplApi.Base.Settings();
// Set the path for projects back to its default
string
sProjectsPath =
""
;
sProjectsPath = oSettings.GetStringDefault(
"USER.TrDMProject.Masterdata.Pathnames.Projects"
, 0);
oSettings.SetStringSetting(
"USER.TrDMProject.Masterdata.Pathnames.Projects"
, sProjectsPath, 0);
Dim
oSettings
As
New
Settings()
' Set the path for projects back to its default
Dim
sProjectsPath
As
String
=
""
sProjectsPath = oSettings.GetStringDefault(
"USER.TrDMProject.Masterdata.Pathnames.Projects"
, 0)
oSettings.SetStringSetting(
"USER.TrDMProject.Masterdata.Pathnames.Projects"
, sProjectsPath, 0)

To make it easier for the API user to find a particular settings key, the s ettings dialog provides a hidden feature. If you set the Boolean setting USER.EnfMVC.ContextMenuSetting.ShowExtended to "true", you will get an additional context menu item in the settings dialog that shows you the path of the selected setting. 
### Remarks 
Due to changes in EPLAN, settings may change their type or name or some settings may be removed completely. We cannot guarantee the long-term compatibility of the settings. When updating to a newer version, please check your source code to see whether the settings you are using still working. 
Indexed settings always have continuous indexes. If a value is removed, the following values move up to fill the gap. This means that if you want to get all the values of an indexed property, all you have to do is loop from index 0 to the number returned by GetCountOfValues(...) minus one. If you try to get the value from an index where no value exists, a BaseException is thrown. See Also 
### API DataModel Project settings

### Przykłady kodu (C#)
```csharp
<?xml version="1.0" encoding="utf-8"?>
<xs:schema attributeFormDefault="unqualified" elementFormDefault="qualified" xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:group name="levlSettingGroup">
    <xs:sequence>
      <xs:element name="Setting">
        <xs:complexType>
          <xs:sequence>
            <xs:element minOccurs="0" maxOccurs="unbounded" name="Val" type="xs:anyType" />
          </xs:sequence>
          <xs:attribute name="name" use="required">
            <xs:simpleType>
              <xs:restriction base="xs:string">
                <xs:pattern value="[a-zA-ZäöüÄÖÜ0-9_\s\+\-#\[\]]*"/>
              </xs:restriction>
            </xs:simpleType>
          </xs:attribute>
          <xs:attribute name="type" use="required">
            <xs:simpleType>
              <xs:restriction base="xs:string">
                <xs:enumeration value="bool"/>
                <xs:enumeration value="int"/>
                <xs:enumeration value="unsigned int"/>
                <xs:enumeration value="long"/>
                <xs:enumeration value="unsigned long"/>
                <xs:enumeration value="double"/>
                <xs:enumeration value="string"/>
                <xs:enumeration value="mlstring"/>
              </xs:restriction>
            </xs:simpleType>
          </xs:attribute>
          <xs:attribute name="info" type="xs:string" use="optional" />
          <xs:attribute name="desc" type="xs:string" use="optional" />
          <xs:attribute name="range" type="xs:string" use="optional" />
        </xs:complexType>
      </xs:element>
    </xs:sequence>   
  </xs:group>
  <xs:attributeGroup name="levlAttrGroup">
    <xs:attribute name="name" use="required">
      <xs:simpleType>
        <xs:restriction base="xs:string">
          <xs:pattern value="[a-zA-ZäöüÄÖÜß0-9_\s\+\-#\[\](),\/@:;\*&amp;]*"/>
        </xs:restriction>
      </xs:simpleType>
    </xs:attribute>
    <xs:attribute name="info" type="xs:string" use="optional" />
    <xs:attribute name="nodekind" type="xs:string" use="optional" />
  </xs:attributeGroup> 
  <xs:element name="Settings">
    <xs:complexType>
      <xs:sequence>
        <xs:element minOccurs="0" maxOccurs="5" name="CAT">                           
          <xs:complexType>               
            <xs:sequence>
              <xs:element minOccurs="0" maxOccurs="unbounded" name="MOD">
                <xs:complexType>
                  <xs:sequence>
                    <xs:choice minOccurs="0" maxOccurs="unbounded">
                      <xs:element name="LEV1">
                          <xs:complexType mixed="true">
                            <xs:sequence>
                              <xs:choice minOccurs="0" maxOccurs="unbounded">
                                <xs:element name="LEV2">
                                  <xs:complexType>
                                    <xs:sequence>
                                      <xs:choice minOccurs="0" maxOccurs="unbounded">                                       
                                        <xs:element name="LEV3">
                                          <xs:complexType>
                                            <xs:sequence>
                                              <xs:choice minOccurs="0" maxOccurs="unbounded">
                                                <xs:element name="LEV4">
                                                  <xs:complexType>
                                                    <xs:sequence>
                                                      <xs:choice minOccurs="0" maxOccurs="unbounded">
                                                        <xs:element name="LEV5">
                                                          <xs:complexType>
                                                            <xs:sequence>
                                                              <xs:choice minOccurs="0" maxOccurs="unbounded">
                                                                <xs:element name="LEV6">
                                                                  <xs:complexType>
                                                                    <xs:sequence>
                                                                      <xs:choice minOccurs="0" maxOccurs="unbounded">
                                                                        <xs:element name="LEV7">
                                                                          <xs:complexType>
                                                                            <xs:sequence>
                                                                              <xs:choice minOccurs="0" maxOccurs="unbounded">
                                                                                <xs:element name="LEV8">
                                                                                  <xs:complexType>
                                                                                    <xs:sequence>
                                                                                      <xs:choice minOccurs="0" maxOccurs="unbounded">
                                                                                        <xs:element name="LEV9">
                                                                                          <xs:complexType>
                                                                                            <xs:sequence>
                                                                                              <xs:choice minOccurs="0" maxOccurs="unbounded">
                                                                                                <xs:element name="LEV10">
                                                                                                  <xs:complexType>
                                                                                                    <xs:group ref="levlSettingGroup"/>
                                                                                                    <xs:attributeGroup ref="levlAttrGroup"/>                                                                                                  
                                                                                                  </xs:complexType>
                                                                                                </xs:element>
                                                                                                <xs:group ref="levlSettingGroup"/>
                                                                                              </xs:choice>
                                                                                            </xs:sequence>                                                                                           
                                                                                            <xs:attributeGroup ref="levlAttrGroup"/>
                                                                                          </xs:complexType>
                                                                                        </xs:element>
                                                                                        <xs:group ref="levlSettingGroup"/>
                                                                                      </xs:choice>
                                                                                    </xs:sequence>
                                                                                    <xs:attributeGroup ref="levlAttrGroup"/>                                                                                
                                                                                  </xs:complexType>
                                                                                </xs:element>
                                                                                <xs:group ref="levlSettingGroup"/>
                                                                              </xs:choice>
                                                                            </xs:sequence>
                                                                            <xs:attributeGroup ref="levlAttrGroup"/>
                                                                          </xs:complexType>
                                                                        </xs:element>
                                                                        <xs:group ref="levlSettingGroup"/>
                                                                      </xs:choice>
                                                                    </xs:sequence>
                                                                    <xs:attributeGroup ref="levlAttrGroup"/>
                                                                  </xs:complexType>
                                                                </xs:element>
                                                                <xs:group ref="levlSettingGroup"/>
                                                              </xs:choice>
                                                            </xs:sequence>
                                                            <xs:attributeGroup ref="levlAttrGroup"/>
                                                          </xs:complexType>
                                                        </xs:element>
                                                        <xs:group ref="levlSettingGroup"/>
                                                      </xs:choice>
                                                    </xs:sequence>
                                                    <xs:attributeGroup ref="levlAttrGroup"/>
                                                  </xs:complexType>
                                                </xs:element>
                                                <xs:group ref="levlSettingGroup"/>
                                              </xs:choice>
                                            </xs:sequence>
                                            <xs:attributeGroup ref="levlAttrGroup"/>
                                          </xs:complexType>
                                        </xs:element>
                                        <xs:group ref="levlSettingGroup"/>
                                      </xs:choice>
                                    </xs:sequence>
                                    <xs:attributeGroup ref="levlAttrGroup"/>
                                  </xs:complexType>
                                </xs:element>
                                <xs:group ref="levlSettingGroup"/>
                              </xs:choice>
                            </xs:sequence>
                            <xs:attributeGroup ref="levlAttrGroup"/>                          
                          </xs:complexType>
                        </xs:element>
                      <xs:group ref="levlSettingGroup"/>                               
                    </xs:choice>
                  </xs:sequence>
                  <xs:attributeGroup ref="levlAttrGroup"/>
                </xs:complexType>
              </xs:element>                 
            </xs:sequence>                 
            <xs:attribute name="name" use="required">               
              <xs:simpleType>
                <xs:restriction base="xs:string">
                  <xs:enumeration value="COMPANY"/>
                  <xs:enumeration value="INSTALL"/>
                  <xs:enumeration value="PROJECT"/>
                  <xs:enumeration value="STATION"/>
                  <xs:enumeration value="USER"/>
                </xs:restriction>
              </xs:simpleType>
            </xs:attribute>
          </xs:complexType>
        </xs:element>
      </xs:sequence>
      <xs:attribute name="format" type="xs:unsignedByte" use="required" />
    </xs:complexType>
  </xs:element>
</xs:schema>
```
```csharp
<?xml version="1.0" encoding="utf-8" ?>
<Settings ver="2.4.1" format="2">
 <CAT name="USER">
  <MOD name="PLEditorGui">
   <Setting name="SortMode" type="int">
    <Val>1</Val>
   </Setting>
  </MOD>
 </CAT>
</Settings>
```
```csharp
<?xml version="1.0" encoding="utf-8" ?>
<Settings ver="2.4.1" format="2">
 <CAT name="STATION">
  <MOD name="Print">
   <Setting name="BlackWhite" type="bool">
    <Val>1</Val>
   </Setting>
   <Setting name="BottomMargin" type="double" range="0/1000">
    <Val>0</Val>
   </Setting>
   <Setting name="ConsiderPageScale" type="bool">
    <Val>1</Val>
   </Setting>
   <Setting name="FitToPage" type="bool">
    <Val>1</Val>
   </Setting>
   <Setting name="KeepAspectRatio" type="bool">
    <Val>1</Val>
   </Setting>
   <Setting name="LeftMargin" type="double" range="0/1000">
    <Val>0</Val>
   </Setting>
   <Setting name="Position" type="unsigned long" range="0/8">
    <Val>0</Val>
   </Setting>
   <Setting name="RightMargin" type="double" range="0/1000">
    <Val>0</Val>
   </Setting>
   <Setting name="ScaleHorizontal" type="double" range="0.001/1000">
    <Val>1.0</Val>
   </Setting>
   <Setting name="ScaleVertical" type="double" range="0.001/1000">
    <Val>1.0</Val>
   </Setting>
   <Setting name="TopMargin" type="double" range="0/1000">
    <Val>0</Val>
   </Setting>
  </MOD>
 </CAT>
</Settings>
```
```csharp
<?xml version="1.0" encoding="utf-8" ?>
<Settings ver="2.4.3" format="2">
 <CAT name="COMPANY">
  <MOD name="GedViewer">
   <Setting name="Fonts" type="mlstring">
    <Val>??_??@Arial;</Val>
    <Val>??_??@Verdana;</Val>
    <Val>??_??@Georgia;</Val>
    <Val>??_??@Tahoma;zh_CN@??;</Val>
    <Val>??_??@Tahoma;zh_CN@??;</Val>
    <Val>??_??@Tahoma;zh_CN@??;</Val>
    <Val>??_??@Tahoma;zh_CN@??;</Val>
    <Val>??_??@Tahoma;zh_CN@??;</Val>
    <Val>??_??@Tahoma;zh_CN@??;</Val>
    <Val>??_??@Tahoma;zh_CN@??;</Val>
   </Setting>
  </MOD>
 </CAT>
</Settings>
```
```csharp
Eplan.EplApi.Base.Settings oSettings = new Eplan.EplApi.Base.Settings();
    oSettings.AddStringSetting("USER.DEMOSETTINGS.TEST1", new string[] { },
    new string[] { }, ISettings.CreationFlag.Insert);
    oSettings.SetStringSetting("USER.DEMOSETTINGS.TEST1", "Testwert1", 0);
    String strTest1 = oSettings.GetStringSetting("USER.DEMOSETTINGS.TEST1", 0);
    if (strTest1 == "Testwert1")
         Console.Out.WriteLine("SetGetAddSetting OK!");
    else
         Console.Out.WriteLine("SetGetAddSetting not OK!");
```
```csharp
Dim oSettings As New Settings()
oSettings.AddStringSetting("USER.DEMOSETTINGS.TEST1", New String() {}, New String() {}, ISettings.CreationFlag.Insert)
oSettings.SetStringSetting("USER.DEMOSETTINGS.TEST1", "Testwert1", 0)
Dim strTest1 As [String] = oSettings.GetStringSetting("USER.DEMOSETTINGS.TEST1", 0)
Dim dec As Decider = New Decider
If strTest1 = "Testwert1" Then
    dec.Decide(EnumDecisionType.eOkDecision,"SetGetAddSetting OK!","", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)
Else
    dec.Decide(EnumDecisionType.eOkDecision,"SetGetAddSetting not OK!","",EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
End If
```
```csharp
Eplan.EplApi.Base.SettingNode oSettingNode = new Eplan.EplApi.Base.SettingNode("STATION.AF.Interfaces");
        uint uiCountOfSettings = oSettingNode.GetCountOfSettings();
        uint uiCountOfNodes = oSettingNode.GetCountOfNodes();
        System.Collections.Specialized.StringCollection
          strColl1 = new System.Collections.Specialized.StringCollection();
        oSettingNode.GetListOfAllSettings(ref strColl1, false);
        System.Collections.Specialized.StringCollection
          strColl2 = new System.Collections.Specialized.StringCollection();
        oSettingNode.GetListOfNodes(ref strColl2, false);
        System.Collections.Specialized.StringCollection
          strColl3 = new System.Collections.Specialized.StringCollection();
        oSettingNode.GetListOfSettings(ref strColl3, false);
        Eplan.EplApi.Base.SettingNode oMuster = new
          Eplan.EplApi.Base.SettingNode("STATION.AF.DefaultSetting.ActionInterface");
        Eplan.EplApi.Base.SettingNode ownSetting = new
          Eplan.EplApi.Base.SettingNode("STATION.AF.ActionTestInterfaces");
        Eplan.EplApi.Base.SettingNode oNew = ownSetting.GetSubNode("TestNode1");
        oNew.MergeWithNode(oMuster);
        oNew.SetStringSetting("ModuleName", "Test1Value1", 0);
        oNew.SetBoolSetting("IsAddIn", true, 0);
        oNew.SetStringSetting("ActionName", "TestAction1", 0);
```
```csharp
Dim oSettingNode As New SettingNode("STATION.AF.Interfaces")
Dim uiCountOfSettings As UInteger = oSettingNode.GetCountOfSettings()
Dim uiCountOfNodes As UInteger = oSettingNode.GetCountOfNodes()
Dim strColl1 As New StringCollection()
oSettingNode.GetListOfAllSettings(strColl1, False)
Dim strColl2 As New StringCollection()
oSettingNode.GetListOfNodes(strColl2, False)
Dim strColl3 As New StringCollection()
oSettingNode.GetListOfSettings(strColl3, False)
Dim oMuster As New SettingNode("STATION.AF.DefaultSetting.ActionInterface")
Dim ownSetting As New SettingNode("STATION.AF.ActionTestInterfaces")
Dim oNew As SettingNode = ownSetting.GetSubNode("TestNode1")
oNew.MergeWithNode(oMuster)
oNew.SetStringSetting("ModuleName", "Test1Value1", 0)
oNew.SetBoolSetting("IsAddIn", True, 0)
oNew.SetStringSetting("ActionName", "TestAction1", 0)
```
```csharp
SchemeSetting oSchemeSetting = new SchemeSetting();
    oSchemeSetting.Init("USER.DXF.SCHEMES");
    int iCount = oSchemeSetting.GetCount();
    String strName = oSchemeSetting.GetName();
    int iExportFormatVersion = oSchemeSetting.GetNumericSetting("EXPORT.FORMAT_VERSION", 0);
```
```csharp
Dim oSchemeSetting As New SchemeSetting()
oSchemeSetting.Init("USER.DXF.SCHEMES")
Dim iCount As Integer = oSchemeSetting.GetCount()
Dim strName As [String] = oSchemeSetting.GetName()
Dim iExportFormatVersion As Integer = oSchemeSetting.GetNumericSetting("EXPORT.FORMAT_VERSION", 0)
```
```csharp
Eplan.EplApi.Base.Settings oSettings = new Eplan.EplApi.Base.Settings();
    // Set the path for projects back to its default
    string sProjectsPath = "";
    sProjectsPath = oSettings.GetStringDefault("USER.TrDMProject.Masterdata.Pathnames.Projects", 0);
    oSettings.SetStringSetting("USER.TrDMProject.Masterdata.Pathnames.Projects", sProjectsPath, 0);
```
```csharp
Dim oSettings As New Settings()
' Set the path for projects back to its default
Dim sProjectsPath As String = ""
sProjectsPath = oSettings.GetStringDefault("USER.TrDMProject.Masterdata.Pathnames.Projects", 0)
oSettings.SetStringSetting("USER.TrDMProject.Masterdata.Pathnames.Projects", sProjectsPath, 0)
```

---

## Writing system messages
*Źródło: `Writing system messages.html`*
*Ścieżka: EPLAN API / User Guide / API Miscellaneous / Writing system messages*

Writing system messages EPLAN expects system errors to be handled by exceptions. For this resason, the interface to the EPLAN system messages is implemented in the BaseException class. This means that in order to write a system message, a BaseException object must first be created. However, the exception does not have to be thrown! 

The fixMessage() function of the exception adds the message to the EPLAN system messages. 
- C# 
- VB Eplan.EplApi.Base.BaseException exc =
new
Eplan.EplApi.Base.BaseException(
"CSharpAction really failed!!"
,
Eplan.EplApi.Base.MessageLevel.Error);
exc.FixMessage();
Dim
exc
As
Eplan.EplApi.Base.BaseException =
New
(
"CSharpAction really failed!!"
, _
Eplan.EplApi.Base.MessageLevel.Error)
exc.FixMessage

### Przykłady kodu (C#)
```csharp
Eplan.EplApi.Base.BaseException exc = new Eplan.EplApi.Base.BaseException("CSharpAction really failed!!",
                                      Eplan.EplApi.Base.MessageLevel.Error);
exc.FixMessage();
```
```csharp
Dim exc As Eplan.EplApi.Base.BaseException = New ("CSharpAction really failed!!", _
                                             Eplan.EplApi.Base.MessageLevel.Error)
exc.FixMessage
```

---

## XML Converters
*Źródło: `XML Converters.html`*
*Ścieżka: EPLAN API / API Reference / XML Converters*

XML Converters This is the list of the available XML converters, which can be used in import and export methods. They are divided on categories 
- Category DeviceListXmlConverter 
- 
- XDLCsvCommaSepImporterExporter 
- XDLCsvImporterExporter 
- XDLTxtImporterExporter 
- XDLXmlExporter 
- Category LanguageDbXmlConverter 
- 
- XTrLanguageDbXml2E21UnicodeTabConverter 
- XTrLanguageDbXml2TabConverterImpl 
- Category PartsListXmlConverter 
- 
- XPalCSVConverter 
- XPalXmlExporter 
- Category XPamExport 
- 
- IXPartsImportExportEdz 
- XPamExportXml 
- Category XPamImport 
- 
- XPamImportXml 
- Category PLCXmlConverter 
- 
- PlcDcAMLExchangerGeneral 
- PlcDcExchangerBeckhoffTC3AML 
- PlcDcExchangerBoschAML 
- PlcDcExchangerLogiCals3AML 
- PlcDcExchangerMitsubishiAML 
- PlcDcExchangerMitsubishi110AML 
- PlcDcExchangerOmron120AML 
- PlcDcExchangerPhoenixContactAML 
- PlcDcExchangerRockwellArchitectAML 
- PlcDcExchangerSiemensTIA15AML 
- PlcDcExchangerSiemensTIA16AML 
- PlcDcExchangerSiemensTIA17AML 
- PlcDcExchangerSiemensTIA151AML 
- PlcDcExchangerSiemensTSTAML 
- PlcDcXMLExchangerABB 
- PlcDcXMLExchangerBandR 
- PlcDcXmlExchangerRexroth 
- PlcDCXmlExchangerSchneider 
- PlcDcXMLExchangerSiemens 
- PlcDcXMLExchangerUniversal 
- XmlLblXmlExportConverterImpl

---

## XMLProcessor
*Źródło: `XMLProcessor.html`*
*Ścieżka: EPLAN API / User Guide / API Miscellaneous / XMLProcessor*

XMLProcessor ### The XMLProcessor interface 
In general, EPLAN uses XML as its interchange format. Furthermore EPLAN is required to support various other export / import formats. It is not practical to consider all possible of these formats. 

### Solution 
EPLAN carries on exporting / importing its XML format. Additionally, conversion modules can be added to EPLAN that convert the created XML files into other import / export formats. 

Import of different formats: 

Export of different formats: 

The following work flow is used: 

Import: 
- starting the import and selecting the import format XYZ 
- converting XYZ to XML through the conversion module 
- importing the XML file 

Export: 
- starting the export and selecting the export format XYZ 
- exporting the XML file 
- converting XML to XYZ through the conversion module 

### Interface 
API conversion modules can be created by implementing the IXMLProcessor interface. Although not all formats are read as well as written, it makes sense to handle both import and export in one interface. 

The following example shows the usage of the interface, where only the export is implemented: 

### C# 
### Copy Code 
| public
class
MySimpleXMLConverter : Eplan.EplApi.ApplicationFramework.IXMLProcessor
{
public
MySimpleXMLConverter()
{
//
// TODO: Add constructor logic here
//
}
string
m_sError =
string
.Empty;
Options m_optionsXMLProcessor =
new
Options();
#region
IXMLProcessor Members
///
<summary>
/// Returns a settings dialog for this processor.
/// Dialog is only created, but not displayed!
///
</summary>
///
<returns>
Interface of the created dialog.
</returns>
public
Eplan.EplApi.ApplicationFramework.IOptions GetOption()
{
return
m_optionsXMLProcessor;
}
///
<summary>
/// Returns the name of the converter, as it will appear in the selection list.
///
</summary>
///
<returns>
Name of converter, is shown in selection list.
</returns>
public
string
GetName()
{
String strName =
"SimpleXMLProcessor"
;
strName +=
" ("
;
strName += GetFileFilter();
strName +=
")"
;
return
strName;
}
///
<summary>
/// Returns an error message if an error occurred during export/import.
///
</summary>
///
<returns>
Error message
</returns>
public
string
GetErrorMessage()
{
// TODO: Add XMLProcessor.getErrorMessage implementation
return
m_sError;
}
///
<summary>
/// Is called after import has been completed.
///
</summary>
///
<returns>
If true, an Information dialog box is displayed.
</returns>
public
bool
PostImport()
{
// TODO: Add XMLProcessor.postImport implementation
return
false
;
}
///
<summary>
/// Is called after export has been completed.
///
</summary>
///
<returns>
If true, an Information dialog box is displayed.
</returns>
public
bool
PostExport()
{
// TODO: Add XMLProcessor.postExport implementation
return
false
;
}
///
<summary>
/// Indicates whether the converter provides an export option.
///
</summary>
///
<param name="oContext">
Context with parameters
</param>
///
<param name="bSupportsProgress">
Indicates whether the converter supports a progress bar.
</param>
///
<returns>
true: export is possible; false: export is not possible
</returns>
public
bool
CanExport(Eplan.EplApi.Base.Context oContext,
ref
bool
bSupportsProgress)
{
bSupportsProgress =
false
;
return
true
;
}
///
<summary>
/// Converts the XML file to a special file.
///
</summary>
///
<param name="strXmlFile">
Input file
</param>
///
<param name="strOutputFile">
Output file
</param>
///
<param name="oContext">
Context with parameters
</param>
///
<returns>
Returns true if successful.
</returns>
public
bool
Export(
string
strXmlFile,
string
strOutputFile, Eplan.EplApi.Base.Context oContext)
{
bool
bRet =
false
;
try
{
// Short example for a simple export conversion
System.Xml.XmlTextReader xRead =
new
System.Xml.XmlTextReader(strXmlFile);
System.IO.StreamWriter swOut =
new
System.IO.StreamWriter(strOutputFile);
xRead.WhitespaceHandling = System.Xml.WhitespaceHandling.None;
string
sFirstLang =
string
.Empty;
while
(xRead.Read())
{
if
((xRead.XmlLang.CompareTo(String.Empty) != 0) && (xRead.Value.CompareTo(String.Empty) != 0))
{
if
(sFirstLang.CompareTo(String.Empty) == 0) sFirstLang = xRead.XmlLang;
if
(xRead.XmlLang.CompareTo(sFirstLang) == 0) swOut.WriteLine();
swOut.Write(xRead.XmlLang +
":"
+ xRead.Value +
";"
);
}
}
swOut.Close();
xRead.Close();
bRet =
true
;
}
catch
(Exception e)
{
m_sError =
string
.Format(
"Exception: {0}"
, e.ToString());
}
return
bRet;
}
///
<summary>
/// Returns the filter string for the file selection box.
///
</summary>
///
<returns>
Filter string
</returns>
public
string
GetFileFilter()
{
string
strFilter =
"*.*"
;
return
strFilter;
}
///
<summary>
/// Indicates whether the converter can convert external formats to XML.
///
</summary>
///
<param name="oContext">
Context with parameters
</param>
///
<param name="bSupportsProgress">
Indicates whether the converter supports a progress bar.
</param>
///
<returns>
true: conversion is possible; false: conversion is not possible
</returns>
public
bool
CanImport(Eplan.EplApi.Base.Context oContext,
ref
bool
bSupportsProgress)
{
bSupportsProgress =
false
;
return
false
;
}
///
<summary>
/// Conversion from sImportFile to sXmlFile.
/// sXmlFile might be passed as "". In this case, the converter must set a file name.
/// EContext may point to an EProgress object to support a progress bar.
/// Returns true if successful.
///
</summary>
///
<param name="strInputFile">
Input file
</param>
///
<param name="strXmlFile">
Output file
</param>
///
<param name="oContext">
Context with parameters
</param>
public
bool
Import(
string
strInputFile,
string
strXmlFile, Eplan.EplApi.Base.Context oContext)
{
// TODO: Add XMLProcessor.import implementation
return
false
;
}
}

Registering a conversion module 
Each conversion module must be registered with EPLAN so that it is available during import or export. Since a conversion is only intended for a specific task, the scope of functions of the converter must be set during registration. This is done via the IInterface interface, as it is shown at the end of the above example. 
The InterfaceName property returns the interface name followed by the interface category. The category specifies in which export dialog the new processor will be displayed. The available interface categories can be found in the list of available XML processors under Eplan.EplApi.ApplicationFramework.XMLConverter and Eplan.EplApi.ApplicationFramework.XMLConverterCategories . See Also 
### XML Converters XML Converters 
### Reference IXMLProcessor Interface

### Przykłady kodu (C#)
```csharp
public class MySimpleXMLConverter : Eplan.EplApi.ApplicationFramework.IXMLProcessor
{
    public MySimpleXMLConverter()
    {
        //
        // TODO: Add constructor logic here
        //
    }
    string m_sError = string.Empty;
    Options m_optionsXMLProcessor = new Options();
    #region IXMLProcessor Members
    /// <summary>
    /// Returns a settings dialog for this processor.
    /// Dialog is only created, but not displayed!
    /// </summary>
    /// <returns>Interface of the created dialog.</returns>
    public Eplan.EplApi.ApplicationFramework.IOptions GetOption()
    {
        return m_optionsXMLProcessor;
    }
    /// <summary>
    /// Returns the name of the converter, as it will appear in the selection list.
    /// </summary>
    /// <returns>Name of converter, is shown in selection list.</returns>
    public string GetName()
    {
        String strName = "SimpleXMLProcessor";
        strName += " (";
        strName += GetFileFilter();
        strName += ")";
        return strName;
    }
    /// <summary>
    /// Returns an error message if an error occurred during export/import.
    /// </summary>
    ///<returns>Error message</returns>
    public string GetErrorMessage()
    {
        // TODO:  Add XMLProcessor.getErrorMessage implementation
        return m_sError;
    }
    /// <summary>
    /// Is called after import has been completed.
    /// </summary>
    /// <returns>If true, an Information dialog box is displayed.</returns>
    public bool PostImport()
    {
        // TODO:  Add XMLProcessor.postImport implementation
        return false;
    }
    /// <summary>
    /// Is called after export has been completed.
    /// </summary>
    /// <returns>If true, an Information dialog box is displayed.</returns>
    public bool PostExport()
    {
        // TODO:  Add XMLProcessor.postExport implementation
        return false;
    }
    /// <summary>
    /// Indicates whether the converter provides an export option.
    /// </summary>
    /// <param name="oContext">Context with parameters</param>
    /// <param name="bSupportsProgress">Indicates whether the converter supports a progress bar.</param>
    /// <returns>true: export is possible; false: export is not possible</returns>
    public bool CanExport(Eplan.EplApi.Base.Context oContext, ref bool bSupportsProgress)
    {
        bSupportsProgress = false;
        return true;
    }
    /// <summary>
    /// Converts the XML file to a special file.
    /// </summary>
    /// <param name="strXmlFile">Input file</param>
    /// <param name="strOutputFile">Output file</param>
    /// <param name="oContext">Context with parameters</param>
    /// <returns> Returns true if successful.</returns>
    public bool Export(string strXmlFile, string strOutputFile, Eplan.EplApi.Base.Context oContext)
    {
        bool bRet = false;
        try
        {
            // Short example for a simple export conversion
            System.Xml.XmlTextReader xRead = new System.Xml.XmlTextReader(strXmlFile);
            System.IO.StreamWriter swOut = new System.IO.StreamWriter(strOutputFile);
            xRead.WhitespaceHandling = System.Xml.WhitespaceHandling.None;
            string sFirstLang = string.Empty;
            while (xRead.Read())
            {
                if ((xRead.XmlLang.CompareTo(String.Empty) != 0) && (xRead.Value.CompareTo(String.Empty) != 0))
                {
                    if (sFirstLang.CompareTo(String.Empty) == 0) sFirstLang = xRead.XmlLang;
                    if (xRead.XmlLang.CompareTo(sFirstLang) == 0) swOut.WriteLine();
                    swOut.Write(xRead.XmlLang + ":" + xRead.Value + ";");
                }
            }
            swOut.Close();
            xRead.Close();
            bRet = true;
        }
        catch (Exception e)
        {
            m_sError = string.Format("Exception: {0}", e.ToString());
        }

        return bRet;
    }
    /// <summary>
    /// Returns the filter string for the file selection box.
    /// </summary>
    /// <returns>Filter string</returns>
    public string GetFileFilter()
    {
        string strFilter = "*.*";
        return strFilter;
    }
    /// <summary>
    /// Indicates whether the converter can convert external formats to XML.
    /// </summary>
    /// <param name="oContext">Context with parameters</param>
    /// <param name="bSupportsProgress">Indicates whether the converter supports a progress bar.</param>
    /// <returns>true: conversion is possible; false: conversion is not possible</returns>
    public bool CanImport(Eplan.EplApi.Base.Context oContext, ref bool bSupportsProgress)
    {
        bSupportsProgress = false;
        return false;
    }
    /// <summary>
    /// Conversion from sImportFile to sXmlFile.
    /// sXmlFile might be passed as "". In this case, the converter must set a file name.
    /// EContext may point to an EProgress object to support a progress bar.
    /// Returns true if successful.
    /// </summary>
    /// <param name="strInputFile">Input file</param>
    /// <param name="strXmlFile">Output file</param>
    /// <param name="oContext">Context with parameters</param>
    public bool Import(string strInputFile, string strXmlFile, Eplan.EplApi.Base.Context oContext)
    {
        // TODO:  Add XMLProcessor.import implementation
        return false;
    }
}
```

---
