import bpy
import struct
from mathutils import Vector, Color, Matrix
from math import pi

import time

bdata = bpy.data
bcontext = bpy.context
bscene = bcontext.scene

collecMain = bcontext.collection

timeStart = time.time() # start timer
print(f"TIME STARTED {time.localtime().tm_hour}:{time.localtime().tm_min}")



filePath = "G:/Emulated/Playstation 2/Games/SSX Tricky/data/models/"
fileName = "snow"
fileSuff = "pbd" # ps2 = .pbd, xbox = xbd, ngc = nbd


scaleDiv = 100 # 100 for Blender resize, 1 for SSX default
createBounds = False
lightPower = 5
lightGrouping = 128 # must be power of 2 (…, 16, 32, 64, 128, 256, …)
groupByType = True



def recurLayerCollection(layerColl, collName):
    found = None
    if (layerColl.name == collName):
        return layerColl
    for layer in layerColl.children:
        found = recurLayerCollection(layer, collName)
        if found:
            return found

def collectionGrouping(name, i): # collection name, increment

    collName = f"{name}.{int(i / lightGrouping)+1}"

    newColl = bpy.data.collections.get(collName)

    if newColl is None: # if it doesn't exist create it
        newColl = bdata.collections.new(collName)

    if not bscene.user_of_id(newColl): # if not in scene/layer bring it
        collecMain.children.link(newColl)

    # excluding/disabling
    layer_collection = bpy.context.view_layer.layer_collection 
    recurLC = recurLayerCollection(layer_collection, collName)
    recurLC.exclude = True

    return newColl




def import_lights():

    f = open(filePath+"/"+fileName+"."+fileSuff, 'rb')


    f.seek(0x3, 0)
    (enByte,) = struct.unpack('B', f.read(1))

    en = "<"
    if enByte == 3: # 1 = ps2, 2 = xbox, 3 = ngc
        en = ">"


    f.seek(0x1C, 0)

    (lightCount ,) = struct.unpack(en+'I', f.read(4))

    f.seek(0x58, 0)

    (lightOffset,) = struct.unpack(en+'I', f.read(4))

    #lightCount = 257

    f.seek(lightOffset, 0)

    lightsWorld = []
    lightsPoint = []
    lightsSpot  = []

    for i in range(lightCount):


        curAddress = str(hex(f.tell()))

        (lightType,)   = struct.unpack(en+'I', f.read(4))
        (spriteScale,) = struct.unpack(en+'I', f.read(4))
        (unkFloat1,) = struct.unpack(en+'f', f.read(4))
        (unkInt1,)   = struct.unpack(en+'I', f.read(4))

        rgb          = struct.unpack(en+'fff', f.read(12)) # color (red, green, blue)
        lightVec     = struct.unpack(en+'fff', f.read(12)) # direction it's pointing
        xyz          = struct.unpack(en+'fff', f.read(12)) # location
        bboxPt1      = struct.unpack(en+'fff', f.read(12)) # bounding box point
        bboxPt2      = struct.unpack(en+'fff', f.read(12)) # bounding box point
        (unkFloat2,) = struct.unpack(en+'f', f.read(4))
        (unkInt2,)   = struct.unpack(en+'I', f.read(4))
        (unkFloat3,) = struct.unpack(en+'f', f.read(4))
        (unkInt3,)   = struct.unpack(en+'I', f.read(4))




        light_data = bpy.data.lights.new(name=f"point_{fileName}.{i}", type='POINT')
        light_data.color = rgb #Color(rgb)
        light_data.energy = lightPower
        light_data.shadow_soft_size = 1 # falloff radius


        light_object = bpy.data.objects.new(name=f"light_{fileName}.{i}", object_data=light_data)

        light_object.location = Vector(xyz)/scaleDiv
        light_object["Index"] = i
        light_object["Address: 0x"] = curAddress[2:] # [2:] removes first 2 characters "0x"
        light_object["Type"]  = lightType
        light_object["Scale"] = spriteScale
        light_object["Direction"] = lightVec
        light_object["UnkFloat1"] = unkFloat1
        light_object["unkFloat2"] = unkFloat2
        light_object["unkFloat3"] = unkFloat3
        light_object["UnkInt1"] = unkInt1
        light_object["unkInt2"] = unkInt2
        light_object["unkInt3"] = unkInt3


        if lightType == 3: # TYPE: Ambient
            light_object.data.energy = 0.04
            light_object.data.type   = 'SUN'
            light_object.data.use_shadow = False # Disable shadows
            if groupByType   == True:
                light_object.name = f"{fileName}_ambi.{i}"
                lightsWorld.append(light_object)
            elif groupByType == False:
                light_object.name = f"{fileName}.{i}_ambi"


        if lightType == 0: # TYPE: Directional
            light_object.data.energy = 0.08
            light_object.data.type   = 'SUN'

            if groupByType   == True:
                light_object.name = f"{fileName}_dire.{i}"
                lightsWorld.append(light_object)
            elif groupByType == False:
                light_object.name = f"{fileName}.{i}_dire"


        if lightType == 1: # TYPE: Spot
            light_object.data.type = "SPOT"
            light_object.data.spot_size  = pi #3.14  2.094395
            light_object.data.spot_blend = 1.0

            if groupByType   == True:
                light_object.name = f"{fileName}_spot.{i}"
                lightsSpot.append(light_object)
            elif groupByType == False:
                light_object.name = f"{fileName}.{i}_spot"


        if lightType == 2: # TYPE: Point
            light_object.data.type = "POINT" # already set to this but whatever
            light_object.data.energy = 100
            
            if groupByType   == True:
                light_object.name = f"{fileName}_point.{i}"
                lightsPoint.append(light_object)
            elif groupByType == False:
                light_object.name = f"{fileName}.{i}_point"


        if groupByType == False:
            if i % lightGrouping == 0:
                newColl = collectionGrouping(f"{fileName}_lights", i)
            newColl.objects.link(light_object)

        if createBounds:
            create_bounds(f"light_bounds_{fileName}.{i}", bboxPt1, bboxPt2)


    if groupByType: # == True:

        for i in range(len(lightsWorld)):
            if i % lightGrouping == 0:
                newColl = collectionGrouping(f"{fileName}_world", i)
            newColl.objects.link(lightsWorld[i])
    
        for i in range(len(lightsSpot)):
            if i % lightGrouping == 0:
                newColl = collectionGrouping(f"{fileName}_spot", i)
            newColl.objects.link(lightsSpot[i])
    
        for i in range(len(lightsPoint)):
            if i % lightGrouping == 0:
                newColl = collectionGrouping(f"{fileName}_point", i)
            newColl.objects.link(lightsPoint[i])

    
    timeEnd = time.time()
    print(f"\nFINISHED ({time.localtime().tm_hour}:{time.localtime().tm_min})\nTime taken {round(timeEnd-timeStart, 4)}s")

    f.close()



def create_empty(name, pos): # create empty object
    empty = bdata.objects.new(name, None) # Object instances
    collection.objects.link(empty)
    empty.empty_display_type = 'ARROWS'
    empty.empty_display_size = 250
    empty.show_name = True
    empty.location = pos

def create_bounds(name, pos1, pos2): # create just bounds

    mesh = bdata.meshes.new(name)
    obj = bdata.objects.new(name, mesh)
    collection.objects.link(obj)
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


run_wout_update(import_lights)
