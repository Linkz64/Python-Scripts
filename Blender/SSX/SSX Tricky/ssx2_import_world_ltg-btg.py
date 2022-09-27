import bpy
import struct
import mathutils

import time

bdata = bpy.data
collec = bpy.context.collection

timeStart = time.time() # start timer
print(f"TIME STARTED {time.localtime().tm_hour}:{time.localtime().tm_min}")

def read_bounds():

    filePath = "G:/Emulated/Playstation 2/Games/SSX Tricky/data/models/"
    fileName = "gari"+".ltg"
    f = open(filePath+"/"+fileName, 'rb')

    en = "<"

    f.seek(0x3,  0)
    (enByte,) = struct.unpack('B', f.read(1))

    if enByte == 1:
        en = ">"


    worldBounds = []
    for i in range(3):
        wb_xyz  = struct.unpack(en+'fff', f.read(12))
        worldBounds.append(wb_xyz)

    print(worldBounds)

    create_all("bbox_world", worldBounds[0], worldBounds[1], worldBounds[2])

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

        firstBounds = [(0,0,0)]*3
        for j in range(3):
            firstBounds[j]  = struct.unpack(en+'fff', f.read(12))

        firstExtras = struct.unpack(en+'I'*12, f.read(4*12))
    
        #create_all(f"bbox_{i}_a", firstBounds[0], firstBounds[1], firstBounds[2])
        create_bounds(f"bbox_{i}_a", firstBounds[0], firstBounds[1])

        print(f"\nbbox_{i}_a    Ends:{hex(f.tell())}    Values:\n{firstBounds}\n{firstExtras}\n")


        for j in range(gridBoxCount):

            secondBounds = [(0,0,0)]*3
            for k in range(3):
                secondBounds[k] = struct.unpack(en+'fff', f.read(4*3))

            secondExtras = struct.unpack(en+'I'*10, f.read(4*10))
    
            #create_all(f"bbox_b_{i}_{j}", secondBounds[0], secondBounds[1], secondBounds[2])
            create_bounds(f"bbox_{i}_b_{j}", secondBounds[0], secondBounds[1])
    
            print(f"bbox_{i}_b_{j}    Ends:{hex(f.tell())}    Values:\n{secondBounds}\n{secondExtras}")
    
    
    timeEnd = time.time()
    print(f"\nFINISHED ({time.localtime().tm_hour}:{time.localtime().tm_min})\nTime taken {round(timeEnd-timeStart, 4)}s")

    f.close()



def clear_list(messyList): # removes 0's from list
    clearedList = []
    for i in range(len(messyList)):
        for j in range(len(messyList[0])): # remove null offsets
            if messyList[i][j] > 0:
                clearedList.append(messyList[i][j])
    return clearedList

def create_empty(name, pos): # create empty object
    empty = bdata.objects.new(name, None) # Object instances
    collec.objects.link(empty)
    empty.empty_display_type = 'ARROWS'
    empty.empty_display_size = 250
    empty.show_name = True
    empty.location = pos

def create_bounds(name, pos1, pos2): # create just bounds

    mesh = bdata.meshes.new(name)
    obj = bdata.objects.new(name, mesh)
    collec.objects.link(obj)
    mesh.from_pydata([pos1, pos2], [], [])
    obj.display_type = 'BOUNDS'

def create_all(name, pos0, pos1, pos2): # create bounds with 3rd point as object origin

    mesh = bdata.meshes.new(name)
    obj = bdata.objects.new(name, mesh)
    collec.objects.link(obj)
    mesh.from_pydata([ pos0, pos1 ], [], [])
    obj.display_type = 'BOUNDS'

    bpy.context.scene.cursor.location = pos2        # moves cursor to pos0
    obj.select_set(True)                            # selects object
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR') # sets object origin to cursor
    bpy.context.scene.cursor.location = (0,0,0)     # moves cursor to world origin
    obj.select_set(False)                           # deselects object



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


run_wout_update(read_bounds)
