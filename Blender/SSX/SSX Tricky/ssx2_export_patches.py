""" 
Blender (2.93+) script that exports surface patches into SSX Tricky's .*bd files

Credits:
    SSX Tricky patch export code
        Linkz - https://github.com/Linkz64

    Decoded SSX patch points
        Archy - https://github.com/GlitcherOG
        Kris  - https://github.com/Kris2ffer


How to use:
    - Load/Paste this in Blender's "Scripting" tab
    - Optional: Open Terminal to see progress and errors (Window > Toggle System Console)
    - Run script
    - Set custom properties
    - Choose and Export file


To do:
    - Nothing
"""
import os
import bpy
import time
import struct
import mathutils

bdat = bpy.data
vec  = mathutils.Vector

timeStart = time.time()

print(f"\n\nExporter Script Initiated {time.localtime().tm_hour}:{time.localtime().tm_min}\n\n")



def write_file_data(context, filepath, consVer, scale, use_count, count, override):



    #if this file exists check if version is matching
        #fbd.seek(0x3, 0)
        #consVer = struct.unpack('B', fbd.read(1))
        #consVer = int(consVer[0])


    bd_name, bd_suffix = os.path.splitext(filepath)
    print(f"{bd_name}\n")


    # Console/Platform  |  1 = ps2, 2 = xbx, 3 = ngc
    if   consVer == '1': # PLAYSTATION 2
        #en      = "<" # Endianess (< = Little, > = Big)
        ext = ".pbd"
        fbd = open(filepath+ext, 'r+b') # rb = read binary, wb = write binary, r+b = write/read binary advanced
        fbd.seek(0x8, 0)
        patchCount = struct.unpack('I', fbd.read(4)) # uint32 patch count
        patchCount = int(patchCount[0])
        fbd.seek(0x44, 0)
        patchOffset  = struct.unpack('I', fbd.read(4)) # uint32 offset of raw control points
        patchAddress = int(patchOffset[0])

    elif consVer == '2': # XBOX
        #en      = "<"
        ext = ".xbd"
        fbd = open(filepath+ext, 'r+b')
        fbd.seek(0x8, 0)
        patchCount = struct.unpack('I', fbd.read(4))
        patchCount = int(patchCount[0])
        fbd.seek(0x50, 0)
        patchOffset  = struct.unpack('I', fbd.read(4)) # uint32 offset of raw control points
        patchAddress = int(patchOffset[0])

    elif consVer == '3': # GAMECUBE
        #en      = ">"
        ext = ".nbd"
        fbd = open(filepath+ext, 'r+b')
        fbd.seek(0x8, 0)
        patchCount = struct.unpack('>I', fbd.read(4))
        patchCount = int(patchCount[0])
        fbd.seek(0x44, 0)
        patchOffset  = struct.unpack('>I', fbd.read(4)) # uint32 offset of processed control points
        patchAddress = int(patchOffset[0])
    else:
        print(f"ERROR: Invalid version.")
        fbd.close()


    # CUSTOM VARS

    if   use_count and count < patchCount: # if use_count is True and count is less than existing patch count
        patchCount = count

    elif use_count and count > patchCount:
        print(f"\nERROR: Custom patch count exceeds the number of patches in the file!")
        
        fbd.close()
        return {'CANCELLED'}

    elif override and count < patchCount:
        fbd.seek(0x8, 0)
        fbd.write(struct.pack("I", count))

    elif override and count > patchCount:
        print(f"\nWARNING: Patch count exceeds the number of patches in the file!")
        

    pchScale = scale      # scale multiplier

    patchObjName = "Patch"




    fbd.seek(patchAddress, 0)


    def export_patches_ps2(): # OVERRIDE PS2 PATCHES (SONY PLAYSTATION 2)

            patchPointLists = []
    
            for pch in range(patchCount):
            
                
    
                try:
                    
        
                    surface_object = bdat.objects[f"{patchObjName}{pch}"].data.splines
    
                    fbd.seek(0x50, 1) # placeholder skip UVs
        
    
                    pointsList = []
                    for s in surface_object:
                        for p in s.points:
                            #print(p.co)
                            pointsList.append(mathutils.Vector(
                                (p.co[0]*pchScale, p.co[1]*pchScale, p.co[2]*pchScale)))
                            #p.select = False
        
        
                    #pointsList = rearrange(pointsList)
                    pointProcList = process_patch_points(pointsList)
        
        
                    patchPointLists.append(pointProcList)
        
        
                    for i in range(16): # write to .*bd file
                        if   i == 0: # skip point 1
                            fbd.seek(16, 1)
                        elif i == 1: # skip point 2
                            fbd.seek(16, 1)
                        elif i == 4: # skip point 5
                            fbd.seek(16, 1)
                        elif i == 5: # skip point 6
                            fbd.seek(16, 1)
                        else:
                            packedPoints = struct.pack('ffff', 
                                pointProcList[i][0], pointProcList[i][1], pointProcList[i][2], 1.0)
                            fbd.write(packedPoints)
        
                    #print(hex(fbd.tell()))
        
        
                    bounds = struct.pack('f'*6, *minmax(pointsList))
                    fbd.write(bounds)
        
                    corners = struct.pack('f'*16, *get_corners(pointsList))
                    fbd.write(corners)
        
        
        
                    fbd.seek(0x18, 1) # skip unknown
        
                    #fbd.seek(0x70, 1) # placeholder skip extras
        
                    print(f"Patch: {pch+1:6} out of {patchCount:} exported succesfully. {hex(fbd.tell()-336)}")
    
                except KeyError:
                    fbd.seek(0x1C0, 1)
                    print(f"Patch: {pch+1:6} out of {patchCount:} failed. {hex(fbd.tell()-336)}\nERROR: Failed to export '{patchObjName}{pch}', object not found.\n\n")
                    
            
            fbd.close()

    
    def export_patches_xbx(): # OVERRIDE PS2 PATCHES (SONY PLAYSTATION 2)

            patchPointLists = []
    
            for pch in range(patchCount):

    
                try:
                    
        
                    surface_object = bdat.objects[f"{patchObjName}{pch}"].data.splines
    
                    fbd.seek(0x50, 1) # placeholder skip UVs
        
    
                    pointsList = []
                    for s in surface_object:
                        for p in s.points:
                            #print(p.co)
                            pointsList.append(mathutils.Vector(
                                (p.co[0]*pchScale, p.co[1]*pchScale, p.co[2]*pchScale)))
                            #p.select = False
        
        
                    #pointsList = rearrange(pointsList)
                    pointProcList = process_patch_points(pointsList)
        
        
                    patchPointLists.append(pointProcList)
        
        
                    for i in range(16): # write to .*bd file
                        if   i == 0: # skip point 1
                            fbd.seek(16, 1)
                        elif i == 1: # skip point 2
                            fbd.seek(16, 1)
                        elif i == 4: # skip point 5
                            fbd.seek(16, 1)
                        elif i == 5: # skip point 6
                            fbd.seek(16, 1)
                        else:
                            fbd.write(struct.pack(
                                'ffff', pointProcList[i][0], pointProcList[i][1], pointProcList[i][2], 1.0)
                            )
        
                    #print(hex(fbd.tell()))
        
        
                    bounds = struct.pack('f'*6, *minmax(pointsList))
                    fbd.write(bounds)

                    fbd.seek(0x18, 1) # skip unknown
        
                    corners = struct.pack('f'*16, *get_corners(pointsList))
                    fbd.write(corners)
        
        
        
                    fbd.seek(0x110, 1) # skip unknown

        
                    print(f"Patch: {pch+1:6} out of {patchCount:} exported succesfully. {hex(fbd.tell()-336)}")
    
                except KeyError:
                    fbd.seek(0x1C0, 1)
                    print(f"Patch: {pch+1:6} out of {patchCount:} failed. {hex(fbd.tell()-336)}\nERROR: Failed to export '{patchObjName}{pch}', object not found.\n\n")
                    
            
            fbd.close()
    

    def export_patches_ngc(): # OVERRIDE GAMECUBE PATCHES (NINTENDO GAMECUBE)
        
            patchPointLists = []
    
            for pch in range(patchCount):
    
    
                try:
                    fbd.seek(0x50, 1) # placeholder skip UVs
        
                    surface_object = bdat.objects[f"{patchObjName}{pch}"].data.splines
        
        
        
                    pointsList = []
                    for s in surface_object:
                        for p in s.points:
                            #print(p.co)
                            pointsList.append(mathutils.Vector(
                                (p.co[0]*pchScale, p.co[1]*pchScale, p.co[2]*pchScale)))
                            #p.select = False
        
        
                    #pointSortList = rearrange(pointsList)
                    #pointProcList = process_patch_points(pointSortList)
                    pointProcList = process_patch_points(pointsList)
        
        
                    patchPointLists.append(pointProcList)
        
        
                    for i in range(16): # write to .*bd file
        
                        if   i == 0: # skip point 1
                            fbd.seek(16, 1)
                        elif i == 1: # skip point 2
                            fbd.seek(16, 1)
                        elif i == 4: # skip point 5
                            fbd.seek(16, 1)
                        elif i == 5: # skip point 6
                            fbd.seek(16, 1)
                        else:
                            fbd.write( struct.pack(
                                '>ffff', pointProcList[i][0], pointProcList[i][1], pointProcList[i][2], 1.0)
                            )
        
        
                    bounds = struct.pack('>ffffff', *minmax(pointsList))
                    fbd.write(bounds)

                    fbd.seek(0x4, 1)
        
                    corners = struct.pack('>ffffffffffffffff', *get_corners(pointsList))
                    fbd.write(corners)
        
        
                    fbd.seek(0x14, 1) # skip unknown
        
    
                    print(f"Patch: {pch+1:6} out of {patchCount:} exported. {hex(fbd.tell()-336)}")
    
                except KeyError:
                    print(f"Patch: {pch+1:6} out of {patchCount:}\nERROR: Failed to export '{patchObjName}{pch}', object not found.\n\n")
                    fbd.seek(0x1C0, 1)
            
            fbd.close()
    
    
    
    def minmax(p):
        x_list, y_list, z_list = [], [], []
        for i in range(16):
            x_list.append(p[i][0])
            y_list.append(p[i][1])
            z_list.append(p[i][2])
        ret = (min(x_list), min(y_list), min(z_list), 
               max(x_list), max(y_list), max(z_list))
        return ret
    
    
    def get_corners(p):
        ret = (p[ 0][0], p[ 0][1], p[ 0][2], 1.0,
               p[12][0], p[12][1], p[12][2], 1.0,
               p[ 3][0], p[ 3][1], p[ 3][2], 1.0,
               p[15][0], p[15][1], p[15][2], 1.0)
        return ret
    
    
    def rearrange(p):
        ret = [p[3], p[7], p[11], p[15],
               p[2], p[6], p[10], p[14], 
               p[1], p[5], p[ 9], p[13],
               p[0], p[4], p[ 8], p[12],]
        return ret
    
    
    def process_patch_points(r): # EQUATIONS, CALCULATIONS, EXAGGERATIONS, THE LOT!
    
        # r = Raw point, e = Encoded point
    
        # e16 = same as r[0]
        e15 = (r[1] - r[0])*3
        e14 = (r[2] - r[1])*3 - e15
        e13 = r[3] - e14 - e15 - r[0]
    
        e12 = (r[4] - r[0])*3
        e11 = r[5]*9 - r[0]*9 - e15*3 - e12*3
        e10 = 9*r[6] - r[5]*9 - e14*3 - e15*3 - e11
        e9  = r[7]*3 - r[3]*3 - e12 - e11 - e10
    
        e8  = (r[8] - r[4])*3 - e12
        e7  = 9*r[9] - r[5]*9 - e12*3 - e8*3 - e11
        e6  = r[10]                                   # missing equation
        e5  = r[11]*3 - r[7]*3 - e12 - e11 - e7 - e9 - e10 - e8 - e6 # wrong due to e6 missing
    
        e4  = r[12] - r[0] - e12 - e8
        e3  = r[13]*3 - r[12]*3 - e15 - e11 - e7
        e2  = r[14]*3 - r[13]*3 - e15 - e11 - e7 - e14 - e10 - e3 - e6   # wrong due to e6 missing
        e1  = r[15] - (r[0]+e15+e14+e13+e12+e11+e9+e8+e7+e6+e5+e4+e3+e2) # wrong due to e6 missing
    
    
    
        #print(f"""
        #    { e1 = }\n{ e2 = }\n{ e3 = }\n{ e4 = }
        #    { e5 = }\n{ e6 = }\n{ e7 = }\n{ e8 = }
        #    { e9 = }\n{e10 = }\n{e11 = }\n{e12 = }
        #    {e13 = }\n{e14 = }\n{e15 = }\n{r[0] = }\n""")
    
    
        processedPoints = [e1, e2, e3, e4, 
                           e5, e6, e7, e8, 
                           e9, e10, e11, e12, 
                           e13, e14, e15, r[0]]
    
    
        return processedPoints
        
    
    
    
    if patchCount > 0:
        if   consVer == '1':
            export_patches_ps2()
        elif consVer == '2':
            export_patches_xbx()
        elif consVer == '3':
            export_patches_ngc()
        else:
            print("INVALID PLATFORMMMMMMMMMMM")

            fbd.close()
            return {'CANCELLED'}
    else:
        fbd.close()
        print("\nPatch count is invalid. patchCount =", patchCount)
    
    
    timeEnd = time.time()
    print(f"\n\nFINISHED\nTime Taken: {round(timeEnd-timeStart, 6)}\n")

    return {'FINISHED'}



