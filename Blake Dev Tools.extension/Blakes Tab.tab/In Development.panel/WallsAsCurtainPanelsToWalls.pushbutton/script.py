# -*- coding: utf-8 -*-
"""Changes walls hosted by curtain walls to schedule as walls"""

__title__ = 'Walls as\nCurtain Panels'

import Autodesk.Revit.DB as DB
from pyrevit import script

doc = __revit__.ActiveUIDocument.Document

# target parameter, walls as curtain panels schedule as parameter
scheduleAs_paramId = DB.ElementId(DB.BuiltInParameter.HOST_PANEL_SCHEDULE_AS_PANEL_PARAM)

# Use our parameter ID to create a filterable value provider
scheduleAs_paramProv = DB.ParameterValueProvider(scheduleAs_paramId)

# create numeric value rule evaluator
param_equality = DB.FilterNumericEquals()

# create a filter rule (integer) using a filter value rule (equality) to 1, which is walls scheduling as curtain panels
scheduleAs_rule = DB.FilterIntegerRule(scheduleAs_paramProv, param_equality, 1)

# create slow filter via subclass - element parameter filter
paramFilter = DB.ElementParameterFilter(scheduleAs_rule)

# Creating collector instance and collecting filtered curtain panels from the model
panel_collector = DB.FilteredElementCollector(doc) \
                    .WhereElementIsNotElementType() \
                    .WherePasses(paramFilter) \
                    .ToElements()

nonOperableElements = 0
nonOperableGroups = []
# Iterate over panels and set panels to schedule as walls
t = DB.Transaction(doc, "Walls as Curtain Panels")
t.Start()

for panel in panel_collector:
    if panel.GroupId == DB.ElementId.InvalidElementId:
        panel_is_editable = True
    else:
        group = panel.Document.GetElement(panel.GroupId)
        groupSize = group.GroupType.Groups.Size
        if groupSize == 1:
            panel_is_editable = True
        else:
            panel_is_editable = False
            nonOperableElements += 1
            nonOperableGroups.append((group.Id, group.Name))
    if panel_is_editable is True:
        scheduleAsPanels = panel.get_Parameter(DB.BuiltInParameter.HOST_PANEL_SCHEDULE_AS_PANEL_PARAM)
        scheduleAsPanels.Set(0)

t.Commit()

if len(nonOperableGroups) > 0:
    output = script.get_output()
    output.print_md("# Warning!")
    output.print_md("Unable to edit " + (str(nonOperableElements)) + " panels since they are in groups with more than \
                                                                   1 instance. Their groups are listed below:")
    unique_groups = set(nonOperableGroups)
    for grp in unique_groups:
        print ("■ " + output.linkify(grp[0]) + " Type Name : " + (grp[1]))
'''add options for active view. return group info. add logic for single group instances'''
