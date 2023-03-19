'''
To Do:

1. eliminate redundancy with room/door methods being directly split + modified slightly
2. allow other categories? Will need to remove a lot of hard coding

'''

import Autodesk.Revit.DB as DB
import os as os

from Autodesk.Revit.Exceptions import ArgumentException
from pyrevit import revit, forms, coreutils
from System.Collections.Generic import List
from System import MissingMemberException
from pyrevit.forms import WPFWindow
from pyrevit.framework import Windows
from System.Collections.ObjectModel import ObservableCollection
from System.Windows.Controls import DataGrid
from System.ComponentModel import ListSortDirection, SortDescription

doc = __revit__.ActiveUIDocument.Document
app = __revit__.Application

rvt_year = int(app.VersionNumber)

all_levels = DB.FilteredElementCollector(doc) \
    .OfCategory(DB.BuiltInCategory.OST_Levels) \
    .WhereElementIsNotElementType() \
    .ToElements()

all_level_names = []
all_level_elevations = []

for lvl in all_levels:
    all_level_names.append(lvl.Name)
    all_level_elevations.append(lvl.Elevation)

min_lvl_elev = min(all_level_elevations)
max_lvl_elev = max(all_level_elevations)

levels = []


class WPFlevels():
    # creates items to be displayed in the levels wpf datagrid with custom "properties"
    def __init__(
            self,
            level_element,
            inclusion,
            level_name,
            level_elevation,
            level_identifier="",
    ):
        # type: (str, bool, str, float, str) -> None
        self.level_element = level_element
        self.inclusion = inclusion
        self.level_name = level_name
        self.level_elevation = level_elevation
        self.level_identifier = level_identifier


class ReValueItem(object):
    """entire class straight yoinked from pyrevit Revalue pushbutton"""

    def __init__(self, oldvalue):
        self.oldvalue = oldvalue
        self.newvalue = ''

    def format_value(self, from_pattern, to_pattern):
        try:
            if to_pattern is None:
                to_pattern = ""

            if from_pattern:
                # if format contains pattern finders use reformatter
                if any(x in from_pattern for x in ['{', '}']):
                    self.newvalue = \
                        coreutils.reformat_string(self.oldvalue,
                                                  from_pattern,
                                                  to_pattern)
                # otherwise use a simple find/replacer
                else:
                    self.newvalue = \
                        self.oldvalue.replace(from_pattern, to_pattern, 1)
            else:
                self.newvalue = ''
        except Exception:
            self.newvalue = ''


class ComboboxSampleItem:
    """wrapper to keep the element binding consistent between categories"""
    # used to display the sample item in the preview panel

    def __init__(
            self,
            item_element,
            item_name,
            item_value,
    ):
        # type: (str, bool, str, float, str) -> None
        self.item_element = item_element
        self.item_name = item_name
        self.item_value = item_value


def setup_sample_items(items):
    # Function for creating the actual sample items using the ComboboxSampleItem class.
    samples = []
    for element in items:
        name = ""
        # Check to see if it has a Number param, if not we'll grab mark.
        if hasattr(element, "Number"):
            value = element.Number
        else:
            try:
                value = element.get_Parameter(DB.BuiltInParameter.ALL_MODEL_MARK).AsString()
            except:
                # shouldn't be needed, will only be used if scope of tool expands beyond Rooms and FamilyInstances
                pass

        args = (
            element,
            name,
            value,
        )
        samples.append(ComboboxSampleItem(*args))
    return samples


