from pyrevit import forms, revit

from Shape_Edits.shape_edits import clean_lines, add_split_lines
from Units.unit_conversions import convert_mm_or_in_to_internal_units
from Select.iselectors import select_single_w_multiple_cats_by_name
from Events.event import CustomizableEvent

from pyrevit.forms import WPFWindow
from pyrevit.framework import Windows

import Autodesk.Revit.DB as DB

from System.Collections.Generic import List

app = __revit__.Application
doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
activeView = doc.ActiveView

#
__persistentengine__ = True

def click_faces():
    try:
        uidoc.Selection.SetElementIds(List[DB.ElementId]())
        uidoc.RefreshActiveView()
        with forms.WarningBar(title='Pick Faces'):
            faces = revit.pick_faces()
        return faces

    except Exception as e:
        print(e)

def select_target():
    try:
        return select_single_w_multiple_cats_by_name('Pick Target Floor/Roof:', doc, ["Roofs", "Floors"], False)
    except Exception as e:
        print(e)

def run(faces, target, offset, units):
    all_edges = []
    for f in faces:
        edges = f.GetEdgesAsCurveLoops()
        for loop in edges:
            for line in loop:
                all_edges.append(line)

    # cleanup duplicates
    clean_edges = clean_lines(all_edges)

    # add function to offset z heights
    value = convert_mm_or_in_to_internal_units(offset, units)
    transform = DB.Transform.CreateTranslation(DB.XYZ(0, 0, value))

    translated_edges = []
    for e in clean_edges:
        translated_edges.append(e.CreateTransformed(transform))


    t = DB.Transaction(doc, "Copy Faces")
    t.Start()

    """add shape edits from geometry"""
    add_split_lines(translated_edges, target)

    t.Commit()


customizable_event = CustomizableEvent()

# A simple WPF form used to call the ExternalEvent
class ModelessForm(WPFWindow):
    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)
        self.last_text = "0.00"
        self.faces = None
        self.target = None
        self.ready_flag = False
        self.setup_export_units()
        self.Show()

    def check_ready(self):
        if self.faces != None and self.target != None:
            self.button_run.IsEnabled = True
        else:
            self.button_run.IsEnabled = False


    def setup_export_units(self):
        self.export_units_cb.ItemsSource = ['INCH', 'MM']
        is_metric = False
        units = revit.doc.GetUnits()

        metric_units = [DB.UnitTypeId.Meters,
                        DB.UnitTypeId.Centimeters,
                        DB.UnitTypeId.Millimeters]
        if int(app.VersionNumber) > 2021:
            length_fo = units.GetFormatOptions(DB.SpecTypeId.Length)
            is_metric = length_fo.GetUnitTypeId() in metric_units

        if is_metric:
            self.export_units_cb.SelectedIndex = 1
        else:
            self.export_units_cb.SelectedIndex = 0

    def click_select_faces(self, sender, e):
        try:
            self.Hide()
            self.faces = click_faces()
            self.Show()
            if self.faces is not None:
                sender.Content = str(len(self.faces))+" Faces Selected"
            else:
                sender.Content = "No Faces Selected!"
            self.check_ready()
        except Exception as e:
            print(e)

    def click_select_target(self, sender, e):
        try:
            self.Hide()
            self.target = select_target()
            self.Show()
            if self.target is not None:
                type = DB.Document.GetElement(doc, self.target.GetTypeId())
                type_name = str(DB.Element.Name.GetValue(type))
                id = str(self.target.Id)
                sender.Content = type_name + " Id: " + id
            self.check_ready()
        except Exception as e:
            print(e)

    def click_run(self, sender, e):
        try:
            customizable_event.raise_event(run, self.faces, self.target, float(self.tb_offset.Text), self.export_units_cb.SelectedIndex)
        except Exception as e:
            print(e)

    def offset_changed(self, sender, e):
        try:
            text = sender.Text
            try:
                float(text)
                self.last_text = text
            except ValueError:
                if not (text == "" or text == "-"):
                    sender.Text = self.last_text
                    sender.CaretIndex = e.Changes[0].Offset
        except Exception as e:
            print(e)





# Let's launch our beautiful and useful form !
modeless_form = ModelessForm("copy faces.xaml")
