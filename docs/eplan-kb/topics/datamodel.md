# EPLAN API — datamodel

*MVP — Project, Page, Function, właściwości, transakcje*

Dokumentów: 19

## API DataModel
*Źródło: `API DataModel.html`*
*Ścieżka: EPLAN API / User Guide / API DataModel*

API DataModel The electrotechnical data model ( Eplan.EplApi.DataModel namespace) contains all the classes / objects belonging to an EPLAN project, such as the project itself, pages, functions, placements, etc. Each class is derived from the StorableObject base class and has its specific properties. In contrast to the EPLAN 21 data model, EPLAN does not strictly differentiate between the graphical and the logical information. For example, a page keeps record of both the functions (logical) and the placements (graphical). There is no device object that stores the functions with the same device tag. 

Note 
The class Function is named like a keyword of Visual Basic. In order to get no compilation errors in VB, you need to always refer to a Function object by its complete name space: Eplan.EplApi.DataModel.Function or in square brackets: [Function] . 

We recommend you to explicitly release data model objects when they are no longer needed. This is especially true for loops that set a large number of properties. Make sure that the garbage collector has the opportunity to clean up these objects by frequently calling System.GC.WaitForPendingFinalizers() . 

Please take into account that generally data model objects store length values in millimeters and dimensions are according to graphical coordinate system.

---

## Accessing selected objects
*Źródło: `Accessing selected objects.html`*
*Ścieżka: EPLAN API / User Guide / API Higher Electrotechnical services / Accessing selected objects*

Accessing selected objects The advantage of an add-in is that it is called from within the context of a running EPLAN version and can access the currently selected objects. This can be achieved by using the SelectionSet class. The class provides a number of methods for retrieving a list of items currently selected by the user. 
You can either get the project the user is currently working on using the SelectionSet::GetCurrentProject method, or you can get the currently selected page(s) using the SelectionSet::GetSelectedPages method. Depending on whether the graphical editor or the page overview dialog currently has the focus, one or more pages can be selected. 
Most importantly, you can get any set of objects selected from any focused (non-modal) dialog through the SelectionSet.Selection property. The objects are returned by the function as an array of StorableObjects. You can loop over the array and determine the types (and any other information) about the objects. 
The following example shows how to access the selection. 
- C# 
- VB SelectionSet selectionSet =
new
SelectionSet();
StorableObject[] storableObjects = selectionSet.Selection;
if
(storableObjects.Length == 0)
{
Console.WriteLine(
"No current selection!"
);
}
else
{
foreach
(StorableObject so
in
storableObjects)
{
if
(so
is
Function)
Console.WriteLine(
" StorableObject is a function: "
+ ((Function) so).Name);
else
Console.WriteLine(
" StorableObject: "
+ so.ToString());
}
}
Dim
selectionSet
As
New
SelectionSet()
Dim
storableObjects
As
StorableObject() = selectionSet.Selection
If
storableObjects.Length = 0
Then
Console.WriteLine(
"No current selection!"
)
Else
Dim
so
As
StorableObject
For
Each
so
In
storableObjects
If
TypeOf
so
Is
Function
Then
Console.WriteLine((
" StorableObject is a function: "
+
CType
(so,
Function
).Name))
Else
Console.WriteLine((
" StorableObject: "
+ so.ToString()))
End
If
Next
so
End
If

### Przykłady kodu (C#)
```csharp
SelectionSet selectionSet = new SelectionSet();
StorableObject[] storableObjects = selectionSet.Selection;
if (storableObjects.Length == 0)
{
    Console.WriteLine("No current selection!");
}
else
{
    foreach(StorableObject so in storableObjects)
    {
        if(so is Function)
           Console.WriteLine(" StorableObject is a function: " + ((Function) so).Name);
        else
            Console.WriteLine(" StorableObject: " + so.ToString());
    }
}
```
```csharp
Dim selectionSet As New SelectionSet()
Dim storableObjects As StorableObject() = selectionSet.Selection
If storableObjects.Length = 0 Then
   Console.WriteLine("No current selection!")
Else
   Dim so As StorableObject
   For Each so In  storableObjects
      If TypeOf so Is Function Then
         Console.WriteLine((" StorableObject is a function: " + CType(so, Function).Name))
      Else
         Console.WriteLine((" StorableObject: " + so.ToString()))
      End If
   Next so
End If
```

---

## Connections overview
*Źródło: `Connections overview.html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / Navigating the project data / Connections overview*

Connections overview The following illustration shows how to navigate between functions, their pins and the connections.

---

## Creating or opening projects
*Źródło: `Creating or opening projects.html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / Creating or opening projects*

Creating or opening projects The most important object in the Eplan.EplApi.DataModel namespace is the Project . The project must be opened in EPLAN in order to be able to work with it. In an add-in, you will usually work with the project that the user has opened interactively via the GUI. You can get the project currently selected by the user via the SelectionSet object described in the " Getting the current selection " topic. 

However, you may also want to open or create a project in EPLAN via the API – this will certainly be the case with offline programs . For this and other project-related tasks, the Eplan.EplApi.DataModel namespace provides the ProjectManager class. 

To create a project, use the CreateProject method. It takes two parameters, the full filename of the new project link file to be created and the project template link file. The project template can be a basic project in *.zw9 format or a project backup in *.zw1 format. After successfully creating the project, it is opened and the method returns the new Project object. 

The following example shows how to create a project. 

### C# 
### Copy Code 
| Project oProject =
new
ProjectManager().CreateProject(
"$(MD_PROJECTS)\\Example_003.elk"
,
"$(MD_TEMPLATES)\\IEC_bas003.zw9"
);

To open a project, use the OpenProject method. Its only parameter is the full name and path of the project link file. 

### C# 
### Copy Code 
| Project oProject =
new
ProjectManager().OpenProject(
"$(MD_PROJECTS)\\EPLAN_Sample_Project.elk"
);

### Remarks In offline programs, you need to open a LockingStep, before you open or create an EPLAN project or use any other data model object.

### Przykłady kodu (C#)
```csharp
Project oProject = new ProjectManager().CreateProject("$(MD_PROJECTS)\\Example_003.elk", "$(MD_TEMPLATES)\\IEC_bas003.zw9");
```
```csharp
Project oProject = new ProjectManager().OpenProject("$(MD_PROJECTS)\\EPLAN_Sample_Project.elk");
```

---

