import bpy
import bmesh
import os


def check_and_create_file_path(file_path: list[str]):

    for path in file_path:
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"Created {path} directory")

    print("All directories exist")


def clean_up_data():

    # clear emptys
    remove_empty_collections()

    # remove orphan data
    remove_orphan_data()

    # purge data
    purge_data()


def remove_empty_collections():

    for col in bpy.data.collections:
        if (len(col.all_objects) == 0):
            bpy.data.collections.remove(col)


def save_file(arg0):

    print('\nSaving File')
    # save file
    bpy.ops.wm.save_mainfile()
    print(arg0 + "\n")


def purge_data():
    """Remove data blocks with no users ie orphaned data
    """
    # print starting orphan data removal
    print("\n-- STARTING ORPHAN PURGE DATA REMOVAL --\n\n")

    object_counter = sum(block.users == 0 for block in bpy.data.objects)
    object_scene_counter = sum(
        block.users_scene == 0 for block in bpy.data.objects)
    mesh_counter = sum(block.users == 0 for block in bpy.data.meshes)
    material_counter = sum(block.users == 0 for block in bpy.data.materials)
    texture_counter = sum(block.users == 0 for block in bpy.data.textures)
    image_counter = sum(block.users == 0 for block in bpy.data.images)
    obs = [o for o in bpy.data.objects if not o.users_scene]
    bpy.data.batch_remove(obs)

    # get max num to delete
    num_to_delete = max(object_counter, object_scene_counter,
                        mesh_counter, material_counter, texture_counter, image_counter)

    # purge data
    bpy.ops.outliner.orphans_purge(
        num_deleted=num_to_delete, do_local_ids=True, do_linked_ids=True, do_recursive=False)
    bpy.ops.outliner.orphans_purge(
        num_deleted=num_to_delete, do_local_ids=True, do_linked_ids=True, do_recursive=True)

    # print done and how much was removed
    print("\n\n-- PURGE DATA REMOVAL FINISHED --\n")


def remove_orphan_data():
    """Remove data blocks with no users ie orphaned data
    """
    # print starting orphan data removal
    print("\n-- STARTING ORPHAN DATA REMOVAL --")

    mesh_counter = 0
    material_counter = 0
    texture_counter = 0
    image_counter = 0
    object_counter = 0

    object_scene_counter = sum(
        block.users_scene == 0 for block in bpy.data.objects)
    obs = [o for o in bpy.data.objects if not o.users_scene]
    bpy.data.batch_remove(obs)

    for block in bpy.data.objects:
        if block.users == 0:
            bpy.data.meshes.remove(block)
            object_counter += 1

    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
            mesh_counter += 1

    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)
            material_counter += 1

    for block in bpy.data.textures:
        if block.users == 0:
            bpy.data.textures.remove(block)
            texture_counter += 1

    for block in bpy.data.images:
        if block.users == 0:
            bpy.data.images.remove(block)
            image_counter += 1

    # print done and how much was removed
    print(
        f"\n\tNUMBER OF OBJECTS DATA REMOVED: {object_counter} \n\tNUMBER OF OBJECTS SCENE DATA REMOVED: {object_scene_counter}  \n\tNUMBER OF MESH DATA REMOVED: {mesh_counter} \n\tNUMBER OF MATERIAL DATA REMOVED: {material_counter} \n\tNUMBER OF TEXTURES REMOVED: {texture_counter} \n\tNUMBER OF IMAGES REMOVED: {image_counter}\n\n-- ORPHAN DATA REMOVAL FINISHED -- ")


def export_model_to_fbx(col_name: str, export_file_path: str):

    current_context = set_context_mode_get_current('EDIT')

    bpy.ops.mesh.select_all(action='SELECT')

    bpy.ops.mesh.select_all(action='DESELECT')

    _ = set_context_mode_get_current('OBJECT')

    # DESELECT ALL OBJS
    bpy.ops.object.select_all(action='DESELECT')

    # get view layer
    layer_col = bpy.context.view_layer.layer_collection

    # get layer col from col name
    for child_layer in layer_col.children:
        if child_layer.name == col_name:
            export_layer_col = child_layer
            break

    # set active layer collection
    bpy.context.view_layer.active_layer_collection = export_layer_col

    bpy.ops.export_scene.fbx(filepath=export_file_path, use_active_collection=True, use_mesh_modifiers=True, mesh_smooth_type='FACE',
                             use_mesh_edges=True, use_tspace=True, use_triangles=True, path_mode='ABSOLUTE', embed_textures=True, axis_forward='X', axis_up='Z')

    set_context_mode_get_current(current_context)
    return


def set_active_obj(obj_name: str):

    if bpy.context.view_layer.objects.active is not bpy.data.objects.get(obj_name):

        # current active is not obj
        current_active = bpy.context.view_layer.objects.active.name

        # DESELECT ALL OBJS
        bpy.ops.object.select_all(action='DESELECT')

        # set obj as active
        bpy.context.view_layer.objects.active = bpy.data.objects.get(obj_name)

    else:
        # current active is obj set it as active
        current_active = obj_name

    return current_active


