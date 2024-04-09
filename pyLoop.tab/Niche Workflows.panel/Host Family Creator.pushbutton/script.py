'''
Takes family instances placed in the project environment,
combines them into a single host family,
and inserts it in the same place within the project
'''
__title__ = 'Create\nNested Families'

import Autodesk.Revit.DB as DB
import Autodesk.Revit.DB.Structure as ST
import Autodesk.Revit.UI as UI
import os as os
import Autodesk.Revit.Exceptions as Exceptions


from pyrevit import revit, forms, coreutils, HOST_APP
from System.Collections.Generic import List
from pyrevit.forms import WPFWindow
from pyrevit.framework import Windows


from math import sin, cos

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
activeView = doc.ActiveView



fam_symbols = None


def create_and_load_temp_material_family(doc, target_doc, material):

    class CustomFamilyLoadOptions(DB.IFamilyLoadOptions):
        def OnFamilyFound(self, familyInUse, overwriteParameterValues):
            overwriteParameterValues.Value = True
            return True

        def OnSharedFamilyFound(self, sharedFamily, familyInUse, source, overwriteParameterValues):
            source.Value = DB.FamilySource.Family
            overwriteParameterValues.Value = True
            return True

    with DB.Transaction(doc, "Temp Material Xfer Family Add") as temp_transaction:
        '''This method still doesn't quite work for some reason, it doesn't seem to overwrite the param values '''

        ''' NEXT THING TO TRY -  CREATING NEW FAMILY TYPES FOR EACH MATERIAL AND LOADING IT INTO THE TARGET DOCUMENT ONCE'''

        fam_name = "TEMP_MATERIAL_XFER_R22"

        file_dir = os.path.dirname(__file__)
        fam_file_dir = file_dir + r"\\" + fam_name + ".rfa"

        temp_transaction.Start()

        temp_family = DB.Document.LoadFamily(doc, fam_file_dir, CustomFamilyLoadOptions())
        try:
            fam_symbols = temp_family[1].GetFamilySymbolIds()
        except AttributeError:
            pass
            # param_family = DB.ElementId(DB.BuiltInParameter.ALL_MODEL_FAMILY_NAME)
            # f_param_value = fam_name
            # f_param = DB.ParameterValueProvider(param_family)
            # evaluator = DB.FilterStringEquals()
            # f_rule = DB.FilterStringRule(f_param, evaluator, f_param_value, True)
            # filter_family_name = DB.ElementParameterFilter(f_rule)
            # fam_symbols = DB.FilteredElementCollector(doc).OfClass(DB.Family).WherePasses(filter_family_name).ToElementIds()
            # print(fam_symbols)

        # get familysymbolids always returns a list
        for elem_id in fam_symbols:
            symbol = DB.Document.GetElement(doc, elem_id)
            if not symbol.IsActive:
                # I don't really know what this does, but families must be activated to be used
                symbol.Activate()
            new_fam_symbol = symbol
        temp_family_instance = doc.Create.NewFamilyInstance(DB.XYZ(0, 0, 0), new_fam_symbol, ST.StructuralType.NonStructural)
        symbol_params = temp_family_instance.Symbol.Parameters

        for p in symbol_params:
            if not p.IsReadOnly:
                if p.StorageType == DB.StorageType.ElementId:
                    if p.Definition.ParameterGroup == DB.BuiltInParameterGroup.PG_MATERIALS:
                        p.Set(material.Id)

        temp_transaction.Commit()

        fam = temp_family_instance.Symbol.Family
        fam_doc = doc.EditFamily(fam)
        loaded_family = fam_doc.LoadFamily(target_doc, CustomFamilyLoadOptions())



        with DB.Transaction(target_doc, "Temp Material Xfer Family Add") as temp_transaction:
            temp_transaction.Start()
            fam_symbols = loaded_family.GetFamilySymbolIds()
            # get familysymbolids always returns a list
            for elem_id in fam_symbols:
                symbol = DB.Document.GetElement(target_doc, elem_id)
                if not symbol.IsActive:
                    # I don't really know what this does, but families must be activated to be used
                    symbol.Activate()
                new_fam_symbol = symbol


            target_doc.FamilyCreate.NewFamilyInstance(DB.XYZ(0,0,0), new_fam_symbol, ST.StructuralType.NonStructural)
            # DB.Document.Delete(target_doc, loaded_family.Id)
            temp_transaction.Commit()
        fam_doc.Close(False)

    with DB.Transaction(doc, "Temp Material Xfer Family Remove") as temp_transaction:
        temp_transaction.Start()
        temp_elem_family = temp_family_instance.Symbol.Family.Id
        DB.Document.Delete(doc, temp_family_instance.Id)
        DB.Document.Delete(doc, temp_elem_family)

        temp_transaction.Commit()