## Creating pages
*Źródło: `Creating pages.html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / Creating pages*

Creating pages To create a page in a project, the Eplan.EplApi.DataModel.Page class provides a Create method. You first instantiate an empty Page object and then call Create . The method takes three parameters: first the project, in which the page is to be created, then the type of the page, and finally a PagePropertyList with the identifying properties of the page. 
The types of pages you can create are listed in the DocumentTypeManager.DocumentType enumeration. 

The following example shows how to create a schematic page: 
- C# 
- VB // Create new schematic page in current project
PagePropertyList oPagePropList =
new
PagePropertyList();
// Set Plant
oPagePropList[Properties.Page.DESIGNATION_PLANT] =
"P1"
;
// Set Location
oPagePropList[Properties.Page.DESIGNATION_LOCATION] =
"L1"
;
Page oNewPage =
new
Page();
oNewPage.Create(m_oTestProject, DocumentTypeManager.DocumentType.Circuit, oPagePropList);
' Create new schematic page in current project
Dim
oPagePropList
As
New
PagePropertyList()
' Set Plant
oPagePropList(Properties.Page.DESIGNATION_PLANT) = PropertyValue.op_Implicit(
"P1"
)
' Set Location
oPagePropList(Properties.Page.DESIGNATION_LOCATION) = PropertyValue.op_Implicit(
"L1"
)
' Set Counter
oPagePropList(Properties.Page.PAGE_COUNTER) = PropertyValue.op_Implicit(4)
Dim
oNewPage
As
New
Page()
oNewPage.Create(m_oTestProject, DocumentTypeManager.DocumentType.Circuit, oPagePropList)

Remarks 
Please mind that when you create a page, you cannot set descriptive properties in the PropertyList mentioned above. Only parts of the page name can be set using this list. 
Other properties need to be set after creating the page by Page.Properties .

### Przykłady kodu (C#)
```csharp
// Create new schematic page in current project
PagePropertyList oPagePropList = new PagePropertyList();
// Set Plant
oPagePropList[Properties.Page.DESIGNATION_PLANT] = "P1";
// Set Location
oPagePropList[Properties.Page.DESIGNATION_LOCATION] = "L1";
Page oNewPage = new Page();
oNewPage.Create(m_oTestProject, DocumentTypeManager.DocumentType.Circuit, oPagePropList);
```
```csharp
' Create new schematic page in current project
Dim oPagePropList As New PagePropertyList()
' Set Plant
oPagePropList(Properties.Page.DESIGNATION_PLANT) = PropertyValue.op_Implicit("P1")
' Set Location
oPagePropList(Properties.Page.DESIGNATION_LOCATION) = PropertyValue.op_Implicit("L1")
' Set Counter
oPagePropList(Properties.Page.PAGE_COUNTER) = PropertyValue.op_Implicit(4)
Dim oNewPage As New Page()
oNewPage.Create(m_oTestProject, DocumentTypeManager.DocumentType.Circuit, oPagePropList)
```

---

## DMObjectsFinder overview
*Źródło: `DMObjectsFinder overview.html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / Navigating the project data / DMObjectsFinder overview*

DMObjectsFinder overview The following illustration shows how you can also access primary project objects using the DMObjectsFinder class.

---

## DataModel class diagram
*Źródło: `DataModel class diagram.html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / Navigating the project data / DataModel class diagram*

DataModel class diagram The following illustration shows the class diagram in the Eplan.EplApi.DataModel namespace.

---

## DataModel navigation overview
*Źródło: `DataModel navigation overview.html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / Navigating the project data / DataModel navigation overview*

DataModel navigation overview The following illustration shows how to access objects of the Eplan.EplApi.DataModel namespace.

---

## EObjects overview
*Źródło: `EObjects overview.html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / Navigating the project data / EObjects overview*

EObjects overview Class diagram of the EPLAN data model in Eplan.EplApi.DataModel.EObjects namespace.

---

## EPLAN properties
*Źródło: `EPLAN properties.html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / EPLAN properties*

EPLAN properties The EPLAN API allows accessing object properties, i.e. characteristics that are visible in GUI in the Properties dialog. 
This is possible through the Properties property which is defined for almost all data model objects. 
The list of all available properties for a particular object can be found in the properties of the Properties class (for example Properties::AllMDSymbolLibraryPropIDs ). 

### Property types 
EPLAN properties are typed. The property values can have one of the following types: 
- bool 
- int 
- double 
- DateTime 
- PointD 
- MultiLangString 

With help of the PropertyDefinition.PropertyType, you can determine the type of a property: 

### PropertyDefinition.PropertyType 
### Corresponding .NET Framework type 
| Point | 
| MultilangString | 
| Variable | System.String 
| String | System.String 
| Time | System.DateTime 
| Bool | System.Boolean 
| Double | System.Double 
| Coord | System.Double 
| Long | System.Int64 
The following example gets the type of a page property: 
- C# 
- VB PropertyDefinition.PropertyType oPropType = oPage.Properties[Properties.Page.DESIGNATION_PLANT].Definition.Type;
Dim
oPropType
As
PropertyDefinition.PropertyType = oPage.Properties(Properties.Page.DESIGNATION_PLANT).Definition.Type

### Setting and getting a property 
The following example shows how to set a bool property: 
- C# 
- VB oFunction.Properties[Properties.Function.FUNC_ARTICLE_SUPPRESSINPARTSLIST] =
true
;
oFunction.Properties(Properties.Function.FUNC_ARTICLE_SUPPRESSINPARTSLIST) = PropertyValue.op_Implicit(
True
)

The following example shows how to get a MultiLangString property (project description): 

- C# 
- VB MultiLangString mlTest = oProject.Properties[Properties.Project.PROJ_INSTALLATIONNAME];
Dim
mlTest
As
MultiLangString = oProject.Properties(Properties.Project.PROJ_INSTALLATIONNAME).ToMultiLangString()

As an alternative syntax, you can also write: 
- C# 
- VB MultiLangString mlTest = oProject.Properties.PROJ_INSTALLATIONNAME;
Dim
mlTest
As
MultiLangString = oProject.Properties.PROJ_INSTALLATIONNAME.ToMultiLangString()

Finally an example that loops over all string properties of a project: 
- C# 
- VB string
strTmp =
string
.Empty;
PropertyValue oPropValue;
// Iterate over all project properties
foreach
(AnyPropertyId hPProp
in
Eplan.EplApi.DataModel.Properties.AllProjectPropIDs)
{
// Check if exists
if
(!m_oProject.Properties[hPProp].IsEmpty)
{
if
(m_oProject.Properties[hPProp].Definition.Type == PropertyDefinition.PropertyType.String)
{
// Read string property
oPropValue = m_oProject.Properties[hPProp];
strTmp = oPropValue.ToString();
}
}
}
Dim
strTmp
As
String
=
String
.Empty
Dim
oPropValue
As
PropertyValue
' Iterate over all project properties
Dim
hPProp
As
AnyPropertyId
For
Each
hPProp
In
Eplan.EplApi.DataModel.Properties.AllProjectPropIDs
' Check if exists
If
Not
m_oProject.Properties(hPProp).IsEmpty
Then
If
m_oProject.Properties(hPProp).Definition.Type = PropertyDefinition.PropertyType.String
Then
' Read string property
oPropValue = m_oProject.Properties(hPProp)
strTmp = oPropValue.ToString()
End
If
End
If
Next
hPProp

### Setting name properties In the case of the name properties, their setting must be done through the .NameParts property, for example: 
- C# var
functionBasePropertyList =
new
FunctionBasePropertyList();
// Set function name
functionBasePropertyList.DESIGNATION_LOCATION =
"A1"
;
functionBasePropertyList.DESIGNATION_PLANT =
"E01"
;
oNewFunction.NameParts = functionBasePropertyList;
The only difference is with DESIGNATION_PRODUCT property. It needs to be set by FUNC_CODE and FUNC_COUNTER then it is composed from them. 

### Conversion property value to another types 
It is possible to get a property as a value of the .NET Framework type or EPLAN API type (for example Eplan.EplApi.Base.MultiLangString ). It can be done explicitly by the PropertyValue.To<type>() , for example: 

### C# 
### Copy Code 
| string
strStringValue = oFunction.Properties.FUNC_CODE.ToString();

or implicitly: 

### C# 
### Copy Code 
| int
nValue = oFunction.Properties.FUNC_CRAFT;

It is not allowed to convert the property value to a non-matching type, for example MultiLangString to int . In such cases, a runtime warning is generated (as an EPLAN system message) or an exception is thrown: 

