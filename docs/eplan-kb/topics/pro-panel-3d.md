# EPLAN API — pro-panel-3d

*Poza MVP — szafy 3D*

Dokumentów: 22

## 3D macros
*Źródło: `3D macros.html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / API Pro Panel / 3D macros*

3D macros The standard WindowMacro class is used to represent both 3D and 2D window macros. It has been extended with methods that cover 3D functionality. 

Creating 3D window macros: 

### C# 
### Copy Code 
| MultiLangString oMultiLangString =
new
MultiLangString();
oMultiLangString.AddString(ISOCode.Language.L_en_US,
"Window macro 3D description"
);
string
strWindowMacro3DFilePath = m_oTestProject.ProjectDirectoryPath +
"\\test_window_macro3D.ema"
;

WindowMacro oWMacro =
new
WindowMacro();
oWMacro.Create(strWindowMacro3DFilePath, 0,
new
Placement3D[] { oComponent1, oComponent2, oComponent3 },
true
, oMultiLangString);

Inserting: 

### C# 
### Copy Code 
| // Preparing transformation
Matrix3D oMatrix =
new
Matrix3D(); 
Quaternion oQaternion =
new
Quaternion(
new
Vector3D(1.0, 1.0, 1.0), 0.2); 
oMatrix.Rotate(oQaternion);
// Preparing WindowMacro object
string
strWindowMacroName =
"c:\\SIE.3LD9 284-1B.ema"
; 
WindowMacro oWMacro =
new
WindowMacro(); 
oWMacro.Open(strWindowMacroName, m_oTestProject, 0);
// Insert macro into an InstallationSpace
Insert3D oInsert3D =
new
Insert3D(); 
StorableObject[] arrStorableObjects = oInsert3D.WindowMacro(oWMacro, nVariant, oInstallationSpace, 
oMatrix, Insert3D.MoveKind.Absolute, WindowMacro.Enums.NumerationMode.None);

### Przykłady kodu (C#)
```csharp
MultiLangString oMultiLangString = new MultiLangString();
oMultiLangString.AddString(ISOCode.Language.L_en_US, "Window macro 3D description");
string strWindowMacro3DFilePath = m_oTestProject.ProjectDirectoryPath + "\\test_window_macro3D.ema";

WindowMacro oWMacro = new WindowMacro();
oWMacro.Create(strWindowMacro3DFilePath, 0, new Placement3D[] { oComponent1, oComponent2, oComponent3 }, true, oMultiLangString);
```
```csharp
// Preparing transformation 
Matrix3D oMatrix = new Matrix3D(); 
Quaternion oQaternion = new Quaternion(new Vector3D(1.0, 1.0, 1.0), 0.2); 
oMatrix.Rotate(oQaternion); 
// Preparing WindowMacro object 
string strWindowMacroName = "c:\\SIE.3LD9 284-1B.ema"; 
WindowMacro oWMacro = new WindowMacro(); 
oWMacro.Open(strWindowMacroName, m_oTestProject, 0); 
// Insert macro into an InstallationSpace 
Insert3D oInsert3D = new Insert3D(); 
StorableObject[] arrStorableObjects = oInsert3D.WindowMacro(oWMacro, nVariant, oInstallationSpace, 
oMatrix, Insert3D.MoveKind.Absolute, WindowMacro.Enums.NumerationMode.None);
```

---

## API Pro Panel
*Źródło: `API Pro Panel.html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / API Pro Panel*

API Pro Panel EPLAN API currently provides users with access to EPLAN Pro Panel objects. In general, any functionality that can be done via the user interface is also available in the API Pro Panel. 
This chapter gives the user an overview of how API objects can be used in EPLAN Pro Panel. The following pages show how to create particular objects and how they look in the GUI. 

### Basics 
API Pro Panel was created as an extension to the standard API DataModel ( Eplan.EplApi.DataModelu.dll assembly). 
So there is a new namespace Eplan:EplApi:DataModel:E3D for 3D classes and HEServices methods that operate on them. 
Usually it is enough to have EPLAN Electric P8 to use API Pro Panel. However, some methods / properties however may require the installation of EPLAN Pro Panel with appropriate license. 

### UML class diagram 
The diagram below shows the hierarchy of the most important classes in the Pro Panel API.

---

## Area (restricted placing/drilling area in GUI)
*Źródło: `Area (restricted placing_drilling area in GUI).html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / API Pro Panel / Area (restricted placing/drilling area in GUI)*

Area (restricted placing/drilling area in GUI) The Area is a part of the mounting surface on which 3D placements can not be placed. As soon as a parts placement is put into a restricted placing area, an error is generated (by verification no. 026012). 

### C# 
### Copy Code 
| MountingPanel oMountingPanel =
new
MountingPanel();
oMountingPanel.Create(m_oTestProject, 500.0, 500.0, 2.0);
oMountingPanel.Parent = m_oInstallationSpace;
MultiLangString oFunctionDefinitionName =
new
MultiLangString();

oFunctionDefinitionName.AddString(ISOCode.Language.L_en_US,
"Restricted mounting area"
);
MultiLangString oGroup =
new
MultiLangString();
oGroup.AddString(ISOCode.Language.L_en_US,
"Restricted area"
);
FunctionDefinition oFunctionDefinition =
new
FunctionDefinition(m_oTestProject, Function.Enums.Category.AreaDefinition, oGroup, oFunctionDefinitionName); Area oArea =
new
Area();
oArea.Create(m_oTestProject, oFunctionDefinition);
oArea.Parent = oMountingPanel.Planes[0];
oArea.Size =
new
PointD(200.0, 250.0);

### Przykłady kodu (C#)
```csharp
MountingPanel oMountingPanel = new MountingPanel();
oMountingPanel.Create(m_oTestProject, 500.0, 500.0, 2.0);
oMountingPanel.Parent = m_oInstallationSpace;
MultiLangString oFunctionDefinitionName = new MultiLangString();

