# EPLAN API — parts-masterdata

*Później — BOM, części*

Dokumentów: 5

## API MasterData
*Źródło: `API MasterData.html`*
*Ścieżka: EPLAN API / User Guide / API MasterData*

API MasterData The API MasterData ( Eplan.EplApi.MasterData ) namespace provides functionality to access parts database items and symbol libraries.

---

## API Parts Management Extension
*Źródło: `API Parts Management Extension.html`*
*Ścieżka: EPLAN API / User Guide / API Miscellaneous / API Parts Management Extension*

API Parts Management Extension The API Parts Management Extension feature can be used to add your own custom information to parts stored in the EPLAN parts database. It is intended for information that you don't want to set as part properties. 
You store this information in your own database and can attach it to the part and visualize it. When a part which references such custom information is exported or stored in a project, the information is stored as a sting in the indexed ARTICLE_CUSTOM_DATA_INDEX and ARTICLE_CUSTOM_DATA_VALUE properties. The first property contains the name of the add-in to which the information belongs, and the second property contains the data string at the same index position. 
To use this feature, you must call the MDPartsManagement.RegisterAddin(<Add-inName>, <ActionName>) and MDPartsManagement.RegisterItem(<Add-inName>, <ItemType>) methods in your add-in. As <ItemType> you set the string "eplan.part" (There is also the possibility to register other custom items in the parts management tree by setting other values for <ItemType> ). As <Add-inName> you set the assembly name of your add-in, which is usually the DLL title without the extension .dll . In your add-in, you implement an action with the name you set in the parameter <ActionName> . 
Your action will then be called on different events in the parts management. It has a different set of parameters passed in the ActionCallingContext on each time. The action parameter tells you what kind of "event" is called. The parameter can contain the following values: 
### List of "action" calls: 

### "Action" value 
### Description 
### Parameters 

