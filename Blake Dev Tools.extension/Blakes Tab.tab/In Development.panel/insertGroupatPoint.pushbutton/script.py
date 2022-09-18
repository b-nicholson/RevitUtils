# -*- coding: utf-8 -*-
import math
from math import sin, cos, pi
import Autodesk.Revit.DB as DB
from pyrevit import forms, revit, clr, script

clr.AddReference('System')
from System.Collections.Generic import List

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
activeView = doc.ActiveView


param_type = DB.ElementId(DB.BuiltInParameter.ALL_MODEL_TYPE_NAME)
param_family = DB.ElementId(DB.BuiltInParameter.ALL_MODEL_FAMILY_NAME)

f_param_value = 'Jig'
f_param = DB.ParameterValueProvider(param_type)
evaluator = DB.FilterStringEquals()

f_rule = DB.FilterStringRule(f_param, evaluator, f_param_value, True)

filter_type_name = DB.ElementParameterFilter(f_rule)

jig_collector = DB.FilteredElementCollector(doc) \
    .WherePasses(filter_type_name) \
    .WhereElementIsNotElementType() \
    .ToElements()


locations = []
rotations = []
mirrored = []
for jig in jig_collector:
    locations.append(jig.Location.Point)
    rotations.append(jig.Location.Rotation)
    mirrored.append(jig.Mirrored)

groupType_collector = DB.FilteredElementCollector(doc) \
    .OfCategory(DB.BuiltInCategory.OST_IOSModelGroups) \
    .WhereElementIsElementType() \
    .ToElements()

grouptypes = []

for g in groupType_collector:
    grouptypes.append(g)


t = DB.Transaction(doc, "Place Groups at Jig")
t.Start()

for loc, angle, flip in zip(locations, rotations, mirrored):
    new_group = doc.Create.PlaceGroup(loc, grouptypes[4])
    axis_line = DB.Line.CreateBound(loc, loc + DB.XYZ.BasisZ)
    DB.ElementTransformUtils.RotateElement(doc, new_group.Id, axis_line, angle)
    if flip:
        origin = (loc.X, loc.Y)
        point = (loc.X+1, loc.Y)
        new_pt_x = origin[0] + cos(angle) * (point[0] - origin[0]) - sin(angle) * (point[1] - origin[1])
        new_pt_y = origin[1] + sin(angle) * (point[0] - origin[0]) + cos(angle) * (point[1] - origin[1])
        rotated_pt = DB.XYZ(new_pt_x, new_pt_y, loc.Z)
        axis_plane = DB.Plane.CreateByThreePoints(rotated_pt, loc, loc + DB.XYZ.BasisZ)
        flipped_group = DB.ElementTransformUtils.MirrorElement(doc, new_group.Id, axis_plane)
        doc.Delete(new_group.Id)
t.Commit()

'''mirroring needs to be the very last step, since the MirrorElement method does not return the element ids!?!?
must make the axis_plane creation's 2nd point be rotated by the family's rotation
'''