### C# 
### Copy Code 
| string
strValue = oArticle.Properties.ARTICLE_DEPTH.ToString();
// Will generate a system warning
double
dValue = oArticle.Properties.ARTICLE_DEPTH.ToDouble();
// OK
string
strValue2 = oArticle.Properties.ARTICLE_DEPTH.ToDouble().ToString(
"0.00"
, CultureInfo.InvariantCulture);
// Also OK

Here is a table that shows which conversions are allowed: 

### 

### Eplan.EplApi.Base.Point 
PropertyValue.ToPointD() 
### Eplan.EplApi.Base.MultiLangString 
PropertyValue.ToMultiLangString() 
### System.String 
PropertyValue.ToString() 
### System.DateTime 
PropertyValue.ToTime() 
### bool 
PropertyValue.ToBool() 
### double 
PropertyValue.ToDouble() 
### long 
PropertyValue.ToInt() 
| PropertyType.Point | ✓ | | | | | | 
| PropertyType.MultilangString | | ✓ | | | | | 
| PropertyType.Variable | | | ✓ | | | | 
| PropertyType.String | | | ✓ | | | | 
| PropertyType.Time | | | | ✓ | | | 
| PropertyType.Bool | | | | | ✓ | | 
| PropertyType.Double | | | | | | ✓ | 
| PropertyType.Coord | | | | | | ✓ | 
| 
PropertyType.Long | | | | | | ✓ | ✓ 

### Indexed properties 
Properties can have more than one value. In this case, we call it an " indexed property ". The index is passed after the property designation. The example gets the index 1 of the function property FUNC_CONNECTIONDESIGNATION : 
- C# 
- VB strConnDes1 = oFunction.Properties[Properties.Function.FUNC_CONNECTIONDESIGNATION, 1].ToString();
strConnDes1 = oFunction.Properties(Properties.Function.FUNC_CONNECTIONDESIGNATION, 1).ToString()

Alternatively: 
- C# 
- VB strConnDes1 = oFunction.Properties.FUNC_CONNECTIONDESIGNATION[1].ToString();
strConnDes1 = oFunction.FUNC_CONNECTIONDESIGNATION(1).ToString()

### User-defined properties 
EPLAN API supports also user-defined properties that were introduced in EPLAN 2.4. 
The following enhancements were added due to it: 
- Access to properties by case-sensitive string identifiers: 

### C# 
### Copy Code 
| // Setting user-defined property
oProject.Properties[
"EPLAN.Project.UserSupplementaryField1"
] =
"test1"
;
// Getting user-defined property
string
strValue = oProject.Properties[
"EPLAN.Project.UserSupplementaryField1"
];

- UserDefinedPropertyDefinition class extending PropertyDefinition . The class allows creating custom property definitions or accessing information from existing ones: 

### C# 
### Copy Code 
| // Create a new property definition:
UserDefinedPropertyDefinition oUDPDProject = UserDefinedPropertyDefinition.Create(oCurrentProject,
"API.Property.Project"
, UserDefinedPropertyDefinition.Enums.ClientType.Project);
oCurrentProject.Properties[
"API.Property.Project"
] =
"something"
;
var
oCategory = oProject.Properties[
"EPLAN.Project.UserSupplementaryField1"
].Category;
// Gets the category information
MultiLangString strDisplayedName = oProject.Properties[
"EPLAN.Project.UserSupplementaryField1"
].DisplayedName;
// Gets the name that is displayed in the GUI properties window

- Import / export property definitions ( ExportPropertyDefinitions , ImportPropertyDefinitions from the PrePlanningService class) 
- The new AnyPropertyId constructor allowing to create an ID of a user-defined property: 

### C# 
### Copy Code 
| public
AnyPropertyId(
ref
Eplan::EplApi::DataModel::Project pProject,
ref
System::String strUserDefiniedPropertyIdentName
);

- The AnyPropertyId.AsString propety to get the identifying name from AnyPropertyId which represents a user-defined property. 
- Actions that expect the ID of a property were extended to support also identifying names. Please go to the " API Reference " section for details. 

### Accessing default user-defined properties 
Some user-defined properties are created by default, for example "EPLAN.Project.UserSupplementaryField1". 
They have the same internal IDs as the old *_CUSTOM_SUPPLEMENTARYFIELD* properties (like "PROJ_CUSTOM_SUPPLEMENTARYFIELD01", etc). 
The use of old identifiers is still possible for compatibility reasons, but they generate warnings and will be removed in the future. 
Therefore, please replace them with the new IDs to avoid problems in forthcoming EPLAN versions: 

### C# 
### Copy Code 
| MultiLangString oMLS = oProject.Properties.PROJ_CUSTOM_SUPPLEMENTARYFIELD01;
// Old code, generates warning
MultiLangString oMLS = oProject.Properties[
"EPLAN.Project.UserSupplementaryField1"
];
// New code
m_oTestProject.Properties.FUNC_ARTICLE_CUSTOM_SUPPLEMENTARYFIELD01[1] = strTestValue;
// Old code, generates warning:
ArticleReference oArticleReference = oProject.ArticleReferences[0];
// New code
oArticleReference.Properties[
"EPLAN.PartRef.UserSupplementaryField1"
] = strTestValue;
oArticleReference.StoreToObject();

### Accessing user-defined properties through ArticleReference parent object 
In the case of an ArticleReference object, when accessing a user-defined property through a parent ArticleReference , it is necessary to add the EPLAN.ArticleRef. prefix to its identifying name. In addition, an index must be provided to indicate the position of the ArticleReference in the parent object. 

### C# 
### Copy Code 
| var
propertyValue1 = oArticleReference.Properties[
"UserProperty.1"
].ToString();
// Accessing user-defined property from ArticleReference
var
propertyValue2 = oArticleReference.Parent.Properties[
"EPLAN.ArticleRef.UserProperty.1"
][1].ToString();
// Accessing user-defined property from a parent of the ArticleReference

