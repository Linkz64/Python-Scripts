""" 
Blender (2.92+) script that exports surface patches into SSX Tricky's .*bd files

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
    - Choose an existing file and click "Export Patches"


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

    
            for pch in range(patchCount):
            
                
    
                try:
                    
        
                    surface_object = bdat.objects[f"{patchObjName}{pch}"].data.splines
    
                    fbd.seek(0x50, 1) # placeholder skip UVs


                    rawPoints = [vec((0.0, 0.0, 0.0))]*16 # test if I can do this with tuple and compare time
        
    
                    pointsList = []
                    for s in surface_object:
                        for p in s.points:
                            #print(p.co)
                            pointsList.append(mathutils.Vector(
                                (p.co[0]*pchScale, p.co[1]*pchScale, p.co[2]*pchScale)))
                            #p.select = False

                    rawPoints = sort_a(pointsList)


                    pointProcList = process_patch_points(rawPoints)


                    #print(pointProcList)
        
                    for i in range(16):                         # write patch points to .*bd file
                            fbd.write(struct.pack('ffff', pointProcList[i][0], pointProcList[i][1], pointProcList[i][2], 1.0))
        
                    #print(hex(fbd.tell()))
        
                    fbd.write(struct.pack('f'*6, *minmax(rawPoints))) # write bounds (2 points)
                    fbd.write(struct.pack('f'*16, *get_corners(rawPoints))) # write corners (4 points)
        
        
        
                    fbd.seek(0x18, 1) # skip unknown
        
                    #fbd.seek(0x70, 1) # placeholder skip extras
        
                    print(f"Patch: {pch+1:6} out of {patchCount:} exported succesfully. {hex(fbd.tell()-336)}")
    
                except KeyError:
                    fbd.seek(0x1C0, 1)
                    print(f"Patch: {pch+1:6} out of {patchCount:} failed. {hex(fbd.tell()-336)}\nERROR: Failed to export '{patchObjName}{pch}', object not found.\n\n")
                    
            
            fbd.close()

    
    def export_patches_xbx(): # OVERRIDE PS2 PATCHES (SONY PLAYSTATION 2)

    
            for pch in range(patchCount):

    
                try:
                    
        
                    surface_object = bdat.objects[f"{patchObjName}{pch}"].data.splines
    
                    fbd.seek(0x50, 1) # placeholder skip UVs
        
    
                    rawPoints = [vec((0.0, 0.0, 0.0))]*16 # test if I can do this with tuple and compare time
        
    
                    pointsList = []
                    for s in surface_object:
                        for p in s.points:
                            #print(p.co)
                            pointsList.append(mathutils.Vector(
                                (p.co[0]*pchScale, p.co[1]*pchScale, p.co[2]*pchScale)))
                            #p.select = False

                    rawPoints = sort_a(pointsList)


                    pointProcList = process_patch_points(rawPoints)


                    #print(pointProcList)
        
                    for i in range(16):                         # write patch points to .*bd file
                            fbd.write(struct.pack('ffff', pointProcList[i][0], pointProcList[i][1], pointProcList[i][2], 1.0))
        
        
                    fbd.write(struct.pack('f'*6, *minmax(rawPoints))) # write bounds (2 points)

                    fbd.seek(0x18, 1) # skip unknown

                    fbd.write(struct.pack('f'*16, *get_corners(rawPoints))) # write corners (4 points)
        
        
        
                    fbd.seek(0x110, 1) # skip unknown

        
                    print(f"Patch: {pch+1:6} out of {patchCount:} exported succesfully. {hex(fbd.tell()-336)}")
    
                except KeyError:
                    fbd.seek(0x1C0, 1)
                    print(f"Patch: {pch+1:6} out of {patchCount:} failed. {hex(fbd.tell()-336)}\nERROR: Failed to export '{patchObjName}{pch}', object not found.\n\n")
                    
            
            fbd.close()
    

    def export_patches_ngc(): # OVERRIDE GAMECUBE PATCHES (NINTENDO GAMECUBE)
        
    
            for pch in range(patchCount):
    
    
                try:
                    fbd.seek(0x50, 1) # placeholder skip UVs
        
                    surface_object = bdat.objects[f"{patchObjName}{pch}"].data.splines
        
        
                    rawPoints = [vec((0.0, 0.0, 0.0))]*16 # test if I can do this with tuple and compare time
        
    
                    pointsList = []
                    for s in surface_object:
                        for p in s.points:
                            #print(p.co)
                            pointsList.append(mathutils.Vector(
                                (p.co[0]*pchScale, p.co[1]*pchScale, p.co[2]*pchScale)))
                            #p.select = False

                    rawPoints = sort_a(pointsList)


                    pointProcList = process_patch_points(rawPoints)


                    #print(pointProcList)
        
                    for i in range(16):                         # write patch points to .*bd file
                            fbd.write(struct.pack('>ffff', pointProcList[i][0], pointProcList[i][1], pointProcList[i][2], 1.0))
        
        
                    fbd.write(struct.pack('>ffffff', *minmax(rawPoints)))

                    fbd.seek(0x4, 1) # gap/padding/filler
        
                    fbd.write(struct.pack('>ffffffffffffffff', *get_corners(rawPoints)))
        
        
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
    
    
    def sort_a(p):
        ret = [p[3], p[7], p[11], p[15],
               p[2], p[6], p[10], p[14], 
               p[1], p[5], p[ 9], p[13],
               p[0], p[4], p[ 8], p[12],]
        return ret

    def sort_b(p):
        pass


    def raw_to_mid_eq1(a, b, rawPoints):
        return (rawPoints[a] - rawPoints[b]) * 3
    
    def raw_to_mid_eq2(a, b, midA, rawPoints, midTablePoints):
        return (rawPoints[a] - rawPoints[b]) * 3 - midTablePoints[midA]
    
    def raw_to_mid_eq3(a,    midA, midB, midC, rawPoints, midTablePoints):
        return rawPoints[a] - midTablePoints[midA] - midTablePoints[midB] - midTablePoints[midC]
    

    def mid_to_proc_eq1(a, b, midTablePoints):
        return (midTablePoints[a] - midTablePoints[b]) * 3
    
    def mid_to_proc_eq2(a, b, EndA, midTablePoints, processedPoints):
        return (midTablePoints[a] - midTablePoints[b]) * 3 - processedPoints[EndA]
    
    def mid_to_proc_eq3(a,         midA, midB, midC, midTablePoints, processedPoints):
        return midTablePoints[a] - processedPoints[midA] - processedPoints[midB] - processedPoints[midC]

    
    
    def process_patch_points(rawPoints):
    
        midTablePoints  = [vec((0.0, 0.0, 0.0))]*16
        processedPoints = [vec((0.0, 0.0, 0.0))]*16

    
        midTablePoints[ 0] = rawPoints[0]
        midTablePoints[ 1] = raw_to_mid_eq1(1, 0, rawPoints)
        midTablePoints[ 2] = raw_to_mid_eq2(2, 1, 1, rawPoints, midTablePoints)
        midTablePoints[ 3] = raw_to_mid_eq3(3, 2, 1, 0, rawPoints, midTablePoints)

        midTablePoints[ 4] = rawPoints[4]
        midTablePoints[ 5] = raw_to_mid_eq1(5, 4, rawPoints)
        midTablePoints[ 6] = raw_to_mid_eq2(6, 5, 5, rawPoints, midTablePoints)
        midTablePoints[ 7] = raw_to_mid_eq3(7, 6, 5, 4, rawPoints, midTablePoints)

        midTablePoints[ 8] = rawPoints[8]
        midTablePoints[ 9] = raw_to_mid_eq1(9, 8, rawPoints)
        midTablePoints[10] = raw_to_mid_eq2(10, 9, 9, rawPoints, midTablePoints)
        midTablePoints[11] = raw_to_mid_eq3(11, 10, 9, 8, rawPoints, midTablePoints)

        midTablePoints[12] = rawPoints[12]
        midTablePoints[13] = raw_to_mid_eq1(13, 12, rawPoints)
        midTablePoints[14] = raw_to_mid_eq2(14, 13, 13, rawPoints, midTablePoints)
        midTablePoints[15] = raw_to_mid_eq3(15, 14, 13, 12, rawPoints, midTablePoints)


        processedPoints[ 0] = midTablePoints[0]
        processedPoints[ 1] = midTablePoints[1]
        processedPoints[ 2] = midTablePoints[2]
        processedPoints[ 3] = midTablePoints[3]

        processedPoints[ 4] = mid_to_proc_eq1(4, 0, midTablePoints)
        processedPoints[ 5] = mid_to_proc_eq1(5, 1, midTablePoints)
        processedPoints[ 6] = mid_to_proc_eq1(6, 2, midTablePoints)
        processedPoints[ 7] = mid_to_proc_eq1(7, 3, midTablePoints)

        processedPoints[ 8] = mid_to_proc_eq2( 8, 4, 4, midTablePoints, processedPoints)
        processedPoints[ 9] = mid_to_proc_eq2( 9, 5, 5, midTablePoints, processedPoints)
        processedPoints[10] = mid_to_proc_eq2(10, 6, 6, midTablePoints, processedPoints)
        processedPoints[11] = mid_to_proc_eq2(11, 7, 7, midTablePoints, processedPoints)

        processedPoints[12] = mid_to_proc_eq3(12,  8, 4, 0, midTablePoints, processedPoints)
        processedPoints[13] = mid_to_proc_eq3(13,  9, 5, 1, midTablePoints, processedPoints)
        processedPoints[14] = mid_to_proc_eq3(14, 10, 6, 2, midTablePoints, processedPoints)
        processedPoints[15] = mid_to_proc_eq3(15, 11, 7, 3, midTablePoints, processedPoints)


        #processedPoints.reverse() # terrible rounding

        test = list(reversed(processedPoints)) # normal

        #test = [processedPoints[15], processedPoints[14], processedPoints[13], processedPoints[12], 
        #         processedPoints[11], processedPoints[10], processedPoints[ 9], processedPoints[ 8], 
        #         processedPoints[ 7], processedPoints[ 6], processedPoints[ 5], processedPoints[ 4], 
        #         processedPoints[ 3], processedPoints[ 2], processedPoints[ 1], processedPoints[ 0]]

        #print(list(test))

        return test
        
    
    
    
    if patchCount > 0:
        if   consVer == '1':
            export_patches_ps2()
        elif consVer == '2':
            export_patches_xbx()
        elif consVer == '3':
            export_patches_ngc()
        else:
            print("ERROR: Invalid Platform.")

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
        default = 500,
        min     = 1,
        max     = 1000000,
        subtype = 'UNSIGNED'
    )

    override_count: BoolProperty(
        name="Override Game Count",
        description="Allows you to decrease the number of patches rendered in game.\nWARNING: Increasing past original patch count may corrupt the file.",
        default=False,
    )


    def execute(self, context):


        return write_file_data(context, self.filepath, self.platform, self.scale, self.use_count, self.count, self.override_count)


def register():
    bpy.utils.register_class(Export_Data)

def unregister():
    bpy.utils.unregister_class(Export_Data)


if __name__ == "__main__":
    register()
    
    bpy.ops.export_patches.patch_data('INVOKE_DEFAULT') # test call