oFunctionDefinitionName.AddString(ISOCode.Language.L_en_US, "Restricted mounting area");
MultiLangString oGroup = new MultiLangString();
oGroup.AddString(ISOCode.Language.L_en_US, "Restricted area");
FunctionDefinition oFunctionDefinition = new FunctionDefinition(m_oTestProject, Function.Enums.Category.AreaDefinition, oGroup, oFunctionDefinitionName); Area oArea = new Area();
oArea.Create(m_oTestProject, oFunctionDefinition);
oArea.Parent = oMountingPanel.Planes[0];
oArea.Size = new PointD(200.0, 250.0);
```

---

## BusBarSystem
*Źródło: `BusBarSystem.html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / API Pro Panel / BusBarSystem*

BusBarSystem BusBarSystem class represent "Busbar system" items in Pro Panel. 
### 
- C# // InstallationSpace
var
oInstallationSpace =
new
InstallationSpace();
oInstallationSpace.Create(oProject,
"BusBarSystem_InstallationSpace"
);
// CopperBundle
var
copperBundle = CopperBundle.Create(oProject,
new
List<Placement3D>());
copperBundle.Parent = oInstallationSpace;
copperBundle.Properties.COPPERBUNDLE_DESIGNATION =
"RIT.BBS.RiLine60_1_ECu15x05_2400 - BusBarSystem"
;
// BusBarSystem
var
oBusBarSystem =
new
BusBarSystem();
var
article =
"RIT.BBS.RiLine60_1_ECu15x05_2400"
;
var
variant =
"1"
;
var
numberOfHolders = 3;
var
length = 240;
oBusBarSystem.Create(oProject, article, variant, numberOfHolders, length);
oBusBarSystem.Parent = copperBundle;

### Przykłady kodu (C#)
```csharp
// InstallationSpace
var oInstallationSpace = new InstallationSpace();
oInstallationSpace.Create(oProject, "BusBarSystem_InstallationSpace");

// CopperBundle
var copperBundle = CopperBundle.Create(oProject, new List<Placement3D>());
copperBundle.Parent = oInstallationSpace;
copperBundle.Properties.COPPERBUNDLE_DESIGNATION = "RIT.BBS.RiLine60_1_ECu15x05_2400 - BusBarSystem";

// BusBarSystem
var oBusBarSystem = new BusBarSystem();
var article = "RIT.BBS.RiLine60_1_ECu15x05_2400";
var variant = "1";
var numberOfHolders = 3;
var length = 240;
oBusBarSystem.Create(oProject, article, variant, numberOfHolders, length);
oBusBarSystem.Parent = copperBundle;
```

---

## Cabinet (enclosure in GUI)
*Źródło: `Cabinet (enclosure in GUI).html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / API Pro Panel / Cabinet (enclosure in GUI)*

Cabinet (enclosure in GUI) ### C# 
### Copy Code 
| Cabinet oCabinet =
new
Cabinet();
oCabinet.Create(oTestProject,
"TS 8886.500"
,
"1"
);
oCabinet.Parent = oInstallationSpace;

### Przykłady kodu (C#)
```csharp
Cabinet oCabinet = new Cabinet();
oCabinet.Create(oTestProject, "TS 8886.500", "1");
oCabinet.Parent = oInstallationSpace;
```

---

## Component (part placement in GUI)
*Źródło: `Component (part placement in GUI).html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / API Pro Panel / Component (part placement in GUI)*

Component (part placement in GUI) The Component class represents various Pro Panel items, such as doors, frame profiles, accessories, etc. 
Terminal: 

### C# 
### Copy Code 
| InstallationSpace oInstallationSpace =
new
InstallationSpace();
oInstallationSpace.Create(m_oTestProject,
"Terminal installation space"
);

Component oTerminal =
new
Component();
oTerminal.Create(m_oTestProject,
"PXC.3022276"
,
"1"
);
oTerminal.Parent = oInstallationSpace;

Plug: 

### C# 
### Copy Code 
| InstallationSpace oInstallationSpace =
new
InstallationSpace();
oInstallationSpace.Create(m_oTestProject,
"Plug installation space"
);

Component oComponent =
new
Component();
oComponent.Create(m_oTestProject,
"Plug.3-pole+PE"
,
"1"
);
oComponent.Parent = oInstallationSpace;

Power supply: 

### C# 
### Copy Code 
| InstallationSpace oInstallationSpace =
new
InstallationSpace();
oInstallationSpace.Create(m_oTestProject,
"Power supply unit installation space"
);
Component oComponent =
new
Component();
oComponent.Create(m_oTestProject,
@"PXC.2938581"
,
"1"
);
oComponent.Parent = oInstallationSpace;

### Przykłady kodu (C#)
```csharp
InstallationSpace oInstallationSpace = new InstallationSpace();
oInstallationSpace.Create(m_oTestProject, "Terminal installation space");

Component oTerminal = new Component();
oTerminal.Create(m_oTestProject, "PXC.3022276", "1");
oTerminal.Parent = oInstallationSpace;
```
```csharp
InstallationSpace oInstallationSpace = new InstallationSpace();
oInstallationSpace.Create(m_oTestProject, "Plug installation space");

Component oComponent = new Component();
oComponent.Create(m_oTestProject, "Plug.3-pole+PE", "1");
oComponent.Parent = oInstallationSpace;
```
```csharp
InstallationSpace oInstallationSpace = new InstallationSpace();
oInstallationSpace.Create(m_oTestProject, "Power supply unit installation space");
Component oComponent = new Component();
oComponent.Create(m_oTestProject, @"PXC.2938581", "1");
oComponent.Parent = oInstallationSpace;
```

---