### Przykłady kodu (C#)
```csharp
PropertyDefinition.PropertyType oPropType = oPage.Properties[Properties.Page.DESIGNATION_PLANT].Definition.Type;
```
```csharp
Dim oPropType As PropertyDefinition.PropertyType = oPage.Properties(Properties.Page.DESIGNATION_PLANT).Definition.Type
```
```csharp
oFunction.Properties[Properties.Function.FUNC_ARTICLE_SUPPRESSINPARTSLIST] = true;
```
```csharp
oFunction.Properties(Properties.Function.FUNC_ARTICLE_SUPPRESSINPARTSLIST) = PropertyValue.op_Implicit(True)
```
```csharp
MultiLangString mlTest = oProject.Properties[Properties.Project.PROJ_INSTALLATIONNAME];
```
```csharp
Dim mlTest As MultiLangString = oProject.Properties(Properties.Project.PROJ_INSTALLATIONNAME).ToMultiLangString()
```
```csharp
MultiLangString mlTest = oProject.Properties.PROJ_INSTALLATIONNAME;
```
```csharp
Dim mlTest As MultiLangString = oProject.Properties.PROJ_INSTALLATIONNAME.ToMultiLangString()
```
```csharp
string strTmp = string.Empty;
 PropertyValue oPropValue;
 // Iterate over all project properties
 foreach (AnyPropertyId hPProp in Eplan.EplApi.DataModel.Properties.AllProjectPropIDs)
 {
     // Check if exists
     if (!m_oProject.Properties[hPProp].IsEmpty)
     {
         if (m_oProject.Properties[hPProp].Definition.Type == PropertyDefinition.PropertyType.String)
         {
             // Read string property
             oPropValue = m_oProject.Properties[hPProp];
             strTmp = oPropValue.ToString();
         }
     }
 }
```
```csharp
Dim strTmp As String = String.Empty
Dim oPropValue As PropertyValue
' Iterate over all project properties
Dim hPProp As AnyPropertyId
For Each hPProp In  Eplan.EplApi.DataModel.Properties.AllProjectPropIDs
   ' Check if exists
   If Not m_oProject.Properties(hPProp).IsEmpty Then
      If m_oProject.Properties(hPProp).Definition.Type = PropertyDefinition.PropertyType.String Then
         ' Read string property
         oPropValue = m_oProject.Properties(hPProp)
         strTmp = oPropValue.ToString()
      End If
   End If
Next hPProp
```
```csharp
var functionBasePropertyList = new FunctionBasePropertyList();
// Set function name
functionBasePropertyList.DESIGNATION_LOCATION = "A1";
functionBasePropertyList.DESIGNATION_PLANT = "E01";
oNewFunction.NameParts = functionBasePropertyList;
```
```csharp
string strStringValue = oFunction.Properties.FUNC_CODE.ToString();
```
```csharp
int nValue = oFunction.Properties.FUNC_CRAFT;
```
```csharp
string strValue = oArticle.Properties.ARTICLE_DEPTH.ToString(); // Will generate a system warning
double dValue = oArticle.Properties.ARTICLE_DEPTH.ToDouble(); // OK
string strValue2 = oArticle.Properties.ARTICLE_DEPTH.ToDouble().ToString("0.00", CultureInfo.InvariantCulture); // Also OK
```
```csharp
strConnDes1 = oFunction.Properties[Properties.Function.FUNC_CONNECTIONDESIGNATION, 1].ToString();
```
```csharp
strConnDes1 = oFunction.Properties(Properties.Function.FUNC_CONNECTIONDESIGNATION, 1).ToString()
```
```csharp
strConnDes1 = oFunction.Properties.FUNC_CONNECTIONDESIGNATION[1].ToString();
```
```csharp
strConnDes1 = oFunction.FUNC_CONNECTIONDESIGNATION(1).ToString()
```
```csharp
// Setting user-defined property
oProject.Properties["EPLAN.Project.UserSupplementaryField1"] = "test1";
// Getting user-defined property
string strValue = oProject.Properties["EPLAN.Project.UserSupplementaryField1"];
```
```csharp
// Create a new property definition:
UserDefinedPropertyDefinition oUDPDProject = UserDefinedPropertyDefinition.Create(oCurrentProject, "API.Property.Project", UserDefinedPropertyDefinition.Enums.ClientType.Project);
oCurrentProject.Properties["API.Property.Project"] = "something";

var oCategory = oProject.Properties["EPLAN.Project.UserSupplementaryField1"].Category;  // Gets the category information
MultiLangString strDisplayedName = oProject.Properties["EPLAN.Project.UserSupplementaryField1"].DisplayedName; // Gets the name that is displayed in the GUI properties window
```
```csharp
public AnyPropertyId(
    ref Eplan::EplApi::DataModel::Project pProject,
    ref System::String strUserDefiniedPropertyIdentName
);
```
```csharp
MultiLangString oMLS = oProject.Properties.PROJ_CUSTOM_SUPPLEMENTARYFIELD01;             // Old code, generates warning
MultiLangString oMLS = oProject.Properties["EPLAN.Project.UserSupplementaryField1"];     // New code

m_oTestProject.Properties.FUNC_ARTICLE_CUSTOM_SUPPLEMENTARYFIELD01[1] = strTestValue;     // Old code, generates warning:
ArticleReference oArticleReference = oProject.ArticleReferences[0];                       // New code
oArticleReference.Properties["EPLAN.PartRef.UserSupplementaryField1"] = strTestValue;
oArticleReference.StoreToObject();
```
```csharp
var propertyValue1 = oArticleReference.Properties["UserProperty.1"].ToString();  // Accessing user-defined property from ArticleReference
var propertyValue2 = oArticleReference.Parent.Properties["EPLAN.ArticleRef.UserProperty.1"][1].ToString(); // Accessing user-defined property from a parent of the ArticleReference
```

---

## Filtering overview
*Źródło: `Filtering overview.html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / Navigating the project data / Filtering overview*

Filtering overview The following diagram shows how to set filter classes used for example by the DMObjectsFinder .

---

## Graphics overview
*Źródło: `Graphics overview.html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / Navigating the project data / Graphics overview*

Graphics overview Class diagram of the EPLAN data model in Eplan.EplApi.DataModel.Graphics namespace.

---

