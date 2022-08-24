"""Changes walls hosted by curtain walls to schedule as walls"""


__title__ = 'Walls as\nCurtain Panels'

import Autodesk.Revit.DB as DB

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

# Iterate over panels and set panels to schedule as walls
t = DB.Transaction(doc, "Walls as Curtain Panels")
t.Start()

for panel in panel_collector:
    if panel.GroupId.IntegerValue < 0:
        scheduleAsPanels = panel.get_Parameter(DB.BuiltInParameter.HOST_PANEL_SCHEDULE_AS_PANEL_PARAM)
        scheduleAsPanels.Set(0)

t.Commit()
'''add options for active view. return group info. add logic for single group instances'''