import bpy
import struct
import mathutils


class ImportInstanceTransformations(bpy.types.Operator):
	bl_idname = "object.importobjectinstance"
	bl_label = "Import Object Instance Locations"

	def execute(self, context):

		pbd_folder_path = ("F:/Development/Python/Blender/Scripts/SSX Tricky Instance Importer/")
		# ^ path to folder containing a .pbd
		instance_list_folder_path = ("F:/Development/Python/Blender/Scripts/SSX Tricky Instance Importer/")
		# ^ path to folder containing InstanceList.txt


		gari = {
			'name': "Garibaldi",
			'pbd': "gari.pbd",
			'instCount': 3393, # instance count from .pbd
			'offset': 0x1A8F50, # offset of instance transforms in .pbd (where the first matrix value is)
			'lineNum': 917 # line number of map name in InstanceList.txt
		}

		snow = {
			'name': "Snowdream",
			'pbd': "snow.pbd",
			'instCount': 3230,
			'offset': 0xB4D50,
			'lineNum': 4314
		}

		# __ choose which to import __
		choice = gari

		count = choice["instCount"]
		#count = 7 #custom count





		with open(instance_list_folder_path+"InstanceList.txt") as instances:
			contents = instances.readlines()
		instances.close() # with open() already takes care of closing I think

		#instListFilePath = (instance_list_folder_path+"InstanceList.txt")
		#fm = open(instListFilePath)

		#contents = fm.readlines()
		#fm.close()


		pbdFilePath = (pbd_folder_path+choice["pbd"])
		f = open(pbdFilePath, 'rb')

		f.seek(choice["offset"], 0) # offset of instance transforms

		collection = bpy.context.collection
		bdata = bpy.data

		for i in range(count):

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
			
			f.seek(0xC4, 1)
		
		f.close()
		#fm.close()

		print("\nImported "+choice["name"]+"\n")

		return{'FINISHED'}

def register():
	bpy.utils.register_class(ImportInstanceTransformations)

def unregister():
	bpy.utils.unregister_class(ImportInstanceTransformations)
	
if __name__ == "__main__":
	register()
	bpy.ops.object.importobjectinstance()
