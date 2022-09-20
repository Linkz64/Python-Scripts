""" 
Blender (2.92+) script that imports surface patches from SSX Tricky's files as NURBS
Supported file formats: .pbd (PS2), .xbd (Xbox), .nbd (GameCube)

Credits:
    SSX Tricky patch import code
        Linkz - https://github.com/Linkz64

    Decoding SSX patch points
        Archy - https://github.com/GlitcherOG
        Kris  - https://github.com/Kris2ffer
    
    Original Blender patch object code
        redits zeffii, feesta - https://blender.stackexchange.com/a/8593
    
    Performance boost code
        scurest - https://blender.stackexchange.com/questions/7358/python-performance-with-blender-operators


How to use:
    - Load this in Blender's "Scripting" tab
    - Optional: Open Terminal to see progress and errors (Window > Toggle System Console)
    - Run script
    - Optional: Set custom properties
    - Choose and Import file


To do:
    - Fix problem where some patch edges have swapped control points
    - Group patches in collections (Sort them based on type or name prefix)
    - Implement UVs (Currently not possible)
    - Implement Materials and Textures
    - Import custom properties (Name, Texture ID, Surface type, etc)
    - Disable count input in file browser if use_count is False

"""

import bpy
import time
import struct
import mathutils

bdat = bpy.data
vec  = mathutils.Vector
collec = bpy.context.collection


timeStart = time.time() # start timer

print(f"\n\nExporter Script Initiated {time.localtime().tm_hour}:{time.localtime().tm_min}\n\n")


