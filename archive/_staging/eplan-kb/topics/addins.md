# EPLAN API — addins

*Przyszłość — migracja z .cs do DLL*

Dokumentów: 10

## Add-ins
*Źródło: `Add-ins.html`*
*Ścieżka: EPLAN API / User Guide / API Framework / Add-ins*

Add-ins EPLAN has a modular architecture. It is possible to add functionality to EPLAN and to change existing functionality. 
These different means to modify the system are implemented in modules, which can be loaded by EPLAN, so-called add-ins. So if you want to add functionality to EPLAN, you first need to create an add-in. You can enhance existing functionality for example by: 
- Adding new GUI items, such as ribbon buttons 
- Adding new actions, verifications, interactions, messages, XML processors 
- Handling EPLAN events and raising ones 
An add-in is an assembly, written in one of the .NET Framework programming languages. There are different ways to create such an assembly. Basically, you just need a simple text editor and the compiler provided by the .NET Framework. The rather more convenient way to create an add-in is by using an integrated development environment (IDE), like Visual Studio. 
### Remarks 
Add-in assemblies should be named like <YourCompanyName>.EplAddin.<NameOfTheProject>.dll . 
See Also 
### Development environment Development environment

---

## Assemblies
*Źródło: `Assemblies.html`*
*Ścieżka: EPLAN API / API Reference / Assemblies*

Assemblies Here is a detail description of all available API assemblies

---

## Creating add-ins in CSharp
*Źródło: `Creating add-ins in CSharp.html`*
*Ścieżka: EPLAN API / User Guide / API Framework / Add-ins / Creating add-ins in CSharp*

Creating add-ins in CSharp This section shows how to create an EPLAN add-in in C#. In order to show that the installation of the .NET Framework already provides all the necessary tools (C-Sharp compiler, etc.), the add-in is not created as a VisualStudio project, but simply using a text editor and the command line tools of the .NET Framework. 
### a) Getting started: First, it is useful to create a directory to store the source code for your add-in. For this example we create a folder named "SimpleCSharpAddIn". 
Now start your text editor of choice, e.g. notepad, and start writing the source code. 
### b) Creating the module class: 
Every EPLAN add-in, including the C# add-in we are going to create, requires a certain class for managing the add-in. This class must implement the functions declared by the IEplAddIn interface: 

### C# 
### Copy Code 
| public
class
AddInModule: Eplan.EplApi.ApplicationFramework.IEplAddIn
{
public
bool
OnRegister(
ref
System.Boolean bLoadOnStart)
{
bLoadOnStart=
true
;
return
true
;
}
public
bool
OnUnregister()
{
return
true
;
}
public
bool
OnInit()
{
return
true
;
}
public
bool
OnInitGui()
{
return
true
;
}
public
bool
OnExit()
{
return
true
;
}
}

Now save this source code in the folder "SimpleCSharpAddIn" as a file named "AddInModule.cs". 
### c) Compiling the assembly (DLL) 
Now it is time to use the C-Sharp compiler. The compiler is located in the directory of the .NET Framework, for example C:\WINDOWS\Microsoft.NET\Framework\v2.0.50727 . This folder should be in the search path. Open your favorite shell and change to the "SimpleCSharpAddInwhere" directory where you just saved "AddInModul.cs". 

Run the C-Sharp compiler ( csc.exe ) with the following parameters: 
csc /target:library /reference:..\..\..\..\bin\Eplan.EplApi.AFu.dll /out: EPLAN.EplAddin.SimpleCSharp.dll AddinModule.cs 

What is the meaning of these parameters? 

- /taget:library :  We want to create a DLL and no exe file. 
- /reference:..\..\..\..\bin\Eplan.EplApi.AFu.dll :  Search in Eplan.EplApi.AFu.dll for all missing data (e.g. I EplAddIn ) 
- /out : EPLAN.EplAddin.SimpleCSharp.dl l :  Name of the DLL to build is "EPLAN.EplAddin.SimpleCSharp.dll" 
- AddinModul.cs :  Name of the source file to compile 

If nothing went wrong with the compilation, you'll now find the DLL "EPLAN.EplAddin.SimpleCSharp.dll" in the folder "SimpleCSharpAddIn". Copy this file to the EPLAN platform bin folder. 
### d) Loading an add-in in EPLAN 
Now start EPLAN. If the following system extensions are loaded in EPLAN (which should normally be the case): EplanEplApiModuleu.erx , EplanEplApiModuleGUIu.erx . 
Click on the ribbon File > Extras > Interfaces . > API > Manage . 

After clicking on Manage , a dialog – as shown below – will appear. After pressing the button Load , you can select "Eplan.EplAddin.SimpleCSharp.dll" from the bin directory. 

Our add-in now appears in the list of the API modules dialog and will be loaded when EPLAN is started.That is about all it can do. What we need now is an action! 

