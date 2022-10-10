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
fileSuff = "pbd" # ps2 = .pbd, xbox = .xbd, ngc = .nbd


scaleDiv = 100 # 100 for Blender resize, 1 for SSX default
createBounds = False




def import_splines():

    f = open(filePath+"/"+fileName+"."+fileSuff, 'rb')


    f.seek(0x3, 0)
    platformID = struct.unpack('B', f.read(1))[0]

    en = "<"
    countOffset  = 0x20
    offsetOffset = 0x5C

    if   platformID == 2:      # 1 = ps2, 2 = xbox, 3 = ngc
        countOffset  = 0x28
        offsetOffset = 0x70

    elif platformID == 3:
        en = ">"


    f.seek(countOffset, 0)

    splineCount = struct.unpack(en+'I', f.read(4))[0]
    splineSegmentCount = struct.unpack(en+'I', f.read(4))[0]


    f.seek(offsetOffset, 0)

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


        splineSegmentPointList.append((
                Vector((splineSegment["point1"][0],splineSegment["point1"][1],splineSegment["point1"][2])),
                Vector((splineSegment["point2"][0],splineSegment["point2"][1],splineSegment["point2"][2])),
                Vector((splineSegment["point3"][0],splineSegment["point3"][1],splineSegment["point3"][2])),
                Vector((splineSegment["point4"][0],splineSegment["point4"][1],splineSegment["point4"][2]))
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



        curveName = f'spline{i}'

        curve = bpy.data.curves.new(curveName+"_NURBS", "CURVE")

        for j in range(spline["segmentCount"]):
            coords = decode_curve_points(  splineSegmentPointList[ spline["segmentIndex"]+j ]  )


            cspline = curve.splines.new('NURBS')

            curve.dimensions = '3D'

            cspline.points.add(len(coords)-1) # already contains a point that's why it's adding 1 less than total
            for (index, point) in enumerate(coords):
                cspline.points[index].co = (point[0]/scaleDiv, point[1]/scaleDiv, point[2]/scaleDiv, 1.0)

            cspline.use_endpoint_u = True


        curveObj = bpy.data.objects.new(curveName, curve)
        collecMain.objects.link(curveObj)

    
        curveObj["Address 0x"]   = curAddress[2:]
        curveObj["unkInt1"]      = spline["unkInt1"]
        curveObj["segmentCount"] = spline["segmentCount"]
        curveObj["segmentIndex"] = spline["segmentIndex"]
        curveObj["unkInt2"]      = spline["unkInt2"]


    timeEnd = time.time()
    print(f"\nFINISHED ({time.localtime().tm_hour}:{time.localtime().tm_min})\nTime taken {round(timeEnd-timeStart, 4)}s")

    f.close()










def decode_curve_points(encPoints): # decoding with equations

    midPoints = [Vector((0.0, 0.0, 0.0))]*4
    decPoints = [Vector((0.0, 0.0, 0.0))]*4


    midPoints[0] =  encPoints[0]
    midPoints[1] =  encPoints[1]/3 + midPoints[0]
    midPoints[2] = (encPoints[2]   + encPoints[1])/3 + midPoints[1]
    midPoints[3] =  encPoints[3]   + encPoints[2]    + encPoints[1] + encPoints[0]

    decPoints[0] = midPoints[0]
    decPoints[1] = midPoints[1]
    decPoints[2] = midPoints[2]
    decPoints[3] = midPoints[3]

    return decPoints









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