def load_family(elem, insertion_pt, target_doc):
    # get family, open in background, load into new fam doc, close
    fam = elem.Symbol.Family
    fam_type_name = DB.Element.Name.GetValue(elem.Symbol)
    fam_doc = doc.EditFamily(fam)
    loaded_family = fam_doc.LoadFamily(target_doc)
    fam_doc.Close(False)


    # get location parameters
    elem_rotation = elem.Location.Rotation
    elem_mirrored = elem.Mirrored


    # get all element parameters, and only save ones that are editable, and currently kills all element id based ones.
    '''edit to allow materials to pass through, if that method ends up actually working'''
    host_params = elem.Parameters

    relevant_params = []
    for p in host_params:
        # if not p.IsReadOnly and p.HasValue and (p.StorageType != DB.StorageType.ElementId):
        if not p.IsReadOnly and p.HasValue:
            p_def = p.Definition
            specific_p_str_name = str(p_def.Name) + str(p_def.ParameterGroup) + str(p_def.ParameterType)
            if p.StorageType == DB.StorageType.Integer:
                value = p.AsInteger()
            if p.StorageType == DB.StorageType.Double:
                value = p.AsDouble()
            if p.StorageType == DB.StorageType.String:
                value = p.AsString()
            if p.StorageType == DB.StorageType.None:
                value = None
            if p.StorageType == DB.StorageType.ElementId:
                param = (DB.Document.GetElement(doc, p.AsElementId()))

                if type(param) == DB.NestedFamilyTypeReference:
                    # if the family has nested families, we need to record a unique identifier to select inside the fam
                    # the element id is unfortunately different in project vs fam, so we need to string match
                    value = param.FamilyName + param.TypeName
                elif type(param) == DB.Material:
                    create_and_load_temp_material_family(doc, target_doc, param)
                    value = param.Name
                else:
                    # ignore things like level ids and such
                    value = None







            relevant_params.append((specific_p_str_name, value))

    # Get types from target family selection
    fam_symbols = loaded_family.GetFamilySymbolIds()

    t = DB.Transaction(target_doc, "Place Family")
    t.Start()

    for elem_id in fam_symbols:
        symbol = DB.Document.GetElement(target_doc, elem_id)
        if DB.Element.Name.GetValue(symbol) == fam_type_name:
            if not symbol.IsActive:
                # I don't really know what this does, but it throws an error without it
                symbol.Activate()
            family = symbol

    # create family instance in new family document
    fam = target_doc.FamilyCreate.NewFamilyInstance(insertion_pt, family, ST.StructuralType.NonStructural)

    target_params = fam.Parameters
    # rotate if required
    location = DB.XYZ(insertion_pt.X, insertion_pt.Y, 0)
    axis_line = DB.Line.CreateBound(location, location + DB.XYZ.BasisZ)
    DB.ElementTransformUtils.RotateElement(target_doc, fam.Id, axis_line, elem_rotation)

    # get all element parameters, and only save ones that are editable, and currently kills all element id based ones.
    '''edit to allow materials to pass through, if that method ends up actually working'''
    for tp in target_params:
        # only target useful parameters
        if not tp.IsReadOnly and tp.HasValue:
            tp_def = tp.Definition
            specific_tp_str_name = str(tp_def.Name) + str(tp_def.ParameterGroup) + str(tp_def.ParameterType)
            # search within the host parameters list for the new family
            for hp in relevant_params:
                if specific_tp_str_name == hp[0]:
                    # if the correct parameter is found, set param values
                    if tp.StorageType != DB.StorageType.ElementId:
                        tp.Set(hp[1])
                    else:
                        # element id storage is annoying
                        # we need to find the element within the family document by string matching
                        if tp.StorageType == DB.StorageType.ElementId:
                            fam_param = (DB.Document.GetElement(target_doc, tp.AsElementId()))

                            # nested families
                            if type(fam_param) == DB.NestedFamilyTypeReference:
                                nested_elems_ids = fam.Symbol.Family.GetFamilyTypeParameterValues(tp.Id)
                                for element in nested_elems_ids:
                                    nesty_param = (DB.Document.GetElement(target_doc, element))
                                    combined_para_name = nesty_param.FamilyName + nesty_param.TypeName

                                    if combined_para_name == hp[1]:
                                        tp.Set(element)
                                        # exit loop because we found the correct param
                                        break
                            # if type(fam_param) == DB.:
                    # exit loop when the relevant parameter has been found
                    break

    t.Commit()



    if elem_mirrored:
        t = DB.Transaction(target_doc, "Mirror")
        t.Start()
        """this has to be the last item done, becuase the mirror method doesn't return the new family instance"""
        ''' If the instance is mirrored, we need to create a plane to mirror the group,
                            aligned with the group's rotation'''
        origin = (location.X, location.Y)
        point = (location.X + 1, location.Y)
        new_pt_x = origin[0] + cos(elem_rotation) * (point[0] - origin[0]) - sin(elem_rotation) * (point[1] - origin[1])
        new_pt_y = origin[1] + sin(elem_rotation) * (point[0] - origin[0]) + cos(elem_rotation) * (point[1] - origin[1])
        rotated_pt = DB.XYZ(new_pt_x, new_pt_y, location.Z)
        axis_plane = DB.Plane.CreateByThreePoints(rotated_pt, location, location + DB.XYZ.BasisZ)
        DB.ElementTransformUtils.MirrorElement(target_doc, fam.Id, axis_plane)
        # Revit forces you to make a copy when mirroring, so we need to delete the old instance
        target_doc.Delete(fam.Id)
        t.Commit()