### e) Adding an Action to the C-Sharp add-in 
Therefore, create a second source file and save it as "SimpleCSharpAction.cs" in your source directory. To create an action, we need a class that implements the I EplAction interface. For a more detailed explanation, see the " Actions " topic. 

### C# 
### Copy Code 
| using
Eplan.EplApi.ApplicationFramework;
public
class
CSharpAction: IEplAction
{
public
bool
Execute(ActionCallingContext ctx )
{
new
Decider().Decide(EnumDecisionType.eOkDecision,
"CSharpAction was called!"
,
""
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
return
true
;
}
public
bool
OnRegister(
ref
string
Name,
ref
int
Ordinal)
{
Name =
"CSharpAction"
;
Ordinal = 20;
return
true
;
}
public
void
GetActionProperties(
ref
ActionProperties actionProperties)
{
actionProperties.Description=
"Action test with parameters."
;
}
}

Now the compiler call needs to be slightly extended: 
csc /target:library /reference:..\..\..\..\bin\Eplan.EplApi.AFu.dll /reference:..\..\..\..\bin\Eplan.EplApi.Baseu.dll /out:SimpleCSharpAddIn.dll AddinModule.cs SimpleCSharpAction.cs 

If you added an action to an already loaded add-in, the add-in needs to be unloaded and loaded again for the changes to take effect. 
So you just open the API modules dialog again, select the add-in in the list and click the Unload button. Then load the add-in again. 

Now, you can call your new action in EPLAN via a command line call: 
W3u.exe CSharpAction 

When you start the action, the Execute() function of the CSharpAction is called. This function just shows a message box with the text "CSharpAction was called!". ( new Decider().Decide(EnumDecisionType.eOkDecision, "CSharpAction was called!", "", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK); ). 
### Remarks 
Please mind that users may start EPLAN in QUIET mode using W3u.exe /Quiet or the API could be initialized by an offline program . Because of this, it is not recommended to show any message boxes in the methods of the IEplAddIn interface. If you encounter some problem during registering or initializing an add-in, just create and throw a BaseException or use BaseException.FixMessage(...) to add the message to the system messages list. See Also Creating add-ins in Visual Basic.Net

### Przykłady kodu (C#)
```csharp
public class AddInModule: Eplan.EplApi.ApplicationFramework.IEplAddIn
       {
            public bool OnRegister(ref System.Boolean bLoadOnStart)
            {
                  bLoadOnStart=true;
                  return true;
             }
            public bool OnUnregister()
            {
                  return true;
            }
            public bool OnInit()
            {
                  return true;
            }
            public bool OnInitGui()
            {
                  return true;
            }
            public bool OnExit()
            {
                  return true;
            }
      }
```
```csharp
using Eplan.EplApi.ApplicationFramework;
public class CSharpAction: IEplAction
{
      public bool Execute(ActionCallingContext ctx )
      {
            new Decider().Decide(EnumDecisionType.eOkDecision, "CSharpAction was called!", "", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
            return true;
      }
      public bool OnRegister(ref string Name, ref int Ordinal)
      {
            Name  = "CSharpAction";
            Ordinal     = 20;
            return true;
      }
      public  void GetActionProperties(ref ActionProperties actionProperties)
      {
           actionProperties.Description= "Action test with parameters.";
      }
}
```

---

## Creating add-ins in Visual Basic.Net
*Źródło: `Creating add-ins in Visual Basic.Net.html`*
*Ścieżka: EPLAN API / User Guide / API Framework / Add-ins / Creating add-ins in Visual Basic.Net*

Creating add-ins in Visual Basic.Net Writing an add-in in Visual Basic.NET is basically the same as described in the topic " Creating add-ins in CSharp ". The only difference is the source code syntax and the way the compiler is called. 

Create a "VBAddInModule.vb" file with the following content: 

### VB 
### Copy Code 
| Public
Class
AddInModule
Implements
Eplan.EplApi.ApplicationFramework.IEplAddIn
Public
Function
OnRegister(
ByRef
bLoadOnStart
As
System.Boolean)
As
Boolean
_
Implements
Eplan.EplApi.ApplicationFramework.IEplAddIn.OnRegister
bLoadOnStart =
True
Return
True
End Function
'OnRegister
Public
Function
OnUnregister()
As
Boolean
_
Implements
Eplan.EplApi.ApplicationFramework.IEplAddIn.OnUnregister
Return
True
End Function
'OnUnregister
Public
Function
OnInit()
As
Boolean
_
Implements
Eplan.EplApi.ApplicationFramework.IEplAddIn.OnInit
Return
True
End Function
'OnInit
Public
Function
OnInitGui()
As
Boolean
_
Implements
Eplan.EplApi.ApplicationFramework.IEplAddIn.OnInitGui
Return
True
End Function
'OnInitGui
Public
Function
OnExit()
As
Boolean
_
Implements
Eplan.EplApi.ApplicationFramework.IEplAddIn.OnExit
Return
True
End Function
'OnExit
End Class
'AddInModule

Invoke the Visual Basic compiler ( vbc.exe ) with the following parameters: 
vbc /target:library /reference:..\..\..\..\bin\Eplan.EplApi.AFu.dll /out:SimpleVBAddIn.dll VBAddinModule.vb 

For an action create the following source file and save it as "SimpleVBAction.cs" in your source directory. To create an action, we need a class that implements the IEplAction interface. For a more detailed explanation, see the " Actions " topic. 

### VB 
### Copy Code 
| Imports
Eplan.EplApi.ApplicationFramework
Public
Class
VBAction
Implements
IEplAction
Public
Function
Execute(ctx
As
ActionCallingContext)
As
Boolean
Implements
IEplAction.Execute
Dim
dec
As
Decider =
New
Decider
dec.Decide(EnumDecisionType.eOkDecision,
"VBAction was called!"
,
""
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)
Return
True
End Function
'Execute
Public
Function
OnRegister(
ByRef
Name
As
String
,
ByRef
Ordinal
As
Integer
)
As
Boolean
_
Implements
IEplAction.OnRegister
Name =
"VBAction"
Ordinal = 20
Return
True
End Function
'OnRegister
Public
Sub
GetActionProperties(
ByRef
actionProperties
As
ActionProperties) _
Implements
IEplAction.GetActionProperties
actionProperties.Description =
"Action test with parameters."
End Sub
'GetActionProperties
End Class
'VBAction

vbc /target:library /reference:..\..\..\..\bin\Eplan.EplApi.AFu.dll /reference:..\..\..\..\bin\Eplan.EplApi.Baseu.dll /out:SimpleVBAddIn.dll VBAddinModule.vb SimpleVBAction.vb

### Przykłady kodu (C#)
```csharp
Public Class AddInModule
   Implements Eplan.EplApi.ApplicationFramework.IEplAddIn

   Public Function OnRegister(ByRef bLoadOnStart As System.Boolean) As Boolean _
     Implements Eplan.EplApi.ApplicationFramework.IEplAddIn.OnRegister
      bLoadOnStart = True
      Return True
   End Function 'OnRegister

   Public Function OnUnregister() As Boolean _
    Implements Eplan.EplApi.ApplicationFramework.IEplAddIn.OnUnregister
      Return True
   End Function 'OnUnregister

   Public Function OnInit() As Boolean _
    Implements Eplan.EplApi.ApplicationFramework.IEplAddIn.OnInit
      Return True
   End Function 'OnInit

   Public Function OnInitGui() As Boolean _
    Implements Eplan.EplApi.ApplicationFramework.IEplAddIn.OnInitGui
      Return True
   End Function 'OnInitGui

   Public Function OnExit() As Boolean _
    Implements Eplan.EplApi.ApplicationFramework.IEplAddIn.OnExit
      Return True
   End Function 'OnExit
End Class 'AddInModule
```
```csharp
Imports Eplan.EplApi.ApplicationFramework

Public Class VBAction
   Implements IEplAction
   Public Function Execute(ctx As ActionCallingContext) As Boolean Implements IEplAction.Execute
      Dim dec As Decider = New Decider
      dec.Decide(EnumDecisionType.eOkDecision, "VBAction was called!", "", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)
      Return True
   End Function 'Execute

   Public Function OnRegister(ByRef Name As String, ByRef Ordinal As Integer) As Boolean _
    Implements IEplAction.OnRegister
      Name = "VBAction"
      Ordinal = 20
      Return True
   End Function 'OnRegister

   Public Sub GetActionProperties(ByRef actionProperties As ActionProperties) _
    Implements IEplAction.GetActionProperties
      actionProperties.Description = "Action test with parameters."
   End Sub 'GetActionProperties
End Class 'VBAction
```

---

## Creating an add-in in VisualStudio
*Źródło: `Creating an add-in in VisualStudio.html`*
*Ścieżka: EPLAN API / User Guide / API Framework / Add-ins / Creating an add-in in VisualStudio*

Creating an add-in in VisualStudio Compared to using a text editor and the compiler provided by the .NET Framework, it is much easier to create an add-in with using a development environment such as Visual Studio 2022. 
Eplan templates are installed in Visual Studio with the API setup, which can be downloaded from the EPLAN homepage . 
To create an add-in, just create a project in Visual Studio using the "Eplan Api Addin" template from C# Projects: 

The new project already references the essential EPLAN API assemblies and a file with the module class: 

You can add a new Action class by the Add New Item menu point and selecting the template "Eplan Action": 

For Visual Basic, the work flow is identical.

---

## Registration
*Źródło: `Registration.html`*
*Ścieżka: EPLAN API / User Guide / API Framework / Add-ons / Registration*

Registration ### Manual registration of an add-on 
Start EPLAN now. In ribbon item File > Extras > Interfaces you will find the category Add-ons > Manage . 

Figure 1: Ribbon option Add-ons 
After clicking on Manage , a dialog – as shown below – will appear. By pressing the button you can select the install.xml file from the CFG directory. 

Figure 2: Manual registration of an add-on 
The add-on now appears in the add-on list. To register it, you have to check the corresponding check-box in the "Registered" column. Only then will the DLL file stored in the BIN folder appear in the list of the API modules dialog and will be loaded. 

### Registration of an add-on via an action 
It is also possible to register an add-on via an action call. This is based on automatic actions for the EPLAN command line functionalities – also called "command line actions". 
Tip: 
For further information about " Automatic actions " see our API Help. 
For the proper use of that command line action, it is necessary to pass further general command line parameters. 
| 
Parameter | 
Description 
| 
Path | 
The path where the add-on is located 
| 
InstallFile | 
The complete path to the install.xml 

Example: 
Registering Add-ons: 
XSettingsRegisterAction /Path:c:\MyAddOn 
XSettingsRegisterAction /InstallFile: c:\MyAddOn\CFG\Install.xml 

After registering the add-on via an action call, you have to verify if the add-on is registered in the add-ons dialog and the belonging add-in files are loaded. 
### Automatic registration of an add-on 
There are two ways to initiate the automatic registration of an add-on when EPLAN is started. 
### Automatic registration with registry settings 
In the Registry Editor – see figure 3 – all EPLAN installation can be found at: 
HKEY_LOCAL_MACHINE / SOFTWARE / EPLAN / EPLAN W3 

Figure 3: Automatic registration with registry settings in the Registry Editor 

An add-on can be found like this: 
<Add-on> 
<Version> 
Autoreg TRUE 
XMLPath C:\Program Files\EPLAN\ApiTest Add-on\2.9.0\Cfg\install.xml 

Autoreg : When this flag is "TRUE", the add-on can register automatically. 
XMLPath : The path to install.xml of the add-on. 
After double clicking on Autoreg , a dialog – as shown below – will appear. 

Figure 4: Value editor 
Now you can set the value for the automatic registration to "TRUE" or "FALSE". 
### Automatic registration with company settings 
Start EPLAN now. Select the ribbon item File and select the option Settings… . 

Figure 5: Option Settings... 
After clicking on Settings... , the settings service dialog – as shown below – will appear. By navigating to Company > Management > Add-ons you can then register a server path to EPLAN. 

Figure 6: Settings: Add-ons 
At the startup of EPLAN, this folder is searched for install.xml files. When an add-on install.xml is found (this means the install.xml is in the CFG folder, the version matches, etc.), the add-on will be registered.

---

## Shadow Copying
*Źródło: `Shadow Copying.html`*
*Ścieżka: EPLAN API / User Guide / API Framework / Add-ons / Shadow Copying*

Shadow Copying Since version 2.6, EPLAN API assemblies are shadow copied, i.e. during registration, they are stored into a temporary folder, and loaded from there (See API Help: " Shadow Copying API Assemblies "). 
This concerns both add-ons and add-ins. 
For add-ons, the entire bin directory of the add-on with subdirectories is copied to the user application roaming directory ( %appdata%\EPLAN\ShadowCopyAssemblies\Process-ID\Addon-Name ). 
Example: 

So all files ( *.dlls and *.exe ) and all bin subdirectories (language subdirectories etc.) are also copied. This is done when EPLAN starts and an add-on is registered or when an add-on is manually registered from the Add-ons dialog. 
EPLAN will load the assemblies of the add-on from the shadow directory and not from the original add-on directory. This means that an add-on can be updated without having to stop all EPLAN instances that use the add-on. 

### What EPLAN does ? 
At any start of EPLAN, the registry or the path for server add-ons is scanned for new add-ons. The install.xml is read and the following things are done: 
- Does this add-on fit to the main version? 
- Is the correct license option booked? 
- Is the version correct? 
When everything is done so far, EPLAN then registers the new add-on: 
- Read all *.xml files from the CFG folder. The settings are copied to the settings of the main version. 
- Read the eplset<applicationmodifer>.xml : All binaries defined there are loaded now. 
- Load the API modules. 
- Register the API references. 
- Register the scripts. 
- Copy the base data of the add-on to the base data of EPLAN.

---

## Shadow Copying API Assemblies
*Źródło: `Shadow Copying API Assemblies.html`*
*Ścieżka: EPLAN API / User Guide / API Framework / Add-ins / Shadow Copying API Assemblies*

Shadow Copying API Assemblies Since version 2.6, EPLAN API assemblies are shadow copied, i.e. they are saved in a temporary folder during registration and loaded from there. 
The benefit of the shadow copy technique is that the original assemblies are not locked, so that newer versions can be distributed via a network share even if they are currently being used by other workstations. 
This applies to both add-ons and add-ins. 

### Add-ons 
The entire bin directory of the add-on with its subdirectories is copied to the user application roaming directory ( %appdata%\EPLAN\ShadowCopyAssemblies\Process-ID\Addon-Name ). 
This means that all files ( *.dlls and *.exe ) and all bin subdirectories (language subdirectories, etc.) are also copied. This is done when EPLAN is started and an add-on is registered or when an add-on is registered manually from the Add-ons dialog. 
EPLAN loads the assemblies of the add-on from the shadow directory and not from the original add-on directory. This allows an add-on to be updated without the need to stop all EPLAN instances using the add-on. 

### Add-ins 
When an add-in is loaded by EPLAN start or via API > Manage option, it is copied to a shadow directory ( %appdata%\EPLAN\ShadowCopyAssemblies\Process-ID\ ). 
EPLAN keeps the original add-in path for further assembly resolving. This means that if an add-in references other assemblies from the add-in original path, these referenced assemblies will be found. 
After resolving they will be copied to the shadow directory. The problem could be referencing data from other directories using a relative path to the original add-in directory. 
As a solution, IEplAddInShadowCopy interface was created, which allows to get the original path of an add-in. 
In addition, conflicts can arise when multiple add-in / add-on projects in a solution refer to an assembly with a namespace and class of the same name, but different versions. The following scenario should be considered: For example, if you use the "Write" library of version 1.0.0 in one project (Project1) and the "Write" library of version 2.0.0 in the other project (Project2), this will lead to unwanted behavior in your solution. 

Depending on which project – be it Project1 or Project2 – you call first, it will be executed correctly and will reference the correct library. If you then execute the other project, it will reference the previous library, the first version is executed. 
To work around this behavior, sign the library versions independently of each other. You can then use the library with different versions at will. 
Signing gives the library a specific key token or "strong name" that helps distinguish the libraries. 
See Also https://msdn.microsoft.com/en-us/library/ms404279(v=vs.110).aspx

---

## Signing EPLAN assemblies
*Źródło: `Signing EPLAN assemblies.html`*
*Ścieżka: EPLAN API / User Guide / API Miscellaneous / Signing EPLAN assemblies*

Signing EPLAN assemblies As a part of your EADN (EPLAN API Developer Network) partnership with EPLAN GmbH & Co. KG, you get the opportunity to sign your software interface with our products. This allows you (or your customer) to use the API assembly without having an EPLAN API developer license on his workstations. Instead, he receives – through you – a runtime license for an API interface. 
This chapter describes how you (or your developers) should proceed, to get properly signed EADN modules. 

### What is possible with API licenses? 
At first there should be clarified why signing is necessary. There are 2 kinds of API licenses: 
a) API developer license – It should be used only for development and testing of an API interface. Normally it has a limitation of a maximum size of EPLAN projects to 5 pages. Only unsigned API programs can be loaded using it. 
b) API runtime license – In this case there can be used only signed API programs, so we need to sign it. The routine how to do it is described bellow. 

