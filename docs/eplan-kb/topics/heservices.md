# EPLAN API — heservices

*MVP — wstawianie makr .ema, Insert, PlaceHolder*

Dokumentów: 4

## API Higher Electrotechnical services
*Źródło: `API Higher Electrotechnical services.html`*
*Ścieżka: EPLAN API / User Guide / API Higher Electrotechnical services*

API Higher Electrotechnical services The Eplan.EplApi.HEServices namespace mainly contains functionality that is not directly connected to the data model. There are classes for backing up projects and master data, for creating reports or for printing. A lot of modules of EPLAN are represented in this namespace, such as the labeling module and the parts management.

---

## Displaying a preview
*Źródło: `Displaying a preview.html`*
*Ścieżka: EPLAN API / User Guide / API Higher Electrotechnical services / Displaying a preview*

Displaying a preview The Eplan.EplApi.HEServices namespace provides the DrawingService class that contains functionality for outputting objects ( WindowMacros , SymbolVariants , Placements ,  or Pages ) on a window or control. 

Displaying the preview takes two steps: 
The first step is to create a so-called display list using the CreateDisplayList function. This actually processes the data into a list of graphical primitives that can be drawn. Depending on what kind of data you want to show, this function will take some time. For example, if you want to create a preview of a macro, CreateDisplayList loads the macro file, analyzes it and creates the items to display. You need to call this function just once for a given preview. 
The second step actually shows the preview (the created display list) on a window. It takes a System.Windows.Forms.PaintEventArgs object as parameter, which is provided by any control in the Paint callback. 
The DrawingService class also provides the possibility to influence the appearance of the preview in many ways, such as zooming and changing the background color. 

