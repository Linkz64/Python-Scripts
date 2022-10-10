import bpy
import struct
from mathutils import Vector, Color, Matrix
import time

bdata = bpy.data
bcontext = bpy.context
bscene = bcontext.scene

collecMain = bcontext.collection

timeStart = time.time() # start timer
print(f"TIME STARTED {time.localtime().tm_hour}:{time.localtime().tm_min}")



filePath = "G:/Emulated/Playstation 2/Games/SSX Tricky/data/models"
fileName = "gari"
fileSuff = "pbd" # ps2 = .pbd, xbox = xbd, ngc = nbd ( ONLY TESTED ON PBD )


scaleDiv = 100 # 100 for Blender resize, 1 for SSX default
createBounds = False




def import_splines():

    f = open(filePath+"/"+fileName+"."+fileSuff, 'rb')


    f.seek(0x3, 0)
    enByte = struct.unpack('B', f.read(1))[0]

    en = "<"
    if enByte == 3: # 1 = ps2, 2 = xbox, 3 = ngc
        en = ">"


    f.seek(0x20, 0)

    splineCount = struct.unpack(en+'I', f.read(4))[0]
    splineSegmentCount = struct.unpack(en+'I', f.read(4))[0]

    f.seek(0x5C, 0)

    splineOffset = struct.unpack(en+'I', f.read(4))[0]
    splineSegmentOffset = struct.unpack(en+'I', f.read(4))[0]



    #splineCount = 8



    # SPLINE SEGMENTS

    f.seek(splineSegmentOffset, 0)


    splineSegmentList = []
    splineSegmentPointList = []

    for i in range(splineSegmentCount): # length d128 x80

        curAddress = str(hex(f.tell()))

        splineSegment = {
            "point4": Vector(struct.unpack(en+'ffff', f.read(16))),
            "point3": Vector(struct.unpack(en+'ffff', f.read(16))),
            "point2": Vector(struct.unpack(en+'ffff', f.read(16))),
            "point1": Vector(struct.unpack(en+'ffff', f.read(16))),

            "scalePoint": Vector(struct.unpack(en+'ffff', f.read(16))),

            "prevSegment":  struct.unpack(en+'I', f.read(4))[0],
            "nextSegment":  struct.unpack(en+'I', f.read(4))[0],
            "splineParent": struct.unpack(en+'I', f.read(4))[0],

            "bboxPt1": Vector(struct.unpack(en+'fff', f.read(12))), # bounding box point
            "bboxPt2": Vector(struct.unpack(en+'fff', f.read(12))), # bounding box point
    
            "currSegmentDistance": struct.unpack(en+'f', f.read(4))[0],
            "prevSegmentDistance": struct.unpack(en+'f', f.read(4))[0],
            "unknown": struct.unpack(en+'I', f.read(4))[0],
        }

        splineSegmentList.append(splineSegment)


        splineSegmentPointList.append(
            (
                Vector((splineSegment["point1"][0],splineSegment["point1"][1],splineSegment["point1"][2])),
                Vector((splineSegment["point2"][0],splineSegment["point2"][1],splineSegment["point2"][2])),
                Vector((splineSegment["point3"][0],splineSegment["point3"][1],splineSegment["point3"][2])),
                Vector((splineSegment["point4"][0],splineSegment["point4"][1],splineSegment["point4"][2])),
            )
        )



        if createBounds: # creating bounds for testing

            boundsName = f"{fileName}_splineSegment.{i}_bounds"
    
            create_bounds(boundsName, splineSegment["bboxPt1"], splineSegment["bboxPt2"])

            boundsObj = bdata.objects[boundsName]
    
            boundsObj["Address 0x"]  = curAddress[2:]
            boundsObj["prevSegment"] = str(splineSegment["prevSegment"])
            boundsObj["nextSegment"] = str(splineSegment["nextSegment"])
            boundsObj["splineParent"] = splineSegment["splineParent"]

            boundsObj["currSegmentDistance"] = splineSegment["currSegmentDistance"]
            boundsObj["prevSegmentDistance"] = splineSegment["prevSegmentDistance"]
            boundsObj["unknown"] = splineSegment["unknown"]




    # SPLINES

    f.seek(splineOffset, 0)


    splineList = []

    for i in range(splineCount): # length d40 x28

        curAddress = str(hex(f.tell()))

        spline = {
            "bboxPt1": struct.unpack(en+'fff', f.read(12)), # bounding box point
            "bboxPt2": struct.unpack(en+'fff', f.read(12)), # bounding box point
    
            "unkInt1":      struct.unpack(en+'I', f.read(4))[0],
            "segmentCount": struct.unpack(en+'I', f.read(4))[0],
            "segmentIndex": struct.unpack(en+'I', f.read(4))[0], # index inside segment list
            "unkInt2":      struct.unpack(en+'i', f.read(4))[0], # FFFFFFFF or -1
        }

        splineList.append(spline)
        #print(spline)


        if createBounds: # creating bounds for testing

            boundsName = f"{fileName}_spline.{i}_bounds"
    
            create_bounds(boundsName, spline["bboxPt1"], spline["bboxPt2"])
    
            boundsObj = bdata.objects[boundsName]
    
            boundsObj["Address 0x"]   = curAddress[2:]
            boundsObj["unkInt1"]      = spline["unkInt1"]
            boundsObj["segmentCount"] = spline["segmentCount"]
            boundsObj["segmentIndex"] = spline["segmentIndex"]
            boundsObj["unkInt2"]      = spline["unkInt2"]


        coordsList = []
        for j in range(spline["segmentCount"]):
            curSegCoords = decode_curve_points(  splineSegmentPointList[ spline["segmentIndex"]+j ]  )

            coordsList.append(curSegCoords[0])
            coordsList.append(curSegCoords[1])
            coordsList.append(curSegCoords[2])
            coordsList.append(curSegCoords[3])

        print(coordsList)

        create_curve_obj(coordsList, f'curve{i}')


    timeEnd = time.time()
    print(f"\nFINISHED ({time.localtime().tm_hour}:{time.localtime().tm_min})\nTime taken {round(timeEnd-timeStart, 4)}s")

    f.close()







