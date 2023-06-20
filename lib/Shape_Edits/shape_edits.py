import System
import Autodesk.Revit.Exceptions as Exceptions

# remove duplicate lines
def clean_lines(curves):
    C0 = []
    C1 = []
    for c in curves:
        start = c.GetEndPoint(0)
        end = c.GetEndPoint(1)

        flip_crv = c.CreateReversed()
        flip_start = flip_crv.GetEndPoint(0)
        flip_end = flip_crv.GetEndPoint(1)

        str_og = str(start) + str(end)
        str_flip = str(flip_start) + str(flip_end)
        sL = str(c.Length)
        # Added Length to allow for better accuracy identifying duplicates
        if str_og + sL not in C1 and str_flip + sL not in C1:
            C0.append(c)
            C1.append(str_og + sL)
            C1.append(str_flip + sL)
    return C0


# adds split lines to a target floor/roof/slab based on 3d lines
def add_split_lines(edges, target):
    for e in edges:
        start_point = e.GetEndPoint(0)
        end_point = e.GetEndPoint(1)

        try:
            st_point = target.SlabShapeEditor.DrawPoint(start_point)
        except System.MissingMemberException:
            st_point = None
            pass
        try:
            ed_point = target.SlabShapeEditor.DrawPoint(end_point)
        except System.MissingMemberException:
            ed_point = None
            pass

        if st_point is not None and ed_point is not None:
            try:
                target.SlabShapeEditor.DrawSplitLine(st_point, ed_point)
            except Exceptions.ArgumentException:
                pass