class CustomISelectionFilter(UI.Selection.ISelectionFilter):
    def __init__(self):
        pass
        # self.category_name = category_name

    def AllowElement(self, e):
        return  True
        # cat = e.Category.Name
        # if (cat == self.category_name):
        #     return True
        # else:
        #     return False

    def AllowReference(self, ref, point):
        return False

# get current preselection
rawSelection = uidoc.Selection.GetElementIds()

# if something is selected, filter for familyinstances
if len(rawSelection) > 0:
    '''add logic to deal with in place families'''
    filteredSelection = DB.FilteredElementCollector(doc, rawSelection).OfClass(DB.FamilyInstance) \
        .WhereElementIsNotElementType() \
        .ToElements()
    if len(filteredSelection) > 0:
        collector = filteredSelection
    else:
        forms.alert('Selection must contain family instances. \n Try again.', exitscript=True)

else:
    # if nothing is pre-selected, create new selection, which filters for family instances.
    # with forms.WarningBar(title='Select Families to Add'):
    forms.alert('Select Families to Add')

    selectionNew = []
    selection_completed = False
    while selection_completed is not True:
        try:
            selector = uidoc.Selection.PickObjects(UI.Selection.ObjectType.Element,
                                                   CustomISelectionFilter())
            if selector.Count > 0:
                selection_completed = True
            else:
                forms.alert("Nothing selected, try again.")
        except Exceptions.OperationCanceledException:
            forms.alert('Selection Cancelled. Try again?', yes=True, no=True, exitscript=True)

    for ref in selector:
        selectionNew.append(DB.Document.GetElement(doc, ref))
    newSelectionIds = []
    if len(selectionNew) > 0:
        for i in selectionNew:
            newSelectionIds.append(i.Id)

    newSelectionIds = List[DB.ElementId](newSelectionIds)
    '''add logic to remove in place families'''
    collector = DB.FilteredElementCollector(doc, newSelectionIds).OfClass(DB.FamilyInstance)\
        .WhereElementIsNotElementType().ToElements()


'''clean this up, it should be smarter than just grabbibng the first instance'''
elem = collector[0]
el_cat_id = elem.Category.Id.IntegerValue