def read_file_data(context, filepath, scale, use_count, count):
    fbd = open(filepath, 'rb') # rb = read binary, wb = write binary, r+b = write/read binary advanced
    
    fbd.seek(0x3, 0)
    consVer = struct.unpack('B', fbd.read(1))
    consVer = int(consVer[0])
    
    
    if  consVer == 1: # PLAYSTATION 2
    
        fbd.seek(0x8, 0)
        patchCount = struct.unpack('I', fbd.read(4)) # uint32 patch count
        patchCount = int(patchCount[0])
        fbd.seek(0x44, 0)
        patchOffset  = struct.unpack('I', fbd.read(4)) # uint32 offset of processed control points
        patchAddress = int(patchOffset[0])
    
    elif consVer == 2: # XBOX
    
        fbd.seek(0x8, 0)
        patchCount = struct.unpack('I', fbd.read(4))
        patchCount = int(patchCount[0])
        fbd.seek(0x54, 0)
        patchOffset  = struct.unpack('I', fbd.read(4)) # uint32 offset of raw control points
        patchAddress = int(patchOffset[0])
    
    elif consVer == 3: # GAMECUBE

        en = ">" # endianness = big (Big Endian byte order)
    
        fbd.seek(0x8, 0)
        patchCount = struct.unpack('>I', fbd.read(4))
        patchCount = int(patchCount[0])
        fbd.seek(0x44, 0)
        patchOffset  = struct.unpack('>I', fbd.read(4)) # uint32 offset of processed control points
        patchAddress = int(patchOffset[0])
    
    else:
        print(f"ERROR: Invalid platform. 3rd byte should be 1, 2 or 3.")
        fbd.close()
    

    if   use_count and count < patchCount:
        patchCount = count

    elif use_count and count > patchCount:
        print(f"\nERROR: Custom patch count exceeds the number of patches in the file!")
        fbd.close()
        return {'FINISHED'}

    pchScale = scale # Scale division
    
    processedPoints = [vec((0.0, 0.0, 0.0))]*16
    processedPointsW = [1.0]*16
    
    
    def import_patches_ps2(): # PLAYSTATION 2
        try:
            fbd.seek(patchAddress, 0) # jump to start of patches

            for pch in range(patchCount): # go through patches
    
                fbd.seek(0x50, 1) # skip UVs


                for pp in range(16): # unpack points
                    x,y,z,w = struct.unpack('ffff', fbd.read(16))

                    processedPoints[ -pp+15] = mathutils.Vector((x / pchScale, y / pchScale, z / pchScale))
                    processedPointsW[-pp+15] = w

                    #print(x,y,z)

                    #patchPoints.append(mathutils.Vector((x/pchScale, y/pchScale, z/pchScale, 0.0)))


                #print(processedPoints)

                create_patch_obj(decode_patch_points(), "Patch"+str(pch), pch)
    
                fbd.seek(0x70, 1) # skip extra
    
                print(f"Patch: {pch+1:6} out of {patchCount:} imported.")
        
            fbd.close()

        except Exception as e:

            print(f"\nPatch: {pch+1:6} out of {patchCount:} failed.\n {e}")
            
            fbd.close()
    
    
    def import_patches_xbx(): # XBOX
        try:
            fbd.seek(patchAddress, 0)

            for pch in range(patchCount): # go through patches
    
                patchPoints = []
                for pp in range(16): # unpack points
                    x,y,z = struct.unpack('fff', fbd.read(12))
                    #print(x,y,z)
                    #print(f"{round(x, 4), round(y, 4), round(z, 4)}")
                    fbd.seek(0x8, 1) # or unpack extras (unk, unk1) = struct.unpack('f'*2, fbd.read(4*2))
                    patchPoints.append((x/pchScale, y/pchScale, z/pchScale, 1.0))
                
                create_patch_obj(patchPoints, "Patch"+str(pch), pch)
                #create_patch_obj(sort_d(patchPoints), "Patch"+str(pch), pch)
                #create_patch_obj(sort_b(patchPoints), "Patch"+str(pch), pch)
    
                print(f"Patch: {pch+1:6} out of {patchCount:} imported.")
    
            
            fbd.close()

        except Exception as e:

            print(f"\nPatch: {pch+1:6} out of {patchCount:} failed.\n {e}")
            
            fbd.close()
    
    
    def import_patches_ngc(): # GAMECUBE
        try:

            fbd.seek(patchAddress, 0) # jump to start of patches

            for pch in range(patchCount): # go through patches
    
                fbd.seek(0x50, 1) # skip UVs
    
                for pp in range(16): # unpack points
                    x,y,z,w = struct.unpack('>ffff', fbd.read(16))

                    processedPoints[ -pp+15] = mathutils.Vector((x / pchScale, y / pchScale, z / pchScale))
                    processedPointsW[-pp+15] = w

    
                create_patch_obj(decode_patch_points(), "Patch"+str(pch), pch)
    
                fbd.seek(0x70, 1) # skip extra
    
                print(f"Patch: {pch+1:6} out of {patchCount:} imported.    {hex(fbd.tell())}")
        
            
            fbd.close()

        except Exception as e:

            print(f"\nPatch: {pch+1:6} out of {patchCount:} failed.\n {e}")
            
            fbd.close()
    
    
    
    
    
    # UTILITIES
    
    
    def tell_hex():
        return hex(fbd.tell())
    
    def midpoint2(a, b):
        return (a + b)/ 2
    
    def midpoint4(a, b, c, d):
        e = (a + b)/2
        f = (c + d)/2
        return midpoint2(e,f)
    
    def sum_vectors(p): # Sum List of Vectors
        vec = mathutils.Vector((0.0, 0.0, 0.0, 0.0))
        for i in range(len(p)):
            vec += p[i]
        return vec
    
    def sort_a(r):
        a = [r[3], r[7], r[11], r[15],
             r[2], r[6], r[10], r[14], 
             r[1], r[5], r[ 9], r[13],
             r[0], r[4], r[ 8], r[12]]
        return a
    
    def sort_b(r):
        b = [r[ 0], r[ 4], r[ 8], r[12],
             r[ 1], r[ 5], r[ 9], r[13], 
             r[ 2], r[ 6], r[10], r[14],
             r[ 3], r[ 7], r[11], r[15]]
        return b
    
    def sort_c(r):
        c = [r[12], r[ 8], r[ 4], r[ 0],
             r[13], r[ 9], r[ 5], r[ 1], 
             r[14], r[10], r[ 6], r[ 2],
             r[15], r[11], r[ 7], r[ 3]]
        return c

    def sort_d(r):
        c = [r[15], r[11], r[ 7], r[ 3],
             r[14], r[10], r[ 6], r[ 2], 
             r[13], r[ 9], r[ 5], r[ 1],
             r[12], r[ 8], r[ 4], r[ 0]]
        return c

    
    def proc_to_mid_eq1(a, b,                   processedPoints, midTablePoints):
        return processedPoints[a] / 3 + midTablePoints[b]

    def proc_to_mid_eq2(a, b, midA,             processedPoints, midTablePoints):
        return (processedPoints[a] + processedPoints[b]) / 3 + midTablePoints[midA]

    def proc_to_mid_eq3(a,    midA, midB, midC, processedPoints, midTablePoints):
        return processedPoints[a] + processedPoints[midA] + processedPoints[midB] + processedPoints[midC]


    def mid_to_raw_eq1(a, b,                   midTablePoints, rawPoints):
        return midTablePoints[a] / 3 + rawPoints[b]

    def mid_to_raw_eq2(a, b, midA,             midTablePoints, rawPoints):
        return (midTablePoints[a] + midTablePoints[b]) / 3 + rawPoints[midA]

    def mid_to_raw_eq3(a,    midA, midB, midC, midTablePoints):
        return midTablePoints[a] + midTablePoints[midA] + midTablePoints[midB] + midTablePoints[midC]
    
    
    
    def decode_patch_points():

        midTablePoints  = [vec((0.0, 0.0, 0.0))]*16
        rawPoints       = [vec((0.0, 0.0, 0.0))]*16


        midTablePoints[ 0] = processedPoints[0]
        midTablePoints[ 1] = proc_to_mid_eq1( 1,  0,         processedPoints, midTablePoints)
        midTablePoints[ 2] = proc_to_mid_eq2( 2,  1,  1,     processedPoints, midTablePoints)
        midTablePoints[ 3] = proc_to_mid_eq3( 3,  2,  1,  0, processedPoints, midTablePoints)

        midTablePoints[ 4] = processedPoints[4]
        midTablePoints[ 5] = proc_to_mid_eq1( 5,  4,         processedPoints, midTablePoints)
        midTablePoints[ 6] = proc_to_mid_eq2( 6,  5,  5,     processedPoints, midTablePoints)
        midTablePoints[ 7] = proc_to_mid_eq3( 7,  6,  5,  4, processedPoints, midTablePoints)

        midTablePoints[ 8] = processedPoints[8]
        midTablePoints[ 9] = proc_to_mid_eq1( 9,  8,         processedPoints, midTablePoints)
        midTablePoints[10] = proc_to_mid_eq2(10,  9,  9,     processedPoints, midTablePoints)
        midTablePoints[11] = proc_to_mid_eq3(11, 10,  9,  8, processedPoints, midTablePoints)

        midTablePoints[12] = processedPoints[12]
        midTablePoints[13] = proc_to_mid_eq1(13, 12,         processedPoints, midTablePoints)
        midTablePoints[14] = proc_to_mid_eq2(14, 13, 13,     processedPoints, midTablePoints)
        midTablePoints[15] = proc_to_mid_eq3(15, 14, 13, 12, processedPoints, midTablePoints)


        rawPoints[ 0] = midTablePoints[0]
        rawPoints[ 1] = midTablePoints[1]
        rawPoints[ 2] = midTablePoints[2]
        rawPoints[ 3] = midTablePoints[3]

        rawPoints[ 4] = mid_to_raw_eq1( 4,  0,         midTablePoints, rawPoints)
        rawPoints[ 5] = mid_to_raw_eq1( 5,  1,         midTablePoints, rawPoints)
        rawPoints[ 6] = mid_to_raw_eq1( 6,  2,         midTablePoints, rawPoints)
        rawPoints[ 7] = mid_to_raw_eq1( 7,  3,         midTablePoints, rawPoints)

        rawPoints[ 8] = mid_to_raw_eq2( 8,  4,  4,     midTablePoints, rawPoints)
        rawPoints[ 9] = mid_to_raw_eq2( 9,  5,  5,     midTablePoints, rawPoints)
        rawPoints[10] = mid_to_raw_eq2(10,  6,  6,     midTablePoints, rawPoints)
        rawPoints[11] = mid_to_raw_eq2(11,  7,  7,     midTablePoints, rawPoints)

        rawPoints[12] = mid_to_raw_eq3(12,  8,  4,  0, midTablePoints)
        rawPoints[13] = mid_to_raw_eq3(13,  9,  5,  1, midTablePoints)
        rawPoints[14] = mid_to_raw_eq3(14, 10,  6,  2, midTablePoints)
        rawPoints[15] = mid_to_raw_eq3(15, 11,  7,  3, midTablePoints)



        for i in range(16):
            rawPoints[i] = vec((rawPoints[i][0], rawPoints[i][1], rawPoints[i][2], 1.0))

    
        #print(rawPoints)


        #rawPoints = sort_b(rawPoints)
    
        return rawPoints
    
    
    def create_patch_obj(patchPoints, name, increment): # List of xyzw values, Name of patch object, Current loop increment value
        surface_data = bpy.data.curves.new(f"Patch", 'SURFACE')
        surface_data.dimensions = '3D'
        
        # set points per segments (U * V)
        for i in range(0, 16, 4):
            spline = surface_data.splines.new(type='NURBS')
            spline.points.add(3)  # already has a default vector
            spline.use_endpoint_u = True
            spline.use_endpoint_v = True
            spline.resolution_u = 2
            spline.resolution_v = 2
    
            for p, new_co in zip(spline.points, patchPoints[i:i+4]):
                p.co = new_co
    
        surface_object = bpy.data.objects.new(name, surface_data)
        bpy.context.collection.objects.link(surface_object)
        
        splines = surface_object.data.splines
        for s in splines:
            for p in s.points:
                p.select = True
    
        bpy.context.view_layer.objects.active = surface_object
        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.curve.make_segment()
        bpy.context.object.data.splines[0].order_u = 4
        bpy.context.object.data.splines[0].order_v = 4
    
    
        bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.context.active_object.select_set(False)
    
    
    
    
    
    
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
    
    
    
    
    
    # RUN FUNCTIONS
    
    if patchCount > 0:
        if   consVer == 1:
            run_wout_update(import_patches_ps2) # PLAYSTATION 2
        elif consVer == 2:
            run_wout_update(import_patches_xbx) # XBOX
        elif consVer == 3:
            run_wout_update(import_patches_ngc) # GAMECUBE
        else:
            fbd.close()
            print("ERROR: Invalid platform.")
    else:
        fbd.close()
        print("\nPatch count is invalid. patchCount =", patchCount)


    timeEnd = time.time()
    print(f"\n\nFINISHED\nTime Taken: {round(timeEnd-timeStart, 6)}s\n")

    return {'FINISHED'}








