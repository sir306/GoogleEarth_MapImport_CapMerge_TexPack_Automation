import bpy
import bmesh
from datetime import datetime
from math import *  # import radian function from math
import time  # import time to display execution time
from typing import Optional
from shared_common_methods import *


def more_than_one_material(mesh_name: str):

    obj = bpy.data.objects.get(mesh_name)

    return len(obj.data.materials) > 1


def duplicate_object(duplicate_obj_name: str, selected_obj_name: str):

    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects.get(selected_obj_name).select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects.get(
        selected_obj_name)

    # Duplicate Object
    bpy.ops.object.duplicate(linked=False)

    # Rename Duplicate to include low_poly
    bpy.context.object.data.name = duplicate_obj_name
    bpy.context.active_object.name = duplicate_obj_name

    # Hide original
    bpy.data.objects.get(selected_obj_name).hide_viewport = True

    # Apply Transform to low poly
    bpy.ops.object.transform_apply(
        location=True, rotation=True, scale=True, properties=True, isolate_users=False)

    # clear custom split normals data
    bpy.ops.mesh.customdata_custom_splitnormals_clear()

    # Turn off Auto Smooth for low poly
    bpy.data.objects.get(duplicate_obj_name).data.use_auto_smooth = False


def create_material_uv_and_bake(selected_obj_name: str, target_low_poly_obj_name: str, image_file_path: str, extrusion: float, ray_distance: float, image_texture_margin: int, mat_number: int = 1, image_qual: float = 1024, image_texture_quality: float = 1024):
    print('\nStarting create_uv_material_bake')

    # get current context mode
    current_context_mode = set_context_mode_get_current('OBJECT')

    # Remove materials from obj
    bpy.data.objects.get(target_low_poly_obj_name).data.materials.clear()

    # remove existing uv map
    bpy.ops.mesh.uv_texture_remove()

    # create new material
    img, bsdf_node, img_node, mesh_mat = create_new_material(
        obj_name=target_low_poly_obj_name, image_file_path=image_file_path, mat_number=mat_number, image_qual=image_qual, image_texture_quality=image_texture_quality)

    # create smart uv map
    uv_map_create(image_texture_margin=image_texture_margin,
                  image_texture_quality=image_texture_quality)

    save_file('Saved File')

    # perform bake
    bake_low_poly(selected_obj=bpy.data.objects.get(selected_obj_name), duplicate_obj=bpy.data.objects.get(
        target_low_poly_obj_name), extrusion=extrusion, ray_distance=ray_distance, image_texture_margin=image_texture_margin)

    # save image
    img.save()

    print('\tImage saved')

    # attach material
    mesh_mat.node_tree.links.new(bsdf_node.inputs[0], img_node.outputs[0])

    print('\tImage linked to bsdf node')

    # Hide original
    bpy.data.objects.get(selected_obj_name).hide_viewport = True

    # switch to back to previous mode if not in object
    if (current_context_mode != 'OBJECT'):
        # back to whatever mode we were in
        bpy.ops.object.mode_set(mode=current_context_mode)

    print(f'Finished create_uv_material_bake for {target_low_poly_obj_name}\n')