'''this is pretty clunky becuase its hardcoded, and is repeated inside the wpf window class. its stolen from pychillizer. should add options for template dirs'''
templates_dict = {
    -2001000: "\Metric Casework.rft",
    -2000080: "\Metric Furniture.rft",
    -2001040: "\Metric Electrical Equipment.rft",
    -2001370: "\Metric Entourage.rft",
    -2001100: "\Metric Furniture System.rft",
    -2000151: "\Metric Generic Model.rft",
    -2001120: "\Metric Lighting Fixture.rft",
    -2001140: "\Metric Mechanical Equipment.rft",
    -2001180: "\Metric Parking.rft",
    -2001360: "\Metric Planting.rft",
    -2001160: "\Metric Plumbing Fixture.rft",
    -2001260: "\Metric Site.rft",
    -2001350: "\Metric Specialty Equipment.rft",
}
template = None
if el_cat_id in templates_dict:
    template = templates_dict[el_cat_id]
else:
    template = "\Metric Generic Model.rft"
fam_template_path = "C:\ProgramData\Autodesk\RVT " + \
                    HOST_APP.version + "\Family Templates\English" + template



try:
    new_family_doc = revit.doc.Application.NewFamilyDocument(fam_template_path)
except:
    forms.alert(msg="No Template",
                sub_msg="No Template for family found.",
                ok=True,
                warn_icon=True, exitscript=True)


# with forms.WarningBar(title='Pick Insertion Point for the New Host Family'):
forms.alert('Pick Insertion Point for the New Host Family')
'''User picks where they want the selected elements to be relative to the host family origin'''
if activeView.SketchPlane is None and type(activeView) is not DB.ViewDrafting:
    t_temp = DB.Transaction(doc, "TempSketchPlane")
    t_temp.Start()
    sketch_plane = DB.SketchPlane \
        .Create(doc, DB.Plane.CreateByNormalAndOrigin(activeView.ViewDirection, activeView.Origin))
    activeView.SketchPlane = sketch_plane
    try:
        point = uidoc.Selection.PickPoint()
    except Exceptions.InvalidOperationException:
        t_temp.RollBack()
        import sys
        sys.exit()
    t_temp.RollBack()
else:
    try:
        point = uidoc.Selection.PickPoint()
    except Exceptions.OperationCanceledException:
        forms.alert("Cancelled", exitscript=True)
    except Exceptions.InvalidOperationException:
        import sys
        sys.exit()

insertion_point = point