class SettingsWindow(WPFWindow):

    def __init__(self):
        file_dir = os.path.dirname(__file__)
        xaml_source = os.path.join(file_dir, 'typical_floors.xaml')
        WPFWindow.__init__(self, xaml_source)

        self.setup_source_parameters_cbs()

        self.data_grid_content = ObservableCollection[object]()
        self.datagrid.ItemsSource = self.data_grid_content
        self.sort_datagrid(self.datagrid, 3)

        self.refresh_samples()
        self.setup_units()
        self.setup_datagrid_levels()
        self.setup_phases()
        self.setup_datagrid_level_header()

        for level in levels:
            self.data_grid_content.Add(level)

    """pyrevit revalue yoink start"""

    @property
    def old_format(self):
        return self.id_source.Text

    @old_format.setter
    def old_format(self, value):
        self.id_source.Text = value

    @property
    def new_format(self):
        return self.new_format_tb.Text

    """pyrevit revalue yoink end"""

    @property
    def target_category_id(self):
        return self.cb_category.SelectedItem.Id

    @property
    def move_to_host_location(self):
        return self.cx_move_target.IsChecked

    @property
    def same_rm_name_only(self):
        return self.cx_match_rm_name.IsChecked

    @property
    def matching_door_families_only(self):
        return self.cx_match_dr_fam.IsChecked

    @property
    def matching_door_types_only(self):
        return self.cx_match_dr_type.IsChecked

    @property
    def is_metric(self):
        # find if project units are in imperial or metric and return the result
        units = revit.doc.GetUnits()

        metric_units = [DB.UnitTypeId.Meters,
                        DB.UnitTypeId.Centimeters,
                        DB.UnitTypeId.Millimeters]
        if rvt_year > 2021:
            length_fo = units.GetFormatOptions(DB.SpecTypeId.Length)
            is_metric = length_fo.GetUnitTypeId() in metric_units
        else:
            length_fo = units.GetFormatOptions(DB.UnitType.UT_Length)
            is_metric = length_fo.DisplayUnits in metric_units
        return is_metric

    @property
    def match_properties(self):
        return self.cx_match_properties.IsChecked

    @property
    def scary_parameters(self):
        return self.cx_scary_options.IsChecked

    def setup_datagrid_level_header(self):
        # needed to add the units suffix to the header instead of the item due to it sorting strings not number
        # (11 m came before 2 m)
        if self.is_metric:
            self.level_elev_header.Header = "Level Elevation (m)"
        else:
            self.level_elev_header.Header = "Level Elevation (ft)"

    def setup_datagrid_levels(self):
        all_level_collector = DB.FilteredElementCollector(doc) \
            .OfCategory(DB.BuiltInCategory.OST_Levels) \
            .WhereElementIsNotElementType() \
            .ToElements()
        
        # Use WPF levels class to provide custom parameters for use in WPF datagrid
        for level in all_level_collector:
            identifier = ""
            args = (
                level,
                False,
                level.Name,
                self.convert_to_display_units(level.Elevation, self.is_metric),
                identifier,
            )
            levels.append(WPFlevels(*args))

    def setup_source_parameters_cbs(self):
        # provide source level combobox with data
        self.cb_source_level.DataContext = all_levels
        # setup target category combobox with desired categories
        cats = List[DB.Category]()
        cats.Add(DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_Rooms))
        cats.Add(DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_Doors))
        self.cb_category.DataContext = cats
        self.cb_category.SelectedIndex = 0

    def setup_units(self):
        # set up the units combobox & slider in the door distance checks
        self.export_units_cb.ItemsSource = ['INCH', 'MM']
        if self.is_metric:
            self.export_units_cb.SelectedIndex = 1
            self.max.Text = str(600)
        else:
            self.export_units_cb.SelectedIndex = 0
            self.max.Text = str(24)

    def setup_phases(self):
        # adds data to the phase combobox
        phases = DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Phases).ToElements()
        self.cb_phases.DataContext = phases

    def phases_changed(self, sender, e):
        # Change visibility of the phase dialog options based on user input on utilization of phases in the project
        if self.cx_phases.IsChecked:
            self.phase_dialog.Visibility = Windows.Visibility.Visible
        else:
            self.phase_dialog.Visibility = Windows.Visibility.Collapsed

    def refresh_samples(self):
        # When user changes the source level, we need to grab new items to use in the sample items combobox
        """No idea why it returns none on init despite being after their setup, so we need to provide none options"""
        category = self.cb_category.SelectedItem
        if category is None:
            category = DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_Rooms)

        level = self.cb_source_level.SelectedItem
        if level is None:
            level = all_levels[0]

        samples = DB.FilteredElementCollector(doc) \
            .OfCategoryId(category.Id) \
            .WherePasses(DB.ElementLevelFilter(level.Id)) \
            .WhereElementIsNotElementType() \
            .ToElements()

        sample_elements = setup_sample_items(samples)

        self.cb_sample_item.DataContext = None
        self.cb_sample_item.DataContext = sample_elements

        if self.cb_sample_item.SelectedIndex == -1:
            self.cb_sample_item.SelectedIndex = 0
        return sample_elements

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

    def cell_updated(self, sender, args):
        if sender.Text is not "":
            self.datagrid.CurrentItem
            # check the box when you edit text, just a QOL feature
            self.datagrid.CurrentItem.inclusion = True

    def src_changed(self, sender, args):
        # Change the available UI options based on category selected
        self.refresh_samples()
        if self.cb_category.SelectedIndex == 1:
            self.door_locations_label.Visibility = Windows.Visibility.Visible
            self.distance_options.Visibility = Windows.Visibility.Visible
            self.cx_match_dr_fam.Visibility = Windows.Visibility.Visible
            self.cx_match_dr_type.Visibility = Windows.Visibility.Visible
            self.cx_match_rm_name.Visibility = Windows.Visibility.Collapsed
            self.cx_match_rm_name.IsChecked = False

        else:
            self.door_locations_label.Visibility = Windows.Visibility.Collapsed
            self.distance_options.Visibility = Windows.Visibility.Collapsed
            self.cx_match_dr_fam.Visibility = Windows.Visibility.Collapsed
            self.cx_match_dr_type.Visibility = Windows.Visibility.Collapsed
            self.cx_match_dr_type.IsChecked = False
            self.cx_match_dr_fam.IsChecked = False
            self.cx_match_rm_name.Visibility = Windows.Visibility.Visible

    def sample_changed(self, sender, args):
        # Used to preview changes to the sample item in the preview panel
        try:
            old_value = self.cb_sample_item.SelectedItem.item_value
            # show old number in the sample original value field in the preview section
            self.tb_og_number.Text = old_value
        except AttributeError:
            # ignore when there is no valid preview element selection
            pass
        try:
            newitem = ReValueItem(oldvalue=old_value)
            newitem.format_value(self.old_format,
                                 self.new_format)

            self._revalue_items = newitem
        except (AttributeError, UnboundLocalError):
            # ignore when there is no valid preview element selection
            pass

        # do the conversion?? don't remember what this does
        self.revalue()

    def revalue(self):
        # don't remember what this does
        self._revalue_items.format_value(self.old_format,
                                         self.new_format)
        self.tb_new_number.Text = self._revalue_items.newvalue

    def on_format_change(self, sender, args):
        # when source level pattern to find changes, do something but idk what the revalue function does anymore
        self.revalue()

    def convert_to_internal_units(self, length, unit_type):
        # keeping < 2022 functionality for future reference
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

    def convert_to_display_units(self, length, unit_type):
        if rvt_year < 2022:
            if unit_type is True:
                old_units = DB.DisplayUnitType.DUT_METERS
                suffix = " m"
            else:
                old_units = DB.DisplayUnitType.DUT_FEET_FRACTIONAL_INCHES
                suffix = " ft"
            return str(DB.UnitUtils.Convert(length, old_units, DB.DisplayUnitType.DUT_DECIMAL_FEET)) + suffix
        else:
            if unit_type is True:
                new_units = DB.UnitTypeId.Meters
                new_value = round(DB.UnitUtils.ConvertFromInternalUnits(length, new_units), 3)
                suffix = " m"
            else:
                new_value = round(length, 2)
                suffix = " ft"

            # return str(new_value) + suffix
            return float(new_value)

    def match_prop_changed(self, sender, args):
        if self.cx_match_properties.IsChecked:
            self.expander_scary.Visibility = Windows.Visibility.Visible
        else:
            self.cx_scary_options.IsChecked = False
            self.expander_scary.Visibility = Windows.Visibility.Collapsed

    def match_properties(self, selected_parameters, host, target):
        if selected_parameters is not None:
            for target_param in selected_parameters:

                # if the parameter isn't built in, we need to search it by name rather than by the DB entry
                if target_param.Definition.BuiltInParameter == DB.BuiltInParameter.INVALID:
                    custom_param_name = target_param.Definition.Name
                    host_param = host.LookupParameter(custom_param_name)
                    target_param = target.LookupParameter(custom_param_name)
                else:
                    param_name = target_param.Definition.BuiltInParameter
                    host_param = host.get_Parameter(param_name)
                    target_param = target.get_Parameter(param_name)

                # start of logic to handle groups
                if target.GroupId != DB.ElementId(-1):
                    in_group = True
                else:
                    in_group = False

                valid_param = False
                if host_param is not None:
                    # end of logic to handle groups
                    if in_group:
                        valid_param = host_param.Definition.VariesAcrossGroups
                    else:
                        valid_param = True

                    # pull data based on the parameter's storage type
                    storage_type = host_param.StorageType
                    if storage_type == DB.StorageType.Double:
                        value = host_param.AsDouble()
                    if storage_type == DB.StorageType.Integer:
                        value = host_param.AsInteger()
                    if storage_type == DB.StorageType.ElementId:
                        value = host_param.AsElementId()
                    if storage_type == DB.StorageType.String:
                        value = host_param.AsString()

                # check to make sure we want to change things, do it based on the storage type. You need to be explicit
                if valid_param:
                    if storage_type == DB.StorageType.Double:
                        target_param.Set(value or 0.0)
                    if storage_type == DB.StorageType.Integer:
                        target_param.Set(value or 0)
                    if storage_type == DB.StorageType.ElementId:
                        target_param.Set(value)
                    if storage_type == DB.StorageType.String:
                        target_param.Set(value or "")

    def coordinate_typ_floors \
                    (self, category, target_lvls, target_lvl_names, target_prefixes, source_level, source_prefix,
                     properties):
        # create a list of filters to target elements on user selected levels
        target_filters = List[DB.ElementFilter]()
        for lv in target_lvls:
            target_filters.Add(DB.ElementLevelFilter(lv.Id))

        # Only do something if the user selected a target level
        if len(target_filters) > 0:
            room_cat_id = DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_Rooms).Id
            door_cat_id = DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_Doors).Id
            combo_filter = DB.LogicalOrFilter(target_filters)

            if self.target_category_id == room_cat_id:
                # find rooms with area greater than 0
                area_f_val_p = DB.ParameterValueProvider(DB.ElementId(DB.BuiltInParameter.ROOM_AREA))
                area_f_eval = DB.FilterNumericGreater()
                area_f_rule = DB.FilterDoubleRule(area_f_val_p, area_f_eval, 0, 1E-6)
                area_filter = DB.ElementParameterFilter(area_f_rule)

                # add filter for phase if the user selects that the project uses phases
                if self.cx_phases.IsChecked:
                    phase_f_val_p = DB.ParameterValueProvider(DB.ElementId(DB.BuiltInParameter.ROOM_PHASE))
                    phase_f_eval = DB.FilterNumericEquals()
                    phase_f_rule = DB.FilterElementIdRule(phase_f_val_p, phase_f_eval, self.cb_phases.SelectedItem.Id)
                    phase_filter = DB.ElementParameterFilter(phase_f_rule)
                    filter_list = List[DB.ElementFilter]()
                    for i in [combo_filter, area_filter, phase_filter]:
                        filter_list.Add(i)
                    combo_filter = DB.LogicalAndFilter(filter_list)
                else:
                    combo_filter = DB.LogicalAndFilter(combo_filter, area_filter)
            # if not rooms, treat it differently
            else:
                if self.cx_phases.IsChecked:
                    # create list of phase statuses to use to filter items that shouldn't be selected based on phase
                    acceptable_statuses = List[DB.ElementOnPhaseStatus]()
                    for para in [DB.ElementOnPhaseStatus.New, DB.ElementOnPhaseStatus.Temporary]:
                        acceptable_statuses.Add(para)
                    # only add existing items if the user wants it
                    if self.cx_existing_items.IsChecked:
                        acceptable_statuses.Add(DB.ElementOnPhaseStatus.Existing)

                    phase_filter = DB.ElementPhaseStatusFilter(self.cb_phases.SelectedItem.Id, acceptable_statuses)
                    combo_filter = DB.LogicalAndFilter(combo_filter, phase_filter)

            category_id = category.Id

            # Grab elements on host level based on user category selection
            host_collector = DB.FilteredElementCollector(doc) \
                .OfCategoryId(category_id) \
                .WherePasses(DB.ElementLevelFilter(source_level.Id)) \
                .WhereElementIsNotElementType() \
                .ToElements()

            # grab target elements based on user inputs. Id's not elements to use in subsequent detailed selections
            target_elems_collector = DB.FilteredElementCollector(doc) \
                .OfCategoryId(category_id) \
                .WherePasses(combo_filter) \
                .WhereElementIsNotElementType() \
                .ToElementIds()

            nonOperableElements = 0
            nonOperableGroups = []

            # used when finding doors to determine tolerance between host/target
            distance = self.convert_to_internal_units(self.slider.Value, self.export_units_cb.SelectedIndex)

            t = DB.Transaction(doc, "Coordinate Typical Floors")
            t.Start()

            max_value = len(target_elems_collector)
            with forms.ProgressBar(title='Updating Values... ({value} of {max_value})', cancellable=True) as pb:
                i = 0

                for h_c in host_collector:
                    if self.target_category_id == room_cat_id:
                        host_name = h_c.get_Parameter(DB.BuiltInParameter.ROOM_NAME).AsString()

                    # get host bounding box, so we can use it in a quick filter later.
                    host_bb = h_c.get_BoundingBox(None)
                    host_bb_pt_min = host_bb.Min
                    host_bb_pt_max = host_bb.Max
                    # Manipulate the bounding box to cover whole project z, so we can intersect targets w it
                    pt_min = DB.XYZ(host_bb_pt_min.X, host_bb_pt_min.Y, (min_lvl_elev - 30))
                    pt_max = DB.XYZ(host_bb_pt_max.X, host_bb_pt_max.Y, (max_lvl_elev + 30))

                    target_fine_filters = List[DB.ElementFilter]()

                    """quick filter to prefilter the elements for careful, slow analysis later"""
                    bb_outline = DB.Outline(pt_min, pt_max)
                    bb_filter = DB.BoundingBoxIntersectsFilter(bb_outline)
                    target_fine_filters.Add(bb_filter)

                    if self.target_category_id == room_cat_id:
                        """find rooms with areas greater than 0"""
                        target_fine_filters.Add(area_filter)

                    if self.same_rm_name_only:
                        """find rooms with the same name"""
                        name_f_val_p = DB.ParameterValueProvider(DB.ElementId(DB.BuiltInParameter.ROOM_NAME))
                        name_f_eval = DB.FilterStringEquals()
                        name_f_rule = DB.FilterStringRule(name_f_val_p, name_f_eval, host_name)
                        name_filter = DB.ElementParameterFilter(name_f_rule)
                        target_fine_filters.Add(name_filter)

                    if self.matching_door_families_only:
                        """find only doors with same family name"""
                        host_family = h_c.get_Parameter(DB.BuiltInParameter.ELEM_FAMILY_PARAM).AsValueString()
                        family_f_val_p = DB.ParameterValueProvider(
                            DB.ElementId(DB.BuiltInParameter.ALL_MODEL_FAMILY_NAME))
                        family_f_eval = DB.FilterStringEquals()
                        family_f_rule = DB.FilterStringRule(family_f_val_p, family_f_eval, host_family)
                        family_filter = DB.ElementParameterFilter(family_f_rule)
                        target_fine_filters.Add(family_filter)

                    if self.matching_door_types_only:
                        """find only doors with same family name"""
                        host_type = h_c.get_Parameter(DB.BuiltInParameter.ELEM_TYPE_PARAM).AsValueString()
                        type_f_val_p = DB.ParameterValueProvider(
                            DB.ElementId(DB.BuiltInParameter.ALL_MODEL_TYPE_NAME))
                        type_f_eval = DB.FilterStringEquals()
                        type_f_rule = DB.FilterStringRule(type_f_val_p, type_f_eval, host_type)
                        family_filter = DB.ElementParameterFilter(type_f_rule)
                        target_fine_filters.Add(family_filter)

                    combo_fine_filter = DB.LogicalAndFilter(target_fine_filters)
                    try:
                        target_collector = DB.FilteredElementCollector(doc, target_elems_collector) \
                            .OfCategoryId(category_id) \
                            .WherePasses(combo_fine_filter) \
                            .WhereElementIsNotElementType() \
                            .ToElements()
                    except ArgumentException:
                        t.RollBack()
                        forms.alert("No target elements in selection criteria, check settings", exitscript=True)

                    if self.target_category_id == room_cat_id:
                        # main room renumbering function
                        host_elevation = h_c.Level.Elevation
                        for t_c in target_collector:
                            t_c_pt = t_c.Location.Point
                            # project target point onto the level of the host,
                            # so we can check if the target point is inside it
                            target_pt = DB.XYZ(t_c_pt.X, t_c_pt.Y, host_elevation)

                            if h_c.IsPointInRoom(target_pt):
                                host_num = h_c.Number
                                target_level = t_c.Level.Name

                                # this method is highly contingent on how the data is stored.
                                # (IDK what the above really means anymore, I guess it has to do with index matching?)
                                target_index = target_lvl_names.index(target_level)
                                target_prefix = target_prefixes[target_index]
                                if target_prefix is not "" and source_prefix is not "":
                                    newitem = ReValueItem(oldvalue=host_num)
                                    newitem.format_value(source_prefix, target_prefix)
                                    t_c.Number = newitem.newvalue

                                if self.match_properties:
                                    # this function will skip invalid/not editable params
                                    self.match_properties(properties, h_c, t_c)

                                if self.move_to_host_location:
                                    # can't move stuff it is in a group, check first
                                    if t_c.GroupId == DB.ElementId.InvalidElementId:
                                        room_is_editable = True
                                    else:
                                        group = t_c.Document.GetElement(t_c.GroupId)
                                        room_is_editable = False
                                        nonOperableElements += 1
                                        nonOperableGroups.append((group.Id, group.Name))

                                    if room_is_editable is True:
                                        # if we're able to move the room, combine host X,Y with target Z and change loc
                                        h_c_pt = h_c.Location.Point
                                        x = h_c_pt.X
                                        y = h_c_pt.Y
                                        z = t_c_pt.Z
                                        new_location = DB.XYZ(x, y, z)
                                        t_c.Location.Move(new_location - t_c_pt)

                            if pb.cancelled:
                                # exit script if user cancels operation with forms.warningbar function
                                break
                            else:
                                # update forms.warningbar UI with progress for every target element
                                pb.update_progress(i, max_value)
                    i += 1

                    if category_id == DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_Doors).Id:
                        try:
                            host_location = h_c.Location.Point
                        except MissingMemberException:
                            # curtain wall doors don't have a location, pretty stupid. Need to use a different method
                            host_location = h_c.GetTransform().Origin
                        host_location_x = host_location.X
                        host_location_y = host_location.Y
                        host_pt_flat = DB.XYZ(host_location_x, host_location_y, 0)
                        host_num = h_c.get_Parameter(DB.BuiltInParameter.ALL_MODEL_MARK).AsString()

                        for t_c in target_collector:
                            try:
                                target_location = t_c.Location.Point
                            except MissingMemberException:
                                # curtain wall doors don't have a location, pretty stupid.
                                # Need to use a different method
                                target_location = t_c.GetTransform().Origin
                            target_location_x = target_location.X
                            target_location_y = target_location.Y
                            target_pt_flat = DB.XYZ(target_location_x, target_location_y, 0)

                            target_level = DB.Document.GetElement(doc, t_c.LevelId).Name

                            distance_test = target_pt_flat.DistanceTo(host_pt_flat)
                            # test if target family is within user set tolerance from host family
                            if distance_test <= distance:
                                target_index = target_lvl_names.index(target_level)
                                target_prefix = target_prefixes[target_index]
                                target_num = t_c.get_Parameter(DB.BuiltInParameter.ALL_MODEL_MARK)

                                # Check if we want to renumber based on user inputs
                                if target_prefix is not "" and source_prefix is not "":
                                    newitem = ReValueItem(oldvalue=host_num)
                                    newitem.format_value(source_prefix,
                                                         target_prefix)
                                    target_num.Set(newitem.newvalue)

                                if self.match_properties:
                                    # this function will skip invalid/not editable params
                                    self.match_properties(properties, h_c, t_c)

                                if self.move_to_host_location:
                                    # can't move stuff it is in a group, check first
                                    if t_c.GroupId == DB.ElementId.InvalidElementId:
                                        door_is_editable = True
                                    else:
                                        group = t_c.Document.GetElement(t_c.GroupId)
                                        door_is_editable = False
                                        nonOperableElements += 1
                                        nonOperableGroups.append((group.Id, group.Name))

                                    if door_is_editable is True:
                                        # if we're able to move the door, do stuff
                                        try:
                                            h_c_pt = h_c.Location.Point
                                        except MissingMemberException:
                                            # not really viable to change doors in curtain walls
                                            pass
                                        # create a target point from host x,y and target z
                                        x = h_c_pt.X
                                        y = h_c_pt.Y
                                        z = target_location.Z
                                        new_location = DB.XYZ(x, y, z)
                                        try:
                                            # move location by creating vector from og point to new pt
                                            t_c.Location.Move(new_location - target_location)
                                        except MissingMemberException:
                                            # again don't move curtainwall doors
                                            pass
                            if pb.cancelled:
                                # exit script if user cancels operation with forms.warningbar function
                                break
                            else:
                                # update forms.warningbar UI with progress for every target element
                                pb.update_progress(i, max_value)
                        i += 1

            t.Commit()

    def click_run(self, sender, args):
        selected_params = None
        self.hide()

        # match properties
        if self.cx_match_properties.IsChecked:
            forms.alert("Please be deliberate with your parameter selection. "
                        "Parameter matching can be quite destructive if used incorrectly. ")

            # get an element on the target floor to use as a host to grab parameters from. Not sure if this is the best
            # option 1. Select from list of elements. Kinda useless??
            # option 2. Grab all elements in project, aggregate all unique parameters and push them through. Too much??
            component = self.cb_sample_item.SelectedItem.item_element
            params = component.Parameters

            instance_params = []
            for p in params:
                if not p.IsReadOnly:
                    instance_params.append(p)
            # create dictionary to display name in the select from list dropdown. Exclude params that target model geo
            if self.scary_parameters:
                dict_params = {fr.Definition.Name: fr for fr in instance_params if
                               fr.Definition.BuiltInParameter != DB.BuiltInParameter.ROOM_NUMBER
                               and fr.Definition.BuiltInParameter != DB.BuiltInParameter.ALL_MODEL_MARK}
            else:
                dict_params = {fr.Definition.Name: fr for fr in instance_params if
                               fr.Definition.BuiltInParameter != DB.BuiltInParameter.ROOM_NUMBER
                               and fr.Definition.BuiltInParameter != DB.BuiltInParameter.ROOM_LOWER_OFFSET
                               and fr.Definition.BuiltInParameter != DB.BuiltInParameter.ROOM_UPPER_OFFSET
                               and fr.Definition.BuiltInParameter != DB.BuiltInParameter.ROOM_UPPER_LEVEL
                               and fr.Definition.BuiltInParameter != DB.BuiltInParameter.ROOM_UPPER_LEVEL
                               and fr.Definition.BuiltInParameter != DB.BuiltInParameter.FAMILY_LEVEL_PARAM
                               and fr.Definition.BuiltInParameter != DB.BuiltInParameter.INSTANCE_HEAD_HEIGHT_PARAM
                               and fr.Definition.BuiltInParameter != DB.BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM
                               and fr.Definition.BuiltInParameter != DB.BuiltInParameter.PHASE_CREATED
                               and fr.Definition.BuiltInParameter != DB.BuiltInParameter.PHASE_DEMOLISHED
                               and fr.Definition.BuiltInParameter != DB.BuiltInParameter.ALL_MODEL_MARK
                               and fr.Definition.BuiltInParameter != DB.BuiltInParameter.ELEM_FAMILY_PARAM
                               and fr.Definition.BuiltInParameter != DB.BuiltInParameter.ELEM_FAMILY_AND_TYPE_PARAM
                               and fr.Definition.BuiltInParameter != DB.BuiltInParameter.ELEM_TYPE_PARAM}
            selected_parameters = forms.SelectFromList.show(dict_params.keys(), multiselect=True,
                                                            title="Select Parameters to Copy", button_name="Select")
            selected_params = []
            if selected_parameters is not None:
                for s in selected_parameters:
                    selected_params.append(dict_params[s])

        # gather properties to push to main function
        category = self.cb_category.SelectedItem
        datagrid_items = self.datagrid.Items
        lvls = []
        names = []
        prefixes = []

        for d in datagrid_items:
            if d.inclusion:
                lvls.append(d.level_element)
                names.append(d.level_name)
                prefixes.append(d.level_identifier)

        source_level = self.cb_source_level.SelectedItem
        source_identifier = self.id_source.Text

        self.coordinate_typ_floors(category, lvls, names, prefixes, source_level, source_identifier, selected_params)
        self.Close()


SettingsWindow().ShowDialog()