def bake_low_poly(selected_obj: bpy.types.Object, duplicate_obj: bpy.types.Object, extrusion: float, ray_distance: float, image_texture_margin: int):
    """Perform a diffuse texture bake from the selected_obj to the duplicate_obj.
    Bake Settings:
    1. Render Engine = "CYCLES"
    2. Cycles Feature Set = "SUPPORTED"
    3. Set Cycle Device = "CPU"
    4. Cycle Preview Samples = 1024
    5. Cycles Samples = 1024
    6. Cycles Time Limit = 0
    7. Render Bake Target = 'IMAGE_TEXTURES'
    8. Render Bake Use Clear = True
    9. Render Bake Margin Type = 'ADJACENT_FACES'
    10. Render Bake Cage Extrusion = 0.06
    11. Render Bake Max Ray Distance = 0.6
    12. Render Bake Margin = 64
    13 Bake(type='DIFFUSE', pass_filter={'COLOR'})

    Args:
        selected_obj (bpy.data.object): The selected object where the baking will take this mesh texture and output it to the duplicate_obj
        duplicate_obj (bpy.data.object): The duplicated object that will be recieving the texture from the selected object
    """
    # log start
    print('\nStarting bake')

    # get current context mode and set to object if not
    current_context_mode = set_context_mode_get_current(mode='OBJECT')

    # record bake time
    bake_time_start = time.time()

    # Unhide original
    selected_obj.hide_viewport = False

    # select high poly
    bpy.data.objects[selected_obj.name].select_set(True)

    # set duplicate as active
    bpy.context.view_layer.objects.active = bpy.data.objects[duplicate_obj.name]

    # set render engine to cycles
    bpy.context.scene.render.engine = "CYCLES"

    # set feature set to supported
    bpy.context.scene.cycles.feature_set = 'SUPPORTED'

    # set device to cpu
    bpy.context.scene.cycles.device = 'CPU'

    # set preview samples
    bpy.context.scene.cycles.preview_samples = 1024

    # set render samples (20 is good speed and not a lot of texture loss but 1024 is cleaner)
    bpy.context.scene.cycles.samples = 1  # 5 # 1024

    # set render time limit to 0
    bpy.context.scene.cycles.time_limit = 0

    # set output to image texture
    bpy.context.scene.render.bake.target = 'IMAGE_TEXTURES'

    # clear image set to true
    bpy.context.scene.render.bake.use_clear = True

    # set margin type to adjecent faces
    bpy.context.scene.render.bake.margin_type = 'ADJACENT_FACES'

    # selected tp active set to True - THIS IS IMPORTANT OTHERWISE IT WILL BAKE OVER THE SELECTED TEXTURES AND WILL BECOME BLACK!!!
    bpy.context.scene.render.bake.use_selected_to_active = True

    # set cage extrusion
    bpy.context.scene.render.bake.cage_extrusion = extrusion

    # set ray distance
    bpy.context.scene.render.bake.max_ray_distance = ray_distance

    # set bake margin - set to image texture margin for 8k its 64px
    bpy.context.scene.render.bake.margin = image_texture_margin

    # set bake type and pass filter in case below fails due to blender bugs of 3.6
    bpy.context.scene.cycles.bake_type = 'DIFFUSE'
    bpy.context.scene.render.bake.use_pass_direct = False
    bpy.context.scene.render.bake.use_pass_indirect = False

    # bake
    bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'})

    # switch to back to previous mode if not in object
    if (current_context_mode != 'OBJECT'):
        # back to whatever mode we were in
        bpy.ops.object.mode_set(mode=current_context_mode)

    # Show bake time
    print("Baking took:", time.strftime(
        "%H hours, %M minutes and %S seconds to Complete\n", time.gmtime(time.time()-bake_time_start)))


def output_mesh_stats(was_no_mesh_supplied: bool, duplicate_obj_name: str, bm: Optional[bmesh.types.BMesh] = None):
    """Output current mesh stats of the mesh supplied or will create a new mesh and get from the current context object. It is preferable to supply a mesh as this reduces execution time.

    Warning:
        If no mesh is supplied, it will remove it at the end. But if one is supplied remember to free it after it is called as this will not.

    Args:
        was_no_mesh_supplied (bool): Set to true if not supplying mesh 
        bm (Optional[bmesh.types.BMesh], optional): This is bmesh that will be used for the method, it must be of bmesh.types.BMesh and will create one if not supplied. Defaults to None.
    """

    # if the bm is none but the flag is set to false then a mistake has occured and needs to be created any way
    if (was_no_mesh_supplied or bm is None):
        # create new bmesh
        bm, _ = create_bm_from_mesh_set_mode_to_object(duplicate_obj_name)

        # set to true in case of user error
        was_no_mesh_supplied = True

    print(
        f"\nThere is {len(bm.verts[:])} vertices, {len(bm.edges[:])} edges and {len(bm.faces[:])} faces\n")

    # remove bmesh if no mesh was supplied
    if (was_no_mesh_supplied):
        # remove bmesh data
        bm.free()