## Locking
*Źródło: `Locking.html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / Locking*

Locking In computer science, locking is a synchronization mechanism for enforcing limits on access to a resource in a multi-threaded environment (multiple-user environment). Locks are one way of enforcing concurrency control policies. 
In EPLAN API, the term " locking an object " means to set an object reference to a state, where it can be edited by the current user / process, whereas no other user / process can edit it. In general, the user can always get an object in an un-locked / read-only way, even if it is locked by another user. If even this read-only access is not possible, we speak of an " exclusive lock ". Exclusive locking is necessary, if e.g. the structure of an EPLAN project is changed or if a project is copied, renamed or a backup is done. 
Please take into account that API locking only wraps P8 locking techniques. For further details about this functionality please refer to EPLAN Help > Editing and Managing Project > Multi-user Operation chapter of P8 help. 

### What can be locked "automatically"? 
- All project data – This can be done by getting the project from the SelectionSet (in add-ins) or by opening it via the ProjectManager . This depends on the LockProjectByDefault property, which is set to "true" by default. Also getting the selected project by the HeServices.SelectionSet.GetCurrentProject method locks the project (and its data) completely. Please note that read-only access is still possible from other P8 instances. 

- Exclusive project locking – This is done by setting the USER.TrDMProject.OperationMode.OpenProjectsExclusive setting to "true" before opening the project. As mentioned above, some project-wide operations require such an exclusive lock of a project, where it can be used by only one single P8 instance. 

- Selected elements – This is possible by setting the SelectionSet.LockSelectionByDefault property  to "true". By default, the option is enabled (set to "true"), so when getting selected items of a project, they can be changed in the API without setting this property. 

### SafetyPoint 
The SafetyPoint class provides automatic locking of data model objects. The mechanism is enabled from the time a SafetyPoint object is created until it is distroyed, so it is recommended to use it with the using keyword: 

### C# 
### Copy Code 
| var
project =
new
ProjectManager {LockProjectByDefault =
false
}.OpenProject(
@"$(MD_PROJECTS)\EPLAN-DEMO.elk"
);
// View placement '8' (on page =EB3+ETM/4)
ViewPlacement viewPlacement8 = project
.Pages[42]
.AllFirstLevelPlacements
.OfType<ViewPlacement>()
.FirstOrDefault(item => item.Properties.DMG_VIEWPLACEMENT_DESIGNATION.ToString() ==
"8"
);
using
(SafetyPoint safetyPoint = SafetyPoint.Create())
{ 
Console.WriteLine(viewPlacement8.IsLocked);
// False
viewPlacement8.Scale = 44.44;
// Set another scale
Console.WriteLine(viewPlacement8.IsLocked);
// True
safetyPoint.Commit();
// Necessary, otherwise changes are rolled back
}
Console.WriteLine(viewPlacement8.IsLocked);
// Again false

"Automatic" means that they are locked internally before any change is made and unlocked after SafetyPoint is disposed of. This way is recommended when you need to lock as little as possible and it is not clear which objects need to be locked to perform a change. After the SafetyPoint block, please call the Commit method, otherwise the changes will be rolled back. 

### What is a LockingStep? 
A LockingStep is an object used to automatically unlock API resources (such as projects, functions, etc). There are 2 ways to create this object: 
- Explicitly – Must be done in modeless dialog boxes and in offline API applications: 

### C# 
### Copy Code 
| using
(LockingStep oLockingStep =
new
LockingStep())
{
....
}

When there is necessary access to some resources and the LockingStep is not created, an exception will be thrown ( NoLockingStepException ). 
- P8 framework a ctions and scripts 
Anyway, there is no "Unlock" method in any data model class. The LockingStep class remembers all locks set during its lifespan and releases them when the LockingStep is being disposed. This guarantees that objects are released, even if an exception was thrown within the block. 
In rare cases, however, it may be necessary to switch off LockingStep creation (manual or automatical). This can be done using the PauseManualLock() and ResumeManualLock() methods of the LockingVector class. Please use them only in exceptional cases, i.e. when it is necessary to "manually" decide what to lock instead of relying on the P8 framework (see below). 

### Manual locking mode 
In addition to the automatic locking mechanism, it is also possible to call locking methods directly on the required objects. This low-level type of locking can be used concurrently with "automatic" locking or as the only locking. 
- Locking single StorableObject – This is done by calling LockObject on the required object. Please note that only properties directly connected with objects can be locked this way (such as internal / normal properties, sub-functions or sub-placements are excluded). 
- Locking all placements of a page in exclusive mode – This can be done by calling Page::LockAllObjects . Please consider that it is different than calling Page::LockObject , which locks only properties of a page. 
- Locking all objects of a project – This can be done with Project::LockAllObjects . 
- Locking all objects of a device – This is done with Function::LockDevice . Calling this method also locks all functions placed on the same page as functions of a device. 

### Guideline to Locking of data model objects 
If you don't need to mind multiple-user issues, e.g. when creating a new project with your own schematics generator, you should always lock the entire project. The project is locked by default when it is opened or created using the respective methods ( OpenProject(...) / CreateProject(...) ) of the ProjectManager class in DataModel . Also, getting the selected project through the method GetCurrentProject(...) in the HeServices.SelectionSet class, will lock the project completely. 
If you need to consider other users or processes working on the same project, you should lock as little of the project data as possible . To do this, you should first get, open, or create the project in an unlocked way. This can be done by setting the LockProjectByDefault property of a ProjectManager or the SelectionSet object to "false". With this unlocked project object, you simply lock the object (e.g. page) you want to change. Also mind that the locks are only released when disposing the respective LockingSteps, so set as few locks as possible in one l ocking step . 

### Differences between add-ins and offline API 
The main difference between locking in add-ins and offline API applications is that the Execute(...) method of the IEplAction interface, is already surrounded by a l ocking step , while the API programmer needs to implement the locking step(s) in an offline application by himself. 

### API Verifications 
Verification methods called by the EPLAN framework are not surrounded by a locking step. If this is necessary, the user needs to implement it himself. Please have in mind that the creation of a locking step inside a verification method has a great influence on the performance of the entire check. Therefore, this should be done as little as possible. 

### Locking in service methods (HeServices/ Actions ) 
All service functionality to which you pass a project resource as a string parameter will always automatically lock / unlock that resource. If locking is not possible due to multi-user issues, an exception will be thrown. This applies to all command line actions that take only string parameters. The HeServices classes have most of the time method overloads with both string-based and object passed parameters. If you pass an object to the method, you need to take care for the locking. 

### Determining which users currently have the project open 
To find out which users are currently working on the project, the Project class provides a CurrentUsers property that returns an array of UserInfo structures of the users who are accessing the project.

### Przykłady kodu (C#)
```csharp
var project = new ProjectManager {LockProjectByDefault = false}.OpenProject(@"$(MD_PROJECTS)\EPLAN-DEMO.elk");
// View placement '8' (on page =EB3+ETM/4)
ViewPlacement viewPlacement8 = project
.Pages[42]
.AllFirstLevelPlacements
.OfType<ViewPlacement>()
.FirstOrDefault(item => item.Properties.DMG_VIEWPLACEMENT_DESIGNATION.ToString() == "8");
using (SafetyPoint safetyPoint = SafetyPoint.Create())
{               
    Console.WriteLine(viewPlacement8.IsLocked);     // False
    viewPlacement8.Scale = 44.44;                   // Set another scale
    Console.WriteLine(viewPlacement8.IsLocked);     // True                  
    safetyPoint.Commit();                           // Necessary, otherwise changes are rolled back
}
Console.WriteLine(viewPlacement8.IsLocked);         // Again false
```
```csharp
using(LockingStep oLockingStep = new LockingStep())
{
   ....
}
```

---

## MasterData overview
*Źródło: `MasterData overview.html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / Navigating the project data / MasterData overview*

MasterData overview Class diagram of the EPLAN data model in the Eplan.EplApi.DataModel.MasterData namespace.

---

