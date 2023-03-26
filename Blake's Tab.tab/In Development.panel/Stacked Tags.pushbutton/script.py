'''
Creates Stacked Tags by Selection
Shift-Click to Enter Settings
Recommend assigning a keyboard shortcut
'''

import Autodesk.Revit.DB as DB
import Autodesk.Revit.Exceptions as Exceptions
from pyrevit import forms, clr, UI, EXEC_PARAMS, script

clr.AddReference('System')

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
activeView = doc.ActiveView

cfg = script.get_config()

if EXEC_PARAMS.config_mode:
    import os as os
    from pyrevit.forms import WPFWindow


    class SettingsWindow(WPFWindow):

        def __init__(self):
            file_dir = os.path.dirname(__file__)
            xaml_source = os.path.join(file_dir, 'tag_stacker.xaml')
            WPFWindow.__init__(self, xaml_source)

            cfg = script.get_config()
            leaders = cfg.get_option("leader", "True")
            attached = cfg.get_option("attached", "True")

            self.cx_leader.IsChecked = leaders == "True"
            self.cx_leader_attached.IsChecked = attached == "True"

        def save_settings(self, sender, args):
            cfg = script.get_config()
            cfg.leader = str(self.cx_leader.IsChecked)
            cfg.attached = str(self.cx_leader_attached.IsChecked)
            script.save_config()
            self.Close()

    SettingsWindow().ShowDialog()


class ElementInLinkSelectionFilter(UI.Selection.ISelectionFilter):
    def __init__(self, cat):
        self._doc = doc
        self.LinkedDocument = None
        self.LinkInstance = None
        self.LastElementCategory = cat

    @property
    def LastCheckedWasFromLink(self):
        return self.LinkedDocument is not None

    def AllowElement(self, e):
        if type(e) == DB.RevitLinkInstance:
            return True
        elif self.LastElementCategory is None:
            return True
        elif e.Category.Id == self.LastElementCategory:
            return True
        else:
            return False

    def AllowReference(self, ref, point):
        self.LinkedDocument = None
        e = self._doc.GetElement(ref)

        if type(e) == DB.RevitLinkInstance:
            # print("yo")
            # li = e.AsLinkInstance()
            self.LinkInstance = e
            self.LinkedDocument = e.GetLinkDocument()
            e = self.LinkedDocument.GetElement(ref.LinkedElementId)
        return e


class Selected_Element():
    # There started to be too many properties that I needed to track, cleaner to wrap the element in a class
    def __init__(
            self,
            element,
            reference,
            bounding_box,
    ):
        # type: (DB.Element, DB.Reference, DB.BoundingBoxXYZ) -> None
        self.element = element
        self.reference = reference
        self.bounding_box = bounding_box


def transform_linked_boundingbox(boundingbox, link_instance):
    link_transform = link_instance.GetTotalTransform()
    new_pt_min = link_transform.OfPoint(boundingbox.Min)
    new_pt_max = link_transform.OfPoint(boundingbox.Max)
    boundingbox.Min = new_pt_min
    boundingbox.Max = new_pt_max
    return boundingbox

def select_from_hostdoc_or_link():
    with forms.WarningBar(title='Pick Element to Tag. Press Esc to Finish Selection.'):
        new_selection_completed = False
        cat = None
        elems = []
        while new_selection_completed is not True:
            # first element can be of any category, if it's in the host doc, next selection is restricted to same cat.
            # links are more restrictive so no sanitization for links
            filter = ElementInLinkSelectionFilter(cat)
            try:
                r = uidoc.Selection.PickObject(UI.Selection.ObjectType.PointOnElement, filter)
                if filter.LastCheckedWasFromLink:
                    e = filter.LinkedDocument.GetElement(r.LinkedElementId)
                    try:
                        ref = DB.Reference(e).CreateLinkReference(filter.LinkInstance)
                        bb = transform_linked_boundingbox(e.get_BoundingBox(activeView), filter.LinkInstance)

                    except Exceptions.ArgumentNullException:
                        e = doc.GetElement(r)
                        ref = DB.Reference(e)
                        bb = e.get_BoundingBox(activeView)

                else:
                    e = doc.GetElement(r)
                    ref = DB.Reference(e)
                    bb = e.get_BoundingBox(activeView)
                cat = e.Category.Id

                args = (e, ref, bb)
                elems.append(Selected_Element(*args))

            except Exceptions.OperationCanceledException:
                new_selection_completed = True
        return elems


def active_view_is_section_view():
    if type(activeView) == DB.ViewSection:
        return True
    else:
        return False


if activeView.Category.Id == DB.ElementId(DB.BuiltInCategory.OST_Sheets):
    forms.alert("Active View Cannot Be a Sheet. Try a model view", exitscript=True)

if type(activeView) is DB.ViewDrafting:
    forms.alert("Drafting Views are weird. Contact me if you need this functionality.", exitscript=True)

selection = select_from_hostdoc_or_link()

if len(selection) is 0:
    forms.alert("Nothing Selected.", exitscript=True)

with forms.WarningBar(title='Pick Location to Place the Tag Stack'):
    if activeView.SketchPlane is None and type(activeView) is not DB.ViewDrafting:
        t_temp = DB.Transaction(doc, "TempSketchPlane")
        t_temp.Start()
        sketch_plane = DB.SketchPlane.Create(doc, DB.Plane.CreateByNormalAndOrigin(activeView.ViewDirection, activeView.Origin))
        activeView.SketchPlane = sketch_plane
        point = uidoc.Selection.PickPoint()
        t_temp.RollBack()
    else:
        try:
            point = uidoc.Selection.PickPoint()
        except Exceptions.OperationCanceledException:
            forms.alert("Cancelled", exitscript=True)

    stable_point = point

t = DB.Transaction(doc, "Create Stacked Tags")
t.Start()

tags = []
for elem in selection:
    try:
        tag = DB.IndependentTag.Create(doc, activeView.Id, elem.reference, False, DB.TagMode.TM_ADDBY_CATEGORY,
                                         DB.TagOrientation.Horizontal, point)
    except Exceptions.InvalidOperationException:
        t.RollBack()
        forms.alert("No loaded tags for that element's category", exitscript=True)

    tag_boundingbox = tag.get_BoundingBox(activeView)
    if active_view_is_section_view():
        tag_offset = tag_boundingbox.Max.Z - tag_boundingbox.Min.Z
        point = point - DB.XYZ(0, 0, tag_offset)
    else:
        tag_offset = tag_boundingbox.Max.Y - tag_boundingbox.Min.Y
        point = point - DB.XYZ(0, tag_offset, 0)
    tags.append(tag)

elem_boundingbox = selection[0].bounding_box
bb_min = elem_boundingbox.Min
bb_max = elem_boundingbox.Max

tag_is_above_elements = False
if active_view_is_section_view():
    if stable_point.Z > bb_max.Z:
        tag_is_above_elements = True
else:
    if (stable_point.Y > bb_max.Y) and (stable_point.X < bb_max.X) and not (stable_point.X < bb_min.X):
        tag_is_above_elements = True

leaders = cfg.get_option("leader", "True")
attached = cfg.get_option("attached", "True")

if leaders == "True":
    tags[0].HasLeader = True

if tag_is_above_elements:
    tags[0].LeaderEndCondition = DB.LeaderEndCondition.Free
    tag_ref = tags[0].GetTaggedReferences()
    end_condition = tags[0].GetLeaderEnd(tag_ref[0])
    tags[0].HasLeader = False

    tags[-1].HasLeader = True
    tags[-1].LeaderEndCondition = DB.LeaderEndCondition.Free
    tags[-1].SetLeaderEnd(tags[-1].GetTaggedReferences()[0], end_condition)

if attached != "True":
    tags[0].LeaderEndCondition = DB.LeaderEndCondition.Free

t.Commit()