### input 
### output 
| GetRootLevel | The first tree level is requested. | itemtype : Type of the item for which the root node is being requested | key : Identifying key 
text : Text to display in the tree 
subnode : (bool) Are further sub nodes available? (1 = yes, 0 = no) 
| GetNextLevel | The next level of the tree is requested. | itemtype : Type of the item being expanded in the tree 
key : Node below which the next tree level is requested | key : Identifying key 
text : Text to display in the tree 
subnode : (bool) Are further sub nodes available? (1 = yes, 0 = no) 
| CreateDatabase | A new parts database was created. | database : Name of the created database | 
| OpenDatabase | A new parts database was opened. | database : (string) Name of the newly opened database 
readonly : (bool) Read-only status of the opened parts database (1 = "read-only", 0 = "read/write") | 
| CloseDatabase | The current database was closed. | | 
| SelectItem | An item / part was selected in parts management. | itemtype : Item type of the selected element 
partnr : Selected part number (if only one part is selected) 
variant : Selected part variant (if only one variant is selected) 
key : Identifying key of the selected element | 
| PreShowTab | An item / part was selected in parts management. You have now the possibility to show / hide tab sheets that are registered for this element. | itemtype : Item type of the selected element 
partnr : Selected part number (if only one part is selected) 
variant : Selected part variant (if only one variant is selected) 
key : Identifying key of the selected element 
tabsheet : Tab sheet to be checked. The tab sheet was previously registered using MDPartsManagement.RegisterTabsheet(...) | show : (bool) Should the tab sheet be displayed? (1 = yes (default), 0 = no) 
| SaveItem | An item / part was saved in parts management. | partnr : Selected part number (if only one part is selected) 
variant : Selected part variant (if only one variant is selected) 
itemtype : Item type of the selected element 
key : Identifying key of the selected element | 
| CopyItem | An item / part was copied in parts management (by the context menu items Copy and Paste ). | itemtype : Item type of the copied element 
key : Identifying key of the currently selected element (optional) 
sourcekey : Identifying key of the element to copy | 
| CutCopyItem | An item / part was cut in parts management (by the context menu items Cut and Paste ). | itemtype : Item type of the cut element 
key : Identifying key of the currently selected element (optional) 
sourcekey : Identifying key of the element to cut | key : Identifying key of the created element 
| SelectCopyItem | The context menu item Copy was clicked in parts management tree. | itemtype : Item type of the copied element 
key : Identifying key of the selected element (optional) | 
| SelectCutItem | The context menu item Cut was clicked in parts management tree. | itemtype : Item type of the cut element 
key : Identifying key of the selected element (optional) | 
| SelectPasteItem | The context menu item Paste was clicked in parts management tree. | itemtype : Item type of the pasted element 
key : Identifying key of the selected element (optional) | 
| NewItem | An item / part was created in parts management. | itemtype : Item type of the newly created element 
key : Identifying key of the currently selected element (optional) | key : Identifying key of the created element 
| DeleteItem | An item / part is being deleted from parts management. | itemtype : Item type of the currently selected to be deleted element 
partnr : Selected part number (if only one part is selected) 
variant : Selected part variant (if only one variant is selected) 
key : Identifying key of the element to be deleted | 
| AddPartToProject | A part from parts management is stored in the project. The add-in can add additional custom data to the stored part. | itemtype : Item type of the stored part (always "eplan.part") 
key : Identifying key of the stored part | value : (string) Custom part data to be stored with the part inside the project (in properties ARTICLE_CUSTOM_DATA_INDEX and ARTICLE_CUSTOM_DATA_VALUE ) 
| AddPartToDatabase | A part is synchronized from the project to the parts management. The additional custom data can now be extracted and stored by the add-in. | itemtype : Item type of the synchronized part (always "eplan.part") 
key : Identifying key of the synchronized part 
value : (string) Custom part data stored with the part inside the project | 
| AddItemToProject | An item (part, manufacturer, drilling pattern, ...) is stored in the project. The add-in can add additional custom data to the stored item. | itemtype : Item types of stored items ( eplan.part, eplan.manufacturer , ...) 
key : Identifying field of stored item's name: name of the stored items (abbreviated name of the manufacturer, name of drilling pattern, ...) | value : (string) Custom data stored with an item inside a project (in properties ARTICLE_CUSTOM_DATA_INDEX and ARTICLE_CUSTOM_DATA_VALUE ) 
| ExportEplanItem | A part is exported from parts management to a file. The additional custom data from the add-in can now be added to the export file. | itemtype : Type of the item to export (always "eplan.part") 
key : Identifying key of the part to export | value : (string) Custom part data to be added to the export file 
| ImportEplanItem | A part is imported to parts management. The additional custom data from the file can now be extracted and stored by the add-in. | itemtype : Item type of the part to import (always "eplan.part") 
key : Identifying key of the imported part 
mode : Import mode. Possible values: 
0 = Append new records only 
1 = Update existing records only 
2 = Update existing records and append new ones 
value : (string) Custom part data to be extracted from the file and stored by the add-in. | 
| ExportCustomItem | All custom items of the respective item type are exported from parts management. 
Please mind that this only works with the XML export (" XPamExportXml " converter). | itemtype : Type of the item to export | value : Custom data of all items to be exported 
| ImportCustomItem | All custom items of the respective item type are imported from a file into parts management. They have to be saved by the add-in. 
Please mind that this only works with the XML import (" XPamExportXml " converter). | itemtype : Type of the item to import 
value : Custom data of all items to be imported 
mode : Import mode. Possible values: 
0 = Append new records only 
1 = Update existing records only 
2 = Update existing records and append new ones | 
| WillDeleteItem | An item / article is to be deleted in parts management | itemtype : Item type of the selected item 
key : Identifying field of the currently selected element 
partnr : Selected item number (only if an item is selected) 
variant : Selected variant (only if an article is selected) 
objectid : ID of a transient object being modified, (before changes) | allow : If set to 0, then DeleteItem is not called (delete is not executed) 
| WillSaveItem | An item / part will be saved in parts management | itemtype : Item type of the selected element 
key : Identifying key of the selected element 
partnr : Selected part number (if only one part is selected) 
variant : Selected part variant (if only one variant is selected) 
objectid : ID of a transient object being modified (before changes) | allow : When set to 0, SaveItem is not called (save is not performed)