## Connection3D
*Źródło: `Connection3D.html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / API Pro Panel / Connection3D*

Connection3D The Connection3D class represents a 3D connection between two Placement3D objects. 
It inherits from the "normal" Connection. 

### C# 
### Copy Code 
| // Creating a 3D connection that exists between two 3D functions
Connection3D oConnection3DNoConnectionPoints =
new
Connection3D();
oConnection3DNoConnectionPoints.Create(oFunction3D_1, oFunction3D_2);
// Creating a 3D connection using connection point indexes
Connection3D oConnection3D =
new
Connection3D();
oConnection3D.Create(oComponent3D_1, 1, oComponent3D_2, 2);
// Route connections
List<StorableObject> olist =
new
List<StorableObject>();
olist.Add(oPlacement3D_1);
olist.Add(oPlacement3D_2);
ConnectionService3D oConnectionService3D =
new
ConnectionService3D();
oConnectionService3D.RouteConnections(olist);

### Przykłady kodu (C#)
```csharp
// Creating a 3D connection that exists between two 3D functions
Connection3D oConnection3DNoConnectionPoints = new Connection3D();
oConnection3DNoConnectionPoints.Create(oFunction3D_1, oFunction3D_2);

// Creating a 3D connection using connection point indexes
Connection3D oConnection3D = new Connection3D();
oConnection3D.Create(oComponent3D_1, 1, oComponent3D_2, 2);

// Route connections
List<StorableObject> olist = new List<StorableObject>();
olist.Add(oPlacement3D_1);
olist.Add(oPlacement3D_2);
ConnectionService3D oConnectionService3D = new ConnectionService3D();
oConnectionService3D.RouteConnections(olist);
```

---

## Creating 3D objects
*Źródło: `Creating 3D objects.html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / API Pro Panel / Creating 3D objects*

Creating 3D objects Creating most 3D objects is done by using an article number and variant. The example below shows how to create and place a cabinet in the InstallationSpace . 

### C# 
### Copy Code 
| Cabinet oCabinet =
new
Cabinet();
oCabinet.Create(oProject,
"TS 8886.500"
,
"1"
);
// Parent will be set to installation space
oCabinet.Parent = oProject.InstallationSpaces[0];
// Create identity matrix
System.Windows.Media.Media3D.Matrix3D oMatrix =
new
System.Windows.Media.Media3D.Matrix3D();
// Change the location to (100, 150, 0)
oMatrix.Transform(
new
System.Windows.Media.Media3D.Point3D(100, 150, 0));
oCabinet.AbsoluteTransformation = oMatrix;

### Przykłady kodu (C#)
```csharp
Cabinet oCabinet = new Cabinet();
oCabinet.Create(oProject, "TS 8886.500", "1");
// Parent will be set to installation space
oCabinet.Parent = oProject.InstallationSpaces[0];
// Create identity matrix
System.Windows.Media.Media3D.Matrix3D oMatrix = new System.Windows.Media.Media3D.Matrix3D();
// Change the location to (100, 150, 0)
oMatrix.Transform(new System.Windows.Media.Media3D.Point3D(100, 150, 0));
oCabinet.AbsoluteTransformation = oMatrix;
```

---

## Drilling (Cut-out in GUI)
*Źródło: `Drilling (Cut-out in GUI).html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / API Pro Panel / Drilling (Cut-out in GUI)*

Drilling (Cut-out in GUI) The Drilling class represents the opening in construction items such as mounting panels and sheets, that are drilled or manufactured by NC robots. 

### C# 
### Copy Code 
| Drilling oDrillingHole = Drilling.CreateTapHole(oProject, 50.0,
null
);
oDrillingHole.SetParent(oPlane,
true
);
oDrillingHole.GetSourceMates(
true
)[0].SnapTo(oPlane.GetTargetMates(
true
)[0]
as
PlaneMate, 0.0, 0.0, 0.0);

Drilling oDrillingHexagon = Drilling.CreateHexagon(oProject, 75.0,
null
);
oDrillingHexagon.SetParent(oPlane,
true
); oDrillingHexagon.GetSourceMates(
true
)[0].SnapTo(oPlane.GetTargetMates(
true
)[0]
as
PlaneMate, 40.0, 30.0, 50.0);

### Przykłady kodu (C#)
```csharp
Drilling oDrillingHole = Drilling.CreateTapHole(oProject, 50.0, null);
oDrillingHole.SetParent(oPlane, true);
oDrillingHole.GetSourceMates(true)[0].SnapTo(oPlane.GetTargetMates(true)[0] as PlaneMate, 0.0, 0.0, 0.0);

Drilling oDrillingHexagon = Drilling.CreateHexagon(oProject, 75.0, null);
oDrillingHexagon.SetParent(oPlane, true); oDrillingHexagon.GetSourceMates(true)[0].SnapTo(oPlane.GetTargetMates(true)[0] as PlaneMate, 40.0, 30.0, 50.0);
```

---

## Duct (wire duct in GUI)
*Źródło: `Duct (wire duct in GUI).html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / API Pro Panel / Duct (wire duct in GUI)*

Duct (wire duct in GUI) The Duct class represents ducts that hold cables in an organized manner and route them to the connected components. 

### C# 
### Copy Code 
| MountingPanel oMountingPanel =
new
MountingPanel();
oMountingPanel.Create(m_oTestProject, 500.0, 400.0, 2.0);
oMountingPanel.Parent = m_oInstallationSpace;
Plane oPlane = oMountingPanel.Planes[0];
Duct oDuct =
new
Duct();
oDuct.Create(m_oTestProject,
"KK3060"
,
"1"
, 250.0);
oDuct.Parent = oPlane;
oDuct.FindSourceMate(
"M4"
,
true
).SnapTo(oPlane.GetTargetMates(
true
)[0]
as
PlaneMate, 0.0, 20.0, 300.0);

### Przykłady kodu (C#)
```csharp
MountingPanel oMountingPanel = new MountingPanel();
oMountingPanel.Create(m_oTestProject, 500.0, 400.0, 2.0);
oMountingPanel.Parent = m_oInstallationSpace;
Plane oPlane = oMountingPanel.Planes[0];
Duct oDuct = new Duct();
oDuct.Create(m_oTestProject, "KK3060", "1", 250.0);
oDuct.Parent = oPlane;
oDuct.FindSourceMate("M4", true).SnapTo(oPlane.GetTargetMates(true)[0] as PlaneMate, 0.0, 20.0, 300.0);
```

