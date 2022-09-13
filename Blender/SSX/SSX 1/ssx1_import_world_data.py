""" 
Blender (2.93+) script that imports surface patches from SSX's (2000) wdf files as NURBS and Instances as Empties


Credits:
    SSX (2000) patch import code
        Linkz - https://github.com/Linkz64

    Decoded SSX patch points
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

To do:
    - Fix problem where some patch edges have swapped control points
    - Group patches in collections (Sort them based on type, name prefix or chunk index)
    - Import custom properties (Name, Texture ID, Surface type, etc)
    - Fix point r11
    - Disable count input in file browser if use_count is False
    - File browser options for importing instances, instance bounds, patches, etc
    - File browser option for custom address

"""

import bpy
import time
import struct
import mathutils

bdat = bpy.data
vec  = mathutils.Vector
collec = bpy.context.collection


timeStart = time.time() # start timer


def read_file_data(context, filepath, scale, use_count, count):
    fbd = open(filepath, 'rb') # rb = read binary, wb = write binary, r+b = write/read binary advanced
    

    chunkCount = 100

    if   use_count:
        chunkCount = count

    pchScale = scale # Scale division

    fbd.seek(0,0)
    
    def import_data():
        try:
            for i in range(chunkCount):
    
                fbd.seek(0x24, 1) # skip 9 floats
                (instCount, ) = struct.unpack('H', fbd.read(2))
                (patchCount,) = struct.unpack('H', fbd.read(2))
                (unk2Count, ) = struct.unpack('H', fbd.read(2))
                (unkxCount, ) = struct.unpack('H', fbd.read(2))
                (unk3Count, ) = struct.unpack('H', fbd.read(2))
                fbd.seek(0x2, 1) # skip FFFF
    
                fbd.seek(0x300, 1) # skip 16 pchRando points
    
                for j in range(unk3Count):
                    fbd.seek(0x4, 1)
    
                fbd.seek(-((unk3Count * 4) % -16), 1) # skip buffer padding/filler/gap if it exists
    
                for k in range(instCount):
                    mtx1 = struct.unpack('ffff', fbd.read(16))
                    mtx2 = struct.unpack('ffff', fbd.read(16))
                    mtx3 = struct.unpack('ffff', fbd.read(16))
                    mtx4 = struct.unpack('ffff', fbd.read(16))

                    create_empty(f"Chk{i}_Ins{k}", (mtx1, mtx2, mtx3, mtx4))
    
                    fbd.seek(0xD0, 1) # skip everything else
    

                #fbd.seek(patchAddress, 0) # jump to start of patches

                curPatchOffset = str(hex(fbd.tell()))[2:]
    
                for pch in range(patchCount): # go through patches
        
                    fbd.seek(0x50, 1) # skip UVs
        
                    patchPoints = [mathutils.Vector((0.0, 0.0, 0.0, 0.0))]
                    for pp in range(16): # unpack points
                        x,y,z,w = struct.unpack('ffff', fbd.read(16))
                        #fbd.seek(0x4, 1)
                        #print(f"{round(x, 4), round(y, 4), round(z, 4), w}")
                        patchPoints.append(mathutils.Vector((x/pchScale, y/pchScale, z/pchScale, 0.0)))
                    #print(patchPoints)
    
                    
                    create_patch_obj(decode_patch_points(patchPoints), f"Chk{i}_Pch{pch}", pch)
        
                    fbd.seek(0x70, 1) # skip extra
        
                    print(f"Patch: {pch+1:6} out of {patchCount:} imported.    {curPatchOffset}")

                
                for l in range(unkxCount):
                    fbd.seek(0x80, 1) # skip everything, 128 bytes
                    # unkxMtx1 = struct.unpack('ffff', fbd.read(16))


                for m in range(unk2Count):
                    fbd.seek(0x58, 1) # skip everything, 88 bytes
                    #fbd.seek(12, 1)
                    #unk2_Pos = struct.unpack('fff', fbd.read(12))


                fbd.seek(-((unk2Count * 88) % -16), 1)




                print(f"Next Chunk at {str(hex(fbd.tell()))[2:]}")

        except Exception as e:

            print(f"\nChunk: {i+1:6} out of {chunkCount:} failed.\n {e}")
            
            fbd.close()

                
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

    def create_empty(name, mtx): # name of empty, matrix 4x4
        empty = bdat.objects.new(name, None) # Object instances
        collec.objects.link(empty)
        empty.empty_display_type = 'ARROWS'
        empty.empty_display_size = 250
        #empty.show_name = True
        empty.matrix_world = mtx
        #empty.location = pos

    
    
    
    
    # IMPORTANT FUNCTIONS
    
    def decode_patch_points(p):
    
        # r = raw point, p = processed point
    
        r01 = p[16]                                                                      # 16
        r02 = p[16] + p[15]/3                                                            # 15
        r03 = r02 + (p[15] + p[14])/3                                                    # 14
        r04 = p[16] + p[15] + p[14] + p[13]                                              # 13
    
        r05 = p[16] + p[12] /3                                                           # 12
        r06 = p[16] + (p[15] + p[12] + p[11]/3 )/3                                       # 11
        r07 = r06 + (p[15] + p[14] + (p[11] + p[10])/3 )/3                               # 10
        r08 = r04 + (p[12] + p[11] + p[10] + p[9])/3                                     # 9
    
        r09 = r05 + (p[12] + p[8]) / 3                                                   # 8
        r10 = r06 + (p[12] + p[8] + (p[11] + p[7])/3 )/3                                 # 7
        r11 = r07 + (p[12] + p[8]/3 + (p[15]+p[11]+p[7])/3 + (p[14]+p[10]+p[6]/3) )/3    # 6
        r12 = (p[5]+p[9]+p[6]+p[10]+p[7]+p[11]+p[8]+p[12])/3 + r08                       # 5
    
        r13 = p[16] + p[12] + p[8] + p[4]                                                # 4
        r14 = r13 + (p[15] + p[11] + p[7] + p[3])/3                                      # 3
        r15 = (p[2] + p[3] + p[7] + p[11] + p[15] + p[14] + p[10] + p[6])/3 + r14        # 2
        r16 = sum_vectors(p)                                                             # 1
    

        r11 = midpoint4(r07, r15, r10, r12)
    
        r01[3]=r02[3]=r03[3]=r04[3]= 1.0
        r05[3]=r06[3]=r07[3]=r08[3]= 1.0
        r09[3]=r10[3]=r11[3]=r12[3]= 1.0
        r13[3]=r14[3]=r15[3]=r16[3]= 1.0
    
    
        procPoints = [r01, r02, r03, r04,
                      r05, r06, r07, r08,
                      r09, r10, r11, r12,
                      r13, r14, r15, r16]
    
        #procPoints = sort_b(procPoints)
    
        return procPoints
    
    
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
    
    
    
    
    
    
    def run_wout_update(func): # run without view update
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
    
    if chunkCount > 0:
        run_wout_update(import_data)
    else:
        fbd.close()
        print("\nChunk count is invalid. chunkCount =", chunkCount)


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
        default="*.wdf",
        options={'HIDDEN'}, # Hide other file extensions
        maxlen=255,  # Max name length
    )

    scale: FloatProperty(
        name="Scale Division",
        description="The bigger the value, the smaller the size.\nDefault   = 100\nSSX scale = 1",
        default = 1,
        min     = 1.0,
    )

    #address: IntProperty(
    #    name    = "Address",
    #    default = 1000,
    #    min     = 1,
    #    max     = 10000000,
    #    subtype = 'UNSIGNED'
    #)

    use_count: BoolProperty(
        name="Custom Chunk Count",
        description="Enable or Disable custom chunk count.",
        default=False,
    )

    count: IntProperty(
        name    = "Chunk Count",
        default = 100,
        min     = 1,
        max     = 10000000,
        subtype = 'UNSIGNED'
    )

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