---

## API Parts Selection Interface
*Źródło: `API Parts Selection Interface.html`*
*Ścieżka: EPLAN API / User Guide / API Miscellaneous / API Parts Selection Interface*

API Parts Selection Interface In EPLAN, you have the possibility to switch between different data sources for the part selection. You can get parts data via: 
- EPLAN database 
- SQL Server 
- API 
Setting the data source to "API" means that an API action will be called in case of operations related to accessing parts, for example: 

- A new part (or reference) is added to a project. 
- The part reference is changed in a project. 
- The part information is loaded from system. 
- A part is synchronized to a project. 
- A new macro with parts is inserted to a project. 
- A new device is inserted to project. 
- A new device is selected (with device section). 
- A new device list item is inserted to project. 

In this way, the user can create his own dialog for setting parts data, set additional properties when selecting a part, etc. 
An example of its use is the "EPLAN Data Portal" scheme – after setting it, the standard dialog for selecting parts is replaced by a custom one, which allows advanced selection of parts from the Data Portal database. 
Please note that the API parts selection cannot completely substitute the parts management databases such as EPLAN database or SQL Server. In some operations, they still have to be used. 
This topic describes how to use the API parts selection interface. 

### a) Setting the API parts selection action 
To be able to use the API parts selection interface, you first have to enable and configure it. To do this, you open the Settings dialog in EPLAN and select User > Management > Parts . In this dialog you create a new scheme and activate the API radio button. 

By clicking the ellipsis [...] button next to the API radio button, you can open a dialog with further settings for the API interface. 

In this dialog you enter the name of an API action that is called by EPLAN when the parts selection is started. 
The following describes how to develop the action and set its parameters. 

### b) Creating an action 
Please create an action with the name that was set in Settings dialog. The best way is to use the Visual Studio wizard: 

### c) Handling action parameters 
The part data is passed through the ActionCallingContext of the action. The object contains a set of input and output parameters that are passed as strings. 
- C# 
- VB public
bool
Execute(ActionCallingContext oActionCallingContext)
Public
Function
Execute(oActionCallingContext
As
Eplan.EplApi.ApplicationFramework.ActionCallingContext)
As
Boolean
_
Implements
Eplan.EplApi.ApplicationFramework.IEplAction.Execute

In this way, it is possible to have an access to properties of a selected part, for example: 

### C# 
### Copy Code 
| string
sMode =
""
;
ctx.GetParameter(
"Modus"
,
ref
sMode);
string
sProp00 =
"(int)Properties.Article.ARTICLE_DEPTH"
+ sSeparator +
"1"
;
ctx.AddParameter(sProp00,
"44.0"
);

The Modus parameter is used to identify the mode in which the parts selection is called. It can take one of the following values: 
- Selection – A part is selected. 
- Read – A part is updated. 
- Create – A part is created and parts selection action is called as alternative parts data source. 
- Exist – Check if part exist. 
Here is also a table with other input parameters: 