---

## Getting 3D objects
*Źródło: `Getting 3D objects.html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / API Pro Panel / Getting 3D objects*

Getting 3D objects Getting 3D objects 
The DMObjectsFinder class was enhanced with methods for searching 3D objects. 

### C# 
### Copy Code 
| // Searching 3D functions with the name '=EB3+ET1-U1'
string
str3DFunction =
"=EB3+ET1-U1"
;
Functions3DFilter oFunctions3DFilter =
new
Functions3DFilter();
Function3DPropertyList oFunction3DPropertyList =
new
Function3DPropertyList();
oFunction3DPropertyList.FUNC_FULLDEVICETAG = str3DFunction;
oFunctions3DFilter.SetFilteredPropertyList(oFunction3DPropertyList);
Function3D[] oFunctions3D =
new
DMObjectsFinder(m_oEplanDemoProject).GetFunctions3D(oFunctions3DFilter);
// Searching 3D and 2D functions with the name '=EB3+ET1-Q1'
FunctionsFilter oFunctionsFilter =
new
FunctionsFilter();
oFunctionsFilter.ExactNameMatching =
true
;
oFunctionsFilter.Name =
"=EB3+ET1-Q1"
;
Functions3DFilter oFunctions3DFilter =
new
Functions3DFilter();
Function3DPropertyList oFunction3DPropertyList =
new
Function3DPropertyList();
oFunction3DPropertyList.FUNC_FULLNAME =
"=EB3+ET1-Q1"
;
oFunctions3DFilter.SetFilteredPropertyList(oFunction3DPropertyList);
IFunctionBase[] oAllWithTheSameName =
new
DMObjectsFinder(m_oEplanDemoProject).GetFunctions(oFunctionsFilter, oFunctions3DFilter);
// Searching 3D placements
Placements3DFilter oPlacements3DFilter =
new
Placements3DFilter();
oPlacements3DFilter.Category = Function.Enums.Category.AreaDefinition;
Placement3D[] oPlacements3D =
new
DMObjectsFinder(oProject).GetPlacements3D(oPlacements3DFilter);

### Przykłady kodu (C#)
```csharp
// Searching 3D functions with the name '=EB3+ET1-U1'
string str3DFunction = "=EB3+ET1-U1";
Functions3DFilter oFunctions3DFilter = new Functions3DFilter();
Function3DPropertyList oFunction3DPropertyList = new Function3DPropertyList();
oFunction3DPropertyList.FUNC_FULLDEVICETAG = str3DFunction;
oFunctions3DFilter.SetFilteredPropertyList(oFunction3DPropertyList);
Function3D[] oFunctions3D = new DMObjectsFinder(m_oEplanDemoProject).GetFunctions3D(oFunctions3DFilter);
// Searching 3D and 2D functions with the name '=EB3+ET1-Q1'
FunctionsFilter oFunctionsFilter = new FunctionsFilter();
oFunctionsFilter.ExactNameMatching = true;
oFunctionsFilter.Name = "=EB3+ET1-Q1";
Functions3DFilter oFunctions3DFilter = new Functions3DFilter();
Function3DPropertyList oFunction3DPropertyList = new Function3DPropertyList();
oFunction3DPropertyList.FUNC_FULLNAME = "=EB3+ET1-Q1";
oFunctions3DFilter.SetFilteredPropertyList(oFunction3DPropertyList);
IFunctionBase[] oAllWithTheSameName = new DMObjectsFinder(m_oEplanDemoProject).GetFunctions(oFunctionsFilter, oFunctions3DFilter);
// Searching 3D placements
Placements3DFilter oPlacements3DFilter = new Placements3DFilter();
oPlacements3DFilter.Category = Function.Enums.Category.AreaDefinition;
Placement3D[] oPlacements3D = new DMObjectsFinder(oProject).GetPlacements3D(oPlacements3DFilter);
```

---

## Import/export 3D graphics
*Źródło: `Import_export 3D graphics.html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / API Pro Panel / Import/export 3D graphics*

Import/export 3D graphics ### Export 
Export of 3D graphics is possible to the STEP or the VRML format: 

Export3D::ProjectToStep – Exports all installation spaces from a project. 
Export3D::InstallationSpacesToStep – Exports installation spaces. 
Export3D::ProjectToVrml – Exports all installation spaces from a project. 
Export3D::InstallationSpacesToVrml – Exports installation spaces. 

### Import 
The item data must be available in the common international STEP format (Standard for the Exchange of Product model data). 
For each import, a new layout space is generated with the name of the imported STEP file. 

### C# 
### Copy Code 
| InstallationSpace oInstallationSpace =
new
Import().Graphics3D(oProject,
"c:\\temp\\BK3100\\BK3xxx.stp"
);

### Przykłady kodu (C#)
```csharp
InstallationSpace oInstallationSpace = new Import().Graphics3D(oProject, "c:\\temp\\BK3100\\BK3xxx.stp");
```

---

## InstallationSpace (layout space in GUI)
*Źródło: `InstallationSpace (layout space in GUI).html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / API Pro Panel / InstallationSpace (layout space in GUI)*

InstallationSpace (layout space in GUI) The InstallationSpace represents a 3-dimensional space where objects can be located. 
It is also a root node for other 3D objects in the Layout spaces navigator. 
The following example shows how to create an InstallationSpace : 

### C# 
### Copy Code 
| InstallationSpace oInstallationSpace =
new
InstallationSpace();
oInstallationSpace.Create(oProject,
"InstallationSpace test"
);

We can retrieve existing InstallationSpace s from a project this way: 

### C# 
### Copy Code 
| InstallationSpace[] arrInstallationSpace = oProject.InstallationSpaces;

In the GUI it is called Layout space. It is independent of pages in a project.

### Przykłady kodu (C#)
```csharp
InstallationSpace oInstallationSpace = new InstallationSpace();
oInstallationSpace.Create(oProject, "InstallationSpace test");
```
```csharp
InstallationSpace[] arrInstallationSpace = oProject.InstallationSpaces;
```

---

## Mates
*Źródło: `Mates.html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / API Pro Panel / Mates*

