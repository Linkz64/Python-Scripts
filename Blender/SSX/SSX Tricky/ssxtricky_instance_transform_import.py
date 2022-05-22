import bpy
import struct
import mathutils


class ImportInstanceTransformations(bpy.types.Operator):
    bl_idname = "object.importinstances"
    bl_label = "Import Object Instance Locations"

    def execute(self, context):

        collection = bpy.context.collection
        bdata = bpy.data

        pbdFilePath = ("F:/Example Folder/File.pbd")
        f = open(pbdFilePath, 'rb') # ^ path to .pbd file

        mapFilePath = ("F:/Example Folder/NamesList.txt")
        fm = open(mapFilePath) # ^ path to "NamesList.txt"

        contents = fm.readlines()
        fm.close()

        print("Imported:\n\n")
        
        f.seek(0x1A8F50, 0) # offset of instance transforms in hex (starting at the first matrix value)
        
        objCount = 5
        # ^ how many instances you'd like to import as empties

        for i in range(objCount):

            line = contents[1+i] # line number of first name inside "NameList.txt"
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
            empty.empty_display_type = 'ARROWS'
            empty.empty_display_size = 200
            empty.matrix_world = (mtx1, mtx2, mtx3, (0.0, 0.0, 0.0, 1.0))
            empty.location = (x, y, z)
            
            f.seek(0xC4, 1)
        
        f.close()
        fm.close()
        return{'FINISHED'}

def register():
    bpy.utils.register_class(ImportInstanceTransformations)

def unregister():
    bpy.utils.unregister_class(ImportInstanceTransformations)
    
if __name__ == "__main__":
    register()
    bpy.ops.object.importinstances()
