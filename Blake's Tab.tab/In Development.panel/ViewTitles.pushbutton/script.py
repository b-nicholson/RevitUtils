# -*- coding: utf-8 -*-
"""Automatically Set Viewport Title Line Lengths to Match Text"""
import Autodesk.Revit.DB as DB
import clr
import os

clr.AddReference('System.Windows.Forms')
clr.AddReference('IronPython.Wpf')
clr.AddReference('System')
from System.Collections.Generic import List
from pyrevit import script, revit, HOST_APP, forms
from System import Windows, Uri
from System.Windows.Media.Imaging import BitmapImage

xamlfile = script.get_bundle_file('ViewTitleLines.xaml')


import wpf

__title__ = 'Change Viewport\nTitle Length'
_min_revit_ver__ = 2022

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
activeView = doc.ActiveView
app = __revit__.Application

def convert_to_internal_units(length, unit_type):
    # keeping < 2022 functionality for future reference
    rvt_year = int(app.VersionNumber)
    if rvt_year < 2022:
        if unit_type == 1:
            old_units = DB.DisplayUnitType.DUT_MILLIMETER
        else:
            old_units = DB.DisplayUnitType.DUT_DECIMAL_INCHES
        return DB.UnitUtils.Convert(length, old_units, DB.DisplayUnitType.DUT_DECIMAL_FEET)
    else:
        if unit_type == 1:
            new_units = DB.UnitTypeId.Millimeters
        else:
            new_units = DB.UnitTypeId.Inches
        return DB.UnitUtils.ConvertToInternalUnits(length, new_units)


def setup_export_units(self):
    self.export_units_cb.ItemsSource = ['INCH', 'MM']
    is_metric = False
    units = revit.doc.GetUnits()

    metric_units = [DB.UnitTypeId.Meters,
                    DB.UnitTypeId.Centimeters,
                    DB.UnitTypeId.Millimeters]
    if HOST_APP.is_newer_than(2021):
        length_fo = units.GetFormatOptions(DB.SpecTypeId.Length)
        is_metric = length_fo.GetUnitTypeId() in metric_units

    if is_metric:
        self.export_units_cb.SelectedIndex = 1
    else:
        self.export_units_cb.SelectedIndex = 0


# UI things
class SetViewLines(Windows.Window):
    def __init__(self):
        # Setup UI
        filename = os.path.join(os.path.dirname(__file__), 'example.png')
        uri = Uri(filename)
        wpf.LoadComponent(self, xamlfile)
        self.example.Source = BitmapImage(uri)
        setup_export_units(self)

        # Load user configs
        cfg = script.get_config()
        self.tailing_distance.Text = cfg.get_option("pad_end", "0")
        self.export_units_cb.SelectedIndex = cfg.get_option("read_units", 1)

    def floatcheck(self, sender, args):
        tailing_distance = self.tailing_distance.Text
        try:
            float(tailing_distance)
        except ValueError:
            tailing_distance = ""
            self.tailing_distance.Text = tailing_distance

        if tailing_distance == "":
            self.create_b.IsEnabled = False
            self.save_button.IsEnabled = False
        else:
            self.create_b.IsEnabled = True
            self.save_button.IsEnabled = True

    def save_settings(self, sender, args):
        # read current settings and save them to config
        pad_start = self.leading_distance.Text
        pad_end = self.tailing_distance.Text
        read_units = self.export_units_cb.SelectedIndex

        cfg = script.get_config()
        cfg.pad_start = pad_start
        cfg.pad_end = pad_end
        cfg.read_units = read_units
        script.save_config()
        self.save_button.Content = "Settings Saved!"

    def target_changed(self, sender, args):
        pass

    def set_lines(self, sender, args):
        # wpf variables
        pad_end = float(self.tailing_distance.Text)
        read_units = self.export_units_cb.SelectedIndex
        active_view = self.active_view_cb.IsChecked
        sheet_set = self.sheet_set_cb.IsChecked
        whole_model = self.entire_model_cb.IsChecked

        if active_view:
            viewports = DB.FilteredElementCollector(doc, activeView.Id) \
                .OfCategory(DB.BuiltInCategory.OST_Viewports).ToElements()
        if whole_model:
            viewports = DB.FilteredElementCollector(doc) \
                .OfCategory(DB.BuiltInCategory.OST_Viewports).ToElements()
        if sheet_set:
            viewports = []
            valid_selection = False
            while valid_selection is False:
                selected_sheets = forms.select_sheets()
                try:
                    if len(selected_sheets) is not 0:
                        valid_selection = True
                        for sheet in selected_sheets:
                            viewports.append(sheet.GetAllViewports())
                except TypeError:
                    forms.alert("Nothing selected, try again?", yes=True, no=True, exitscript=True)

            flat_list = [item for sublist in viewports for item in sublist]
            viewport_list = List[DB.ElementId](flat_list)
            viewports = DB.FilteredElementCollector(doc, viewport_list) \
                .OfCategory(DB.BuiltInCategory.OST_Viewports).ToElements()

        t = DB.Transaction(doc, "View Title Line Length")
        t.Start()
        for vp in viewports:
            vp.LabelLineLength = 0.01
            rotation = vp.Rotation
            if rotation is not DB.ViewportRotation.None:
                vp.Rotation = DB.ViewportRotation.None
            outlines = vp.GetLabelOutline()
            outline_max = outlines.MaximumPoint
            outline_min = outlines.MinimumPoint

            label_offset = vp.LabelOffset
            box_min_pt = vp.GetBoxOutline().MinimumPoint
            new_pt = (box_min_pt + label_offset).X
            symbol_size = new_pt - outline_min.X
            outline_min.X
            length = max(outline_max.X - outline_min.X, outline_max.Y - outline_min.Y) - symbol_size + \
                     (convert_to_internal_units(pad_end, read_units))

            vp.LabelLineLength = length
            if rotation is not DB.ViewportRotation.None:
                vp.Rotation = rotation
        t.Commit()
        self.Close()


SetViewLines().ShowDialog()