A user can check available licenses and select one by starting EPLAN with shift key (then the Select license dialog will appear). When EPLAN is already running, the current license can be retrieved from: 
a) the About EPLAN dialog 
b) in the API using the EplApplication.License property and the License class. 

### The Concept of EADN / API Runtime signing 
EADN / API Runtime signing uses a concept of combining standard .NET strong-naming with additionally including an EPLAN license option to the software. 
To achieve this combination, please follow the instructions in this chapter. 

### Requirements 
After you have concluded your EADN contract or purchased an API Runtime license and you created a new software interface with EPLAN, the main administrator of your EPLAN cloud organization will get informed about a new entitlement for using the cloud-based EADN Signing service. Additionally, you will receive a file containing the public part of a standard signature key, normally used for strong-naming a .NET assembly. We created this key especially for your software. 
For using the EPLAN-Cloud based signing service, you have to be member of the regarding organization and got assigned the role User to the application EADN Singing : 

### How to proceed 
Take the following steps to get your application EADN / API Runtime signed: 

### Modify the AssemblyInfo.cs 
In your software projects, you need to add an additional attribute to your AssemblyInfo files of all the assemblies that are referencing EPLAN API Assemblies. The EplanSignedAssemblyAttribute is implemented in the Eplan.EplApi.Starter.dll , which you always have to reference in your API application. The following example shows how to use the attribute in your AssemblyInfo file: 

