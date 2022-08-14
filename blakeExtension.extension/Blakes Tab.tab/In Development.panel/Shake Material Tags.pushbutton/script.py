#pylint: disable=missing-docstring,import-error,invalid-name,unused-argument
from pyrevit import revit, DB
from pyrevit import script
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, BuiltInParameter, WallUtils, Transaction, ElementTransformUtils


doc = __revit__.ActiveUIDocument.Document
output = script.get_output()

# collect target views
selection = revit.get_selection()
target_views = selection.elements
if not target_views:
    target_views = [revit.active_view]


def shake_material_tags(target_view):
    material_tags = \
        DB.FilteredElementCollector(target_view.Document, target_view.Id)\
          .OfCategory(DB.BuiltInCategory.OST_MaterialTags)\
          .WhereElementIsNotElementType()\
          .ToElements()

    print('Shaking Material Tags in: {}'
          .format(revit.query.get_name(target_view)))

    #for tags in material_tags:
       # with revit.Transaction('Shake Material Tags'):
            #tags.Location.Move(DB.XYZ(1, 0, 0))
            #tags.Location.Move(DB.XYZ(-10, 0, 0))

    for tag in material_tags:
        with revit.Transaction('Shake Material Tags'):
            ElementTransformUtils.MoveElement(doc, tag.Id, DB.XYZ(1, 0, 0))

print('Shaking Material Tags in {} views'.format(len(target_views)))
with revit.TransactionGroup('Shake Material Tags'):
    for idx, view in enumerate(target_views):
        shake_material_tags(view)
        output.update_progress(idx+1, len(target_views))

print('All Material Tags where shaken...')
