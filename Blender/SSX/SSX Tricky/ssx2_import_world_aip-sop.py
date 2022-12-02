import bpy
import struct
from mathutils import Vector

bdata = bpy.data
collec = bpy.context.collection



class ImportObjectLocations(bpy.types.Operator):
    bl_idname = "object.importobjects"
    bl_label = "Import Objects"

    def execute(self, context):

        print("STARTED\n\n")


        filePath = "G:/Emulated/Playstation 2/Games/SSX Tricky/data/models/trick backup"
        fileName = "trick"
        fileSuff = "aip" # aip or sop
    
        scale = 0.01 # 1.0 for SSX default. 0.01 for Blender resize.

        f = open(filePath+"/"+fileName+"."+fileSuff, 'rb')


        f.seek(0x8, 0)

        pathA_Offset = struct.unpack('I', f.read(4))[0] # Relative to 0x10 (decimal 16)
        pathB_Offset = struct.unpack('I', f.read(4))[0]

        pathA_Count = struct.unpack('I', f.read(4))[0]
        #pathA_Count = 1 # Custom A count


        f.seek(0x30, 0)
        

        for a in range(pathA_Count): # Path type A

            pathA_Name = f"aip-sop_objA_{a+1}"

            print(f"{pathA_Name}   {hex(f.tell())}")

            pathA_unkVals = struct.unpack('I'*7, f.read(4*7))

            curAddress = str(hex(f.tell()+8))

            pathA_Vals = unpack_values(f)

            # create testing bounds
            create_all(pathA_Name, pathA_Vals[0]*scale, pathA_Vals[1]*scale, pathA_Vals[2]*scale)
            
            # add custom properties
            bdata.objects[pathA_Name]["Address: 0x"] = curAddress[2:]



        f.seek(pathB_Offset+16, 0) # path type B offset + skip file header

        pathB_HeaderVls = struct.unpack('I'*2, f.read(4*2)) # some count and byte length
        pathB_Count  = struct.unpack('I', f.read(4))[0]
        pathB_Unk    = struct.unpack('I', f.read(4))[0]

        #pathB_Count = 1 # Custom B count


        for b in range(pathB_Count): # Path type B

            pathB_Name = f"aip-sop_objB_{b+1}"

            print(f"{pathB_Name}   {hex(f.tell())}")

            pathB_unkVals = struct.unpack('I'*3, f.read(4*3))
            pathB_unkVal  = struct.unpack('f', f.read(4))[0]

            curAddress = str(hex(f.tell()+8))

            pathB_Vals = unpack_values(f)
            
            # create testing bounds
            create_all(pathB_Name, pathB_Vals[0]*scale, pathB_Vals[1]*scale, pathB_Vals[2]*scale)

            # add custom properties
            bdata.objects[pathB_Name]["Address: 0x"] = curAddress[2:]


        f.close() # Close file

        return{'FINISHED'}





def unpack_values(f):
    pathPoints_Count = struct.unpack('I', f.read(4))[0]
    unk2_Count = struct.unpack('I', f.read(4))[0]
    
    pathPos = Vector(struct.unpack('fff', f.read(12))) # Object Origin
    bboxMin = Vector(struct.unpack('fff', f.read(12))) # Bounding box min (Lowest XYZ)
    bboxMax = Vector(struct.unpack('fff', f.read(12))) # Bounding box max (Highest XYZ)


    pathPoints_Vectors = [] # Direction vectors
    pathPoints_Distances = [] # Distance multipliers (vector3 * distance gives relative position)

    for i in range(pathPoints_Count):
        pathPoints_Vectors.append( Vector(struct.unpack('fff', f.read(12))) )
        pathPoints_Distances.append( struct.unpack('f', f.read(4)) )


    unk2_List = []
    for i in range(unk2_Count):
        unk2_List.append(
             (
             struct.unpack('II', f.read(8)),
             struct.unpack('ff', f.read(8)) # probably for a box
            )
        )

    print(unk2_List)

    return pathPos, bboxMin, bboxMax



def create_empty(name, pos): # create empty object
    empty = bdata.objects.new(name, None) # Object instances
    collec.objects.link(empty)
    empty.empty_display_type = 'ARROWS'
    empty.empty_display_size = 250
    empty.show_name = True
    empty.location = pos

def create_bounds(name, pos1, pos2): # create just bounds

    coords = [[pos1[0], pos1[1], pos1[2]], [pos2[0], pos2[1], pos2[2]]]

    mesh = bdata.meshes.new(name)
    obj = bdata.objects.new(name, mesh)
    collec.objects.link(obj)

    mesh.from_pydata(coords, [[0, 1]], [])

    obj.display_type = 'BOUNDS'

def create_all(name, pos0, pos1, pos2): # create bounds with 1st point as object origin

    coords = [[pos1[0], pos1[1], pos1[2]], [pos2[0], pos2[1], pos2[2]]]

    mesh = bdata.meshes.new(name)
    obj = bdata.objects.new(name, mesh)
    collec.objects.link(obj)
    mesh.from_pydata(coords, [], [])
    obj.display_type = 'BOUNDS'

    bpy.context.scene.cursor.location = pos0        # moves cursor to pos0
    obj.select_set(True)                            # selects object
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR') # sets object origin to cursor
    bpy.context.scene.cursor.location = (0,0,0)     # moves cursor to world origin
    obj.select_set(False)                           # deselects object





def register():
    bpy.utils.register_class(ImportObjectLocations)

def unregister():
    bpy.utils.unregister_class(ImportObjectLocations)
    
if __name__ == "__main__":
    register()
    bpy.ops.object.importobjects() # test call
