"""Disallows Wall Joins"""

__title__ = 'Disallow\nWall Joins'

import Autodesk.Revit.DB as DB

from pyrevit import forms, revit

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
activeView = doc.ActiveView


wall_collector = []

rawSelection = uidoc.Selection.GetElementIds()

if len(rawSelection) > 0:
    filteredSelection = DB.FilteredElementCollector(doc, rawSelection) \
                    .OfCategory(DB.BuiltInCategory.OST_Walls) \
                    .WhereElementIsCurveDriven() \
                    .WhereElementIsNotElementType()\
                    .ToElements()
    if len(filteredSelection) > 0:
        wall_collector = filteredSelection
    else:
        forms.alert('Selection must contain a wall. Try again.', exitscript=True)

else:
    selected_option = forms.CommandSwitchWindow.show(
        ['Entire Model', 'Active View', 'Selection'],
        message='Select Option:',
    )

    if selected_option == 'Entire Model':
        entireModel = forms.alert("This change will be applied to the entire model, "
                          "across all phases, design options etc.\n\n"
                          "This must be used with EXTREME caution\n\n"
                          "Are you sure you want to do this?",
                          ok=False, yes=True, no=True)
        if entireModel:
            selectorOption = DB.FilteredElementCollector(doc)

    if selected_option == 'Active View':
        if forms.check_modelview(activeView):
            selected_option_active = forms.CommandSwitchWindow.show(
                ['All Visible Walls', 'By Wall Type', 'All Instance of Type (By New Selection)'],
                message='Select Option:',
            )
            if selected_option_active == 'All Visible Walls':
                selectorOption = DB.FilteredElementCollector(doc, activeView.Id)

            if selected_option_active == 'All Instance of Type (By New Selection)':
                isType = False
                while isType is not True:
                    with forms.WarningBar(title='Pick Source Wall:'):
                        source_element = revit.pick_element()
                        try:
                            source_element.WallType
                            print (source_element.WallType)
                            isType = True
                        except:
                            forms.alert('Selection must be a wall. Try again?', yes=True, no=True, exitscript=True)


# add selector to grab all of selected wall type













    if selected_option == 'Selection':
        selection2 = uidoc.Selection.GetElementIds()
        if len(selection2) > 0:
            selectorOption = DB.FilteredElementCollector(doc, selection2)


    wall_collector = selectorOption \
                    .OfCategory(DB.BuiltInCategory.OST_Walls) \
                    .WhereElementIsCurveDriven() \
                    .WhereElementIsNotElementType()



t = DB.Transaction(doc, "Disallow Wall Joins")
t.Start()

# Iterate over walls and disallow joins on both ends
for wall in wall_collector:
    if wall is not None:
        DB.WallUtils.DisallowWallJoinAtEnd(wall,0)
        DB.WallUtils.DisallowWallJoinAtEnd(wall,1)


t.Commit()

