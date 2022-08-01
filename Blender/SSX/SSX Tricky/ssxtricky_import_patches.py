""" 
Blender script that imports surface patches from SSX Tricky's (Xbox) .XBD files as NURBS

Credits:
    SSX Tricky patch import code
        Linkz
    
    Original patch generate code 
        redits zeffii, feesta
        https://blender.stackexchange.com/a/8593
    
    Performance boost code
        scurest
        https://blender.stackexchange.com/questions/7358/python-performance-with-blender-operators

To do:
    - Add Blender file select
    - Fix problem where some patch edges have swapped control points
    - Place chunks of patches in collections
    - Implement UVs
    - Implement Materials

"""

import bpy
import time
import struct

timeStart = time.time()

xbd_folder_path = ("G:/Games/SSX Tricky/data/models/") # < path to folder containing a .xbd
xbd_file_name = "gari" # (WITHOUT ".xbd") Example: "gari"

xbdFilePath = (xbd_folder_path+"/"+xbd_file_name+".xbd")
fxbd = open(xbdFilePath, 'rb')


fxbd.seek(0x8, 0)
patchCount = struct.unpack('I', fxbd.read(4)) # uint32 patch count
patchCount = int(patchCount[0])
fxbd.seek(0x54, 0)
patchOffset = struct.unpack('I', fxbd.read(4)) # uint32 offset of raw control points
patchAddress = int(patchOffset[0])


#patchCount   = 1000          # custom amount
#patchAddress = 0x00          # custom address


fxbd.seek(patchAddress, 0)


def run_ops_without_view_layer_update(func):
    from bpy.ops import _BPyOpsSubModOp

    view_layer_update = _BPyOpsSubModOp._view_layer_update

    def dummy_view_layer_update(context):
        pass

    try:
        _BPyOpsSubModOp._view_layer_update = dummy_view_layer_update

        func()

    finally:
        _BPyOpsSubModOp._view_layer_update = view_layer_update



def add_patches():
    if patchCount > 0:
        for patches in range(patchCount):
        
            surface_data = bpy.data.curves.new('Patch', 'SURFACE')
            surface_data.dimensions = '3D'
        
            patchPoints = []
            for pp in range(16):
                x,y,z = struct.unpack('f'*3, fxbd.read(4*3)) #alternative: struct.unpack('fff', fxbd.read(12))
                #(unk, unk1) = struct.unpack('f'*2, fxbd.read(4*2))
                fxbd.seek(0x8, 1)
                patchPoints.append((x, y, z, -1.0))
                
            
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
            
            surface_object = bpy.data.objects.new(f'surface{patches}', surface_data)
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
    
            print(f"Patch: {patches+1:6} out of {patchCount:} imported.")
    
        
        fxbd.close()
    else:
        fxbd.close()
        print("\nPatch count is invalid. patchCount =", patchCount)
    

run_ops_without_view_layer_update(add_patches)


timeEnd = time.time()
print(f"\n\nFINISHED\nTime Taken: {round(timeEnd-timeStart, 6)}\n")