The following example creates a preview of a macro. The first code snippet shows the creation of the display list: 
- C# 
- VB Eplan.EplApi.HEServices.DrawingService oDs =
new
DrawingService();
// ...
if
(oDs ==
null
)
{
oDs =
new
Eplan.EplApi.HEServices.DrawingService();
}
if
(!(gProject ==
null
))
{
try
{
oDs.DrawConnections =
true
;
oDs.MacroPreview =
true
;
oDs.CreateDisplayList(strObj,
""
, 0, gProject);
}
catch
(System.Exception ex)
{
new
Decider().Decide(EnumDecisionType.eOkDecision,
"Can't create display list: \r\n"
+ ex.Message,
""
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
}
// Raise the Paint event
oForm.Picture1.Invalidate();
}
If
oDs
Is
Nothing
Then
oDs =
New
Eplan.EplApi.HEServices.DrawingService
End
If
If
Not
gProject
Is
Nothing
Then
Try
oDs.DrawConnections =
True
oDs.MacroPreview =
True
oDs.CreateDisplayList(strObj,
""
, 0, gProject)
Catch
ex
As
System.Exception
Dim
dec
As
Decider =
New
Decider
dec.Decide(EnumDecisionType.eOkDecision,
"Can't create display list:"
& vbCrLf & ex.Message,
""
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)
End
Try
'raise the Paint event
oForm.Picture1.Invalidate()
End
If

The next piece of source code shows drawing the display list in the Paint method of a picture box: 
- C# 
- VB private
void
Picture1_Paint(
object
sender, System.Windows.Forms.PaintEventArgs e)
{
if
(!(m_DS ==
null
)) {
try
{
m_DS.DrawDisplayList(e);
}
catch
(System.Exception ex) {
new
Decider().Decide(EnumDecisionType.eOkDecision,
"Can't draw display list:"
+
"\r\n"
+ ex.Message,
""
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
}
}
}
Private
Sub
Picture1_Paint(
ByVal
sender
As
Object
,
ByVal
e
As
System.Windows.Forms.PaintEventArgs)
Handles
Picture1.Paint
If
Not
m_DS
Is
Nothing
Then
Try
m_DS.DrawDisplayList(e)
Catch
ex
As
System.Exception
Dim
dec
As
Decider =
New
Decider
dec.Decide(EnumDecisionType.eOkDecision,
"Can't draw display list:"
& vbCrLf & ex.Message,
""
, EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)
End
Try
End
If
End Sub

### 
### Setting image size and the viewport 
To draw more complex images, it may be necessary to set the resolution and a viewport of the drawn image. 
A viewport is a polygon that represents a part of a page that will be rendered: 

This can be done using the SetViewport method. The coordinates should be passed in the graphical coordinate system. 
If the given dimensions are not proportional to the drawing area, they are automatically adjusted to keep the aspect ratio: 
- C# m_Ds.SetViewport(10.0, 200.0, 300.0, 20.0);

In case of 3D drawings, it is also necessary to set the image size, otherwise its quality may be worse than in the EPLAN GED: 

- C# m_Ds.SetWindow(0, 600, 1200, 0);

### Przykłady kodu (C#)
```csharp
Eplan.EplApi.HEServices.DrawingService oDs = new DrawingService();
// ...
if(oDs == null)
{
    oDs = new Eplan.EplApi.HEServices.DrawingService();
}
if (!(gProject == null))
{
    try
    {
   oDs.DrawConnections = true;
   oDs.MacroPreview = true;
   oDs.CreateDisplayList(strObj, "", 0, gProject);
    }
    catch (System.Exception ex)
    {
        new Decider().Decide(EnumDecisionType.eOkDecision, "Can't create display list: \r\n" + ex.Message, "", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
    }
    // Raise the Paint event
    oForm.Picture1.Invalidate();
}
```
```csharp
If oDs Is Nothing Then
   oDs = New Eplan.EplApi.HEServices.DrawingService
End If
If Not gProject Is Nothing Then
   Try
      oDs.DrawConnections = True
      oDs.MacroPreview = True
      oDs.CreateDisplayList(strObj, "", 0, gProject)
   Catch ex As System.Exception
      Dim dec As Decider = New Decider
      dec.Decide(EnumDecisionType.eOkDecision, "Can't create display list:" & vbCrLf & ex.Message, "", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)
   End Try
   'raise the Paint event
   oForm.Picture1.Invalidate()
End If
```
```csharp
private void Picture1_Paint(object sender, System.Windows.Forms.PaintEventArgs e)
{
 if (!(m_DS == null)) {
   try {
     m_DS.DrawDisplayList(e);
   } catch (System.Exception ex) {
     new Decider().Decide(EnumDecisionType.eOkDecision, "Can't draw display list:" + "\r\n" + ex.Message, "", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK);
   }
 }
}
```
```csharp
Private Sub Picture1_Paint(ByVal sender As Object, ByVal e As System.Windows.Forms.PaintEventArgs) Handles Picture1.Paint
    If Not m_DS Is Nothing Then
        Try
            m_DS.DrawDisplayList(e)
        Catch ex As System.Exception
            Dim dec As Decider = New Decider
            dec.Decide(EnumDecisionType.eOkDecision, "Can't draw display list:" & vbCrLf & ex.Message, "", EnumDecisionReturn.eOK, EnumDecisionReturn.eOK)
        End Try
    End If
End Sub
```
```csharp
m_Ds.SetViewport(10.0, 200.0, 300.0, 20.0);
```
```csharp
m_Ds.SetWindow(0, 600, 1200, 0);
```

---

## Placing window macros
*Źródło: `Placing window macros.html`*
*Ścieżka: EPLAN API / User Guide / API Higher Electrotechnical services / Placing window macros*

Placing window macros An EPLAN macro is a piece of schematics that can be introduced into a project – onto a page or as a page. EPLAN uses file macros. They can have the extension *.ema for window macros, *.emp for page macros, and *.ems for symbol macros. 
For placing macros, the EPLAN API provides the class Eplan.EplApi.HEServices.Insert . This class basically contains three overloaded methods for placing each type of macro. A window or symbol macro can be placed on a page either with absolute coordinates or with an offset relative to its original position. 

The following example shows how to place a macro on a page at a given position: 

### C# 
### Copy Code 
| Insert oInsert =
new
Insert();
oInsert.WindowMacro(
"$(MD_MACROS)\BECK.KL1012.ema"
, 0, m_oTestProject.Pages[9],
new
PointD(70.0, 0.0), Insert.MoveKind.Relative);

### Placing macros and assigning value sets 
If there are PlaceHolder objects in a macro, you can assign value sets using the result of the Insert.WindoMacro function: 

### C# 
### Copy Code 
| Insert oInsert =
new
Insert();
StorableObject[] oInsertedObjects = oInsert.WindowMacro(
@"$(MD_MACROS)MacroWithPlaceholder.ema"
, 0, m_oTestProject.Pages[9],
new
PointD(70.0, 0.0), Insert.MoveKind.Relative);
foreach
(StorableObject oSOTemp
in
oInsertedObjects)
{
// We are searching for PlaceHolder "Three-Phase" in the results
PlaceHolder oPlaceHoldeThreePhase = oSOTemp
as
Eplan.EplApi.DataModel.Graphics.PlaceHolder;
if
((oPlaceHoldeThreePhase !=
null
)
&&
(oPlaceHoldeThreePhase.Name ==
"Three-Phase"
)
)
{
oPlaceHoldeThreePhase.ApplyRecord(
"Motor 0,75 KW"
);
}
}

### Przykłady kodu (C#)
```csharp
Insert oInsert = new Insert();
oInsert.WindowMacro("$(MD_MACROS)\BECK.KL1012.ema", 0, m_oTestProject.Pages[9], new PointD(70.0, 0.0), Insert.MoveKind.Relative);
```
```csharp
Insert oInsert = new Insert();
        StorableObject[] oInsertedObjects = oInsert.WindowMacro(@"$(MD_MACROS)MacroWithPlaceholder.ema", 0, m_oTestProject.Pages[9], new PointD(70.0, 0.0), Insert.MoveKind.Relative);

        foreach (StorableObject oSOTemp in oInsertedObjects)
        {
            // We are searching for PlaceHolder "Three-Phase" in the results
             PlaceHolder oPlaceHoldeThreePhase = oSOTemp  as Eplan.EplApi.DataModel.Graphics.PlaceHolder;
            if((oPlaceHoldeThreePhase != null)
                &&
                (oPlaceHoldeThreePhase.Name == "Three-Phase")
                )
             {
                 oPlaceHoldeThreePhase.ApplyRecord("Motor 0,75 KW");
             }
        }
```

---

## Pre-planning macro
*Źródło: `Pre-planning macro.html`*
*Ścieżka: EPLAN API / User Guide / API DataModel / API Pre-planning / Pre-planning macro*

Pre-planning macro For a Pre-planning module, the new PrePlanningMacro class has been created to represent macros. 
These macros are created as follows: 

### C# 
### Copy Code 
| string
strMacroPath = m_oDir.FullName +
"\\TestMacro.emv"
;
PrePlanningMacro oPrePlanningMacro =
new
PrePlanningMacro();
oPrePlanningMacro.Create(
new
[] {oPlanningSegment1, oPlanningSegment2}, strMacroPath, oMultiLangString);

Inserting macros requires parameters such as the parent planning segment, the path to macro and the project object: 

### C# 
### Copy Code 
| string
strMacroPath = m_oDir.FullName +
"\\TestMacro.emv"
;
StorableObject[] arrInsertedPlaObjects =
new
Insert().PrePlanningMacro(strMacroPath, m_oTestProject, oPlanningSegment1);

### Przykłady kodu (C#)
```csharp
string strMacroPath = m_oDir.FullName + "\\TestMacro.emv";
PrePlanningMacro oPrePlanningMacro = new PrePlanningMacro();
oPrePlanningMacro.Create(new[] {oPlanningSegment1, oPlanningSegment2}, strMacroPath, oMultiLangString);
```
```csharp
string strMacroPath = m_oDir.FullName + "\\TestMacro.emv";
StorableObject[] arrInsertedPlaObjects = new Insert().PrePlanningMacro(strMacroPath, m_oTestProject, oPlanningSegment1);
```

---