### C# 
### Copy Code 
| using
System.Reflection;
using
System.Runtime.CompilerServices;
using
System.Runtime.InteropServices;
using
Eplan.EplApi.Starter;
//..
[assembly: EplanSignedAssemblyAttribute(
true
)]

### Delay sign the assemblies 
The easiest way for delay signing your assemblies ( DLL or exe ) is entering the public key file in the signing properties of your software projects in Visual Studio. Check Sign the assembly and activate the Delay sign only flag. See the following image: 

The delay signing is done, when building the software project and with it creating the assembly. 
Alternatively, you can use Microsoft's Assembly Linker "Al.exe" to manually delay sign assemblies. Please refer to respective MSDN documentation. 

### Upload files manually 
Log in to the EPLAN Cloud Developer Portal https://developer.eplan.com 
Notice: 
An EPLAN Cloud account is required to access the developer portal. 
As an old alternative to the "Upload files manually" step, you can use the outdated but still working method of uploading via EPLAN File Exchange. For this see " Outdated process: Using the EPLAN File Exchange ". 

Authorize manual usage of EADN-Signing 
- Select EADN-Signing in available list of APIs 
- Click on Authorize 
→ The authorization dialog opens 
- Click the drop-down list and select EADN Signing 
- Click on Authorize 
→ The API is allowed for manual usage via Try it out feature 
- Click on Close 
→ The authorization dialog is closed 
→ Activated authorization is shown via closed lock symbol Notice: 
When a different API is selected in the list of available APIs, an active authorization is discarded. Repeat the above steps to perform an authorization again. 