Mates It is also possible to transform 3D objects by snapping, i.e. by using auxiliary points called " mates ". 
There are 2 kinds of mates: 
- Source mates – Points of a source object that we want to transform. In the GUI they are grey. 
- Target mates – The ones that we snap to. In the GUI they are blue. 

Another division is based on the purpose and the shape of the mates: 
- Point mates (classes PointMate , HandleMate , BasePointMate , MountingPointMate , PlacementAreaPointMate ) 
- Line mates (classes LineMate , MountingLineMate ) 
- Plane mates (class PlaneMate ) 

### Getting mates 
Mates can be retrieved from a Placement3D using methods: 

### C# 
### Copy Code 
| PointMate[] GetSourceMates(Mate.Enums.PlacementOptions ePlacementOptions)
PointMate FindSourceMate(
string
name, Mate.Enums.PlacementOptions ePlacementOptions)
Mate[] GetTargetMates(
bool
bConsiderMountingClearance)
Mate FindTargetMate(
string
name,
bool
bConsiderMountingClearance)

### Snapping 
Snapping mates causes one object to be positioned close to the other, i.e. a source mate of one object is at the position of a target mate of another object. In this case, we need to find the relevant mates from both objects and then perform snapping usingm the SnapTo method. Here is an example of how to snap a cabinet to another one through a point target mate: 

### C# 
### Copy Code 
| Cabinet oCabinet2 =
new
Cabinet();
oCabinet2.Create(oProject,
"TS 8886.500"
,
"1"
);
// Placing a cabinet next to another cabinet with 0.0 offset
oCabinet2.FindSourceMate(
"C3"
, Mate.Enums.PlacementOptions.None)
.SnapTo(oCabinet.FindTargetMate(
"CUB4"
,
false
), 0.0);

Here are also examples of snapping to a line and a plane mate. They both are base mates, which means that snapping to them will automatically sets a source object as a child of a target. Also, the orientation of a source item is adjusted to a target: 

### C# 
### Copy Code 
| // Get front plane of mounting panel
MountingPanel oMountingPanel = oCabinet.Children[1]
as
MountingPanel;
Plane oFrontPlace = oCabinet.Planes[0];
// Create a mounting rail with a length of 150
MountingRail oRail =
new
MountingRail();
oRail.Create(oProject,
"TS 110_15"
,
"1"
, 500.0);
// Placing a rail by using a plane mate as a target (located 100,200 from start of mounting panel, 
// Without any rotation)
oRail.GetSourceMates(Mate.Enums.PlacementOptions.None)[2]
.SnapTo(oFrontPlace.BaseMate, 0.0, 100.0, 200.0);
// Creating a terminal
Component oTerminal =
new
Component();
oTerminal.Create(oProject,
"SIE.4AV2400-2EB00-0A"
,
"1"
);
// Placing it on a mounting rail with offset 100 from the beginning of it. 
// Target (oRail.BaseMate) is a line mate.
oTerminal.FindSourceMate(
"M4"
,
false
).SnapTo(oRail.BaseMate, 100.0);

Please be aware that not all mates can be snapped to each other. This is determined by the Mate.MatchingMateNames property. To make sure that one mate can be snapped to another, please use the PointMate::CanSnapTo method. 
### Creating custom mates 
It is also possible to create a custom mate, for example a mounting point or a handle. In this case, a mate is first created as a transient object and then needs to be saved on a Placement3D : 

### C# 
### Copy Code 
| // Create a handle relative to placement area
var
transformationToPlacementArea =
new
Matrix3D();
transformationToPlacementArea.Translate(
new
Vector3D(50.0, 500.0, 0.0));
var
transformation = transformationToPlacementArea * placement3D.PlacementArea.RelativeTransformation;
var
handle =
new
HandleMate();
handle.Create(
new
MultiLangString(), transformation);
placement3D.AddMatePersistent(handle);
// Create a handle with extended logic
var
handleWithExtendedLogic =
new
HandleMate();
handleWithExtendedLogic.Create(
new
[] {
"V1"
,
"V2"
},
new
MultiLangString(),
new
Matrix3D());
placement3D.AddMatePersistent(handleWithExtendedLogic);
// Create a base point
var
basePoint =
new
BasePointMate();
basePoint.Create(BasePointMate.Enums.Name.FrameProfileDownLeftRear,
new
MultiLangString(),
new
Matrix3D {OffsetX = 200.0, OffsetY = 300.0});
placement3D.AddMatePersistent(basePoint);
// Create a mounting point
var
mountingPoint =
new
MountingPointMate();
mountingPoint.Create(
"Test mounting point"
,
new
MultiLangString(),
new
Matrix3D{OffsetY = 100.0, OffsetZ = 400.0});
placement3D.AddMatePersistent(mountingPoint);
// Create a mounting line
var
mountingLineMate =
new
MountingLineMate();
mountingLineMate.Create(
"Test mounting line"
,
new
MultiLangString(),
new
PointD3D(10.0, 10.0, 10.0),
new
PointD3D(110.0, 210.0, 310.0));
placement3D.AddMatePersistent(mountingLineMate);

Please be aware that the coordinates of a mate are relative until it is not persistent, i.e. without a Placement set. After calling Placement3D::AddMatePersistent , they are recalculated and become absolute. See Also Transformations in 3D space