def split_mesh_create_uv_material_bake_rejoin(selected_obj_name: str, final_obj_name: str, image_file_path: str, extrusion: float, ray_distance: float, image_texture_margin: int, mat_number: int = 1, image_qual: float = 1024, image_texture_quality: float = 1024):

    print('\nStarting split_mesh_create_uv_material_bake_rejoin')

    # get current context mode and set to object if not
    current_context_mode = set_context_mode_get_current(mode='EDIT')

    # Seperate by material
    bpy.ops.mesh.separate(type='MATERIAL')
    # Object Mode
    bpy.ops.object.mode_set(mode='OBJECT')

    print("\tObject has been seperated by material")

    print("\tRenaming split mesh objects")

    new_obj_name = []
    # get a list of all the selected objs from the seperation store names so they aren't lost when selecting and rename
    for index, obj in enumerate(bpy.context.selected_objects, start=1):

        # set object as active
        bpy.context.view_layer.objects.active = bpy.data.objects[obj.name]

        # Rename obj to include low_poly and part
        bpy.context.active_object.data.name = (
            f'COMPLETE_Low_Poly_{image_qual}K_Part_{str(index)}'
        )
        bpy.context.active_object.name = (
            f'COMPLETE_Low_Poly_{image_qual}K_Part_{str(index)}'
        )

        # add to new name list
        new_obj_name.append(bpy.context.active_object.name)

    print("\tRenaming split mesh objects DONE")

    # loop and hide all objs to help speed
    for obj_name in new_obj_name:
        bpy.data.objects.get(obj_name).hide_viewport = True

    # loop through list and clear old material, then create material and uv, then bake image
    for index, obj_name in enumerate(new_obj_name, start=1):
        # unhide this obj
        bpy.data.objects.get(obj_name).hide_viewport = False

        # Hide original - incase not first loop to help with speed
        bpy.data.objects.get(selected_obj_name).hide_viewport = True

        # deselect all objs so they dont get uv unwrapped together
        bpy.ops.object.select_all(action='DESELECT')

        # set object as active
        bpy.context.view_layer.objects.active = bpy.data.objects[obj_name]

        create_material_uv_and_bake(selected_obj_name=selected_obj_name, target_low_poly_obj_name=obj_name, image_file_path=image_file_path, extrusion=extrusion,
                                    ray_distance=ray_distance, image_texture_margin=image_texture_margin, mat_number=mat_number, image_qual=image_qual, image_texture_quality=image_texture_quality)

        # hide to help with speed and memory
        bpy.data.objects.get(obj_name).hide_viewport = True

    # Hide original
    bpy.data.objects.get(selected_obj_name).hide_viewport = True

    # deselect all objs
    bpy.ops.object.select_all(action='DESELECT')

    print("\tAll seperated objects have been uv mapped, new material created, baked, image saved and nodes linked")

    print("\tSelecting all seperated objects")

    # loop through list and select all
    for obj_name in new_obj_name:
        # unhide this obj
        bpy.data.objects.get(obj_name).hide_viewport = False
        bpy.data.objects[obj_name].select_set(True)

    print("\tSelecting all seperated objects DONE")

    # set first object as active
    bpy.context.view_layer.objects.active = bpy.data.objects[new_obj_name[0]]

    # join all objects into first object of selected_obj_name list
    bpy.ops.object.join()

    print("\tAll objects joined")

    # rename joined obj
    bpy.data.objects[new_obj_name[0]].name = final_obj_name
    bpy.context.active_object.name = final_obj_name

    # Turn off Auto Smooth for low poly
    bpy.data.objects.get(final_obj_name).data.use_auto_smooth = False

    # remove overlap verts from join
    remove_doubles_from_obj(bpy.data.objects.get(final_obj_name))

    # switch to back to previous mode if not in object
    if (current_context_mode != 'OBJECT'):
        # back to whatever mode we were in
        bpy.ops.object.mode_set(mode=current_context_mode)

    print('Finished split_mesh_create_uv_material_bake_rejoin\n')