from bpy_extras.io_utils import ExportHelper # ExportHelper is a helper class, defines filename and...
from bpy.props import StringProperty, FloatProperty, BoolProperty, IntProperty, EnumProperty #... invoke() function which calls the file selector.
from bpy.types import Operator



class Export_Data(Operator, ExportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "export_patches.patch_data"
    bl_label = "Export Patches"


    filename_ext = ""

    #check_extension = True # idk if this works here or what it does



    filter_glob: StringProperty(
        default="*.pbd;*.xbd;*.nbd",
        options={'HIDDEN'}, # Hide other file extensions
        maxlen=255,  # Max name length
    )

    platform: EnumProperty(
        name="Platform",
        description="Choose console/platform.",
        items=[ ('1', ".pbd PS2",      ""), # identifier, text, descriptio, optional thing, optional thing
                ('2', ".xbd Xbox",     ""),
                ('3', ".nbd GameCube", ""),
        ]
    )

    scale: FloatProperty(
        name="Scale Multiplier",
        description="The bigger the value, the bigger the size.\n1 Blender unit = 1,000 SSX units\nDefault: 100",
        default = 100.0,
        min     = 1.0,
    )

    #address: IntProperty(
    #    name    = "Address",
    #    description="Custom decimal address.\nDefault: 0",
    #    default = 0,
    #    min     = 0,
    #    max     = 10000000,
    #    subtype = 'UNSIGNED'
    #)

    use_count: BoolProperty(
        name="Custom Export Count",
        description="Enable or Disable custom patch count",
        default=False,
    )

    count: IntProperty(
        name    = "Patch Count",
        default = 1000,
        min     = 1,
        max     = 1000000,
        subtype = 'UNSIGNED'
    )

    override_count: BoolProperty(
        name="Override Game Count",
        description="Allows you to decrease the number of patches rendered in game.\nCan only be lower than existing patch count",
        default=False,
    )


    def execute(self, context):


        return write_file_data(context, self.filepath, self.platform, self.scale, self.use_count, self.count, self.override_count)


classes = [Export_Data]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
    
    bpy.ops.export_patches.patch_data('INVOKE_DEFAULT') # test call
