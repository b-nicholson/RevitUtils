import Autodesk.Revit.DB as DB
import math

doc = __revit__.ActiveUIDocument.Document
activeView = doc.ActiveView

grid_collector = DB.FilteredElementCollector(doc) \
                    .OfCategory(DB.BuiltInCategory.OST_Grids)\
                    .WhereElementIsNotElementType() \
                    .ToElements()

for grid in grid_collector:
    direction = grid.Curve.GetEndPoint(1).Subtract(grid.Curve.GetEndPoint(0)).Normalize()
    distance2hor = direction.DotProduct(DB.XYZ.BasisY)
    distance2vert = direction.DotProduct(DB.XYZ.BasisX)
    angle = 0
    max_distance = 0.0001

    if abs(distance2hor) < max_distance:
        vector = direction.X
        if vector < 0:
            vector = direction.Negate()
        else:
            vector = direction

        angle = math.asin(-vector.Y)

    if abs(distance2vert) < max_distance:
        vector = direction.Y
        if direction.Y < 0:
            vector = direction.Negate()
        else:
            vector = direction

        angle = math.asin(vector.X)

    if angle != 0:
        line = DB.Line.CreateBound(grid.Curve.GetEndPoint(0), grid.Curve.GetEndPoint(0).Add(DB.XYZ.BasisZ))
        t = DB.Transaction(doc, "Flip Grid Ends - 3D")
        t.Start()

        DB.ElementTransformUtils.RotateElement(doc, grid.Id, line, angle)
        flippedCurves = grid.Curve.CreateReversed()
        t.Commit()