### Przykłady kodu (C#)
```csharp
PointMate[] GetSourceMates(Mate.Enums.PlacementOptions ePlacementOptions)
PointMate FindSourceMate(string name, Mate.Enums.PlacementOptions ePlacementOptions)
Mate[] GetTargetMates(bool bConsiderMountingClearance)
Mate FindTargetMate(string name, bool bConsiderMountingClearance)
```
```csharp
Cabinet oCabinet2 = new Cabinet();
oCabinet2.Create(oProject, "TS 8886.500", "1");
// Placing a cabinet next to another cabinet with 0.0 offset
oCabinet2.FindSourceMate("C3", Mate.Enums.PlacementOptions.None)
.SnapTo(oCabinet.FindTargetMate("CUB4", false), 0.0);
```
```csharp
// Get front plane of mounting panel
MountingPanel oMountingPanel = oCabinet.Children[1] as MountingPanel;
Plane oFrontPlace = oCabinet.Planes[0];
// Create a mounting rail with a length of 150
MountingRail oRail = new MountingRail();
oRail.Create(oProject, "TS 110_15", "1", 500.0);
// Placing a rail by using a plane mate as a target (located 100,200 from start of mounting panel, 
// Without any rotation)
oRail.GetSourceMates(Mate.Enums.PlacementOptions.None)[2]
.SnapTo(oFrontPlace.BaseMate, 0.0, 100.0, 200.0);
// Creating a terminal
Component oTerminal = new Component();
oTerminal.Create(oProject, "SIE.4AV2400-2EB00-0A", "1");
// Placing it on a mounting rail with offset 100 from the beginning of it. 
// Target (oRail.BaseMate) is a line mate.
oTerminal.FindSourceMate("M4", false).SnapTo(oRail.BaseMate, 100.0);
```
```csharp
// Create a handle relative to placement area
var transformationToPlacementArea = new Matrix3D();
transformationToPlacementArea.Translate(new Vector3D(50.0, 500.0, 0.0));
var transformation = transformationToPlacementArea * placement3D.PlacementArea.RelativeTransformation;
var handle = new HandleMate();
handle.Create(new MultiLangString(), transformation);
placement3D.AddMatePersistent(handle);

// Create a handle with extended logic 
var handleWithExtendedLogic = new HandleMate();
handleWithExtendedLogic.Create(new[] {"V1", "V2"}, new MultiLangString(), new Matrix3D());
placement3D.AddMatePersistent(handleWithExtendedLogic);

// Create a base point
var basePoint = new BasePointMate();
basePoint.Create(BasePointMate.Enums.Name.FrameProfileDownLeftRear, 
new MultiLangString(),
new Matrix3D {OffsetX = 200.0, OffsetY = 300.0});
placement3D.AddMatePersistent(basePoint);

// Create a mounting point
var mountingPoint = new MountingPointMate();
mountingPoint.Create("Test mounting point", 
new MultiLangString(),
new Matrix3D{OffsetY = 100.0, OffsetZ = 400.0});
placement3D.AddMatePersistent(mountingPoint);

// Create a mounting line
var mountingLineMate = new MountingLineMate();
mountingLineMate.Create("Test mounting line",
new MultiLangString(),
new PointD3D(10.0, 10.0, 10.0), new PointD3D(110.0, 210.0, 310.0));
placement3D.AddMatePersistent(mountingLineMate);
```

---

## MountingPanel (mounting panel in GUI)
*Źródło: `MountingPanel (mounting panel in GUI).html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / API Pro Panel / MountingPanel (mounting panel in GUI)*

MountingPanel (mounting panel in GUI) ### Mounting panel (with article): 

### C# 
### Copy Code 
| MountingPanel oMountingPanel =
new
MountingPanel();
oMountingPanel.Create(m_oTestProject,
"MP AE 1031.500"
,
"1"
);
oMountingPanel.Parent = oCabinet;
// Can also be, for example, InstallationSpace

### Free mounting panel: 

### C# 
### Copy Code 
| MountingPanel oMountingPanel =
new
MountingPanel();
oMountingPanel.Create(m_oTestProject, 300.0, 400.0, 2.0);
oMountingPanel.Parent = oCabinet;

### Przykłady kodu (C#)
```csharp
MountingPanel oMountingPanel = new MountingPanel();
oMountingPanel.Create(m_oTestProject, "MP AE 1031.500", "1");
oMountingPanel.Parent = oCabinet; // Can also be, for example, InstallationSpace
```
```csharp
MountingPanel oMountingPanel = new MountingPanel();
oMountingPanel.Create(m_oTestProject, 300.0, 400.0, 2.0);
oMountingPanel.Parent = oCabinet;
```

---

## MountingRail (mounting rail in GUI)
*Źródło: `MountingRail (mounting rail in GUI).html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / API Pro Panel / MountingRail (mounting rail in GUI)*

MountingRail (mounting rail in GUI) The MountingRail is an item used to hold devices, usually attached to a Plane or Cabinet . 

### C# 
### Copy Code 
| InstallationSpace oInstallationSpace =
new
InstallationSpace();
oInstallationSpace.Create(m_oTestProject,
"DataModel_081MountingRail_Test001"
);
// Create a mounting panel
MountingPanel oMountingPanel =
new
MountingPanel();
oMountingPanel.Create(m_oTestProject,
"MP AE 1057.500"
,
"1"
);
oMountingPanel.SetParent(oInstallationSpace,
false
);
Plane oPlane1 = oMountingPanel.Planes[0];
// Create a mounting rail
MountingRail oMountingRail =
new
MountingRail();
oMountingRail.Create(m_oTestProject,
"TS 110_15"
,
"1"
, 500.0);
oMountingRail.SetParent(oPlane1,
false
);
oMountingRail.FindSourceMate(
"M4"
,
true
).SnapTo(oPlane1.GetTargetMates(
true
)[0]
as
PlaneMate, 0.0, 10.0, 12.0);

### Przykłady kodu (C#)
```csharp
InstallationSpace oInstallationSpace = new InstallationSpace();
oInstallationSpace.Create(m_oTestProject, "DataModel_081MountingRail_Test001");

// Create a mounting panel
MountingPanel oMountingPanel = new MountingPanel();
oMountingPanel.Create(m_oTestProject, "MP AE 1057.500", "1");
oMountingPanel.SetParent(oInstallationSpace, false);
Plane oPlane1 = oMountingPanel.Planes[0];

// Create a mounting rail
MountingRail oMountingRail = new MountingRail();
oMountingRail.Create(m_oTestProject, "TS 110_15", "1", 500.0);
oMountingRail.SetParent(oPlane1, false);
oMountingRail.FindSourceMate("M4", true).SnapTo(oPlane1.GetTargetMates(true)[0] as PlaneMate, 0.0, 10.0, 12.0);
```

