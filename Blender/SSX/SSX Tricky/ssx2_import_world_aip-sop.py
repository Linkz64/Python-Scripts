import os
import bpy
import time
import struct
from mathutils import Vector

bdata = bpy.data
bcontext = bpy.context
bscene = bcontext.scene

collecMain = bpy.context.collection # Active/selected collection


scale = 0.01 # 1.0 for SSX default. 0.01 for recommended resize. (Gets overridden by Blender File Browser)
createBounds = False
groupByType = True


timeStart = time.time() # start timer

print(f"\n\nScript Initiated at {time.localtime().tm_hour}:{time.localtime().tm_min}\n\n")


def read_file_data(context, filepath, scaleNew, enable_grouping, enable_bbox):

    global scale
    global createBounds
    global groupByType

    scale = scaleNew
    createBounds = enable_bbox
    groupByType = enable_grouping

    input_directory, input_extension = os.path.splitext(filepath) # split directory and file extension
    input_basename = os.path.basename(input_directory) # extract file name only
    fileSuff = input_extension[1:] # remove dot "." from file extension 


    f = open(filepath, 'rb')


    f.seek(0x8, 0)

    pathA_Offset = struct.unpack('I', f.read(4))[0] # Relative to 0x10 (decimal 16)
    pathB_Offset = struct.unpack('I', f.read(4))[0]

    pathA_Count = struct.unpack('I', f.read(4))[0]
    #pathA_Count = 1 # Custom A count


    f.seek(0x30, 0) # Path type A
    

    if groupByType:
        newColl = collectionGrouping(f"{fileSuff}_A")
    else:
        newColl = collecMain


    for a in range(pathA_Count): # Path type A

        pathA_Name = f"{fileSuff}_A_{a+1}"

        print(f"{pathA_Name}   {hex(f.tell())}")

        pathA_unkVals = struct.unpack('I'*7, f.read(4*7))

        pathA_Vals = unpack_and_create_paths(f, pathA_Name, newColl) # file buffer, path object name, Blender collection



    f.seek(pathB_Offset+16, 0) # path type B offset + skip file header

    pathB_HeaderVls = struct.unpack('I'*2, f.read(4*2)) # some count and byte length
    pathB_Count  = struct.unpack('I', f.read(4))[0]
    pathB_Unk    = struct.unpack('I', f.read(4))[0]

    #pathB_Count = 0 # Custom B count


    if groupByType:
        newColl = collectionGrouping(f"{fileSuff}_B")
    else:
        newColl = collecMain


    for b in range(pathB_Count): # Path type B

        pathB_Name = f"{fileSuff}_B_{b+1}"

        print(f"{pathB_Name}   {hex(f.tell())}")

        pathB_unkVals = struct.unpack('I'*3, f.read(4*3))
        pathB_unkVal  = struct.unpack('f', f.read(4))[0]


        pathB_Vals = unpack_and_create_paths(f, pathB_Name, newColl)


    f.close() # Close file

    print(f"\n\nScript finished.\nTime Taken: {round(time.time()-timeStart, 6)}s\n")

    return {'FINISHED'}




def recurLayerCollection(layerColl, collName): # check for recurring collection
    found = None
    if (layerColl.name == collName):
        return layerColl
    for layer in layerColl.children:
        found = recurLayerCollection(layer, collName)
        if found:
            return found

def collectionGrouping(name): # name of new collection

    collecName = f"{name}"

    newCollec = bpy.data.collections.get(collecName)

    if newCollec is None: # if it doesn't exist create it
        newCollec = bdata.collections.new(collecName)

    if not bscene.user_of_id(newCollec): # if not in scene/layer bring it
        collecMain.children.link(newCollec)

    # excluding/disabling
    layer_collection = bpy.context.view_layer.layer_collection 
    recurLC = recurLayerCollection(layer_collection, collecName)
    recurLC.exclude = True

    return newCollec



