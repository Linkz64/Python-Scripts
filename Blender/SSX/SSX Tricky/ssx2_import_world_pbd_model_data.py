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
fileName = "snow"
fileSuff = "pbd" # ps2 = .pbd, xbox = xbd, ngc = nbd ( ONLY TESTED ON PBD )


scaleDiv = 100 # 100 for Blender resize, 1 for SSX default
createBounds = False



f = open(filePath+"/"+fileName+"."+fileSuff, 'rb')

en = "<"

def import_splines():
    global en
    en = "<"

    f.seek(0x3, 0)
    platformID = struct.unpack('B', f.read(1))[0]


    countOffset = 0x2C

    headerModelPointerOffset = 0x68
    #headerModelsOffset = 0x6C

    """

    if   platformID == 2:      # 1 = ps2, 2 = xbox, 3 = ngc
        countOffset = 0x2C
        headerModelPointerOffset = 0x68

    elif platformID == 3:
        en = ">"
    """


    modelCount = unpk_uint_at(countOffset)


    modelPointerOffset = unpk_uint_at(headerModelPointerOffset)
    modelsOffset = unpk_uint()



    # unpacking model pointers

    modelPointerList = [0]*modelCount
    
    f.seek(modelPointerOffset, 0)

    for i in range(modelCount):
        modelPointerList[i] = unpk_uint()



    # unpacking model data

    diffType = ""

    for i in range(modelCount):

        currOffset = modelsOffset+modelPointerList[i]
        f.seek(currOffset, 0)

        totalLength   = unpk_uint()
        unk0          = unpk_uint()  # Type
        unk1          = unpk_uint()  # This header's length?
        unk2          = unpk_uint()  # ID/Index
        unk3          = unpk_uint()  # ID?
        unk4          = unpk_float()
        scale         = unpk_vec3()
        meshCount     = unpk_uint()
        unk5          = unpk_uint()
        triStripCount = unpk_uint()
        vertexCount   = unpk_uint()
        unk6          = unpk_uint()
        unk7          = unpk_int()
        unk8          = unpk_uint()
        unk9          = unpk_uint()
        unk10         = unpk_uint()
        unk11         = unpk_uint()
        unk12         = unpk_int()

        unkLength     = unpk_uint()

        bboxLowest    = unpk_vec3() # Bounding Box
        bboxHighest   = unpk_vec3()

        if unk0 == 1:
            unk13 = unpk_uint()
        elif unk0 == 2:
            unk13 = unpk_vec3()

        entryCount    = unpk_int()
        faceCount     = unpk_int()
        unk14         = unpk_int()

        #print(hex(currOffset)[2:])

        if unk0 != 1:
            diffType += f"({hex(currOffset)[2:]}, Type: {unk0:2}, Index: {unk2:4}, Unk3: {unk3:2})\n"

        # to only import different model types indent everything that follows:

        mdlBboxName = f"mdl.{i}"
        create_bounds(mdlBboxName, bboxLowest, bboxHighest)
        mdlBboxObj  = bdata.objects[mdlBboxName]

        mdlBboxObj["00 Address: 0x"]     = hex(currOffset)[2:]
        mdlBboxObj["01 Length:"]         = totalLength # size in bytes
        mdlBboxObj["02 Type:"]           = unk0
        mdlBboxObj["03 Unk:"]            = unk1
        mdlBboxObj["04 Unk:"]            = unk2
        mdlBboxObj["05 Unk:"]            = unk3
        mdlBboxObj["06 Unk:"]            = unk4
        mdlBboxObj["07 Scale:"]          = scale
        mdlBboxObj["08 Mesh Count:"]     = meshCount
        mdlBboxObj["09 Unk:"]            = unk5
        mdlBboxObj["10 TriStrip Count:"] = triStripCount
        mdlBboxObj["11 Vertex Count:"]   = vertexCount
        mdlBboxObj["12 Unk  6:  "]       = unk6
        mdlBboxObj["13 Unk  7:  "]       = unk7
        mdlBboxObj["14 Unk  8:  "]       = unk8
        mdlBboxObj["15 Unk  9:  "]       = unk9
        mdlBboxObj["16 Unk 10:"]         = unk10
        mdlBboxObj["17 Unk 11:"]         = unk11
        mdlBboxObj["18 Unk 12:"]         = unk12


        mdlBboxObj["19 Unk Length:"]     = unkLength

        mdlBboxObj["20 Bbox Lowest:"]    = bboxLowest
        mdlBboxObj["21 Bbox Highest:"]   = bboxHighest

        mdlBboxObj["22 Unk 13:"]         = unk13

        mdlBboxObj["23 Entry Count:"]    = entryCount
        mdlBboxObj["24 Face Count:"]     = faceCount 
        mdlBboxObj["25 Unk 14:"]         = unk14     





    print(diffType)


    timeEnd = time.time()
    print(f"\nFINISHED ({time.localtime().tm_hour}:{time.localtime().tm_min})\nTime taken {round(timeEnd-timeStart, 4)}s")

    f.close()


def unpk_int():
    return struct.unpack(en+'i', f.read(4))[0]


def unpk_uint_at(offset):
    f.seek(offset) # f.seek(offset,0)
    return struct.unpack(en+'I', f.read(4))[0]

def unpk_uint():
    return struct.unpack(en+'I', f.read(4))[0]

def unpk_float():
    return struct.unpack(en+'f', f.read(4))[0]

def unpk_vec3():
    return Vector(struct.unpack(en+'fff', f.read(12)))






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
