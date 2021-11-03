import bpy

def clear_scene():
    bpy.ops.object.select_by_type(type='LIGHT')
    bpy.ops.object.delete(use_global=False, confirm=False)
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.delete(use_global=False, confirm=False)

    try:
        bpy.data.objects['Camera'].select_set(True)
        bpy.ops.object.delete() 
    except:
        pass
    
    try:
        for material in bpy.data.materials:
            bpy.data.materials.remove(material)
    except Exception as e:
        pass
    
    try:
        for particle in bpy.data.particles:
            bpy.data.particles.remove(particle)
    except Exception as e:
        pass
    try:
        bpy.data.objects['rock'].select_set(True)
        bpy.ops.object.delete() 
    except:
        pass
    
    try:
        for i in range(10,18):
            bpy.data.particles["ParticleSettings.00{}"%i].select = True
            bpy.ops.object.particle_system_remove()
    except Exception as e:
        print(e)
    try:
        name = "ground_collection"
        remove_collection_objects = True

        coll = bpy.data.collections.get(name)

        if coll:
            if remove_collection_objects:
                obs = [o for o in coll.objects if o.users == 1]
                while obs:
                    bpy.data.objects.remove(obs.pop())

            bpy.data.collections.remove(coll)
    except:
        pass


def point_cloud(ob_name, coords, edges=[], faces=[]):
    """Create point cloud object based on given coordinates and name.

    Keyword arguments:
    ob_name -- new object name
    coords -- float triplets eg: [(-1.0, 1.0, 0.0), (-1.0, -1.0, 0.0)]
    """

    # Create new mesh and a new object
    me = bpy.data.meshes.new(ob_name + "Mesh")
    ob = bpy.data.objects.new(ob_name, me)

    # Make a mesh from a list of vertices/edges/faces
    me.from_pydata(coords, edges, faces)

    # Display name and update the mesh
    ob.show_name = True
    me.update()
    return ob

# Create the object
pc = point_cloud("origin", [(0.0, 0.0, 0.0)])

# Link object to the active collection
bpy.context.collection.objects.link(pc)