## Navigating the project data
*Źródło: `Navigating the project data.html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / Navigating the project data*

Navigating the project data There are two distinct methods of navigating through the EPLAN project. The most common is to use the navigation properties which you can find on each data model object. In addition to that, there is the DMObjectsFinder class. By its methods, you can retrieve filtered lists (arrays) of certain objects in a project. 

### Navigating through properties 
Regardless of the underlying implementation of EPLAN, the entire data model can be seen as a graph, with one to many and many to many relationships between the various object types in the graph. For example, a project has a one-to-many relationship with its pages. These relationships can be thought of as if they were simple basic arrays. Each of the objects of the EPLAN data model have a set of properties, which return such arrays of dependant objects, as you can see in the topic " Data model overview ". 
One of the most common requirements of a program is to loop through all of the objects in an array performing some function or other on each element. As an example, the class Eplan.EplApi.DataModel.Page has the following navigation properties, with each of which you can loop over a different collection of objects: 
- AllFirstLevelPlacements 
- AllGraphicalPlacements 
- AllPlacements 
- BoxedDevices 
- Functions 
- PLCs 
- PlugStrips 
- TerminalStrips 

There are also navigational properties with a one-to-one relationship, like Page.Project . 

The following code snippet shows how to loop over the f unctions on a page and get the name of the f unction : 
- C# 
- VB // Get an array with all functions on the page
Function[] arrFuncs = oPage.Functions;
// Loop over the functions and get their names
foreach
(Function oF
in
arrFuncs)
{
string
sName = oF.Name;
// Do something with the Name
}
' Get an array with all functions on the page
Dim
arrFuncs
As
Function
() = oPage.Functions
' Loop over the functions and get their names
Dim
oF
As
Function
For
Each
oF
In
arrFuncs
Dim
sName
As
String
=
oF
.Name
' Do something with the Name
Next

You can even filter these lists before getting them. The following example sets a filter to get only the functions that have the function category "PLUG". 
- C# 
- VB // Set filter category to "PLUG"
oPage.Filter.resetFilter();
oPage.Filter.Category = Function.Enums.Category.PLUG;
// Get all functions filtered by category=PLUG
Function[] arrFuncs = oPage.Functions;
foreach
(Function oF
in
arrFuncs)
{
string
sPlugName = oF.Name;
// Do something with the Name
}
' Set filter category to "PLUG"
oPage.Filter.resetFilter()
oPage.Filter.Category =
Function
.Enums.Category.PLUG
' Get all functions filtered by category=PLUG
Dim
arrFuncs
As
Function
() = oPage.Functions
Dim
oF
As
Function
For
Each
oF
In
arrFuncs
Dim
sPlugName
As
String
=
oF
.Name
' Do something with the Name
Next

Please mind that using navigation properties in order to set properties of an object in a nested way (e.g. oRectangle.Pen.ColorId = 5 ) will not work. In the example you need to first get the Pen object from the rectangle and then change the color ID and afterwards set the changed Pen object back to the Rectangle class. 

### DMObjectsFinder 

The DMObjectsFinder object is always initialized with a project. Starting with the project, it can get nearly any list of objects of a given type. Before getting the lists, they can be filtered by different means like a distinct set of properties. The following example gets all functions with a given device tag ("name"): 

- C# 
- VB string
strFuncName =
"=AP+PT1-X4"
;
// Initialize the DMObjectsFinder with a project
DMObjectsFinder oFinder =
new
DMObjectsFinder(m_oProject);
FunctionsFilter oFunctionsFilter =
new
FunctionsFilter();
oFunctionsFilter.ExactNameMatching =
true
;
oFunctionsFilter.Name = strFuncName;
// Get function with given name from project
Function[] arrFuncs = oFinder.GetFunctions(oFunctionsFilter);
foreach
(Function oF
in
arrFuncs)
{
Console.Out.WriteLine(
"Function name: '{0}'"
, oF.Name);
}
Dim
strFuncName
As
String
=
"=AP+PT1-X4"
' Initialize the DMObjectsFinder with a project
Dim
oFinder
As
New
DMObjectsFinder(m_oProject)
Dim
oFunctionsFilter
As
New
FunctionsFilter()
oFunctionsFilter.ExactNameMatching =
True
oFunctionsFilter.Name = strFuncName
' Get function with given name from project
Dim
arrFuncs
As
Function
() = oFinder.GetFunctions(oFunctionsFilter)
Dim
oF
As
Function
For
Each
oF
In
arrFuncs
Console.Out.WriteLine(
"Function name: '{0}'"
,
oF
.Name)
Next
oF

### Search class 

The Eplan.EplApi.HEServices.Search class offers another way for finding objects in a project. The class corresponds to the dialogs Find > Find... and Find > Show Results... in the GUI of EPLAN. As in this dialogs, you have two result lists to store your search results. 
Using this class, you can search for any string in a specified range of objects. The following example demonstrates the usage of the Search class. 
- C# 
- VB Search oSearch =
new
Search();
// Set all needed settings
oSearch[Search.Settings.CaseSensitive] =
false
;
oSearch[Search.Settings.WholeTexts] =
false
;
oSearch[Search.Settings.DeviceTag] =
true
;
oSearch[Search.Settings.AllProperties] =
false
;
oSearch[Search.Settings.Texts] =
false
;
oSearch[Search.Settings.PageData] =
false
;
oSearch[Search.Settings.ProjectData] =
false
;
oSearch[Search.Settings.GraphicPages] =
false
;
oSearch[Search.Settings.EvalutionPages] =
false
;
oSearch[Search.Settings.NotPlaced] =
false
;

oSearch.ClearSearchDB(oProject);
if
(oPage !=
null
)
{
// Either search in a page...
oSearch.Page(oPage, Name);
}
else
{
// ... or search the complete project
oSearch.Project(oProject, Name);
}
StorableObject[] oResults = oSearch.GetAllSearchDBEntries(oProject);
Dim
oSearch
As
Search =
New
Search
oSearch.SearchDatabaseNr = 0
oSearch.ClearSearchDB(oProject, 0)
oSearch(Search.Settings.AllProperties) =
True
oSearch(Search.Settings.CaseSensitive) =
False
oSearch(Search.Settings.DeviceTag) =
True
oSearch(Search.Settings.LogicPages) =
True
oSearch(Search.Settings.GraphicPages) =
False
oSearch(Search.Settings.EvalutionPages) =
False
oSearch(Search.Settings.NotPlaced) =
False
oSearch(Search.Settings.WholeTexts) =
False
oSearch(Search.Settings.PageData) =
True
oSearch(Search.Settings.ProjectData) =
True
oSearch.Project(oProject, txtSearch.Text)
Dim
oFoundObjects
As
StorableObject() = oSearch.GetAllSearchDBEntries(oProject, 0)

### Przykłady kodu (C#)
```csharp
// Get an array with all functions on the page
Function[] arrFuncs = oPage.Functions;
// Loop over the functions and get their names
foreach(Function oF in arrFuncs)
{
    string sName = oF.Name;
    // Do something with the Name
}
```
```csharp
' Get an array with all functions on the page
Dim arrFuncs As Function() = oPage.Functions
' Loop over the functions and get their names
Dim oF As Function
For Each oF In  arrFuncs
   Dim sName As String = oF.Name
   ' Do something with the Name
Next
```
```csharp
// Set filter category to "PLUG"
oPage.Filter.resetFilter();
oPage.Filter.Category = Function.Enums.Category.PLUG;
// Get all functions filtered by category=PLUG
Function[] arrFuncs = oPage.Functions;
foreach(Function oF in arrFuncs)
{
    string sPlugName = oF.Name;
    // Do something with the Name
}
```
```csharp
' Set filter category to "PLUG"
oPage.Filter.resetFilter()
oPage.Filter.Category = Function.Enums.Category.PLUG
' Get all functions filtered by category=PLUG
Dim arrFuncs As Function() = oPage.Functions
Dim oF As Function
For Each oF In  arrFuncs
   Dim sPlugName As String = oF.Name
   ' Do something with the Name
Next
```
```csharp
string strFuncName = "=AP+PT1-X4";
// Initialize the DMObjectsFinder with a project
DMObjectsFinder oFinder = new DMObjectsFinder(m_oProject);
FunctionsFilter oFunctionsFilter = new FunctionsFilter();
oFunctionsFilter.ExactNameMatching = true;
oFunctionsFilter.Name = strFuncName;
// Get function with given name from project
Function[] arrFuncs = oFinder.GetFunctions(oFunctionsFilter);

foreach(Function oF in arrFuncs)
{
    Console.Out.WriteLine("Function name: '{0}'", oF.Name);
}
```
```csharp
Dim strFuncName As String = "=AP+PT1-X4"
' Initialize the DMObjectsFinder with a project
Dim oFinder As New DMObjectsFinder(m_oProject)
Dim oFunctionsFilter As New FunctionsFilter()
oFunctionsFilter.ExactNameMatching = True
oFunctionsFilter.Name = strFuncName
' Get function with given name from project
Dim arrFuncs As Function() = oFinder.GetFunctions(oFunctionsFilter)

Dim oF As Function
For Each oF In  arrFuncs
   Console.Out.WriteLine("Function name: '{0}'", oF.Name)