| Mode ( Modus parameter) | Input parameters 
| Selection | objectid – The object ID of the function on which the part selection was started. You can use the object ID to locate the function in the project and get additional information about it. 
separator – Contains the separator between property number and part index in parameter name 
SingleSelection – Is set to "1" if only one part can be set. Otherwise it is "0" or an empty string. 
ForceNoResolve – Is set to "1" if the assembly should not be resolved. Otherwise it is "0" or an empty string. 
GraphicalPreview – Is set to "1" if the user wants a preview of the part. Otherwise, it is "0" or an empty string. 
preselectpartnr – Contains the part number in the table cell from which the part selection is started. If the cell is empty, the parameter contains an empty string. 
preselectvariant – Contains the part variant number in the table cell from which the part selection is started. 
PartSelection – Is set to "1" if only a selection dialog should be shown. If it is "0", the parts can also be edited. 
DatabaseId – StorableObject.DatabaseIdentifier of the current project. 
UsePreSelection – Is set to "1" if the preselection list should be considered. Otherwise it is "0" or an empty string. 
codeletter – Identifier property of selected symbol 
symbollib – Symbol library of selected symbol 
symbolnr – Symbol number of selected symbol 
craft – Trade number of selected part 
_cmdline – Name of calling action 
| Read | Separator – Contains separator between property number and part index in parameter name, for example: 
<property number><separator><part index>[<separator><property index>] – e.g. "22001_1", value "SIE.5SX2102-8" 
22024_<part index> – part variant 
_cmdline – Name of calling action 
| Create | Separator – Contains separator between property number and part index in parameter name, for example: 
<property number><separator><part index>[<separator><property index>] – e.g. "22001_1", value "SIE.5SX2102-8" 
_cmdline – Name of calling action 
| Exist | Separator – Contains separator between property number and part index in parameter name, for example 
<property number><separator><part index>[<separator><property index>] – e.g. "22001_1", value "SIE.5SX2102-8" 
22024_<part index> – part variant 
_cmdline – Name of calling action 

The output parameters are the following: 

- The property to set. 
The parameter name has the format: <property number><separator><part index>[<separator><property index>] . 
It is required to set the part number property (22001). Other properties are optional. 
The <part index> is used to pass more than one part simultaneously. 
It starts from the 1. example : "1234_1". As a value, it can be any string for example “11.0”, etc. 
- Count of the parts to transmit. 
The parameter name is count . The value is determined by the last <part index> . 
- In case of the Exists mode, there is also a Result parameter that determines whether a part exists. 

A very important input parameter is the object ID ( objectid ). Using the object ID, you can locate the function in the project and get additional information about it. 
The following example shows an API parts selection action that displays the FormPartSelection user dialog and passes the fields Partnumber , Typenumber and Description1 . 

### C# 
### Copy Code 
| public
class
MyPartSelectionAction : IEplAction
{
public
bool
Execute(ActionCallingContext oActionCallingContext)
{
// Object ID from which part selection is started
string
sObjectId =
""
;
oActionCallingContext.GetParameter(
"ObjectId"
,
ref
sObjectId);
// Get Function object
Function oFunction = getFunction(sObjectId);
FormPartSelection frm =
new
FormPartSelection();
frm.Description =
""
;
frm.Typenumber =
""
;
frm.Partnumber =
"new part"
;
// Start part selection dialog
if
(frm.ShowDialog() == DialogResult.OK)
{
string
sTypenumber = frm.Typenumber;
string
sPartnumber = frm.Partnumber;
string
sDescription = frm.Description;
// Count of parts
oActionCallingContext.addParameter(
"count"
,
"1"
);
// Get separator between property and index
string
sSeparator =
""
;
oActionCallingContext.GetParameter(
"Separator"
,
ref
sSeparator);
int
prop;
int
idx = 1;
string
sProp;
// Set part number
prop = (
int
)Properties.Article.ARTICLE_PARTNR;
sProp = prop.ToString() + sSeparator + idx.ToString();
oActionCallingContext.AddParameter(sProp, sPartnumber);
// Set type number
prop = (
int
)Properties.Article.ARTICLE_TYPENR;
sProp = prop.ToString() + sSeparator + idx.ToString();
oActionCallingContext.AddParameter(sProp, sTypenumber);
// Set description 1
prop = (
int
)Properties.Article.ARTICLE_DESCR1;
sProp = prop.ToString() + sSeparator + idx.ToString();
oActionCallingContext.AddParameter(sProp, sDescription);
if
((oFunction !=
null
))
{
string
strArticleCharacteristics = (
int
)Properties.Article.ARTICLE_CHARACTERISTICS + sSeparator +
"1"
;
ctx.AddParameter(strArticleCharacteristics,
"5,5kW"
);
// Set characteristics to 5,5 kW
}
}
return
true
;
}
// Locate the function by its object ID
private
Function getFunction(
string
sObjectId)
{
ProjectManager projectManager =
new
ProjectManager();
Project project = projectManager.CurrentProject;
DMObjectsFinder objectFinder =
new
DMObjectsFinder(project);
FunctionPropertyList functionPropertyList =
new
FunctionPropertyList();
functionPropertyList[Properties.StorableObject.PROPUSER_DBOBJECTID] = sObjectId;
FunctionsFilter functionsFilter =
new
FunctionsFilter();
functionsFilter.SetFilteredPropertyList(functionPropertyList);
Function[] aFunction = objectFinder.GetFunctions(functionsFilter);
if
(aFunction.Length > 0)
{
return
aFunction[0];
}
return
null
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
"MyPartSelectionAction"
;
Ordinal = 20;
return
true
;
}
public
MyPartSelectionAction()
{}
}