class SettingsWindow(WPFWindow):
    def __init__(self):

        file_dir = os.path.dirname(__file__)
        xaml_source = os.path.join(file_dir, 'family_creator.xaml')
        WPFWindow.__init__(self, xaml_source)

        '''clean this up, it should be smarter than just grabbing the first instance in the selection'''
        self._host_cat = collector[0].Category
        '''this is extremely clunky, clean this up'''
        self._level = DB.Document.GetElement(doc, collector[0].LevelId)

        self.setup_categories(self.host_category)
        self.setup_template_dir(self.host_category)

    @property
    def host_category(self):
        return self._host_cat

    @host_category.setter
    def host_category(self, cat):
        self._host_cat = cat

    @property
    def enable_room_calc_pt(self):
        return self.cx_room_calc_pt.IsChecked

    @property
    def delete_original(self):
        return self.cx_delete_og_fams.IsChecked

    @property
    def file_name(self):
        return self.tb_fam_name.Text

    @property
    def save_dir(self):
        return self.tb_file_dir.Text

    def setup_template_dir(self, category_elem):
        el_cat_id = category_elem.Id.IntegerValue

        '''this is pretty clunky becuase its hardcoded. its stolen from pychillizer. should add options for template dirs'''
        templates_dict = {
            -2001000: "\Metric Casework.rft",
            -2000080: "\Metric Furniture.rft",
            -2001040: "\Metric Electrical Equipment.rft",
            -2001370: "\Metric Entourage.rft",
            -2001100: "\Metric Furniture System.rft",
            -2000151: "\Metric Generic Model.rft",
            -2001120: "\Metric Lighting Fixture.rft",
            -2001140: "\Metric Mechanical Equipment.rft",
            -2001180: "\Metric Parking.rft",
            -2001360: "\Metric Planting.rft",
            -2001160: "\Metric Plumbing Fixture.rft",
            -2001260: "\Metric Site.rft",
            -2001350: "\Metric Specialty Equipment.rft",
        }
        template = None
        if el_cat_id in templates_dict:
            template = templates_dict[el_cat_id]
        else:
            template = "\Metric Generic Model.rft"
        fam_template_path = "C:\ProgramData\Autodesk\RVT " + \
                            HOST_APP.version + "\Family Templates\English" + template

        self.tb_template_dir.Text = fam_template_path

    def setup_categories(self, category_elem):
        cats = [DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_Casework),
                DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_Furniture),
                DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_ElectricalEquipment),
                DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_Entourage),
                DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_FurnitureSystems),
                DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_GenericModel),
                DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_LightingFixtures),
                DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_MechanicalEquipment),
                DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_Parking),
                DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_Planting),
                DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_PlumbingFixtures),
                DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_Site),
                DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_SpecialityEquipment)]

        self.cb_fam_category.ItemsSource = cats

        try:
            el_cat_id = category_elem.Id.IntegerValue
        except AttributeError:
            el_cat_id = 0

        index = 0
        for c in cats:
            if c.Id.IntegerValue == el_cat_id:
                index = cats.index(c)
                break

        self.cb_fam_category.SelectedIndex = index

    def changed_category(self, sender, args):
        if self.host_category != sender.SelectedItem:
            self.setup_template_dir(sender.SelectedItem)

    def name_changed(self, sender, args):
        param_family = DB.ElementId(DB.BuiltInParameter.ALL_MODEL_FAMILY_NAME)
        f_param_value = sender.Text
        f_param = DB.ParameterValueProvider(param_family)
        evaluator = DB.FilterStringEquals()
        f_rule = DB.FilterStringRule(f_param, evaluator, f_param_value, True)
        elem_filter = DB.ElementParameterFilter(f_rule)

        fams = DB.FilteredElementCollector(doc).OfClass(DB.FamilyInstance).WherePasses(elem_filter).ToElements()

        if len(fams) != 0 or sender.Text == "":
            self.name_warning.Visibility = Windows.Visibility.Visible
        else:
            self.name_warning.Visibility = Windows.Visibility.Collapsed

    def click_fam_template_dir(self, sender, args):
        dir = forms.pick_file(file_ext="rft", init_dir=fam_template_path)
        self.tb_template_dir.Text = dir

    def click_save_dir(self, sender, args):
        save_dir = forms.pick_folder()
        self.tb_file_dir.Text = save_dir

    def template_dir_changed(self, sender, args):
        if os.path.exists(sender.Text):
            self.dir_warning.Visibility = Windows.Visibility.Collapsed
        else:
            self.dir_warning.Visibility = Windows.Visibility.Visible

    def save_dir_changed(self, sender, args):
        if os.path.exists(sender.Text):
            self.dir_file_warning.Visibility = Windows.Visibility.Collapsed
        else:
            self.dir_file_warning.Visibility = Windows.Visibility.Visible

    def click_run(self, sender, args):
        # need to determine where the centroid of the group of families is, start with an empty param
        min_x = None
        min_y = None
        min_z = None

        max_x = None
        max_y = None
        max_z = None

        max_value = len(collector)
        # with forms.ProgressBar(title='Transferring Family.. ({value} of {max_value})', cancellable=True) as pb:
        #     i = 0
        for elem in collector:

                geo_boundingbox = elem.get_BoundingBox(None)
                geo_min_x = geo_boundingbox.Min.X
                geo_min_y = geo_boundingbox.Min.Y
                geo_min_z = geo_boundingbox.Min.Z

                geo_max_x = geo_boundingbox.Max.X
                geo_max_y = geo_boundingbox.Max.Y
                geo_max_z = geo_boundingbox.Max.Z

                if min_x is None or geo_min_x < min_x:
                    min_x = geo_min_x

                if min_y is None or geo_min_y < min_y:
                    min_y = geo_min_y

                if min_z is None or geo_min_z < min_z:
                    min_z = geo_min_z

                if max_x is None or geo_max_x > max_x:
                    max_x = geo_max_x

                if max_y is None or geo_max_x > max_x:
                    max_y = geo_max_y

                if max_z is None or geo_max_x > max_x:
                    max_z = geo_max_z

                location = elem.Location
                if type(location) == DB.LocationPoint:
                    fam_relative_location = location.Point
                    fam_location_in_host = DB.XYZ(fam_relative_location.X - insertion_point.X, fam_relative_location.Y - insertion_point.Y, 0)
                    load_family(elem, fam_location_in_host, new_family_doc)




                if type(location) == DB.LocationCurve:
                    '''add curve based elements, currently will just skip it'''
                    print("Found a line-based family. It will be skipped. Tell Blake to stop being lazy and add that option.")
                    print("You'll need to add that family manually :(")
                    print("But i'm serious actually tell me")
                    print("")
                    continue

                # if pb.cancelled:
                #     # exit script if user cancels operation with forms.warningbar function
                #     break
                # else:
                #     # update forms.warningbar UI with progress for every target element
                #     pb.update_progress(i, max_value)
                # i += 1

        family = new_family_doc.OwnerFamily
        param = family.get_Parameter(DB.BuiltInParameter.ROOM_CALCULATION_POINT)
        if param and self.enable_room_calc_pt:
            with DB.Transaction(new_family_doc, "AddRoomCalcPoint") as t:
                t.Start()
                param.Set(1)
                composite_min_pt = DB.XYZ(min_x, min_y, min_z)
                composite_max_pt = DB.XYZ(max_x, max_y, max_z)

                average_bb_mid_pt = (composite_max_pt + composite_min_pt) / 2
                room_calc_pt = -(insertion_point - average_bb_mid_pt)

                pt = DB.FilteredElementCollector(new_family_doc).OfClass(DB.SpatialElementCalculationPoint)
                for p in pt:
                    p.Position = room_calc_pt
                t.Commit()

        path = os.path.join(self.save_dir, self.file_name + ".rfa")
        try:
            new_family_doc.SaveAs(path)
        except:
            overwrite = forms.alert("File Already Exists. Overwrite?", sub_msg=path, yes=True, no=True, exitscript=True)
            if overwrite:
                os.remove(path)
                new_family_doc.SaveAs(path)
            else:
                valid = False
                while valid == False:
                    if os.path.exists(path):
                        pass


        new_family_doc.Close(False)

        del_t = DB.Transaction(doc, "New Host Family")
        del_t.Start()

        class CustomFamilyLoadOptions(DB.IFamilyLoadOptions):
            def OnFamilyFound(self, familyInUse, overwriteParameterValues):
                overwriteParameterValues.Value = False
                return True

            def OnSharedFamilyFound(self, sharedFamily, familyInUse, source, overwriteParameterValues):
                source.Value = DB.FamilySource.Family
                overwriteParameterValues.Value = False
                return False

        new_family = DB.Document.LoadFamily(doc, path, CustomFamilyLoadOptions())

        # 0 index returns if the load was successful or not
        if new_family[0]:

            # 1 index returns the family instance that was loaded
            fam_symbols = new_family[1].GetFamilySymbolIds()

            # get familysymbolids always returns a list
            for elem_id in fam_symbols:
                symbol = DB.Document.GetElement(doc, elem_id)
                if not symbol.IsActive:
                    # I don't really know what this does, but families must be activated to be used
                    symbol.Activate()
                new_fam_symbol = symbol

            # place the combined family in the host document
            doc.Create.NewFamilyInstance(DB.XYZ(insertion_point.X, insertion_point.Y, 0), new_fam_symbol, self._level, ST.StructuralType.NonStructural)

            # delete the original families
            if self.delete_original:
                for elem in collector:
                    if elem.GroupId == DB.ElementId.InvalidElementId:
                        try:
                            DB.Document.Delete(doc, elem.Id)
                        except:
                            print("Could not delete original item (for unknown reasons): " + elem.Name + " " + output.linkify(
                                    elem.Id))
                    else:
                        from pyrevit import script
                        output = script.get_output()
                        print("Could not delete original item (it's in a group): " + elem.Name + " " + output.linkify(elem.Id))


        del_t.Commit()
        self.Close()

SettingsWindow().ShowDialog()