---

## Orientation of 3D objects
*Źródło: `Orientation of 3D objects.html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / API Pro Panel / Orientation of 3D objects*

Orientation of 3D objects In Pro Panel API it is sometimes necessary to recognize sides of a 3D object, for example to place them in a row with the same orientation. 
Please mind that the sides of a Placement3D are something different than the sides of its minimal bounding box. They are related to the same part of the object 3D, independently of a transformation and a viewpoint. 
The representation of sides is in the .Corners property, for example: 
Placement3D.Corners.UpperRightBackAbsolute – Returns the upper right back coordinate in an absolute system. 
Placement3D.Corners.LowerRightFrontRelative – Returns the lower right front coordinate in a relative system. 

### Objects with placement area 
In this case, orientation is according to placement area. 
Example terminal: 

Example rack: 

### Objects without placement area 
In this case, orientation is according to the absolute axis origin (assumed identity transformation): 

| Front | side with the lowest Y 
| Back | side with highest Y 
| Right | side with highest X 
| Left | side with lowest X 
| Top | side with highest Z 
| Bottom | side with lowest Z 

SE isometric viewpoint: 

SW isometric viewpoint : 

See Also API Pro Panel

---

## PlaceHolder3D - placeholder in 3D space
*Źródło: `PlaceHolder3D - placeholder in 3D space.html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / API Pro Panel / PlaceHolder3D - placeholder in 3D space*

PlaceHolder3D - placeholder in 3D space A new placeholder object has been created in EPLAN Pro Panel. A corresponding class Placeholder3D has been created in the APIt. This class Placeholder3D inherits from StorableObject and the IPlaceHolder interface. 
The methods are similar to those of the standard PlaceHolder : 

### C# 
### Copy Code 
| PlaceHolder3D oNewPlaceHolder3D =
new
PlaceHolder3D();
oNewPlaceHolder3D.Create(m_oTestInstallationSpace);
oNewPlaceHolder3D.Name =
"016PlaceHolder3DService_Test008"
;
oNewPlaceHolder3D.AddReference(oComponent);
MultiLangString mlTest =
new
MultiLangString();
mlTest.AddString(ISOCode.Language.L_en_US,
"<Test123_en>"
);
mlTest.AddString(ISOCode.Language.L_de_DE,
"<Test123_de>"
);
oNewPlaceHolder3D.SetPropertyEntry(oComponent, 20011, mlTest);
oNewPlaceHolder3D.AddRecord(
"Record1"
);
oNewPlaceHolder3D.AddRecord(
"Record2"
);
// Setting values for English
oNewPlaceHolder3D.set_Value(
"Record1"
,
"Test123_en"
,
"Value 1"
);
oNewPlaceHolder3D.set_Value(
"Record2"
,
"Test123_en"
,
"Value 2"
);
// Setting values for German
oNewPlaceHolder3D.set_Value(
"Record1"
,
"Test123_de"
,
"Wert 1"
);
oNewPlaceHolder3D.set_Value(
"Record2"
,
"Test123_de"
,
"Wert 2"
);
oNewPlaceHolder3D.ApplyRecord(
"Record1"
);

### Przykłady kodu (C#)
```csharp
PlaceHolder3D oNewPlaceHolder3D = new PlaceHolder3D();
oNewPlaceHolder3D.Create(m_oTestInstallationSpace);
oNewPlaceHolder3D.Name = "016PlaceHolder3DService_Test008";
oNewPlaceHolder3D.AddReference(oComponent);
MultiLangString mlTest = new MultiLangString();
mlTest.AddString(ISOCode.Language.L_en_US, "<Test123_en>");
mlTest.AddString(ISOCode.Language.L_de_DE, "<Test123_de>");
oNewPlaceHolder3D.SetPropertyEntry(oComponent, 20011, mlTest);
oNewPlaceHolder3D.AddRecord("Record1");
oNewPlaceHolder3D.AddRecord("Record2");

// Setting values for English
oNewPlaceHolder3D.set_Value("Record1", "Test123_en", "Value 1");
oNewPlaceHolder3D.set_Value("Record2", "Test123_en", "Value 2");

// Setting values for German
oNewPlaceHolder3D.set_Value("Record1", "Test123_de", "Wert 1");
oNewPlaceHolder3D.set_Value("Record2", "Test123_de", "Wert 2");
oNewPlaceHolder3D.ApplyRecord("Record1");
```

---

## Plane (mounting surface in GUI)
*Źródło: `Plane (mounting surface in GUI).html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / API Pro Panel / Plane (mounting surface in GUI)*

Plane (mounting surface in GUI) The Plane class represents a surface object on which components can be placed. 

### C# 
### Copy Code 
| MountingPanel oMountingPanel =
new
MountingPanel();
oMountingPanel.Create(oTestProject,
"MP AE 1030.500"
,
"1"
);
oMountingPanel.Parent = m_oInstallationSpace; Plane oPlane1 = oMountingPanel.Children[0]
as
Plane;
Plane oPlane2 = oMountingPanel.Children[1]
as
Plane;

### Przykłady kodu (C#)
```csharp
MountingPanel oMountingPanel = new MountingPanel();
oMountingPanel.Create(oTestProject, "MP AE 1030.500", "1");
oMountingPanel.Parent = m_oInstallationSpace; Plane oPlane1 = oMountingPanel.Children[0] as Plane;
Plane oPlane2 = oMountingPanel.Children[1] as Plane;
```

---

## RoutingSegment (routing path in GUI)
*Źródło: `RoutingSegment (routing path in GUI).html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / API Pro Panel / RoutingSegment (routing path in GUI)*

RoutingSegment (routing path in GUI) The RoutingSegments class represents an object in EPLAN that can route connections. 
It can be generated by 2 ways: 
- using RoutingSegment::Create 
- using ConnectionService3D::CreateRoutingSegments