### Upload pre-signed assemblies / executables 

- Click on endpoint POST /assemblies 
→ Section gets expanded and show more details 
- Click on Try it out 
→ Enables value entry in the Request Body section 
- Click on Add file item 
→ Adds a new Choose file row 
- Click on Choose file 
→ File selection dialog opens 
→ Select pre-signed assembly 
→ Confirm with Open to add local file for upload 
→ Repeat steps 3 and 4 for each file which needs to get signed 
- (Optional) Add personal Comment for full upload-job 
→ The authorization dialog is closed 
- Click on Execute 
→ All selected files will get uploaded and tried to get signed 
- Check Response of server in column Code 
- Select and copy value of ID in Response body , for later usage of all files 

### Check status of uploaded files 
Log in to the EPLAN Cloud Developer Portal https://developer.eplan.com 
If required, perform Authorize manual usage of EADN-Signing. 
Make sure you have the ID of the desired upload process handy (see also " Select and copy value of ID in Response body "). Notice: 
Use the endpoint GET /assemblies to return a list of all existing uploaded packages inside your organization and determine the required ID. 

- Click on endpoint GET /assemblies/{id}/status 
→ Section gets expanded and show more details 
- Click on Try it out 
→ Enables value entry in the Parameters section 
- Insert previous copied ID into parameter Id of the uploaded package 
- Click on Execute 
→ Details about given signing job are getting returned 
- Check response of server in section Responses and get details about results of signing process 

