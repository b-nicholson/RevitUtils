import System
import clr
from pyrevit import forms, UI, script, EXEC_PARAMS, revit, HOST_APP

import Autodesk.Revit.DB as DB
import Autodesk.Revit.Creation as CR
import Autodesk.Revit.Exceptions as Exceptions

clr.AddReference('System')
from System.Collections.Generic import List
from pyrevit.forms import WPFWindow
from pyrevit import coreutils
from pyrevit.framework import Windows
import os as os
import re

from System.Collections.ObjectModel import ObservableCollection
from System.Windows.Controls import DataGrid
from System.ComponentModel import ListSortDirection, SortDescription


app = HOST_APP.uiapp
doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
activeView = doc.ActiveView

class CustomISelectionFilter(UI.Selection.ISelectionFilter):
    def __init__(self, category_name):
        self.category_name = category_name

    def AllowElement(self, e):
        cat = e.Category.Name
        if (cat == self.category_name):
            return True
        else:
            return False

    def AllowReference(self, ref, point):
        return False

name_combos = []


class RoomNames():
    def __init__(
            self,
            rm_1,
            rm_2,
    ):
        # type: (str, str) -> None
        self.rm_1 = rm_1
        self.rm_2 = rm_2






class SettingsWindow(WPFWindow):
    def __init__(self):
        file_dir = os.path.dirname(__file__)
        xaml_source = os.path.join(file_dir, 'fix_doors.xaml')
        WPFWindow.__init__(self, xaml_source)

        self.setup_datagrid()
        self.setup_phases()




    @property
    def phase(self):
        return self.cb_phases.SelectedItem

    @property
    def is_built_backwards(self):
        return self.backwards_cx.IsChecked

    @property
    def are_built_inconsistently(self):
        return self.inconsistent_cx.IsChecked

    def setup_datagrid(self):
        self.data_grid_content = ObservableCollection[object]()
        self.datagrid.ItemsSource = self.data_grid_content

        args = (
            "",
            "",
        )
        name_combos.append(RoomNames(*args))

        for combo in name_combos:
            self.data_grid_content.Add(combo)

    def setup_phases(self):
        phases = DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Phases).ToElements()
        self.cb_phases.DataContext = phases

    def target_updated(self, sender, e):
        """"yoinked from pyMEP, don't really know how it works"""
        attribute = self.datagrid.CurrentColumn.SortMemberPath
        current_value = getattr(self.datagrid.CurrentItem, attribute)
        for item in self.datagrid.SelectedItems:
            setattr(item, attribute, current_value)
            item.changed = True
        self.datagrid.Items.Refresh()

    @staticmethod
    def sort_datagrid(datagrid, column_index=0, list_sort_direction=ListSortDirection.Ascending):
        # type: (DataGrid, int, ListSortDirection) -> None
        """Method use to set actual initial sort.
        cf. https://stackoverflow.com/questions/16956251/sort-a-wpf-datagrid-programmatically"""
        """"yoinked from pyMEP, don't really know how it works"""
        column = datagrid.Columns[column_index]

        # Clear current sort descriptions
        datagrid.Items.SortDescriptions.Clear()

        # Add the new sort description
        datagrid.Items.SortDescriptions.Add(
            SortDescription(column.SortMemberPath, list_sort_direction)
        )

        # Apply sort
        for col in datagrid.Columns:
            col.SortDirection = None
        column.SortDirection = list_sort_direction

        # Refresh items to display sort
        datagrid.Items.Refresh()

    def click_add(self, sender, e):
        self.setup_datagrid()


    def click_remove(self, sender, e):
        if self.data_grid_content.Count > 1:
            self.data_grid_content.RemoveAt(self.data_grid_content.Count-1)

        name_combos.pop()

    def update_doors(self, sender, e):

        datagrid_items = self.datagrid.Items
        name_1 = []
        name_2 = []

        for d in datagrid_items:
            name_1.append(d.rm_1)
            name_2.append(d.rm_2)


        if self.active_view_cx.IsChecked:
            doors = DB.FilteredElementCollector(doc, activeView.Id).OfCategory(DB.BuiltInCategory.OST_Doors)\
                .WhereElementIsNotElementType()
        if self.entire_model_cx.IsChecked:
            doors = DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Doors)\
                .WhereElementIsNotElementType()
        if self.selection_cx.IsChecked:
            rawSelection = uidoc.Selection.GetElementIds()
            if len(rawSelection) == 0:
                self.Hide()
                with forms.WarningBar(title='Select Doors'):
                    selectionNew = []
                    selection_completed = False
                    while selection_completed is not True:
                        try:
                            selector = uidoc.Selection.PickObjects(UI.Selection.ObjectType.Element,
                                                                   CustomISelectionFilter("Doors"))
                            selection_completed = True
                        except Exceptions.OperationCanceledException:
                            forms.alert('Selection Cancelled. Try again?', yes=True, no=True, exitscript=True)

                    for ref in selector:
                        selectionNew.append(DB.Document.GetElement(doc, ref))
                    newSelectionIds = []
                    if len(selectionNew) > 0:
                        for i in selectionNew:
                            newSelectionIds.append(i.Id)

                    rawSelection = List[DB.ElementId](newSelectionIds)

            doors = DB.FilteredElementCollector(doc, rawSelection).OfCategory(DB.BuiltInCategory.OST_Doors)\
                .WhereElementIsNotElementType()



        phase = self.phase

        combo_list_1 = []

        for a, b in zip(name_1, name_2):
            combo_list_1.append((a, b))

        t = DB.Transaction(doc, "Fix Door To/From")
        t.Start()

        for door in doors:
            loco = door.GetTransform().Origin

            orientation_vector = door.FacingOrientation * 1.5 + DB.XYZ(0, 0, 1)

            if self.are_built_inconsistently:
                bbox = door.get_BoundingBox(activeView)
                facing_pt = (bbox.Min + bbox.Max) / 2
                orientation_vector = (facing_pt-loco).Normalize()

            if self.is_built_backwards:
                orientation_vector = door.FacingOrientation.Negate() * 1.5 + DB.XYZ(0, 0, 1)




            facing_pt = loco + orientation_vector

            actual_to_room = DB.Document.GetRoomAtPoint(doc, facing_pt, phase)
            if actual_to_room is not None:
                actual_to_room_id = actual_to_room.Id
                actual_to_room_name = actual_to_room.get_Parameter(DB.BuiltInParameter.ROOM_NAME).AsString()
            else:
                actual_to_room_id = None
                actual_to_room_name = None

            if hasattr(door, "FromRoom"):
                from_room = door.FromRoom[phase]
                if from_room is not None:
                    from_room_id = from_room.Id
                    from_room_name = from_room.get_Parameter(DB.BuiltInParameter.ROOM_NAME).AsString()
                else:
                    from_room_id = None
                    from_room_name = None
            else:
                from_room_id = None
                from_room_name = None

            if hasattr(door, "ToRoom"):
                to_room = door.ToRoom[phase]
                if to_room is not None:
                    to_room_id = to_room.Id
                    to_room_name = to_room.get_Parameter(DB.BuiltInParameter.ROOM_NAME).AsString()
                else:
                    to_room_id = None
                    to_room_name = None
            else:
                to_room_name = None




            combo_name_1 = (from_room_name, to_room_name)
            combo_name_2 = (to_room_name, from_room_name)

            is_an_oddball = False
            for oddballs in combo_list_1:
                if combo_name_1 == oddballs or combo_name_2 == oddballs:
                    is_an_oddball = True

            # print (actual_to_room)
            # print (to_room_name)
            # print (from_room_name)
            # print ("-------------------------------------------")

            output = script.get_output()

            dr_num = door.get_Parameter(DB.BuiltInParameter.ALL_MODEL_MARK).AsString()


            message_settings = self.cx_fail_only.IsChecked

            if (actual_to_room_id == to_room_id) or (actual_to_room_id == from_room_id):
                if to_room_name is None and from_room_name is None:
                    print (output.linkify(door.Id) + "" + dr_num + " Door has no rooms touching it")

                elif to_room_id == from_room_id:
                    print (output.linkify(door.Id) + "" + dr_num + " Door only has same to/from room")

                elif is_an_oddball and actual_to_room_id != from_room_id:
                    door.FlipFromToRoom()
                    if not message_settings:
                        print (output.linkify(door.Id) + "" + dr_num + " Successfully changed as per oddball condition")


                elif actual_to_room_id != to_room_id and not is_an_oddball:
                    # print (door.get_Parameter(DB.BuiltInParameter.ALL_MODEL_MARK).AsString())
                    door.FlipFromToRoom()
                    if not message_settings:
                        print (output.linkify(door.Id) + "" + dr_num + " Successfully changed")
                elif not message_settings:
                    print (output.linkify(door.Id) + "" + dr_num + " Ignored, already correct")

            else:
                print (output.linkify(door.Id) + "" + dr_num + \
                       " Rooms intersecting door are jank, check their 3D extents")

        t.Commit()
        self.Close()

SettingsWindow().ShowDialog()