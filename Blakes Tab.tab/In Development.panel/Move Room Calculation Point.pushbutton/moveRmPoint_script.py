# -*- coding: utf-8 -*-
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Transaction, SpatialElementBoundaryOptions, \
    AreaVolumeSettings, SpatialElementGeometryCalculator, SpatialElementType, XYZ
import Autodesk.Revit.DB as DB
from pyrevit import script
from math import sqrt
import time
import sys
sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")
from Queue import PriorityQueue

doc = __revit__.ActiveUIDocument.Document

nonOperableElements = 0
nonOperableGroups = []

# Creating collector instance and collecting all the rooms from the model
room_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()

'''Chain of yoink going on here. Dynamo interpretation taken Genius Loci dynamo package,
which is based on the mapbox PolyLabel algorithm.
Modified to suit pyRevit environment and custom curated to rooms. Some pieces taken from Clockwork room.Boundaries node

https://github.com/albandechasteigner/GeniusLociForDynamo

Finds pole of inaccessibility for a given polygon. Based on Vladimir Agafonkin's https://github.com/mapbox/polylabel


room.Boundaries node reference
https://github.com/andydandy74/ClockworkForDynamo

'''

__title__ = 'Move Room\nLocation Pt'


inf = float("inf")


# yoinked
def _point_to_polygon_distance(x, y, polygon):
    inside = False
    min_dist_sq = inf

    for ring in polygon:
        b = ring[-1]
        for a in ring:

            if ((a[1] > y) != (b[1] > y) and
                    (x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0])):
                inside = not inside

            min_dist_sq = min(min_dist_sq, _get_seg_dist_sq(x, y, a, b))
            b = a

    result = sqrt(min_dist_sq)
    if not inside:
        return -result
    return result


# yoinked
def _get_seg_dist_sq(px, py, a, b):
    x = a[0]
    y = a[1]
    dx = b[0] - x
    dy = b[1] - y

    if dx != 0 or dy != 0:
        tt = ((px - x) * dx + (py - y) * dy) / (dx * dx + dy * dy)

        if tt > 1:
            x = b[0]
            y = b[1]

        elif tt > 0:
            x += dx * tt
            y += dy * tt

    dx = px - x
    dy = py - y

    return dx * dx + dy * dy


# yoinked
class Cell(object):
    def __init__(self, x, y, h, polygon):
        self.h = h
        self.y = y
        self.x = x
        self.d = _point_to_polygon_distance(x, y, polygon)
        self.max = self.d + self.h * sqrt(2)

    def __lt__(self, other):
        return self.max < other.max

    def __lte__(self, other):
        return self.max <= other.max

    def __gt__(self, other):
        return self.max > other.max

    def __gte__(self, other):
        return self.max >= other.max

    def __eq__(self, other):
        return self.max == other.max


# yoinked
def _get_centroid_cell(polygon):
    area = 0
    x = 0
    y = 0
    points = polygon[0]
    b = points[-1]  # prev
    for a in points:
        f = a[0] * b[1] - b[0] * a[1]
        x += (a[0] + b[0]) * f
        y += (a[1] + b[1]) * f
        area += f * 3
        b = a
    if area == 0:
        return Cell(points[0][0], points[0][1], 0, polygon)
    return Cell(x / area, y / area, 0, polygon)
    pass


# yoinked
def polylabel(polygon, precision=1.0, with_distance=False):
    # find bounding box
    first_item = polygon[0][0]
    min_x = first_item[0]
    min_y = first_item[1]
    max_x = first_item[0]
    max_y = first_item[1]
    for p in polygon[0]:
        if p[0] < min_x:
            min_x = p[0]
        if p[1] < min_y:
            min_y = p[1]
        if p[0] > max_x:
            max_x = p[0]
        if p[1] > max_y:
            max_y = p[1]

    width = max_x - min_x
    height = max_y - min_y
    cell_size = min(width, height)
    h = cell_size / 2.0

    cell_queue = PriorityQueue()

    if cell_size == 0:
        if with_distance:
            return [min_x, min_y], None
        else:
            return [min_x, min_y]

    # cover polygon with initial cells
    x = min_x
    while x < max_x:
        y = min_y
        while y < max_y:
            c = Cell(x + h, y + h, h, polygon)
            y += cell_size
            cell_queue.put((-c.max, time.time(), c))
        x += cell_size

    best_cell = _get_centroid_cell(polygon)

    bbox_cell = Cell(min_x + width / 2, min_y + height / 2, 0, polygon)
    if bbox_cell.d > best_cell.d:
        best_cell = bbox_cell

    num_of_probes = cell_queue.qsize()
    while not cell_queue.empty():
        _, __, cell = cell_queue.get()

        if cell.d > best_cell.d:
            best_cell = cell

        if cell.max - best_cell.d <= precision:
            continue

        h = cell.h / 2
        c = Cell(cell.x - h, cell.y - h, h, polygon)
        cell_queue.put((-c.max, time.time(), c))
        c = Cell(cell.x + h, cell.y - h, h, polygon)
        cell_queue.put((-c.max, time.time(), c))
        c = Cell(cell.x - h, cell.y + h, h, polygon)
        cell_queue.put((-c.max, time.time(), c))
        c = Cell(cell.x + h, cell.y + h, h, polygon)
        cell_queue.put((-c.max, time.time(), c))
        num_of_probes += 4
    return XYZ(best_cell.x, best_cell.y, z)


# this is a bit of a yoink from Clockwork. In order to find the boundaries of the room,
# you need to first tell it HOW the room is being calculated.
calculator = SpatialElementGeometryCalculator(doc)
options = SpatialElementBoundaryOptions()
# get boundary location from area computation settings
boundloc = AreaVolumeSettings.GetAreaVolumeSettings(doc).GetSpatialElementBoundaryLocation(SpatialElementType.Room)
options.SpatialElementBoundaryLocation = boundloc

# list of pts used to calculate the polygon pole of inaccessibility.
# Be careful with list levels for rooms with holes in them.
pointList = []
# existing room location points
roomLocations = []
# list of rooms with an area (filtered unplaced rooms)
cleanedRooms = []

for room in room_collector:
    if room.Area > 0:
        if room.GroupId == DB.ElementId.InvalidElementId:
            room_is_editable = True
        else:
            group = room.Document.GetElement(room.GroupId)
            room_is_editable = False
            nonOperableElements += 1
            nonOperableGroups.append((group.Id, group.Name))
        if room_is_editable is True:
            crv = []
            cleanedRooms.append(room)
            roomLocations.append(room.Location.Point)
            for boundlist in room.GetBoundarySegments(options):
                for bound in boundlist:
                    crv.append([bound.GetCurve().GetEndPoint(0).X, bound.GetCurve().GetEndPoint(0).Y])
                    z = bound.GetCurve().GetEndPoint(0).Z
            pointList.append(crv)

centroids = [polylabel([listPoint]) for listPoint in pointList]

t = Transaction(doc, "Move Room Calculation Points")
t.Start()

for (rl, cent, finalrm) in zip(roomLocations, centroids, cleanedRooms):
    finalrm.Location.Move(cent-rl)

t.Commit()

if len(nonOperableGroups) > 0:
    output = script.get_output()
    output.print_md("# Warning!")
    output.print_md("Unable to edit " + (str(nonOperableElements)) + " rooms since they are in groups. \
                                                                        Their groups are listed below:")
    unique_groups = set(nonOperableGroups)
    for grp in unique_groups:
        print ("■ " + output.linkify(grp[0]) + " Type Name : " + (grp[1]))