### Receive the signed Assemblies manually 
Log in to the EPLAN Cloud Developer Portal https://developer.eplan.com 
If required, perform Authorize manual usage of EADN-Signing 
Make sure you have the ID of the desired upload process handy (see also " Select and copy value of ID in Response body "). Notice: 
Use the endpoint GET /assemblies to return a list of all existing uploaded packages inside your organization and determine the required ID. 

- Click on endpoint GET /assemblies/{id} 
→ Section gets expanded and show more details 
- Click on Try it out 
→ Enables value entry in the Parameters section 
- Insert previous copied ID into parameter Id of the uploaded package 
- Click on Execute 
→ Download request is getting executed 
- Click on Download file in section Responses 
→ Save file selection dialog opens 
→ Confirm with Save to download the file 

### Delete uploaded files manually 
Log in to the EPLAN Cloud Developer Portal https://developer.eplan.com 
If required, perform Authorize manual usage of EADN-Signing (see also " Limitations " below) 
Make sure you have the ID of the desired upload process handy (see also " Select and copy value of ID in Response body ") Notice: 
Use the endpoint GET /assemblies to return a list of all existing uploaded packages inside your organization and determine the required ID. 

- Click on endpoint DELETE /assemblies/{id} 
→ Section gets expanded and show more details 
- Click on Try it out 
→ Enables value entry in the Parameters section 
- Insert previous copied ID into parameter Id of the uploaded package 
- Click on Execute 
→ Delete request is getting executed 
- Check result request in column Code in section Responses 

### Fully automated signing process 
### Preparations / prerequisites 
To take advantage of fully automated signing of assemblies during the build process of Visual Studio, you must create a personal access token (further called PAT ) for the application EADN Signing inside the profile editor of your EPLAN Cloud organization. 
See EPLAN Cloud help: 
• Open My Settings 
• Add personal access token (PAT) 
• Roles and permissions Notice: 
Without assigned role User to EADN Service , no PAT creation is available for the user. 
Removing already assigned role User from EADN Signing makes existing PAT invalid. 
No prolonging of already created PAT ( new one needed after expiration ) 
E-Mail notification is automatically sent from EPLAN Cloud. 

