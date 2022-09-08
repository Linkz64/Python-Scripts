""" 
Blender (2.83+) script that imports surface patches from SSX Tricky's files as NURBS
Supported file formats: .pbd (PS2), .xbd (Xbox), .nbd (GameCube)

Credits:
    SSX Tricky patch import code
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
    - Change fbd_folder_path to a path containing a supported file
    - Change fbd_file_name to the file name
    - Change fbd_suffix to the format of your file
    - Optional: Open Terminal to see progress and errors (Window > Toggle System Console)
    - Run script


To do:
    - Add Blender file select
    - Fix problem where some patch edges have swapped control points
    - Group patches in collections (Sort them based on type or name prefix)
    - Implement Materials
    - Make it choose version depending on suffix or preferably header data
    - Import custom properties (Name, Texture ID, Surface type, etc)
    - Fix point r11
    - Import UVs (Currently not possible)

"""

import bpy
import time
import struct
import mathutils

bdat = bpy.data
vec  = mathutils.Vector
collec = bpy.context.collection


timeStart = time.time() # start timer


# path to folder containing a .*bd file
fbd_folder_path = "G:/SSX Tricky/Data/Models"
fbd_file_name   = "gari"
fbd_suffix      = "pbd"



fbdFilePath = (fbd_folder_path+"/"+fbd_file_name+"."+fbd_suffix)
fbd = open(fbdFilePath, 'rb') # rb = read binary, wb = write binary, r+b = write/read binary advanced



# Console Version  |  0 = ps2, 1 = xbx, 2 = ngc
if   fbd_suffix == "pbd":
    consVer = 0
    en      = "<" # Endianess (< Little, > Big)
elif fbd_suffix == "xbd":
    consVer = 1
    en      = "<"
elif fbd_suffix == "nbd":
    consVer = 2
    en      = ">"
else:
    print("Wrong file format")


if  consVer == 0: # PLAYSTATION 2

    fbd.seek(0x8, 0)
    patchCount = struct.unpack('I', fbd.read(4)) # uint32 patch count
    patchCount = int(patchCount[0])
    fbd.seek(0x44, 0)
    patchOffset  = struct.unpack('I', fbd.read(4)) # uint32 offset of processed control points
    patchAddress = int(patchOffset[0])

elif consVer == 1: # XBOX

    fbd.seek(0x8, 0)
    patchCount = struct.unpack('I', fbd.read(4))
    patchCount = int(patchCount[0])
    fbd.seek(0x54, 0)
    patchOffset  = struct.unpack('I', fbd.read(4)) # uint32 offset of raw control points
    patchAddress = int(patchOffset[0])

elif consVer == 2: # GAMECUBE

    fbd.seek(0x8, 0)
    patchCount = struct.unpack('>I', fbd.read(4))
    patchCount = int(patchCount[0])
    fbd.seek(0x44, 0)
    patchOffset  = struct.unpack('>I', fbd.read(4)) # uint32 offset of processed control points
    patchAddress = int(patchOffset[0])

else: 
    print("Invalid version")




#patchCount = 1000         # custom amount
#patchAddr  = 0x00         # custom address
pchScale   = 100 # Scale division




def import_patches_ps2(): # PLAYSTATION 2
    if patchCount > 0:
        try:

            fbd.seek(patchAddress, 0) # jump to start of patches

            for pch in range(patchCount): # go through patches
    
                fbd.seek(0x50, 1) # skip UVs
    
                patchPoints = [mathutils.Vector((0.0, 0.0, 0.0, 0.0))]
                for pp in range(16): # unpack points
                    x,y,z,w = struct.unpack('ffff', fbd.read(16))
                    #fbd.seek(0x4, 1)
                    #print(f"{round(x, 4), round(y, 4), round(z, 4), w}")
                    patchPoints.append(mathutils.Vector((x/pchScale, y/pchScale, z/pchScale, 0.0)))
                #print(patchPoints)

                
                create_patch_obj(decode_patch_points(patchPoints), "Patch"+str(pch), pch)
    
                fbd.seek(0x70, 1) # skip extra
    
                print(f"Patch: {pch+1:6} out of {patchCount:} imported.")
        
            
            fbd.close()

        except Exception as e:

            print(f"\nPatch: {pch+1:6} out of {patchCount:} failed.\n {e}")
            
            fbd.close()

    else:
        
        print("\nPatch count is invalid. patchCount =", patchCount)

        fbd.close() # END