### Przykłady kodu (C#)
```csharp
public bool Execute(ActionCallingContext oActionCallingContext)
```
```csharp
Public Function Execute(oActionCallingContext As Eplan.EplApi.ApplicationFramework.ActionCallingContext) As Boolean _
        Implements Eplan.EplApi.ApplicationFramework.IEplAction.Execute
```
```csharp
string sMode = "";
ctx.GetParameter("Modus", ref sMode);
string sProp00 = "(int)Properties.Article.ARTICLE_DEPTH" + sSeparator + "1";
ctx.AddParameter(sProp00, "44.0");
```
```csharp
public class MyPartSelectionAction : IEplAction
{
    public bool Execute(ActionCallingContext oActionCallingContext)
    {
        // Object ID from which part selection is started
        string sObjectId = "";
        oActionCallingContext.GetParameter("ObjectId", ref sObjectId);
        // Get Function object
        Function oFunction = getFunction(sObjectId);
        FormPartSelection frm = new FormPartSelection();
        frm.Description = "";
        frm.Typenumber = "";
        frm.Partnumber = "new part";
        // Start part selection dialog
        if (frm.ShowDialog() == DialogResult.OK)
        {
            string sTypenumber = frm.Typenumber;
            string sPartnumber = frm.Partnumber;
            string sDescription = frm.Description;
            // Count of parts
            oActionCallingContext.addParameter("count", "1");
            // Get separator between property and index
            string sSeparator = "";
            oActionCallingContext.GetParameter("Separator", ref sSeparator);
            int prop;
            int idx = 1;
            string sProp;
            // Set part number
            prop = (int)Properties.Article.ARTICLE_PARTNR;
            sProp = prop.ToString() + sSeparator + idx.ToString();
            oActionCallingContext.AddParameter(sProp, sPartnumber);
            // Set type number
            prop = (int)Properties.Article.ARTICLE_TYPENR;
            sProp = prop.ToString() + sSeparator + idx.ToString();
            oActionCallingContext.AddParameter(sProp, sTypenumber);
            // Set description 1
            prop = (int)Properties.Article.ARTICLE_DESCR1;
            sProp = prop.ToString() + sSeparator + idx.ToString();
            oActionCallingContext.AddParameter(sProp, sDescription);
            if ((oFunction != null))
            {
               string strArticleCharacteristics = (int)Properties.Article.ARTICLE_CHARACTERISTICS + sSeparator + "1";
               ctx.AddParameter(strArticleCharacteristics, "5,5kW");      // Set characteristics to 5,5 kW
            }
        }
        return true;
    }
    // Locate the function by its object ID
        private Function getFunction(string sObjectId)
        {
            ProjectManager projectManager = new ProjectManager();
            Project project = projectManager.CurrentProject;
            DMObjectsFinder objectFinder = new DMObjectsFinder(project);
            FunctionPropertyList functionPropertyList = new FunctionPropertyList();
            functionPropertyList[Properties.StorableObject.PROPUSER_DBOBJECTID] = sObjectId;
            FunctionsFilter functionsFilter = new FunctionsFilter();
            functionsFilter.SetFilteredPropertyList(functionPropertyList);
            Function[] aFunction = objectFinder.GetFunctions(functionsFilter);
            if (aFunction.Length > 0)
            {
                return aFunction[0];
            }
            return null;
        }

    public bool OnRegister(ref string Name, ref int Ordinal)
    {
        Name = "MyPartSelectionAction";
        Ordinal = 20;
        return true;
    }
    public MyPartSelectionAction()
    {}
}
```