Download the provided PowerShell script from the Developer Portal 
EADN Singing for using it in Post-build event of Visual Studio. 

An example for calling the script including available parameters can be found inside the script itself: 

### 
### Copy Code 
| # Example command line:
#
# powershell -ExecutionPolicy Bypass -file
"<YourFolderName>\PostBuildScript.ps1"
-comment
"This is a test comment from $(USERNAME)"
-accessToken
"<YourPATforEADNSigningService>"
-assemblies
"<SourceFolderWithPreSignedFiles>\$(TargetFileName)"
-destinationPath
"<TargetFolder>"
-deleteAfterwards

Notice: 
Depending on your IT guidelines, calling PowerShell scripts without bypassing executions policy may return an error. 
The active policy can get checked via running command Get-ExecutionPolicy -List 
Tip: 
See also Microsoft documentation . 

### Parameter description 

### Parameter name 
### Mandatory 
### Description 

### baseUrl | No | Only for signing in Chinese environment; use parameter value*: 
https://api.eplan.com.cn/eadn-signing/v1.0 

### comment | No | Comment for complete upload job 

### accessToken | Yes | PAT which was created in User profile 

### assemblies | Yes | Filename(s) of assemblies / executables which have to get signed 

### destinationPath | Yes | Local target folder for downloading result-package ( via PowerShell script target directory is tried to get created if missing ) 

### deleteAfterwards | No | Delete upload-job after tried signing automatically ( Note: storage quota limitations ) 
* current baseUrl can be viewed at any time in the Developer Portal 

Example: Command line call for signing a single file (not China!) 
powershell -ExecutionPolicy Bypass -file "<YourFolderName>\PostBuildScript.ps1" -comment "This is a test comment from $(USERNAME)" -accessToken "<YourPATforEADNSigningService>" 
-assemblies "<SourceFolderWithPreSignedFiles>\$(TargetFileName)" -destinationPath "<TargetFolder>" -deleteAfterwards 
Example: Command line call for signing multiple files (not China!) 
powershell -ExecutionPolicy Bypass -file "<YourFolderName>\PostBuildScript.ps1" -comment "This is a test comment from $(USERNAME)" -accessToken "<YourPATforEADNSigningService>" 
-assemblies "<SourceFolder1>\<YourFile1.dll>,<SourceFolder2>\<YourFile2.dll>" -rootDirectory "<PathToDirectoryOfAssemblies>" -destinationPath "<TargetFolder>" -deleteAfterwards 
Example: Command line call for signing a single file (China only!) 
powershell -ExecutionPolicy Bypass -file "<YourFolderName>\PostBuildScript.ps1" -baseUrl "https://api.eplan.com.cn/eadn-signing/v1.0" -comment "This is a test comment from $(USERNAME)" -accessToken "<YourPATforEADNSigningService>" 
-assemblies "<SourceFolderWithPreSignedFiles>\$(TargetFileName)" -destinationPath "<TargetFolder>" -deleteAfterwards 
Example: Command line call for signing multiple files (China only!) 
powershell -ExecutionPolicy Bypass -file "<YourFolderName>\PostBuildScript.ps1" -baseUrl "https://api.eplan.com.cn/eadn-signing/v1.0" -comment "This is a test comment from $(USERNAME)" -accessToken "<YourPATforEADNSigningService>" 
-assemblies "<SourceFolder1>\<YourFile1.dll>,<SourceFolder2>\<YourFile2.dll>" -rootDirectory "<PathToDirectoryOfAssemblies>" -destinationPath "<TargetFolder>" -deleteAfterwards 

### Adopt command line for PostBuild-event in Visual Studio 

- Click on Build events 
→ Pre- and Post-build details of Visual Studio are shown 
- Click on Edit Post-build… 
→ Post-build Event Command Line dialog opens 
- Paste required command line call 
- Click on OK 
→ Post-build Command Line dialog is closed 
Output console will show details after building: 

All files (no matter if singing process, was successful or not) will get extracted to given folder in parameter destinationPath . 

### Limitations 
• The filenames in one upload have to be unique. Adding the same filename multiple times (on the same folder level) is not allowed, because it can not be reflected in the ZIP-file for download. 

• Each upload job can have a max. total file size of ~40 MB 

• There is an upload limit of max. 9999 kept upload jobs for each organization. 

• No automatic “cleanup” is done in organization storage. 

• If upload limit is reached, older uploaded files have to get deleted before new uploads are possible. Tip: 
It is recommended to delete uploaded files directly after signing (no matter if signing was successful or not), to avoid reaching the upload limit at all. 
Notice: 
Further details can be also found in the Developer Portal: ProblemTypes of EADN signing 

