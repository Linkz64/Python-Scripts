import bpy
import struct
import time

bdata = bpy.data
collec = bpy.context.collection

timeStart = time.time() # start timer
print(f"TIME STARTED {time.localtime().tm_hour}:{time.localtime().tm_min}")


filePath = "G:/Emulated/Playstation 2/Games/SSX Tricky/data/models/"
fileName = "snow"
fileSuff = "ltg"

scaleMult = 100



def export_bounds():

    f = open(filePath+"/"+fileName+"."+fileSuff, 'r+b')

    en = "<"

    f.seek(0x3, 0)
    (enByte,) = struct.unpack('B', f.read(1))

    if enByte == 1:
        en = ">"

    pack_write_bounds(f"{fileName}_bbox.world", f, en) # export world bounds

    f.seek(0x2C, 0)

    (offsetCount    ,) = struct.unpack(en+'I', f.read(4))
    (offsetListCount,) = struct.unpack(en+'I', f.read(4))

    f.seek(0x48, 0)

    (gridBoxCount    ,) = struct.unpack(en+'I', f.read(4)) # = 16
    (offsetListOffset,) = struct.unpack(en+'I', f.read(4)) # = 84
    (offsetListEnd   ,) = struct.unpack(en+'I', f.read(4))

    f.seek(offsetListOffset, 0)

    offsetListContainer = []
    for i in range(offsetListCount):

        offsetTuple = struct.unpack(en+'I'*offsetCount, f.read(4*offsetCount))
        offsetListContainer.append(offsetTuple)


    sortedOffsetList = clear_list(offsetListContainer)


    for i in range(len(sortedOffsetList)):

        f.seek(sortedOffsetList[i], 0)

        objName = f"{fileName}_bbox.a_{i}"

        pack_write_bounds(objName, f, en)

        f.seek(48, 1) # skip extras

        print(f"\n{objName}    Ends:{hex(f.tell())}    Values:\n")


        for j in range(gridBoxCount):

            obj2Name = f"{fileName}_bbox.b_{i}_{j}"

            pack_write_bounds(obj2Name, f, en)

            f.seek(40, 1) # skip extras
    
            print(f"{obj2Name}    Ends:{hex(f.tell())}    Values:\n")
    
    
    timeEnd = time.time()
    print(f"\nFINISHED ({time.localtime().tm_hour}:{time.localtime().tm_min})\nTime taken {round(timeEnd-timeStart, 4)}s")

    f.close()


def midpoint2(a, b):
    return (a + b)/ 2

def clear_list(messyList): # removes 0's from list
    clearedList = []
    for i in range(len(messyList)):
        for j in range(len(messyList[0])): # remove null offsets
            if messyList[i][j] > 0:
                clearedList.append(messyList[i][j])
    return clearedList


def pack_write_bounds(objName, file, endianess): # export bounds and calculated origin

    obj = bdata.objects[objName]
    vertices = obj.data.vertices
    
    verts = [obj.matrix_world @ vert.co for vert in vertices]

    for i in range(len(verts)):
        verts[i] *= scaleMult

    origin = midpoint2(verts[0], verts[1])


    file.write(struct.pack(endianess+'f'*6, *[ # write bounds
        verts[0][0],verts[0][1],verts[0][2],
        verts[1][0],verts[1][1],verts[1][2]
    ]))

    file.write(struct.pack(endianess+'f'*3, *[ # write origin
        origin[0],origin[1],origin[2]
    ]))
    
    #print(verts)
    #print(origin)

    #file.seek(0x24, 1)


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


run_wout_update(export_bounds)