---

## Basic operations on parts
*Źródło: `Basic operations on parts.html`*
*Ścieżka: EPLAN API / User Guide / API MasterData / Basic operations on parts*

Basic operations on parts The following example shows how to work with parts in the parts database: 
- C# // Get all parts
var
listOfAllParts = partsDatabase.Parts;
// Export all parts to the EDZ format
if
(partsDatabase.ExportParts(
"D:\\exportDirectory\\export.edz"
, MDPartsDatabase.DataFormat.EDZ))
new
Decider().Decide(EnumDecisionType.eOkDecision,
"Part export successful"
,
"Export Part"
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
// Add a new part variant
string
partName =
"MyTestPart-123"
;
if
(!partsDatabase.ExistsPart(partName))
{
var
part = partsDatabase.AddPart(partName,
"2"
); 
}
// Get a part, export it and remove it
if
(partsDatabase.ExistsPart(partName));
{
// Get a part by name
var
part = partsDatabase.GetPart(partName);
new
Decider().Decide(
EnumDecisionType.eOkDecision,
"Part number: "
+ part.PartNr +
" \nVariant: "
+ part.Variant,
"Part Loaded"
,
EnumDecisionReturn.eOK,
EnumDecisionReturn.eOK);
// Export selected part(s) to XML
MDPart[] partsToExport =
new
MDPart[] { part };
partsDatabase.ExportParts(
"C:\\exportDirectory\\exportFile.xml"
, MDPartsDatabase.DataFormat.XML, partsToExport);
// Remove part
partsDatabase.RemovePart(part);
if
(!partsDatabase.ExistsPart(partName)) ;
new
Decider().Decide(EnumDecisionType.eOkDecision,
"Part Removed"
,
"Part Removed"
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
}
// Export all database items: parts(true), addresses(true), constructions(true), terminals(true), accessory lists(true), accessory placements(true) to XML
if
(partsDatabase.ExportPartsDatabaseItems(
"C:\\exportDirectory\\exportFile.xml"
, MDPartsDatabase.DataFormat.XML,
true
,
true
,
true
,
true
,
true
,
true
))
new
Decider().Decide(EnumDecisionType.eOkDecision,
"Export successful"
,
"Export Part"
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);

These operations are also available for AccessoryPlacement , ConnectionInfoPoint , Construction , Customer , Manufacturer and AccessoryList . 
For example, to add or remove AccessortList use: 
- C# // Add AccessoryList
MDAccessoryList accessoryList = partsDatabase.AddAccessoryList(
"accessoryListName"
);
// Remove AccessoryList
partsDatabase.RemoveAccessoryList(accessoryList);

### Przykłady kodu (C#)
```csharp
// Get all parts
var listOfAllParts = partsDatabase.Parts;

// Export all parts to the EDZ format
if (partsDatabase.ExportParts("D:\\exportDirectory\\export.edz", MDPartsDatabase.DataFormat.EDZ))
    new Decider().Decide(EnumDecisionType.eOkDecision, "Part export successful", "Export Part", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);

        
// Add a new part variant
string partName = "MyTestPart-123";
if (!partsDatabase.ExistsPart(partName))
{       
    var part = partsDatabase.AddPart(partName, "2");       
}

// Get a part, export it and remove it
if (partsDatabase.ExistsPart(partName));
{
    // Get a part by name
    var part = partsDatabase.GetPart(partName);
    new Decider().Decide(
    EnumDecisionType.eOkDecision,
    "Part number: " + part.PartNr + " \nVariant: " + part.Variant,
    "Part Loaded",
    EnumDecisionReturn.eOK,
    EnumDecisionReturn.eOK); 

    // Export selected part(s) to XML
    MDPart[] partsToExport = new MDPart[] { part };
    partsDatabase.ExportParts("C:\\exportDirectory\\exportFile.xml", MDPartsDatabase.DataFormat.XML, partsToExport);          

    // Remove part
    partsDatabase.RemovePart(part);
    if (!partsDatabase.ExistsPart(partName)) ;
        new Decider().Decide(EnumDecisionType.eOkDecision, "Part Removed", "Part Removed", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
}

// Export all database items: parts(true), addresses(true), constructions(true), terminals(true), accessory lists(true), accessory placements(true) to XML
if (partsDatabase.ExportPartsDatabaseItems("C:\\exportDirectory\\exportFile.xml", MDPartsDatabase.DataFormat.XML, true, true, true, true, true, true))
     new Decider().Decide(EnumDecisionType.eOkDecision, "Export successful", "Export Part", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
```
```csharp
// Add AccessoryList
MDAccessoryList accessoryList = partsDatabase.AddAccessoryList("accessoryListName");

// Remove AccessoryList
partsDatabase.RemoveAccessoryList(accessoryList);
```

---

## Filtering parts database items
*Źródło: `Filtering parts database items.html`*
*Ścieżka: EPLAN API / User Guide / API MasterData / Filtering parts database items*

Filtering parts database items The following example shows how to filter the parts database using the MDObjectFilter() class: 
- C# using
(MDPartsDatabase partsDatabase =
new
MDPartsManagement().OpenDatabase())
{
// Get all parts with part number beginning with "SIE"
MDObjectFilter mDObjectFilter =
new
MDObjectFilter(); 
mDObjectFilter.AddPropertyCondition(22001, MDObjectFilter.CompareOperator.OperatorEqual,
"SIE*"
);
//22001 - enum Properties.MDPartsDatabaseItem
MDPart[] arrParts = partsDatabase.GetParts(mDObjectFilter); 
partsDatabase.ExportParts(
"C:\\exportDirectory\\exportFile.xml"
, MDPartsDatabase.DataFormat.XML, arrParts);
}

Filtering the parts database using a Linq query: 
- C# using
(MDPartsDatabase partsDatabase =
new
MDPartsManagement().OpenDatabase())
{
// Export only parts modified today
var
today = DateTime.Today;
var
partsModifiedToday = partsDatabase.Parts.Where(item => item.Properties.PART_LASTCHANGE_DATE.ToTime() > today);
partsDatabase.ExportPartsDatabaseItems(
"C:\\exportDirectory\\exportFile.xml"
, MDPartsDatabase.DataFormat.XML, partsModifiedToday);
}

### Przykłady kodu (C#)
```csharp
using (MDPartsDatabase partsDatabase = new MDPartsManagement().OpenDatabase())
{
    // Get all parts with part number beginning with "SIE"
    MDObjectFilter mDObjectFilter = new MDObjectFilter();           
    mDObjectFilter.AddPropertyCondition(22001, MDObjectFilter.CompareOperator.OperatorEqual, "SIE*"); //22001 - enum Properties.MDPartsDatabaseItem
    MDPart[] arrParts = partsDatabase.GetParts(mDObjectFilter);       
    partsDatabase.ExportParts("C:\\exportDirectory\\exportFile.xml", MDPartsDatabase.DataFormat.XML, arrParts);
}
```
```csharp
using (MDPartsDatabase partsDatabase = new MDPartsManagement().OpenDatabase())
{
    // Export only parts modified today
    var today = DateTime.Today;
    var partsModifiedToday = partsDatabase.Parts.Where(item => item.Properties.PART_LASTCHANGE_DATE.ToTime() > today);
    partsDatabase.ExportPartsDatabaseItems("C:\\exportDirectory\\exportFile.xml", MDPartsDatabase.DataFormat.XML, partsModifiedToday);
}
```

---