def create_vertex_group(group_name: str, strength: int, duplicate_obj_name: str):
    """Create a vertex group for duplicate_obj with the currently selected vertices and name the group with the group_name input and a vertex group strength of the input strength

    Args:
        group_name (str): The name for the new Vertex Group
        strength (int): The strength value for the Vertex Group
    """
    print("\nStarting create_vertex_group")
    # create new vertex group with name provided for duplicate
    group = bpy.data.objects.get(
        duplicate_obj_name).vertex_groups.new(name=group_name)

    # get current context mode and set to object if not
    current_context_mode = set_context_mode_get_current(mode='OBJECT')

    # get selected vertices
    selectedVerts = [
        v for v in bpy.context.active_object.data.vertices if v.select]

    vertex_indices = [v.index for v in selectedVerts]
    group.add(vertex_indices, strength, 'REPLACE')

    # switch to back to previous mode if not in object
    if (current_context_mode != 'OBJECT'):
        # back to whatever mode we were in
        bpy.ops.object.mode_set(mode=current_context_mode)
    print("Completed create_vertex_group\n")


def seam_mark_dissolve(bm: bmesh.types.BMesh, edge_sharpness=15):
    """Will create a seam from edge sharpness select of edge_sharpness and perform a limited dissolve of double the input while delimiting seams

    Args:
        edge_sharpness (int, optional): The degree of sharpness in integers for seam creation and dissolve. Defaults to 15.
    """

    # double edge sharpness for dissolve
    dissolve_angle = radians(edge_sharpness * 2)

    # print starting seam mark dissolve
    print(f"\nStarting seam mark dissolve with deg set to {edge_sharpness}")

    # get current context mode and set to object if not
    current_context_mode = set_context_mode_get_current(mode='OBJECT')

    # create seam
    create_clear_seam(bm=bm, edge_sharpness=edge_sharpness, clear=False)

    # perform limited dissolve of dissolve_angle
    bmesh.ops.dissolve_limit(
        bm,
        angle_limit=radians(dissolve_angle),
        use_dissolve_boundaries=False,
        verts=bm.verts[:],
        edges=bm.edges[:],
        delimit={'NORMAL', 'SEAM'},
    )

    # flatten faces to make more planar and help with other methods
    bmesh.ops.planar_faces(bm, faces=bm.faces[:], iterations=2, factor=1.0)

    # remove edges and faces with no length or area
    bmesh.ops.dissolve_degenerate(bm, dist=0, edges=bm.edges[:])

    # clear seam data
    create_clear_seam(bm=bm, clear=True)

    # switch to back to previous mode if not in object
    if (current_context_mode != 'OBJECT'):
        # back to whatever mode we were in
        bpy.ops.object.mode_set(mode=current_context_mode)

    print("Completed seam_mark_dissolve\n")


def merge_double_key_seam(was_no_mesh_supplied: bool, duplicate_obj_name: str, angle=5, dist=0.0001, bm: bmesh.types.BMesh = None, target_obj_name: str = None):
    """merge double key seam 
    TODO
    Args:
        was_no_mesh_supplied (bool): _description_
        duplicate_obj_name (str): _description_
        angle (int, optional): _description_. Defaults to 5.
        dist (float, optional): _description_. Defaults to 0.0001.
        bm (bmesh.types.BMesh, optional): _description_. Defaults to None.
        target_obj_name (str, optional): _description_. Defaults to None.
    """

    print(
        f"\nStarting merge_double_key_seam with angle of {angle} for seam and a merge distance of {dist}")

    # start timer
    merge_double_key_seam_start = time.time()

    # get current context mode and set to object if not
    current_context_mode = set_context_mode_get_current(mode='OBJECT')

    if (target_obj_name is None):
        target_obj_name = duplicate_obj_name

    if (was_no_mesh_supplied or bm is None):
        # get current context mode and set to object if not and get data from duplicate
        bm, current_context_mode = create_bm_from_mesh_set_mode_to_object(
            target_obj_name)
        was_no_mesh_supplied = True

    # create seam
    create_clear_seam(bm, edge_sharpness=angle, clear=False)

    # loop through edges and get verts marked seam
    seam_edges = [e for e in bm.edges[:] if e.seam]
    print("\tgot seam edges")

    # get all seam verts from edges - will double up
    seam_verts = list({v for e in seam_edges for v in e.verts})

    print("\tgot seam verts and double ups removed")

    non_in_seam_verts = list(set(bm.verts[:]) - set(seam_verts))
    print("\tgot verts not in seam")

    # Find Doubles.
    # Takes input verts and find vertices they should weld to. Outputs a mapping slot suitable for use with the weld verts bmop.
    # If keep_verts is used, vertices outside that set can only be merged with vertices in that set.
    doubles = bmesh.ops.find_doubles(
        bm, verts=non_in_seam_verts, keep_verts=seam_verts, dist=dist)
    print("\tfound doubles")

    print(
        f"\tNumber of verts: {len(bm.verts[:])}, Number of Edges: {len(bm.edges[:])}, Number of Faces: {len(bm.faces[:])} before weld")

    bmesh.ops.weld_verts(bm, targetmap=doubles['targetmap'])

    print(
        f"\tNumber of verts: {len(bm.verts[:])}, Number of Edges: {len(bm.edges[:])}, Number of Faces: {len(bm.faces[:])} after weld")

    # clear seam
    create_clear_seam(bm, clear=True)

    if (was_no_mesh_supplied):
        # transfer bmesh data to duplicate obj remove bmesh data
        bm_to_mesh_free(bm, target_obj_name)

    # switch to back to previous mode if not in object
    if (current_context_mode != 'OBJECT'):
        # back to whatever mode we were in
        bpy.ops.object.mode_set(mode=current_context_mode)

    # output cleanup loop time
    print("It Took prep for merge_double_key_seam:", time.strftime(
        "%H hours, %M minutes and %S seconds to Complete\n", time.gmtime(time.time()-merge_double_key_seam_start)))