def remove_doubles_from_obj(obj_name: str, merge_distance: float = 0.0001):

    # get current active and set obj as active
    previous_active_name = set_active_obj(obj_name=obj_name)

    bm, current_context_mode = create_bm_from_mesh_set_mode_to_object(obj_name)

    # merge close vertices
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=merge_distance)

    # free bmesh
    bm_to_mesh_back_to_mode(
        bm=bm, mode=current_context_mode, mesh_name=obj_name)

    # set back to active to previous
    bpy.context.view_layer.objects.active = bpy.data.objects.get(
        previous_active_name)

    return


def turn_auto_smooth_on_off(obj_name: str, turn_on_off: bool, auto_smooth_angle: float = 0.523599):

    # if on set angle
    if turn_on_off:
        bpy.data.meshes[obj_name].auto_smooth_angle = auto_smooth_angle

    else:
        bpy.ops.mesh.customdata_custom_splitnormals_clear()
        # turn on or off auto smooth for object
        bpy.data.meshes[obj_name].use_auto_smooth = turn_on_off
        bpy.context.object.data.use_auto_smooth = turn_on_off
        # setting to 0 turns it off as well, during no data being present from imports or duplicates inside of script
        # turning off can cause the smoothing to still be present
        bpy.data.meshes[obj_name].auto_smooth_angle = 0.0


def shade_face_flat(obj_name: str):

    # get current active and set obj as active
    previous_active_name = set_active_obj(obj_name=obj_name)

    # set to edit mode
    current_context_mode = set_context_mode_get_current('EDIT')

    # set to face select mode
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
    bpy.ops.mesh.select_all(action='SELECT')

    # shade faces as flat
    bpy.ops.mesh.faces_shade_flat()

    # set back to active to previous
    bpy.context.view_layer.objects.active = bpy.data.objects.get(
        previous_active_name)

    # set context mode back
    set_context_mode_get_current(current_context_mode)

    return


def set_context_mode_get_current(mode: str):

    current_context_mode = bpy.context.active_object.mode

    if (current_context_mode != mode):
        # set context mode to obkect
        bpy.ops.object.mode_set(mode=mode)

    return current_context_mode


def create_bm_from_mesh_set_mode_to_object(mesh_name: str):

    # get current context mode and set to object if not
    current_context_mode = set_context_mode_get_current(mode='OBJECT')

    # create bmesh
    bm = bmesh.new(use_operators=True)

    # get data from duplicate
    bm.from_mesh(bpy.data.objects.get(mesh_name).data)

    return bm, current_context_mode


def bm_to_mesh_free(bm: bmesh.types.BMesh, mesh_name: str):

    # transfer data back
    bm.to_mesh(bpy.data.objects.get(mesh_name).data)
    # free bm
    bm.free()


def bm_to_mesh_back_to_mode(bm: bmesh.types.BMesh, mode: str, mesh_name: str):

    bm_to_mesh_free(bm, mesh_name)

    # set mode back
    bpy.ops.object.mode_set(mode=mode)


def set_origin_to_center(obj_name: str):

    # set active object and get previous active
    previous_active_name = set_active_obj(obj_name=obj_name)

    # set origin to center
    bpy.ops.object.origin_set(type='GEOMETRY_ORIGIN', center='MEDIAN')

    # set previous active back to active
    set_active_obj(obj_name=previous_active_name)

    return


def write_to_file(filepath: str, lines: list[str] = None, line: str = None):
    if lines is None and line is None:
        print('No lines or line to write to file')
        return

    if lines is not None:
        with open(filepath, "a+") as log_file:
            for l in lines:
                log_file.write(f"{l}\n")
    elif line is not None:
        with open(filepath, "a+") as log_file:
            log_file.write(f"{line}\n")


def print_save_log(filepath: str, lines: list[str] = None, line: str = None, print_to_console: bool = True):

    write_to_file(filepath, lines, line)  # create log file

    if lines is not None and print_to_console:
        for l in lines:
            print(f"{l}")

    elif line is not None and print_to_console:
        print(f"{line}")

    save_file('Saved after log')
    return


def create_col(parent_layer_col: bpy.context.collection, col_name: str):

    new_col = bpy.data.collections.new(col_name)
    parent_layer_col.children.link(new_col)

    new_child_layer_col = bpy.context.view_layer.layer_collection.children[new_col.name]

    bpy.context.view_layer.active_layer_collection = new_child_layer_col

    return new_child_layer_col


def move_objects_from_one_collection_to_target(target_col: bpy.context.collection, move_objs: list[bpy.data.objects]):

    if not move_objs:
        print("no objs to move from collection to target collection")
        return

    for obj in move_objs:

        # remove existing link
        for col in obj.users_collection:
            # unlink
            col.objects.unlink(obj)

        # add link to target collection
        target_col.objects.link(obj)

    print("Target Collection has successfully added objects to its collection")