---

## Transformations in 3D space
*Źródło: `Transformations in 3D space.html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / API Pro Panel / Transformations in 3D space*

Transformations in 3D space Each Placement3D has 2 read-write properties that describe its transformation: 
- Matrix3D Placement3D::AbsoluteTransformation – absolute transformation 
- Matrix3D Placement3D::RelativeTransformation – transformation relative to a parent object 
The properties are represented by a 4x4 transformation matrix: 

M11      M12      M13     M14 
M21      M22      M23     M24 
M31      M32      M33     M34 
OffsetX OffsetY OffsetZ M44 

Here is an example of setting transformation matrix to a 3D object: 

### C# 
### Copy Code 
| Vector3D oVector3D =
new
Vector3D();
oVector3D.X = 3.0;
oVector3D.Y = 4.0;
oVector3D.Z = 5.0;
Quaternion oQuaternion =
new
Quaternion(oVector3D, 2.0);
Matrix3D oMatrix3D =
new
Matrix3D();
oMatrix3D.Rotate(oQuaternion);
oMatrix3D.Translate(
new
Vector3D(1.0, 2.0, 3.0));
oComponent1.AbsoluteTransformation = oMatrix3D;

It is also possible to move a 3D object using the Move() method: 

### C# 
### Copy Code 
| oComponent1.Move(1.0, 2.0, 3.0);

### How to calculate transformation relative to a specified 3D object 

Sometimes it is necessary to calculate local transformation, i. e. relative to a specified 3D object. 
For example, it could be the position of components on a rail from its beginning: 

To calculate the location of objects origin, it is necessary to use the .RelativeTransformationOfMacro property: 

### C# 
### Copy Code 
| Matrix3D terminalTransformation = terminal.RelativeTransformationOfMacro;
var
x_coordinate = terminalTransformation.Transform(
new
Point3D()).X;

Another way is to use absolute transformation: 

### C# 
### Copy Code 
| Matrix3D railTransformation = rail.AbsoluteTransformation;
railTransformation.Invert();
var
x_coordinate = railTransformation.Transform(terminal.AbsoluteTransformation.Transform(
new
Point3D()))).X;

### Rotation angle of a 3D object 
It can also be useful to get information about how an item was rotated during insertion from Placement options dialog: 

To calculate this rotation, there should be used the .RelativeTransformationOfMacro property: 

### C# 
### Copy Code 
| Matrix3D matrix = oPlacement3D.RelativeTransformationOfMacro;
double
oRotationAngleZ = -1 * Math.Atan2(matrix.M21, matrix.M11) * (180.0 / Math.PI);

See Also Matrix3D structure description Transform objects by Mates

### Przykłady kodu (C#)
```csharp
Vector3D oVector3D = new Vector3D();
oVector3D.X = 3.0;
oVector3D.Y = 4.0;
oVector3D.Z = 5.0;
Quaternion oQuaternion = new Quaternion(oVector3D, 2.0);
Matrix3D oMatrix3D = new Matrix3D();
oMatrix3D.Rotate(oQuaternion);
oMatrix3D.Translate(new Vector3D(1.0, 2.0, 3.0));
oComponent1.AbsoluteTransformation = oMatrix3D;
```
```csharp
oComponent1.Move(1.0, 2.0, 3.0);
```
```csharp
Matrix3D terminalTransformation = terminal.RelativeTransformationOfMacro;
var x_coordinate = terminalTransformation.Transform(new Point3D()).X;
```
```csharp
Matrix3D railTransformation = rail.AbsoluteTransformation;
railTransformation.Invert();
var x_coordinate = railTransformation.Transform(terminal.AbsoluteTransformation.Transform(new Point3D()))).X;
```
```csharp
Matrix3D matrix = oPlacement3D.RelativeTransformationOfMacro;
double oRotationAngleZ = -1 * Math.Atan2(matrix.M21, matrix.M11) * (180.0 / Math.PI);
```

---

## ViewPlacement (model view in GUI)
*Źródło: `ViewPlacement (model view in GUI).html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / API Pro Panel / ViewPlacement (model view in GUI)*

ViewPlacement (model view in GUI) Model views are objects used to show a 3D view on a standard EPLAN page. 

Example: 

### C# 
### Copy Code 
| // Creating 3D objects
InstallationSpace oInstallationSpace =
new
InstallationSpace();
oInstallationSpace.Create(m_oTestProject,
"DataModel_081MountingRail_Test001"
);
Cabinet oCabinet =
new
Cabinet();
oCabinet.Create(m_oTestProject,
"TS 8286.500"
,
"1"
);
oCabinet.Parent = oInstallationSpace;
// Creating view placement
ViewPlacement oViewPlacement =
new
ViewPlacement();
oViewPlacement.Create(m_oTestProject, m_InstallationSpace);
oViewPlacement.Page = oPage;
oViewPlacement.Area =
new
RectangleD(
new
PointD(0.0, 0.0),
new
PointD(200.0, 200.0));
oViewPlacement.RootElements =
new
Placement3D[]{oCabinet};
oViewPlacement.Update();

### Przykłady kodu (C#)
```csharp
// Creating 3D objects
InstallationSpace oInstallationSpace = new InstallationSpace();
oInstallationSpace.Create(m_oTestProject, "DataModel_081MountingRail_Test001");
Cabinet oCabinet = new Cabinet();
oCabinet.Create(m_oTestProject, "TS 8286.500", "1");
oCabinet.Parent = oInstallationSpace;

// Creating view placement
ViewPlacement oViewPlacement = new ViewPlacement();
oViewPlacement.Create(m_oTestProject, m_InstallationSpace);
oViewPlacement.Page = oPage;
oViewPlacement.Area = new RectangleD(new PointD(0.0, 0.0), new PointD(200.0, 200.0));
oViewPlacement.RootElements = new Placement3D[]{oCabinet};
oViewPlacement.Update();
```

---