def delete_wire(bm: bmesh.types.BMesh):
    """Delete all wire edges and verts from bmesh

    Args:
        bm (bmesh.types.BMesh): bmesh object to delete wire edges from
    """

    # select all wire verts
    delete_geom = [vert for vert in bm.verts if vert.is_wire]

    # delete selected verts
    bmesh.ops.delete(bm, geom=delete_geom, context="VERTS")

    # empty array if data remains
    delete_geom.clear()

    # select remaining wire edges
    delete_geom = [edge for edge in bm.edges if edge.is_wire]

    # delete selected edges only, as verts may be attached to faces or other edges
    bmesh.ops.delete(bm, geom=delete_geom, context="EDGES")


def create_new_material(obj_name: str, image_file_path: str, mat_number: str = 1, image_qual: float = 1024, image_texture_quality: float = 1024):
    """Create a new material for duplicate_obj called LowPolyMat by:
    1. Create new material called "LowPolyMat"
    2. Create a new ShaderNodeUVMap and inputs the generated uv map for the duplicate_obj
    3. Create a new Image and configures it to be:
        a. Name it with the duplicate_obj.name + " texture"
        b. 8K Texture
        c. Use Alpha
        d. Set RGBA to (0,0,0,0)
    4. Create a new ShaderNodeTexImage and configures it to be:
        a. Set name to "BakeTex_node"
        b. Assign it the new image
    5. Links the ShaderNodeUVMap to the ShaderNodeTexImage
    6. Append the new material to duplicate_obj
    """
    # start timer
    mat_time_start = time.time()

    # get current context mode and set to object if not
    current_context_mode = set_context_mode_get_current(mode='OBJECT')

    # log start
    print('\nCreating material')

    # create new material
    new_material = bpy.data.materials.new(
        name=f"LowPoly_{image_qual}K_Mat{mat_number}"
    )
    # use node tree
    new_material.use_nodes = True

    # get node tree
    nodes = new_material.node_tree.nodes
    bsdf_node = nodes["Principled BSDF"]

    # set specular to 0
    bsdf_node.inputs[7].default_value = 0

    # set roughness to 1
    bsdf_node.inputs[9].default_value = 1

    # create uv node
    uv_shader_map_node = nodes.new(type="ShaderNodeUVMap")
    uv_shader_map_node.location = (-900, 0)
    uv_shader_map_node.uv_map = "UVMap"

    # new image
    img_name = f'{obj_name}_texture_{mat_number}'
    img = bpy.data.images.new(
        img_name, image_texture_quality, image_texture_quality, alpha=False)
    img.generated_color = (0, 0, 0, 0)
    img.filepath_raw = f"{image_file_path}{img_name}.bmp"
    img.file_format = 'BMP'

    tex_image_node = nodes.new(type="ShaderNodeTexImage")
    tex_image_node.location = (-450, 0)
    tex_image_node.name = f'BakeTex_Node_{mat_number}'
    tex_image_node.image = img

    # link uv and tex
    new_material.node_tree.links.new(
        tex_image_node.inputs[0], uv_shader_map_node.outputs[0])

    # append new material
    bpy.data.objects.get(
        obj_name).data.materials.append(new_material)

    # switch to back to previous mode if not in object
    if (current_context_mode != 'OBJECT'):
        # back to whatever mode we were in
        bpy.ops.object.mode_set(mode=current_context_mode)

    # output material time
    print("It Took create_new_material:", time.strftime(
        "%H hours, %M minutes and %S seconds to Complete\n", time.gmtime(time.time()-mat_time_start)))

    return img, bsdf_node, tex_image_node, new_material


