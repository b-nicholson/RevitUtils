# -*- coding: utf-8 -*-
from math import sin, cos
import Autodesk.Revit.DB as DB
from pyrevit import forms

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
activeView = doc.ActiveView


class TypeSelector(forms.TemplateListItem):
    @property
    def name(self):
        # try:
        fam_name = DB.ElementType.FamilyName.GetValue(self.item)
        if fam_name == "Model Group":
            name = "Group Name: {}".format(DB.Element.Name.GetValue(self.item))
        else:
            name = "Family Name: {f_name} --- Type Name: {t_name}"\
                .format(f_name=fam_name,
                        t_name=DB.Element.Name.GetValue(self.item))

        return name


def item_selector(type_collector):
    types_list = []
    button_name = ""
    for item in type_collector:
        if item.FamilyName == "Model Group":
            types_list.append(TypeSelector(item))
            button_name = "Select Group Type to Place at Family Locations"
        else:
            types_list.append(TypeSelector(item))
            button_name = "Select Family Type to Use for Group Placement Point"
    select_type = forms.SelectFromList.show(types_list, multiselect=False, button_name=button_name)
    while select_type is None:
        forms.alert('You must make a selection. Try again?', yes=True, no=True, exitscript=True)
        select_type = forms.SelectFromList.show(types_list, multiselect=False, button_name='Select Type Name')
    return select_type


def place_group_at_family_instance_pt(group_type_list, family_type_selection):
    family_instance_filter = DB.FamilyInstanceFilter(doc, family_type_selection)
    jig_collector = DB.FilteredElementCollector(doc) \
        .WherePasses(family_instance_filter)\
        .ToElements()

    group_type = item_selector(group_type_list)

    locations = []
    rotations = []
    mirrored = []

    for jig in jig_collector:
        locations.append(jig.Location.Point)
        rotations.append(jig.Location.Rotation)
        mirrored.append(jig.Mirrored)

    t = DB.Transaction(doc, "Place Groups at Point")
    t.Start()

    for loc, angle, flip in zip(locations, rotations, mirrored):
        new_group = doc.Create.PlaceGroup(loc, group_type)
        axis_line = DB.Line.CreateBound(loc, loc + DB.XYZ.BasisZ)
        DB.ElementTransformUtils.RotateElement(doc, new_group.Id, axis_line, angle)
        if flip:
            ''' If the instance is mirrored, we need to create a plane to mirror the group, 
                aligned with the group's rotation'''
            origin = (loc.X, loc.Y)
            point = (loc.X+1, loc.Y)
            new_pt_x = origin[0] + cos(angle) * (point[0] - origin[0]) - sin(angle) * (point[1] - origin[1])
            new_pt_y = origin[1] + sin(angle) * (point[0] - origin[0]) + cos(angle) * (point[1] - origin[1])
            rotated_pt = DB.XYZ(new_pt_x, new_pt_y, loc.Z)
            axis_plane = DB.Plane.CreateByThreePoints(rotated_pt, loc, loc + DB.XYZ.BasisZ)
            DB.ElementTransformUtils.MirrorElement(doc, new_group.Id, axis_plane)
            # Revit forces you to make a copy when mirroring, so we need to delete the old instance
            doc.Delete(new_group.Id)
    t.Commit()


jig_type_collector = DB.FilteredElementCollector(doc) \
                        .OfCategory(DB.BuiltInCategory.OST_Entourage) \
                        .WhereElementIsElementType() \
                        .ToElements()

group_type_collector = DB.FilteredElementCollector(doc) \
                        .OfCategory(DB.BuiltInCategory.OST_IOSModelGroups) \
                        .WhereElementIsElementType() \
                        .ToElements()

type_selection = item_selector(jig_type_collector).Id

place_group_at_family_instance_pt(group_type_collector, type_selection)


'''mirroring needs to be the very last step, since the MirrorElement method does not return the element ids!?!?
must make the axis_plane creation's 2nd point be rotated by the family's rotation
'''
