# -*- coding: utf-8 -*-
"""Flips the 3D extents of Grids or Levels. Applies to ALL VIEWS"""

__title__ = 'Flip 3D\n Grid Ends'

import Autodesk.Revit.DB as DB
from pyrevit import forms, script, revit

doc = __revit__.ActiveUIDocument.Document
activeView = doc.ActiveView


def select_by_new_selection():
    is_grid_or_level = False
    while is_grid_or_level is not True:
        with forms.WarningBar(title='Pick Grids or Levels to Flip:'):
            selection = revit.pick_elements()
            cleaned_selection = []
            try:
                for source_element in selection:
                    if (source_element.Category.Id == DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_Grids).Id or
                            source_element.Category.Id == DB.Category.GetCategory(doc,
                                                                                  DB.BuiltInCategory.OST_Levels).Id):
                        cleaned_selection.append(source_element)
                    if (source_element.Category.Id == DB.Category.GetCategory(doc,
                                                                              DB.BuiltInCategory.OST_GridChains).Id):
                        forms.alert('Multi Segmented Grids do not behave intuitively.\
                                                        It is recommended to tab+select the segment you wish to flip.')
                    if cleaned_selection:
                        is_grid_or_level = True
                    else:
                        forms.alert('Selection must be a grid or level. Try again?', yes=True, no=True, exitscript=True)
            except TypeError:
                forms.alert('You must make a selection. Try again?', yes=True, no=True, exitscript=True)
    return cleaned_selection


# grid_collector = DB.FilteredElementCollector(doc) \
#     .OfCategory(DB.BuiltInCategory.OST_Grids) \
#     .WhereElementIsNotElementType() \
#     .ToElements()

nonOperableGrids = 0
nonOperableGroups = []

grid_selector = select_by_new_selection()
print(grid_selector)
t = DB.Transaction(doc, "Flip Grid Ends - 3D")
t.Start()
for grid in grid_selector:
    grid_is_editable = False
    if grid.GroupId == DB.ElementId.InvalidElementId:
        grid_is_editable = True

    else:
        group = grid.Document.GetElement(grid.GroupId)
        group_type = group.GroupType
        groupSize = group.GroupType.Groups.Size
        if groupSize == 1:
            grid_is_editable = True
        if groupSize > 1:
            nonOperableGrids += 1
            nonOperableGroups.append((group.Id, group.Name))

    if grid_is_editable is True:
        gridCurves = grid.GetCurvesInView(DB.DatumExtentType.Model, activeView)
        grid.SetCurveInView(DB.DatumExtentType.Model, activeView, gridCurves[0].CreateReversed())

t.Commit()
if len(nonOperableGroups) > 0:
    output = script.get_output()
    output.print_md("# Warning!")
    output.print_md("Unable to edit " + (str(nonOperableGrids)) + " grids/levels since they are in groups with more \
                                                                    than 1 instance. Their groups are listed below:")
    unique_groups = set(nonOperableGroups)
    for grp in unique_groups:
        print ("■ " + output.linkify(grp[0]) + " Type Name : " + (grp[1]))

''' check multi segmented grids.'''