def unpack_and_create_paths(f, name, newColl):

    curAddress = str(hex(f.tell()+8))

    pathPoints_Count = struct.unpack('I', f.read(4))[0]
    unk2_Count = struct.unpack('I', f.read(4))[0]
    
    pathPos = Vector(struct.unpack('fff', f.read(12))) * scale # Object Origin
    bboxMin = Vector(struct.unpack('fff', f.read(12))) * scale # Bounding box min (Lowest XYZ)
    bboxMax = Vector(struct.unpack('fff', f.read(12))) * scale # Bounding box max (Highest XYZ)


    pathPoints = []

    for i in range(pathPoints_Count):
        tempVector = Vector(struct.unpack('fff', f.read(12)))
        tempMultiplier = struct.unpack('f', f.read(4))[0] * scale

        # vector3 * distance gives point position (relative to parent)
        pathPoints.append(tempVector * tempMultiplier)


    unk2_List = []
    for i in range(unk2_Count):
        unk2_List.append(
             (
             struct.unpack('II', f.read(8)),
             struct.unpack('ff', f.read(8)) # Probably for a box or another path
            )
        )


    # create path object
    create_empty_better(name, pathPos, 250, 'CUBE')
    newColl.objects.link(bdata.objects[name])

    # create testing bounding box
    if createBounds:
        bboxSuff = '_bbox'
        create_bbox(name+bboxSuff, bboxMin, bboxMax)
        #bdata.objects[name+bboxSuff].parent = bdata.objects[name]
        newColl.objects.link(bdata.objects[name+bboxSuff])


        #bdata.objects[name+bboxSuff].location = pathPos


    # create path points
    inc = 0 # increment
    for point in pathPoints:

        pointName = f"{name}_point.{inc}"

        if inc == 0:
            create_empty(pointName, point)
            bdata.objects[pointName].parent = bdata.objects[name]

        else:
            create_empty(pointName, point)
            bdata.objects[pointName].parent = bdata.objects[f"{name}_point.{inc-1}"]

        newColl.objects.link(bdata.objects[pointName])

        inc += 1

    # add custom properties
    bdata.objects[name]["Address: 0x"] = curAddress[2:]



def create_empty_better(name, pos, display_size, display_type): # create empty object
    empty = bdata.objects.new(name, None)
    #collecMain.objects.link(empty)
    empty.empty_display_size = display_size * scale
    empty.empty_display_type = display_type
    empty.show_name = False
    empty.location = pos

def create_empty(name, pos): # create empty object
    empty = bdata.objects.new(name, None)
    #collecMain.objects.link(empty)
    empty.empty_display_type = 'SPHERE'
    empty.empty_display_size = 150 * scale
    empty.show_name = False
    empty.location = pos

def create_bbox(name, pos1, pos2): # create just bounds
    mesh = bdata.meshes.new(name)
    obj = bdata.objects.new(name, mesh)
    #collecMain.objects.link(obj)
    mesh.from_pydata([[pos1[0], pos1[1], pos1[2]], [pos2[0], pos2[1], pos2[2]]], [[0, 1]], [])
    obj.display_type = 'BOUNDS'

def create_bbox_all(name, pos0, pos1, pos2): # create bounds with pos0 as object origin (Can't use this if a collection is disabled/excluded)
    mesh = bdata.meshes.new(name)
    obj = bdata.objects.new(name, mesh)
    #collecMain.objects.link(obj)
    mesh.from_pydata([[pos1[0], pos1[1], pos1[2]], [pos2[0], pos2[1], pos2[2]]], [], [])
    obj.display_type = 'BOUNDS'

    bpy.context.scene.cursor.location = pos0        # moves cursor to pos0
    obj.select_set(True)                            # selects object
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR') # sets object origin to cursor
    bpy.context.scene.cursor.location = (0,0,0)     # moves cursor to world origin
    #bpy.ops.view3d.snap_cursor_to_center()         # moves cursor to world origin
    obj.select_set(False)                           # deselects object





from bpy_extras.io_utils import ImportHelper # ImportHelper is a helper class, defines filename and...
from bpy.props import StringProperty, FloatProperty, BoolProperty, IntProperty #... invoke() function which calls the file selector.
from bpy.types import Operator

class ImportPathData(Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "import_paths.path_data"
    bl_label = "Import aip/sop"


    filter_glob: StringProperty(
        default="*.aip;*.sop",
        options={'HIDDEN'}, # Hide other file extensions
        maxlen=255, # Max name length
    )

    scaleNew: FloatProperty(
        name="Scale",
        description="Recommended default: 0.01 \nSSX default: 1",
        default = 0.01,
        min     = 0.0,
        max     = 2.0
    )

    enable_grouping: BoolProperty(
        name="Group by Type",
        description="Enable or Disable grouping by type.",
        default=True,
    )

    enable_bbox: BoolProperty(
        name="Bounding Boxes",
        description="Enable or Disable bounding box importing.",
        default=False,
    )


    def execute(self, context):
        return read_file_data(context, self.filepath, self.scaleNew, self.enable_grouping, self.enable_bbox)



def register():
    bpy.utils.register_class(ImportPathData)

def unregister():
    bpy.utils.unregister_class(ImportPathData)
    
if __name__ == "__main__":
    register()
    bpy.ops.import_paths.path_data('INVOKE_DEFAULT') # test call