# decoding with equations

def decode_curve_points(encPoints):

    midPoints = [Vector((0.0, 0.0, 0.0))]*4
    rawPoints = [Vector((0.0, 0.0, 0.0))]*4


    midPoints[0] =  encPoints[0]
    midPoints[1] =  encPoints[1]/3 + midPoints[0]
    midPoints[2] = (encPoints[2]   + encPoints[1])/3 + midPoints[1]
    midPoints[3] =  encPoints[3]   + encPoints[2]    + encPoints[1] + encPoints[0]

    rawPoints[0] = midPoints[0]
    rawPoints[1] = midPoints[1]
    rawPoints[2] = midPoints[2]
    rawPoints[3] = midPoints[3]

    return rawPoints







# generate spline curve segment

def create_curve_obj(coords, name):

    cu = bpy.data.curves.new(name+"_NURBS", "CURVE")
    cpath = cu.splines.new('NURBS')  # 'POLY''BEZIER''BSPLINE''CARDINAL''NURBS'

    cu.dimensions = '3D'

    if cpath.type in ['NURBS', 'POLY']:
        cpath.points.add(len(coords)-1)
        for (index, point) in enumerate(coords):
            cpath.points[index].co = (point[0]/scaleDiv, point[1]/scaleDiv, point[2]/scaleDiv, 1.0)

            #create_empty(name, (point[0]/scaleDiv, point[1]/scaleDiv, point[2]/scaleDiv))

            #print(cpath.points[index].co)

        cpath.use_endpoint_u = True


    elif cpath.type in ['BEZIER']:             # don't use this
        cpath.bezier_points.add(len(coords)-1)
        for (index, point) in enumerate(coords):
            x, y, z = point
            cpath.bezier_points[index].co = x, y, z
            cpath.bezier_points[index].handle_left = x-5, y-5, z-5
            cpath.bezier_points[index].handle_right = x+5, y+5, z+5
            print(cpath.bezier_points[index].co)

    ob = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(ob)



"""

def create_curve_obj(coords, name):
    curveData = bpy.data.curves.new(name+"_NURBS", type='CURVE')
    curveData.dimensions = '3D'
    curveData.resolution_u = 2
    
    polyline = curveData.splines.new('NURBS')

    polyline.points.add(len(coords))
    for i, coord in enumerate(coords):
        x,y,z = coord
        polyline.points[i].co = (x/scaleDiv, y/scaleDiv, z/scaleDiv, 1)
        print(polyline.points[i].co)
    polyline.use_endpoint_u = True
    

    curveOB = bpy.data.objects.new(name, curveData)
    bpy.context.collection.objects.link(curveOB)

"""




def create_empty(name, pos): # create empty object
    empty = bdata.objects.new(name, None) # Object instances
    collecMain.objects.link(empty)
    empty.empty_display_type = 'ARROWS'
    #empty.empty_display_size = 250
    empty.show_name = True
    empty.location = pos

def create_bounds(name, pos1, pos2): # create just bounds

    mesh = bdata.meshes.new(name)
    obj = bdata.objects.new(name, mesh)
    collecMain.objects.link(obj)
    mesh.from_pydata([Vector(pos1)/scaleDiv, Vector(pos2)/scaleDiv], [], [])
    obj.display_type = 'BOUNDS'


def run_wout_update(func):              # run without view update
    from bpy.ops import _BPyOpsSubModOp
    view_layer_update = _BPyOpsSubModOp._view_layer_update
    def dummy_view_layer_update(context):
        pass
    try:
        _BPyOpsSubModOp._view_layer_update = dummy_view_layer_update
        func()
    finally:
        _BPyOpsSubModOp._view_layer_update = view_layer_update


run_wout_update(import_splines)