### Special cases 
a) How to sign automatically generated serialization DLLs 
If you use an automatically created serialization DLL for your classes, you need to delay-sign them via the sgen.exe tool. This tool can be found the SDK directory of your development environment. Example: 
"C:\Program Files\Microsoft Visual Studio 8\SDK\v2.0\bin\sgen.exe" /compiler:/delaysign+ /assembly:"MyDllToBeSerialized.dll" /proxytypes 
/reference:"Eplan.EplApi.AFu.dll" /reference:<…all further references you need> /compiler:/keyfile:"D:\MyPublicKey.snk" 
b) Signing of your own COM interop DLLs 
As you probably know, any strong-named .NET assembly can only reference / load other strong-named assemblies. In case your application registers COM DLLs, the development environment normally automatically creates so-called interop DLLs, which contain the .NET wrapping of the respective COM methods. Normally, these DLLs are not signed. To create these assemblies in an already delay-signed way Microsoft provides the command line tool tlbimp.exe – also to be found in the SDK directory of your development environment. See the following example, how it is used: Example: 
"C:\Program Files\Microsoft Visual Studio 8\SDK\v2.0\Bin\tlbimp.exe" yourComInterface.dll /delaysign /publickey:C:\YourKeyFilePublic.snk /out:Interop.yourComInterface.dll 

### Outdated process: Using the EPLAN File Exchange 
As an old alternative to the "Upload files manually" step, you can use the outdated but still working method of uploading via EPLAN File Exchange: 
### Requirements 
You need the login data of your account for the EPLAN file exchange website and the main administrator of your EPLAN cloud organization will get informed about new entitlement for using the cloud-based EADN Signing service. 

### Zip and Upload to EPLAN File Exchange 
Create one or several ZIP archives containing all the assemblies to be signed. Please take into account that the zip files may not be password-protected. 
Log in to the EPLAN file exchange portal at https://service.eplan.de/exchange with the login data mentioned above. 

Select the software project for which the assemblies should be signed. The project has to be the same as the one for which you received and used the respective public key. 

Now upload the zip file to our server by clicking Upload one file , selecting the zip file and clicking Upload . This triggers the signing process. 

### Receive the signed Assemblies 
As soon as your files have been signed you will receive an email that you can download the ready-signed files again from our file exchange portal. Log in again and find your files under "My downloads". The ZIP file contains an additional log file with a message, whether the signing was successful or not. In case the signing procedure failed, the log file will contain further information about the problem. 

### What to do in case of problems 
In case of any problems with signing, please write to EPLAN API Support: support-eplan@eplan.de.

### Przykłady kodu (C#)
```csharp
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using Eplan.EplApi.Starter;
//..
[assembly: EplanSignedAssemblyAttribute(true)]
```
```csharp
# Example command line:
#
# powershell -ExecutionPolicy Bypass -file "<YourFolderName>\PostBuildScript.ps1" -comment "This is a test comment from $(USERNAME)" -accessToken "<YourPATforEADNSigningService>" -assemblies "<SourceFolderWithPreSignedFiles>\$(TargetFileName)" -destinationPath "<TargetFolder>" -deleteAfterwards
```

---

## Unregistration
*Źródło: `Unregistration.html`*
*Ścieżka: EPLAN API / User Guide / API Framework / Add-ons / Unregistration*

Unregistration ### Manual unregistration of an add-on 
After clicking the Add-ons option (as shown in figure 1), the same dialog – as shown in figure 2 – will appear. After deactivating the add-on,  the button will be enabled. 

Figure 7: Unregister add-ons 
By clicking on the delete button, the add-on will be deleted from the list and also will the belonging add-in be deleted from the list of the API module dialog. 
Warning: 
The delete button will only be enabled, when the add-on was manually registered before. 

### Unregistration of an add-on via an action 
It is also possible to unregister an add-on via an action call. 

| 
Parameter | 
Description 
| 
Path | The path where the add-on is located 
| 
InstallFile | 
The complete path to the install.xml 

Example: 
Registering Add-ons: 
XSettingsUnregisterAction /Path:c:\MyAddOn 
XSettingsUnregisterAction /InstallFile: c:\MyAddOn\CFG\Install.xml 

After you unregistered the add-on via the action call, you may want to verify if the add-on is actually unregistered in the Add-ons dialog and the belonging add-in files are unloaded. 
### Automatic unregistration of an add-on 
Like there are two ways to initiate the automatic registration of an add-on when EPLAN is started, there are two ways to reset this setting as well. 
### Automatic unregistration with registry settings 
To reset the automatic registration with the Registry Editor , you only have to change the value data to "FALSE" (see figure 4). 
### Automatic unregistration with company settings 
To reset the automatic registration with company settings, you should leave the File path for automatic add-on registration field in the Settings: Add-ons dialog – as shown in figure 6 – empty .

---