Next oF
```
```csharp
Search oSearch = new Search();
// Set all needed settings
oSearch[Search.Settings.CaseSensitive] = false;
oSearch[Search.Settings.WholeTexts] = false;
oSearch[Search.Settings.DeviceTag] = true;
oSearch[Search.Settings.AllProperties] = false;
oSearch[Search.Settings.Texts] = false;
oSearch[Search.Settings.PageData] = false;
oSearch[Search.Settings.ProjectData] = false;
oSearch[Search.Settings.GraphicPages] = false;
oSearch[Search.Settings.EvalutionPages] = false;
oSearch[Search.Settings.NotPlaced] = false;

oSearch.ClearSearchDB(oProject);
if (oPage != null)
{
    // Either search in a page...
    oSearch.Page(oPage, Name);
}
else
{
    // ... or search the complete project
    oSearch.Project(oProject, Name);
}
StorableObject[] oResults = oSearch.GetAllSearchDBEntries(oProject);
```
```csharp
Dim oSearch As Search = New Search
oSearch.SearchDatabaseNr = 0
oSearch.ClearSearchDB(oProject, 0)
oSearch(Search.Settings.AllProperties) = True
oSearch(Search.Settings.CaseSensitive) = False
oSearch(Search.Settings.DeviceTag) = True
oSearch(Search.Settings.LogicPages) = True
oSearch(Search.Settings.GraphicPages) = False
oSearch(Search.Settings.EvalutionPages) = False
oSearch(Search.Settings.NotPlaced) = False
oSearch(Search.Settings.WholeTexts) = False
oSearch(Search.Settings.PageData) = True
oSearch(Search.Settings.ProjectData) = True
oSearch.Project(oProject, txtSearch.Text)
Dim oFoundObjects As StorableObject() = oSearch.GetAllSearchDBEntries(oProject, 0)
```

---

## Project settings
*Źródło: `Project settings.html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / Project settings*

Project settings Every project has its own set of settings. To get and set these settings, as well as to create new settings, the DataModel namespace provides a class called ProjectSettings . It has similar methods as the settings class in Eplan.EplApi.Base , but an instance of this class is initialized with the project object. Unlike the "normal" settings, the project settings keys don't start with "PROJECT", where the other settings start with "USER", "STATION", or "COMPANY". 

Example for project related settings Projects > <project name> > Connections > General : 

### Example Title 
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
="PROJECT"
>
<
MOD
name
="EsConnection"
>
<
Setting
name
="ManageConnectionsInNDPDialog"
type
="bool"
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
="ManageSaddleJumperConnPointsInNDPDialog"
type
="bool"
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
="SortConnectionsByPlacement"
type
="bool"
desc
="2058"
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

The following example shows how to get the project setting for the project display languages. 
- C# 
- VB Eplan.EplApi.DataModel.ProjectSettings projectSettings =
new
Eplan.EplApi.DataModel.ProjectSettings(oProject);
string
languages = projectSettings.GetExpandedStringSetting(
"TRANSLATEGUI.DISPLAYED_LANGUAGES"
, 0)
Dim
projectSettings
As
New
Eplan.EplApi.DataModel.ProjectSettings(oProject)
Dim
languages
As
String
languages = projectSettings.GetExpandedStringSetting(
"TRANSLATEGUI.DISPLAYED_LANGUAGES"
, _
System.Convert.ToUInt32(0))
See Also 
### API Miscellaneous Working with settings

### Przykłady kodu (C#)
```csharp
<?xml version="1.0" encoding="utf-8" ?>
<Settings ver="2.4.1" format="2">
 <CAT name="PROJECT">
  <MOD name="EsConnection">
   <Setting name="ManageConnectionsInNDPDialog" type="bool">
    <Val>0</Val>
   </Setting>
   <Setting name="ManageSaddleJumperConnPointsInNDPDialog" type="bool">
    <Val>0</Val>
   </Setting>
   <Setting name="SortConnectionsByPlacement" type="bool" desc="2058">
    <Val>0</Val>
   </Setting>
  </MOD>
 </CAT>
</Settings>
```
```csharp
Eplan.EplApi.DataModel.ProjectSettings projectSettings =
          new Eplan.EplApi.DataModel.ProjectSettings(oProject);
string languages = projectSettings.GetExpandedStringSetting("TRANSLATEGUI.DISPLAYED_LANGUAGES", 0)
```
```csharp
Dim projectSettings As New Eplan.EplApi.DataModel.ProjectSettings(oProject)
Dim languages As String
languages = projectSettings.GetExpandedStringSetting("TRANSLATEGUI.DISPLAYED_LANGUAGES", _
                                                       System.Convert.ToUInt32(0))
```

---

## Transactions
*Źródło: `Transactions.html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / Transactions*

Transactions The term " transaction " refers to a set of operations that form a working unit in the EPLAN project database. They can be executed only all together or not a single one. This grouping ensures data integrity and consistency even in the case of a system failure. For example: 

### C# 
### Copy Code 
| using
(Transaction oTransaction =
new
TransactionManager().CreateTransaction())
{
oFunction1.Name =
"=+-NewTestFunctionName_1"
;
oFunction2.Name =
"=+-NewTestFunctionName_2"
;
oTransaction.Commit();
}

So if the execution of the code is aborted before the Commit() was called, the "Name"properties remain unchanged. 

### Nesting API transactions 
It is also possible to nest transactions in API. For example: 

### C# 
### Copy Code 
| oFunction.Name =
"oFunction0"
;
using
(Transaction oTransaction1 =
new
TransactionManager().CreateTransaction())
{
using
(Transaction oTransaction2 =
new
TransactionManager().CreateTransaction())
{
oFunction.Name =
"Function2"
;
oTransaction2.Commit();
}
Console.Writeline(oFunction.Name)
// Will be "oFunction2" returned,
oFunction.Name =
"Function1"
;
Console.Writeline(oFunction.Name)
// Will be "oFunction1" returned,
}
Console.Writeline(oFunction.Name)
// Will be "oFunction0" returned, because outer transaction oTransaction1 wasn't committed

In this case, an inner transaction is treated as one of the operations of the outer transaction. 

### Internal EPLAN and API transactions 
We distinguish two types of transaction: 
1. API transactions – They are opened explicitly or implicitly from API. Explicit opening is done by creating a Transaction object from the TransactionManager : 

### C# 
### Copy Code 
| Transaction oTransaction =
new
TransactionManager().CreateTransaction();

Implicit opening is done by creating the same Transaction object by some EPLAN operations, (like creating new objects, changing a property) in a way that is invisible for API user 
2. EPLAN internal transactions – They are started inside of the EPLAN framework, so they are opened and closed implicitly. 
### Using API transactions and internal transactions at the same 
Using API transactions and internal transactions at the same time can cause problems. So please consider the following rules to avoid them: 
- API transaction within an internal transaction 

An API transaction may always be opened within an internal transaction. The API developer has a possibility to check whether an API transaction is opened using the following property: 

### C# 
### Copy Code 
| TransactionManager::IsTransactionRunning

A commit of an API transaction does not result in a change to the database and is not saved in the database until the termination of the internal transaction. Aborting an API transaction does not abort an internal transaction, but throws an exception because an internal transaction is running and cannot be aborted. 
- An internal transaction within an API transaction 

An internal transaction may always be opened within an API transaction. The API developer has the possibility to check whether an internal transaction is opened using the following property: 

### C# 
### Copy Code 
| TransactionManager::IsEplanTransactionRunning

If an internal transaction is to be opened, the API transaction becomes committed. If an internal transaction is again closed ( Abort or Commit ), then the API transaction will be started again. The API transaction class also has a property that indicates whether an internal transaction was opened and closed within the API transaction: 

### C# 
### Copy Code 
| Transaction::IsImplicitEplanTransactionCommited

### Przykłady kodu (C#)
```csharp
using (Transaction oTransaction = new TransactionManager().CreateTransaction())
{
     oFunction1.Name = "=+-NewTestFunctionName_1";
     oFunction2.Name = "=+-NewTestFunctionName_2";
     oTransaction.Commit();
}
```
```csharp
oFunction.Name = "oFunction0";
using (Transaction oTransaction1 = new TransactionManager().CreateTransaction())
{
     using(Transaction oTransaction2 = new TransactionManager().CreateTransaction())
     {
          oFunction.Name = "Function2";
          oTransaction2.Commit();
     }
     Console.Writeline(oFunction.Name) // Will be "oFunction2" returned,
     oFunction.Name = "Function1";
     Console.Writeline(oFunction.Name) // Will be "oFunction1" returned,
}
Console.Writeline(oFunction.Name) // Will be "oFunction0" returned, because outer transaction oTransaction1 wasn't committed
```
```csharp
Transaction oTransaction = new TransactionManager().CreateTransaction();
```
```csharp
TransactionManager::IsTransactionRunning
```
```csharp
TransactionManager::IsEplanTransactionRunning
```
```csharp
Transaction::IsImplicitEplanTransactionCommited
```

---

## Working with parts
*Źródło: `Working with parts.html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / Working with parts*