from bpy_extras.io_utils import ImportHelper # ImportHelper is a helper class, defines filename and...
from bpy.props import StringProperty, FloatProperty, BoolProperty, IntProperty #... invoke() function which calls the file selector.
from bpy.types import Operator


class ImportData(Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "import_patches.patch_data"
    bl_label = "Import Patches"


    filter_glob: StringProperty(
        default="*.pbd;*.xbd;*.nbd",
        options={'HIDDEN'}, # Hide other file extensions
        maxlen=255,  # Max name length
    )

    scale: FloatProperty(
        name="Scale Division",
        description="The bigger the value, the smaller the size.\nDefault   = 100\nSSX scale = 1",
        default = 100.0,
        min     = 1.0,
    )

    use_count: BoolProperty(
        name="Custom Patch Count",
        description="Enable or Disable custom patch count.",
        default=False,
    )

    count: IntProperty(
        name    = "Patch Count",
        default = 500,
        min     = 1,
        max     = 1000000,
        subtype = 'UNSIGNED'
    )

    #override_count: BoolProperty(
    #    name="Override Game Count",
    #    description="Allows you to decrease the number of patches rendered in game.\nCan only be lower than existing patch count",
    #    default=False,
    #)

    # bpy.props.IntProperty(name="Test")
    # filename, extension = os.path.splitext(self.filepath)

    def execute(self, context):

        return read_file_data(context, self.filepath, self.scale, self.use_count, self.count)


def register():
    bpy.utils.register_class(ImportData)

def unregister():
    bpy.utils.unregister_class(ImportData)


if __name__ == "__main__":
    register()
    
    bpy.ops.import_patches.patch_data('INVOKE_DEFAULT') # test call