def import_patches_xbx(): # XBOX
    if patchCount > 0:
        try:

            fbd.seek(patchAddress, 0)

            for pch in range(patchCount): # go through patches
    
                patchPoints = []
                for pp in range(16): # unpack points
                    x,y,z = struct.unpack('fff', fbd.read(12))
                    #print(f"{round(x, 4), round(y, 4), round(z, 4)}")
                    fbd.seek(0x8, 1) # or unpack extras (unk, unk1) = struct.unpack('f'*2, fbd.read(4*2))
                    patchPoints.append((x/pchScale, y/pchScale, z/pchScale, 1.0))
                

                create_patch_obj(point_arrange_b(patchPoints), "Patch"+str(pch), pch)
    
                print(f"Patch: {pch+1:6} out of {patchCount:} imported.")
    
            
            fbd.close()

        except Exception as e:

            print(f"\nPatch: {pch+1:6} out of {patchCount:} failed.\n {e}")
            
            fbd.close()

    else:
        print("\nPatch count is invalid. patchCount =", patchCount)
        
        fbd.close() # END
        



def import_patches_ngc(): # GAMECUBE
    if patchCount > 0:
        try:

            fbd.seek(patchAddress, 0) # jump to start of patches

            for pch in range(patchCount): # go through patches
    
                print(f"\n\n\n{hex(fbd.tell())}\n")
    
                fbd.seek(0x50, 1) # skip UVs
    
                patchPoints = [mathutils.Vector((0.0, 0.0, 0.0, 0.0))]
                for pp in range(16): # unpack points
                    x,y,z,w = struct.unpack('>ffff', fbd.read(16))
                    #fbd.seek(0x4, 1)
                    #print(f"{round(x, 4), round(y, 4), round(z, 4), w}")
                    patchPoints.append(mathutils.Vector((x/pchScale, y/pchScale, z/pchScale, 0.0)))
                #print(patchPoints)
    
                create_patch_obj(decode_patch_points(patchPoints), "Patch"+str(pch), pch)
    
                fbd.seek(0x70, 1) # skip extra
    
                print(f"Patch: {pch+1:6} out of {patchCount:} imported.")
        
            
            fbd.close()

        except Exception as e:

            print(f"\nPatch: {pch+1:6} out of {patchCount:} failed.\n {e}")
            
            fbd.close()

    else:
        
        print("\nPatch count is invalid. patchCount =", patchCount)

        fbd.close() # END





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

def point_arrange_a(r):
    a = [r[3], r[7], r[11], r[15],
         r[2], r[6], r[10], r[14], 
         r[1], r[5], r[ 9], r[13],
         r[0], r[4], r[ 8], r[12]]
    return a

def point_arrange_b(r):
    b = [r[ 0], r[ 4], r[ 8], r[12],
         r[ 1], r[ 5], r[ 9], r[13], 
         r[ 2], r[ 6], r[10], r[14],
         r[ 3], r[ 7], r[11], r[15]]
    return b

def point_arrange_b(r):
    c = [r[12], r[ 8], r[ 4], r[ 0],
         r[13], r[ 9], r[ 5], r[ 1], 
         r[14], r[10], r[ 6], r[ 2],
         r[15], r[11], r[ 7], r[ 3]]
    return c





# IMPORTANT FUNCTIONS

def decode_patch_points(p): # EQUATIONS, CALCULATIONS, EXAGGERATIONS, THE LOT!

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

    """
    missing [maybe -(H5+(H4+H3/3)) or  or  or =E13+(E3+E4+E5+H3+H4+H5)/3]
    =H12+(B4+B5+(E3+E4+E5)/3+(H3+H4+H5/3))/3
    =H12+(B4+B5/3+(E3+E4+E5)/3+(H3+H4+H5/3))/3

    """

    #r11 = midpoint2(r07, r15)
    r11 = midpoint4(r07, r15, r10, r12)

    r01[3]=r02[3]=r03[3]=r04[3]= 1.0
    r05[3]=r06[3]=r07[3]=r08[3]= 1.0
    r09[3]=r10[3]=r11[3]=r12[3]= 1.0
    r13[3]=r14[3]=r15[3]=r16[3]= 1.0


    procPoints = [r01, r02, r03, r04,
                  r05, r06, r07, r08,
                  r09, r10, r11, r12,
                  r13, r14, r15, r16]

    procPoints = point_arrange_b(procPoints)

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

if patchCount > 0:
    if   consVer == 0:
        run_wout_update(import_patches_ps2) # PLAYSTATION 2
    elif consVer == 1:
        run_wout_update(import_patches_xbx) # XBOX
    elif consVer == 2:
        run_wout_update(import_patches_ngc) # GAMECUBE
    else:
        fbd.close()
        print("INVALID CONSOLE VER")
else:
    fbd.close()
    print("\nPatch count is invalid. patchCount =", patchCount)


timeEnd = time.time()
print(f"\n\nFINISHED\nTime Taken: {round(timeEnd-timeStart, 6)}s\n")