Working with parts As with other master data, all the information about parts that is required to work independently with a project is stored in the project itself. There are always two parts databases (redundant data management): the central parts database for all projects and the project internal parts database, which only contains parts placed into the project. The central parts database (system parts) can be either an EPLAN database ( *.alk ) or an SQL database. The following image represents this situation: 

Within a project, the parts from the parts project database are referenced, i.e. a part that is used 10 times – by a Function , a Connection , or as a project part by the project itself - is stored only once, and is referenced 10 times in the project (via the part number). Parts data can therefore be easily changed or synchronized via the central parts database. 

### How does it work in API? 
In the P8 API, the part stored in the internal parts database of the project is represented by the Eplan.EplApi.DataModel.Article class. The reference to a particular part on a Function , a Connection or the Project , is represented by the Eplan.EplApi.DataModel.ArticleReference class. You can get the ArticleReference objects through the ArticleReferences property on the above-mentioned classes. 
In order to add a new reference to a part, you can use the AddArticleReference methods on Project , Function or Connection . Please mind , that AddArticleReference just adds the reference to a part. An Article is also added to the object, but only if the referenced part already exists in the system or project database. 

In general, articles stored in a P8 project are created explicitly.Therefore you use the method void Article.Create(string partnr, string variant) . This method creates an Article object. If there is already a part ( Article ) with that partnr and variant , an exception will be thrown. After calling the Create method, the Article object is completely empty. Only the part number and the variant are set, but no other property is filled. 
To fill an Article with properties of the master data, please use the explicit function bool Article::LoadFromMasterdata . Using the current part data source, all (the configured) article data of the master data is loaded to the embedded part. If the article ( partnr + variant ) can't be found in the master data, Article::LoadFromMasterdata will return "false". On Success "true" is returned. 

### Adding Parts and referencing them 
The following example shows how to add and reference an Article in Project , Function and Connection: 

### C# 
### Copy Code 
| Article oArticle =
new
Article();
oArticle.Create(oProject,
"KUKA.KR30-3"
,
"1"
);
// An empty Article is created in a Project
bool
bResult = oArticle.LoadFromMasterdata();
// Article is filled with data from system parts database
oProject.AddArticleReference(
"KUKA.KR30-3"
,
"1"
, 1);
// Reference to the Article is created on a Project
oFunction.AddArticleReference(
"KUKA.KR30-3"
,
"1"
, 1);
// Reference to the Article is created on a Function
oConnection.AddArticleReference(
"KUKA.KR30-3"
,
"1"
, 1);
// Reference to the Article is created on a Connection

### Przykłady kodu (C#)
```csharp
Article oArticle = new Article();
    oArticle.Create(oProject, "KUKA.KR30-3", "1");            // An empty Article is created in a Project
    bool bResult = oArticle.LoadFromMasterdata();             // Article is filled with data from system parts database

    oProject.AddArticleReference("KUKA.KR30-3", "1", 1);      // Reference to the Article is created on a Project
    oFunction.AddArticleReference("KUKA.KR30-3", "1", 1);     // Reference to the Article is created on a Function
    oConnection.AddArticleReference("KUKA.KR30-3", "1", 1);   // Reference to the Article is created on a Connection
```

---

## Working with parts database
*Źródło: `Working with parts database.html`*
*Ścieżka: EPLAN API / User Guide / API MasterData / Working with parts database*

Working with parts database The following example shows how to open the default parts database: 
- C# MDPartsManagement oPartsManagement =
new
MDPartsManagement();
MDPartsDatabase partsDatabase = oPartsManagement.OpenDatabase();

It is also possible to open a selected parts database from a file: 
- C# MDPartsDatabase partsDatabase =
new
MDPartsManagement().OpenDatabase(
"C:\\PathToDirectory\\DataBase.alk"
);

Then you can check information about the open database: 
- C# // Show database name
var
bdName = MDPartsManagement.SelectedPartsDatabaseAsString;
new
Decider().Decide(EnumDecisionType.eOkDecision, bdName,
"DB"
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
// Check if database is open
if
(partsDatabase.IsOpen);
new
Decider().Decide(EnumDecisionType.eOkDecision,
"DataBase is open"
,
"DB"
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
// Check if database is readonly
if
(!partsDatabase.IsReadOnly) ;
new
Decider().Decide(EnumDecisionType.eOkDecision,
"DataBase is not readolny"
,
"DB"
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
// Get database version
var
dataBaseVersion = partsDatabase.Version;
// Get database type
var
dataBaseType = partsDatabase.Type;
// Check if database scheme is up to date
if
(partsDatabase.IsSchemeUpToDate) ;
new
Decider().Decide(EnumDecisionType.eOkDecision,
"Scheme is up to date"
,
"DB"
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);

Finally, close the database: 
- C# partsDatabase.Close();

### Przykłady kodu (C#)
```csharp
MDPartsManagement oPartsManagement = new MDPartsManagement();
MDPartsDatabase partsDatabase = oPartsManagement.OpenDatabase();
```
```csharp
MDPartsDatabase partsDatabase = new MDPartsManagement().OpenDatabase("C:\\PathToDirectory\\DataBase.alk");
```
```csharp
// Show database name
var bdName = MDPartsManagement.SelectedPartsDatabaseAsString;
new Decider().Decide(EnumDecisionType.eOkDecision, bdName, "DB", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);

// Check if database is open
if (partsDatabase.IsOpen);
    new Decider().Decide(EnumDecisionType.eOkDecision, "DataBase is open", "DB", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);

// Check if database is readonly
if (!partsDatabase.IsReadOnly) ;
    new Decider().Decide(EnumDecisionType.eOkDecision, "DataBase is not readolny", "DB", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);

// Get database version
var dataBaseVersion = partsDatabase.Version;

// Get database type
var dataBaseType = partsDatabase.Type;

// Check if database scheme is up to date
if (partsDatabase.IsSchemeUpToDate) ;
  new Decider().Decide(EnumDecisionType.eOkDecision, "Scheme is up to date", "DB", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
```
```csharp
partsDatabase.Close();
```

---
