import bpy
import struct
import mathutils


class ImportInstanceTransformations(bpy.types.Operator):
    bl_idname = "object.importobjectinstance"
    bl_label = "Import Object Instance Locations as Empties"

    def execute(self, context):

        pbd_folder_path = ("F:/Modding/SSX/SSX Tricky/") # < path to folder containing a .pbd (MUST HAVE / AT THE END)
        instance_list_folder_path = ("F:/Modding/SSX/SSX Tricky/") # < path to folder containing InstanceList.txt (MUST HAVE / AT THE END)

        ssxfe =     {'name': "Menu",                    'pbd':"ssxfe.pbd",      'lineNum': 2}
        trick =     {'name': "Trick Tutorial",          'pbd':"trick.pbd",      'lineNum': 343}
        gari =      {'name': "Garibaldi",               'pbd':"gari.pbd",       'lineNum': 917}
        elysium =   {'name': "Elysium Alps",            'pbd':"elysium.pbd",    'lineNum': 7548}
        mesa =      {'name': "Mesablanca",              'pbd':"mesa.pbd",       'lineNum': 11485}
        merquer =   {'name': "Merqury City Meltdown",   'pbd':"merquer.pbd",    'lineNum': 14568}
        megaple =   {'name': "Tokyo Megaplex",          'pbd':"megaple.pbd",    'lineNum': 19017}
        aloha =     {'name': "Aloha Ice Jam",           'pbd':"aloha.pbd",      'lineNum': 20315}
        alaska =    {'name': "Alaska",                  'pbd':"alaska.pbd",     'lineNum': 22316}
        pipe =      {'name': "Pipedream",               'pbd':"pipe.pbd",       'lineNum': 23797}
        untrack =   {'name': "Untracked",               'pbd':"untrack.pbd",    'lineNum': 24377}

        # __________________ choose which to import __________________
        choice = gari


        with open(instance_list_folder_path+"InstanceList.txt") as instances:
            contents = instances.readlines()
        instances.close() # with open() already takes care of closing I think

        pbdFilePath = (pbd_folder_path+choice["pbd"])
        f = open(pbdFilePath, 'rb')


        
        f.seek(0xC, 0)
        instCount = struct.unpack('I', f.read(4)) # uint32 instance count

        f.seek(0x48, 0)
        instOffset = struct.unpack('I', f.read(4)) # uint32 offset of instance transforms in .pbd (where the first matrix value is)
        
        f.seek(int(instOffset[0]), 0) # offset of instance transforms


        collection = bpy.context.collection
        bdata = bpy.data

        for i in range(int(instCount[0])):

            line = contents[choice["lineNum"]+i] # get each line from InstanceList.txt
            line = line.split()[0]
            name = (f"obj{i}_{line}")
            print(name)

            for matrices in range(1):
                (mtxA1,) = struct.unpack('f', f.read(4))
                (mtxA2,) = struct.unpack('f', f.read(4))
                (mtxA3,) = struct.unpack('f', f.read(4))
                (mtxA4,) = struct.unpack('f', f.read(4))

                (mtxB1,) = struct.unpack('f', f.read(4))
                (mtxB2,) = struct.unpack('f', f.read(4))
                (mtxB3,) = struct.unpack('f', f.read(4))
                (mtxB4,) = struct.unpack('f', f.read(4))

                (mtxC1,) = struct.unpack('f', f.read(4))
                (mtxC2,) = struct.unpack('f', f.read(4))
                (mtxC3,) = struct.unpack('f', f.read(4))
                (mtxC4,) = struct.unpack('f', f.read(4))
            
            mtx1 = (mtxA1, mtxA2, mtxA3, mtxA4)
            mtx2 = (mtxB1, mtxB2, mtxB3, mtxB4)
            mtx3 = (mtxC1, mtxC2, mtxC3, mtxC4)
            #print(mtx1, mtx2, mtx3, mtx4)

            for locations in range(1):
                (x,) = struct.unpack('f', f.read(4))
                (y,) = struct.unpack('f', f.read(4))
                (z,) = struct.unpack('f', f.read(4))
            print(x, y, z)
            
            empty = bdata.objects.new(name, None)
            collection.objects.link(empty)
            empty.show_name = False
            empty.empty_display_type = 'ARROWS'
            empty.empty_display_size = 200
            empty.matrix_world = (mtx1, mtx2, mtx3, (0.0, 0.0, 0.0, 1.0))
            empty.location = (x, y, z)
            
            f.seek(0xC4, 1) # place "cursor" before the next instance
        
        f.close()

        print("\nImported "+choice["name"]+"\n")

        return{'FINISHED'}

def register():
    bpy.utils.register_class(ImportInstanceTransformations)

def unregister():
    bpy.utils.unregister_class(ImportInstanceTransformations)
    
if __name__ == "__main__":
    register()
    bpy.ops.object.importobjectinstance()