def uv_map_create(image_texture_margin, image_texture_quality):
    """Create a UV Map for duplicate_obj using the smart_project method with a island margin of 0.0001
    """
    # start uv timer
    uv_time_start = time.time()

    # get current context mode and set to edit if not
    current_context_mode = set_context_mode_get_current(mode='EDIT')

    # log start
    print('\nStarted uv_map_create')

    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
    bpy.ops.mesh.select_all(action='SELECT')

    print("\tAll Faces Selected")

    '''
    Image texture margin divided by the image texture quality is the correct way to work out the correct island margin for an unwrap THIS IS IMPORTANT TO BE CORRECT
    AS AN INCORRECT ISLAND MARGIN WILL RESULT IN TEXTURES BLEEDING INTO THE INCORRECT FACES IF TOO SMALL AND IF TO HIGH WILL RESULT IN THE ISLANDS BEING SCALED DOWN TO FIT
    while in some meshes this may be fine especially if the material assigned is the same colour it quickly prevents reuse of the map and when performing a diffuse texture bake
    it will cause lots of issues. 
    '''
    bpy.ops.uv.smart_project(angle_limit=radians(90), margin_method='ADD',
                             island_margin=(image_texture_margin/image_texture_quality), area_weight=0.0, correct_aspect=True, scale_to_bounds=False)

    # while check_uv_map := bpy.ops.uv.select_overlap():
    #     print("UV Map has Overlaps")
    #     bpy.ops.uv.mark_seam()
    #     bpy.ops.mesh.select_all(action='SELECT')
    #     bpy.ops.uv.smart_project(angle_limit=radians(90), margin_method='ADD',
    #                              island_margin=(image_texture_margin/image_texture_quality), area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
    #     bpy.ops.mesh.select_all(action='DESELECT')

    print(
        f"\tObject has been UV unwrapped with smart project with settings set to: angle 90 deg, island margin {image_texture_margin / image_texture_quality}, area weight 0.0, correct aspect True and scale to bounds True"
    )

    # switch to back to previous mode if not in edit
    if (current_context_mode != 'EDIT'):
        # back to whatever mode we were in
        bpy.ops.object.mode_set(mode=current_context_mode)

    # output uv timer
    print("It Took uv_map_create:", time.strftime(
        "%H hours, %M minutes and %S seconds to Complete\n", time.gmtime(time.time()-uv_time_start)))


def error_has_occured(arg0):
    save_file('Saved File\n')

    raise Exception(arg0)


def create_clear_seam(bm: bmesh.types.BMesh, edge_sharpness=15, clear=False):
    """Creates seams at specified edge_sharpness or clears all seams

    Args:
        edge_sharpness (int, optional): The angle of desired sharpness in degrees, only use int values. Defaults to 15.
        clear (bool, optional): Bool value whether to clear all seams or create them at the specified edge_sharpness. Defaults to False.
    """

    print(f"\nStarting create_clear_seam")

    edge_rad = radians(edge_sharpness)

    if (clear):
        for e in bm.edges:
            e.seam = False
        print("\tSeams Cleared")
    else:
        # loop through edges
        for e in bm.edges:
            # set edge if it meets criteria and set seam
            if e.smooth == False and e.calc_face_angle() >= edge_rad:
                e.select_set(True)
                e.seam = True
        print(f"\tSeams created for edge sharpness of: {edge_sharpness}")

    print("Completed create_clear_seam\n")
