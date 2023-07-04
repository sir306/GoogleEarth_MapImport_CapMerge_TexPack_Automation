import math
import time
import bpy
import bmesh
import os
import sys
import glob

# import importlib
import pathlib


target_image_size = 8 # this prevents lily text from going over 8192 x 8192 swap 8 with any int value from 1 to 16
capture_resolution = 1024
shade_flat = True  # set to false if want stock face shading
remove_doubles_verts = True  # set to false if want to stock import
merge_distance = 0.0001  # merge distance for remove doubles
complete_obj_name = 'HighPoly_Model' # what should your final lily cap merge be called

# this script doesn't use auto smooth by default but if you do want it on set auto_smooth_on_off to True and set the smooth angle to how you like
auto_smooth_on_off = False
auto_smooth_angle = 0.0 # set to 0 by default to ensure auto smooth is off
export_model = False # do you want to export model as fbx at the end
delete_rdc_files = False # to delete rdc files after import, set this to true but only do it after you have tested a small amount or backup the rdc files elsewhere


def main():

    file_paths = [GENERATED_TEXTS_FILE_PATH, LOG_FOLDER_PATH,
                  LILY_IMAGE_FILE_PATH, EXPORT_FBX_FILE_PATH]
    check_and_create_file_path(file_paths)

    print_save_log(filepath=f"{LOG_FILE_PATH}",
                   line="Checking Directory Paths Completed")

    print_save_log(filepath=f"{LOG_FILE_PATH}", line="Starting Addon Checks")
    should_stop, has_lily_capture_merger, has_texture_packer = check_for_plugins()

    if should_stop:
        print_save_log(filepath=f"{GENERATED_TEXTS_FILE_PATH}RuntimeError.txt",
                       line="Required Plugin Google Maps Model Importer not found, TERMINATING SCRIPT")
        return

    print_save_log(filepath=f"{LOG_FILE_PATH}", line="Starting Script")

    # set render engine to workbench for speed
    bpy.context.scene.render.engine = "BLENDER_WORKBENCH"

    # clean up data by purging and removing orphans and empty collections
    clean_up_data()

    files = glob.glob(f"{RDC_FILE_PATH}*.rdc")

    if not files:
        print_save_log(
            filepath=f"{GENERATED_TEXTS_FILE_PATH}RuntimeError.txt", line="No RDC files found")
        return

    if len(files) == 1 | has_lily_capture_merger == False:
        main_col = import_all_rdc_files_no_merge(files=files)
        print_save_log(filepath=f"{LOG_FILE_PATH}",
                       line="import_all_rdc_files_no_merge completed")

    else:
        main_col = import_and_lily_capture_merge(files=files)

        print_save_log(filepath=f"{LOG_FILE_PATH}",
                       line="import_and_lily_capture_merge completed")

    if has_texture_packer:
        col_name = has_texture_packer_perform_pack_ops(main_col)

    turn_auto_smooth_on_off(obj_name=complete_obj_name,
                            turn_on_off=auto_smooth_on_off, auto_smooth_angle=auto_smooth_angle)

    if shade_flat:

        shade_face_flat(obj_name=complete_obj_name)

        write_to_file(filepath=f"{LOG_FILE_PATH}",
                      line="shade_face_flat completed")

        save_file('Saved after shade_face_flat')

    if remove_doubles_verts:

        remove_doubles_from_obj(
            obj_name=complete_obj_name, merge_distance=merge_distance)

        write_to_file(filepath=f"{LOG_FILE_PATH}",
                      line="remove_doubles_from_obj completed")

        save_file('Saved after remove_doubles_from_obj')

    if export_model:
        export_model_to_fbx(
            col_name=col_name, export_file_path=f"{EXPORT_FBX_FILE_PATH}{complete_obj_name}.fbx")

        write_to_file(filepath=f"{LOG_FILE_PATH}",
                      line="export_model_to_fbx completed")

        save_file('Saved after export_model_to_fbx')

    # update view layer so orphan data can be removed
    # bpy.context.view_layer.update()

    print('Removing empty collections')
    remove_empty_collections()

    # uncomment this to perform a clean up of orphan data and purge as well
    # it is quicker to do in editor at this point due to the number of objects and purging at this point will remove all
    # clean_up_data()

    save_file('Saved after remove_empty_collections')

    # set render engine to workbench for speed
    bpy.context.scene.render.engine = "BLENDER_EEVEE"

    print("Script Completed")

    write_to_file(filepath=f"{LOG_FILE_PATH}", line="Script completed")


def delete_rdc_files(file_path: str):

    print_save_log(
        filepath=f"{GENERATED_TEXTS_FILE_PATH}deleted_files.txt", line=f"Deleting {file_path}")
    # delete rdc file
    os.remove(file_path)
    print_save_log(
        filepath=f"{GENERATED_TEXTS_FILE_PATH}deleted_files.txt", line=f"Deleted {file_path}")


def has_texture_packer_perform_pack_ops(main_col):

    print_save_log(filepath=f"{LOG_FILE_PATH}",
                   line="Starting has_texture_packer_perform_pack_ops")
    # SELECT ALL OBJS
    bpy.ops.object.select_all(action='SELECT')

    # Apply Transform scale, location, rotation
    bpy.ops.object.transform_apply(
        location=True, rotation=True, scale=True, properties=True, isolate_users=False)

    # DESELECT ALL OBJS
    bpy.ops.object.select_all(action='DESELECT')

    # main_col = 'col_1' # debug

    global capture_resolution
    capture_resolution = get_max_image_size()

    print_save_log(filepath=f"{LOG_FILE_PATH}",
                   line="get_max_image_size completed")

    min_max_coords, obj_dict = rename_objs_and_store_location(main_col)

    print_save_log(filepath=f"{LOG_FILE_PATH}",
                   line="rename_objs_and_store_location completed")

    area_size = get_area_size_for_col_and_save_to_file(main_col)

    print_save_log(filepath=f"{LOG_FILE_PATH}",
                   line="get_area_size_for_col_and_save_to_file completed")

    required_images, _, _ = get_texel_denisty_requirements(area_size=area_size)

    print_save_log(filepath=f"{LOG_FILE_PATH}",
                   line="get_texel_denisty_requirements completed")

    box_sections = define_guide_box(min_max_coords, required_images)

    print_save_log(filepath=f"{LOG_FILE_PATH}",
                   line="define_guide_box completed")

    grouping_dict = sort_object_into_location_groups(
        map_chunk=box_sections, obj_dict=obj_dict)

    print_save_log(filepath=f"{LOG_FILE_PATH}",
                   line="sort_object_into_location_groups completed")

    collection_names = sort_groupings_into_new_col(
        area_groupings=grouping_dict)

    print_save_log(filepath=f"{LOG_FILE_PATH}",
                   line="sort_groupings_into_new_col completed")

    # collection_names=['Pack_1'] # debug

    result = texture_pack_group(col_names=collection_names)

    print_save_log(filepath=f"{LOG_FILE_PATH}",
                   line="texture_pack_group completed")

    print_save_log(filepath=f"{LOG_FILE_PATH}",
                   line="Completed has_texture_packer_perform_pack_ops")

    return result


def get_texel_denisty_requirements(area_size: dict):

    # check key exists
    if ("Total" not in area_size):
        print("No dictionary with Total key supplied!")
        return None

    target_image_quality = 1024 * target_image_size
    total_target_px = target_image_quality * target_image_quality
    capture_texel_density = capture_resolution / 100  # TODO
    current_area_total = area_size["Total"]
    # as the model is in meter square convert to cm square as tex denisty is calculated per cm
    current_area_total_cm = current_area_total * 10000
    # calculate number of pixels for mesh area using target density
    total_number_of_pixels_req = current_area_total_cm * capture_texel_density

    required_number_of_images = total_number_of_pixels_req / total_target_px

    line = f"Currently the target images has {capture_texel_density} a pixel density, to get a max image size of {target_image_quality} x {target_image_quality}, the currently selected objects will require {total_number_of_pixels_req} pixels, the required number of images is {required_number_of_images} and rounded up to {math.ceil(required_number_of_images)}"

    # write obj name and size to file not needed but may be helpful for debugging and working out calculations
    print_save_log(
        filepath=f"{GENERATED_TEXTS_FILE_PATH}texel_denisty_requirements_file.txt", line=line)

    return int(math.ceil(required_number_of_images)), total_target_px, total_number_of_pixels_req


def check_for_plugins():

    print_save_log(filepath=f"{LOG_FILE_PATH}",
                   line="Starting check_for_plugins")

    should_stop = True
    has_lily_capture_merger = False
    has_lily_texture_packer = False

    # get all installed addons
    addons = bpy.context.preferences.addons
    for addon in addons:
        # check import_rdc.google_maps exists
        # check bl_idname exists "import_rdc.google_maps"
        if 'MapsModelsImporter' in addon.module:
            print_save_log(
                filepath=f"{GENERATED_TEXTS_FILE_PATH}RuntimeError_Addons.txt", line="MapsModelsImporter plugin not installed, please install and try again")
            should_stop = False

        # check import_rdc.lily_capture exists
        if "LilyCaptureMerger" in addon.module:
            print_save_log(
                filepath=f"{GENERATED_TEXTS_FILE_PATH}RuntimeError_Addons.txt", line="LilyCaptureMerger plugin not installed")
            has_lily_capture_merger = True

        # check lily_texture_packer exists
        if "LilyTexturePacker" in addon.module:
            print_save_log(
                filepath=f"{GENERATED_TEXTS_FILE_PATH}RuntimeError_Addons.txt", line="LilyTexturePacker plugin not installed")
            has_lily_texture_packer = True

    print_save_log(filepath=f"{LOG_FILE_PATH}",
                   line=f"Completed check_for_plugins, User has MapsModelsImporter : {not should_stop}, LilyCaptureMerger : {has_lily_capture_merger}, LilyTexturePacker : {has_lily_texture_packer}")

    return should_stop, has_lily_capture_merger, has_lily_texture_packer


def import_and_lily_capture_merge(files: list[str]):

    start_time = time.time()
    errors_raised = 0

    master_col = bpy.context.scene.collection

    print_save_log(
        filepath=f"{GENERATED_TEXTS_FILE_PATH}importing_rdc_full_log.txt", line=f"Starting RDC Imports, Number of files to import: {len(files)}")

    print("Please wait for imports to complete, this may take a while")
    # import progress
    wm = bpy.context.window_manager
    wm.progress_begin(0, 100)
    wm.progress_update(0)

    for i, f in enumerate(files, start=1):
        _, tail = os.path.split(f)
        col_name = f"col_{i}"

        my_col = create_col(master_col, col_name=col_name)

        print(f"Attempting import file named {tail}")
        errors_raised = import_rdc_file(
            file=f, name=tail, errors_raised=errors_raised)

        bpy.data.collections[col_name].hide_viewport = True
        my_col.hide_viewport = True

        # update progress
        current_progress = i / len(files) * 100
        current_progress = round(current_progress, 2)
        wm.progress_update(current_progress)
        print(f"Current progress for import is: {current_progress}%")

        if i == 1:
            continue

        print_save_log(filepath=f"{GENERATED_TEXTS_FILE_PATH}import_and_lily_capture_merge.txt",
                       line=f"Merging current imports, to prevent memory issues, this may take a while, current progress for all imports is {current_progress}%")
        layer_col = bpy.context.view_layer.layer_collection
        # DESELECT ALL OBJS
        bpy.ops.object.select_all(action='DESELECT')
        main_col = lily_capture_merger_call(layer_col=layer_col)

    # end progress
    wm.progress_end()

    print_save_log(
        filepath=f"{GENERATED_TEXTS_FILE_PATH}importing_rdc_full_log.txt", lines=["Imports have been completed.", f"It took {time.time() - start_time} seconds to complete and import {len(files)} number of files ", f"There were {errors_raised} errors raised during the import process."])

    return main_col


def import_all_rdc_files_no_merge(files: list[str]):

    start_time = time.time()
    errors_raised = 0

    master_col = bpy.context.scene.collection

    print_save_log(
        filepath=f"{GENERATED_TEXTS_FILE_PATH}importing_rdc_full_log.txt", line=f"Starting RDC Imports, Number of files to import: {len(files)}")

    print("Please wait for imports to complete, this may take a while")
    # import progress
    wm = bpy.context.window_manager
    wm.progress_begin(0, 100)
    wm.progress_update(0)

    for i, f in enumerate(files, start=1):
        _, tail = os.path.split(f)
        col_name = f"col_{i}"

        my_col = create_col(master_col, col_name=col_name)

        print(f"Attempting import file named {tail}")

        errors_raised = import_rdc_file(
            file=f, name=tail, errors_raised=errors_raised)

        bpy.data.collections[col_name].hide_viewport = True
        my_col.hide_viewport = True

        # update progress
        current_progress = i / len(files) * 100
        current_progress = round(current_progress, 2)
        wm.progress_update(current_progress)
        print(f"Current progress for import is: {current_progress}%")

    # end progress
    wm.progress_end()

    print_save_log(
        filepath=f"{GENERATED_TEXTS_FILE_PATH}importing_rdc_full_log.txt", lines=["Imports have been completed.", f"It took {time.time() - start_time} seconds to complete and import {len(files)} number of files ", f"There were {errors_raised} errors raised during the import process."])

    # col_1 is main collection if user has texture packer installed then this will be needed
    return 'col_1'


def import_rdc_file(file: str, name: str, errors_raised: int):
    try:
        bpy.ops.import_rdc.google_maps(
            filepath=(file), filter_glob=".rdc", max_blocks=-1)

        line = f"Successfully imported file named {name}, now hiding"

        print_save_log(filepath=f"{GENERATED_TEXTS_FILE_PATH}successful_import.txt",
                       line=line)

        write_to_file(
            filepath=f"{GENERATED_TEXTS_FILE_PATH}importing_rdc_full_log.txt", line=line)

        if delete_rdc_files:
            delete_rdc_files(file)

    except Exception as e:
        lines = [
            f"Failed to import file named {name}", f"--- Error Raised: {e} ---"]

        print_save_log(
            filepath=f"{GENERATED_TEXTS_FILE_PATH}unsuccessful_import.txt", lines=lines)

        write_to_file(
            filepath=f"{GENERATED_TEXTS_FILE_PATH}importing_rdc_full_log.txt", lines=lines)

        errors_raised += 1

    return errors_raised


def lily_capture_merger_call(layer_col):

    # layer_col_children[0] returns a tuple list ('col_1', bpy.data.scenes['Scene']...LayerCollection)
    layer_col_children = layer_col.children.items()
    print("Starting Lily Capture Merges on collections")

    # loop over children as list is in tuple with the name as key and the layer collection as struct we can seperate out k to get key name and v to the layer collection itself
    for k, v in layer_col_children:

        # as i want col_1 to be parent best to skip this after unhiding it and ref in code by name if you know it or assign a val to the first instance
        if (k == layer_col_children[0][0]):
            bpy.data.collections[k].hide_viewport = False
            v.hide_viewport = False
            continue
        print(f"Merging collection {k} with col_1")
        # print(k) # returns col_1
        # print(v) # returns <bpy_struct, LayerCollection("col_1") at 0x000001D630AF96C8>

        # unhide
        bpy.data.collections[k].hide_viewport = False
        v.hide_viewport = False

        if bpy.data.collections.get(k).objects:
            # select first object
            bpy.data.collections.get(k).objects[0].select_set(True)

        if bpy.data.collections.get('col_1').objects:
            # set first object as active
            bpy.context.view_layer.objects.active = bpy.data.collections.get(
                layer_col_children[0][0]).objects[0]

        # merge objects
        bpy.ops.object.lily_capture_merger()

        if bpy.data.collections.get(k).objects:
            # unselect first object
            bpy.data.collections.get(k).objects[0].select_set(False)

        move_objects_from_one_collection_to_target(bpy.data.collections.get(
            layer_col_children[0][0]), bpy.data.collections.get(k).objects)
        # bpy.context.scene.collection.children.get(layer_col_children[0][0]) -- case data.collections does not work with link

        print(f"Completed collection merge {k} with col_1")

    # remove unused collections
    remove_empty_collections()

    print("Lily capture merger has completed")

    # return the collection name holding all objects
    return layer_col_children[0][0]


def rename_objs_and_store_location(obj_col: str):

    bpy.ops.object.select_all(action="SELECT")

    bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS')

    bpy.ops.object.select_all(action="DESELECT")

    objs = bpy.data.collections.get(obj_col).objects

    # import progress
    wm = bpy.context.window_manager
    wm.progress_begin(0, 100)
    wm.progress_update(0)

    # create dict to hold obj name and key as location
    # obj_dict = dict({(obj.matrix_world.translation[0],obj.matrix_world.translation[1],obj.matrix_world.translation[2]) : obj.name for obj in objs })
    obj_dict = dict(
        {obj.name: (obj.location.x, obj.location.y, obj.location.z) for obj in objs})

    # # sort dict by values in relation to x and y -- note this works but obj locations can be a single float higher or lower in the same row so not always as expected
    # # due to some objs being smaller or bigger but will help with packing
    obj_dict = sorted(obj_dict.items(), key=lambda x: x[1][0])
    obj_dict = dict(obj_dict)

    # dict to hold min max coordinates for defining areas
    min_max_coords = {'min_x': 0, 'min_y': 0,
                      'min_z': 0, 'max_x': 0, 'max_y': 0, 'max_z': 0}

    new_obj_dict = {}

    # rename the objects and prefix it
    for i, (k, v) in enumerate(obj_dict.items(), start=1):

        min_max_coords["max_x"] = max(min_max_coords["max_x"], v[0])
        min_max_coords["max_y"] = max(min_max_coords["max_y"], v[1])
        min_max_coords["max_z"] = max(min_max_coords["max_z"], v[2])

        min_max_coords["min_x"] = min(min_max_coords["min_x"], v[0])
        min_max_coords["min_y"] = min(min_max_coords["min_y"], v[1])
        min_max_coords["min_z"] = min(min_max_coords["min_z"], v[2])

        # get object
        obj = bpy.data.objects.get(k)

        # rename object in outliner and data
        obj.name = f"{i}_section"
        obj.data.name = f"{i}_section"

        new_obj_dict[obj.name] = v

        # progress
        current_progress = i / len(objs) * 100
        print(
            f"\rCurrent progress for rename_objs_and_store_location is: {round(current_progress, 2)}%", end="\r", flush=True)
        # update progress
        wm.progress_update(current_progress)

    # end progress
    wm.progress_end()

    lines = [f"{k} : {v}" for k, v in new_obj_dict.items()]
    write_to_file(
        filepath=f"{GENERATED_TEXTS_FILE_PATH}obj_file.txt", lines=lines)

    return min_max_coords, new_obj_dict


def get_area_size_for_objs(objs: list[bpy.types.Object], area_file: list[str] = None):

    area_size_dict = dict({})

    bm = bmesh.new(use_operators=True)

    area_total = 0

    # loop over objs and get area data
    for obj in objs:
        # select current obj
        bpy.data.objects[obj.name].select_set(True)

        # get mesh data into bm
        bm.from_mesh(obj.data)
        bm.transform(obj.matrix_world)
        current_object_area = sum(f.calc_area() for f in bm.faces)

        area_size_dict[obj.name] = current_object_area

        area_total += current_object_area

        if (area_file is not None):
            area_file.append(
                f"Object name: {obj.name} | Area Size: {current_object_area}\n")

        area_size_dict["Total"] = area_total

        # deselect # obj
        bpy.data.objects[obj.name].select_set(False)

        bm.clear()  # clear data but not free it

    bm.free()  # remove bm from memory

    if (area_file is not None):
        # write total size to file and add to dictionary
        area_file.append(f"Total Area Size: {area_total}\n")
        print('here')
        return area_size_dict, area_file

    else:

        return area_size_dict


def get_area_size_for_col_and_save_to_file(col_name: str):

    objs = bpy.data.collections.get(col_name).objects

    area_txt = []

    area_size_dict, area_txt = get_area_size_for_objs(
        objs=objs, area_file=area_txt)

    # write obj name and size to file not needed but may be helpful for debugging and working out calculations
    write_to_file(
        filepath=f"{GENERATED_TEXTS_FILE_PATH}area_for_collection_{col_name}_file.txt", lines=area_txt)

    return area_size_dict


def define_guide_box(min_max_coords: dict = None, required_images: int = 1):
    # {'min_x':0, 'min_y':0, 'min_z':0, 'max_x':0, 'max_y':0, 'max_z':0}

    vector_groupings = []

    if (required_images == 1):
        vector_groupings.append(
            (min_max_coords['min_x'], min_max_coords['max_x'], min_max_coords['min_y'], min_max_coords['max_y']))
        text_to_write = [f"min_max_coords['min_x'] : {min_max_coords['min_x']}", f"min_max_coords['max_x'] : {min_max_coords['max_x']}",
                         f"min_max_coords['min_y'] : {min_max_coords['min_y']}", f"min_max_coords['max_y'] : {min_max_coords['max_y']}"]
        write_to_file(
            filepath=f"{GENERATED_TEXTS_FILE_PATH}vector_groupings_file.txt", lines=text_to_write)

        return vector_groupings  # all objects will fit into one image stop

    x_range = math.dist([min_max_coords['max_x']], [min_max_coords['min_x']])
    y_range = math.dist([min_max_coords['max_y']], [min_max_coords['min_y']])

    # z_range = math.dist([min_max_coords['max_z']],[min_max_coords['min_z']]) # likely un needed but helpful to hold onto for now

    # total chunk size
    x_chunk = x_range / required_images
    y_chunk = y_range / required_images

    # switch xmin, xmax with ymin, ymax if your model is orientedly differently and would suit that better
    for i in range(required_images + 1):
        # do left side of 0.0 for x
        xmin = min_max_coords['min_x'] + (x_chunk * i)
        xmax = min_max_coords['min_x'] + (x_chunk * (i + 1))

        # left y side
        for i in range(required_images + 1):
            ymin = min_max_coords['min_y'] + (y_chunk * i)
            ymax = min_max_coords['min_y'] + (y_chunk * (i + 1))

            vector_groupings.append([xmin, xmax, ymin, ymax])

    # sort in order
    vector_groupings.sort(key=lambda x: x[0])

    text_to_write = [f"{v}" for v in vector_groupings]
    text_to_write.extend([f"min_max_coords['min_x'] : {min_max_coords['min_x']}", f"min_max_coords['max_x'] : {min_max_coords['max_x']}",
                         f"min_max_coords['min_y'] : {min_max_coords['min_y']}", f"min_max_coords['max_y'] : {min_max_coords['max_y']}"])
    write_to_file(
        filepath=f"{GENERATED_TEXTS_FILE_PATH}vector_groupings_file.txt", lines=text_to_write)

    return vector_groupings


def sort_object_into_location_groups(map_chunk: list, obj_dict: dict):

    sort_chunk = {}

    # only one image required so put all in sort chunk
    if len(map_chunk) == 1:
        sort_chunk['Chunk_1'] = list(obj_dict.keys())

    found = set()
    for i, chunk in enumerate(map_chunk, start=1):

        for k, v in obj_dict.items():

            if (k in found):
                continue

            if (chunk[0] <= v[0] <= chunk[1] and chunk[2] <= v[1] <= chunk[3]):
                if f"Chunk_{i}" not in sort_chunk:
                    sort_chunk[f"Chunk_{i}"] = []
                sort_chunk[f"Chunk_{i}"].append(k)
                found.add(k)
    lines = [f"{k} : {v}" for k, v in sort_chunk.items()]
    write_to_file(
        filepath=f"{GENERATED_TEXTS_FILE_PATH}group_file.txt", lines=lines)

    return sort_chunk


def sort_groupings_into_new_col(area_groupings: dict):

    # return no area grouping
    if not area_groupings:
        return []

    layer_col = bpy.context.scene.collection
    collection_names = []
    current_objs_for_collection = []

    if len(area_groupings) == 1:
        # rename collection
        col = bpy.data.collections.get('col_1')
        col.name = "HighPoly_Pack_1"

        # save col stats
        get_area_size_for_col_and_save_to_file("HighPoly_Pack_1")

        # add to collection name
        collection_names.append(col.name)

    else:
        i = 1
        for v in area_groupings.values():
            # add objs to collection and get areasize

            current_objs_for_collection.extend(
                [bpy.data.objects.get(x) for x in v])
            area_size_dict = get_area_size_for_objs(
                objs=current_objs_for_collection)
            # get current and target density
            _, total_target_px, total_number_of_pixels_req = get_texel_denisty_requirements(
                area_size=area_size_dict)

            # still space for image add more objs
            if (total_target_px > total_number_of_pixels_req):
                continue

            # unlikey to be exact match but if is then this collection is ready for packing
            elif (total_target_px == total_number_of_pixels_req):

                # create collection and move objects to collection
                new_col_layer = create_col(layer_col, f"HighPoly_Pack_{i}")
                new_col = bpy.data.collections.get(new_col_layer.name)
                move_objects_from_one_collection_to_target(
                    target_col=new_col, move_objs=current_objs_for_collection)

                # save col stats
                get_area_size_for_col_and_save_to_file(f"HighPoly_Pack_{i}")

                # clear list
                current_objs_for_collection = []

                # add to collection name
                collection_names.append(f"HighPoly_Pack_{i}")

                i += 1

            # over threshold keep removing objs till back in threshold
            else:
                excess = []  # hold objects that keep it over the required pixels
                # reduce objects till pixels fit inside image target is
                while total_target_px < total_number_of_pixels_req:

                    # keep popping and appending to excess till current pixel total for objs match target
                    ob = current_objs_for_collection.pop()
                    excess.append(ob)

                    # get updated area size and pixels
                    area_size_dict = get_area_size_for_objs(
                        objs=current_objs_for_collection)
                    _, total_target_px, total_number_of_pixels_req = get_texel_denisty_requirements(
                        area_size=area_size_dict)

                # create collection and move objects to collection
                new_col_layer = create_col(layer_col, f"HighPoly_Pack_{i}")
                new_col = bpy.data.collections.get(new_col_layer.name)
                move_objects_from_one_collection_to_target(
                    target_col=new_col, move_objs=current_objs_for_collection)

                # save col stats
                get_area_size_for_col_and_save_to_file(f"HighPoly_Pack_{i}")

                # add to collection name
                collection_names.append(f"HighPoly_Pack_{i}")

                i += 1
                # set list to excess
                current_objs_for_collection = excess

        # if there are still objs left over add to own collection
        if (len(current_objs_for_collection) > 0):
            new_col_layer = create_col(layer_col, "HighPoly_Pack_Leftover")
            new_col = bpy.data.collections.get(new_col_layer.name)
            move_objects_from_one_collection_to_target(
                target_col=new_col, move_objs=current_objs_for_collection)

            # add to collection name
            collection_names.append("HighPoly_Pack_Leftover")

    remove_empty_collections()

    return collection_names


def texture_pack_group(col_names: list[str]):

    print("\nStarting Lily Texture Packer on collections")

    # DESELECT ALL OBJS
    bpy.ops.object.select_all(action='DESELECT')

    # loop over children as list is in tuple with the name as key and the layer collection as struct we can seperate out k to get key name and v to the collection itself
    for col in col_names:

        print(f"\tCurrent Collection: {col}")

        objs = bpy.data.collections.get(col).objects
        for ob in objs:
            ob.select_set(True)

        print("\t\tStarting Lily Texture Packer")
        bpy.ops.object.lily_texture_packer()
        print("\t\tFinished Lily Texture Packer\n\t\tFinding Image")

        obj = objs[0]
        obj_mat = obj.data.materials[0]
        obj_mat_nodes = obj_mat.node_tree.nodes
        img_node = next(
            (
                mat_node
                for mat_node in obj_mat_nodes
                if mat_node.type == 'TEX_IMAGE'
            ),
            None,
        )
        '''
        this is here as i have never used or seen next used like this before so for my own purpose
        # img_node = None
        
        # for mat_node in obj_mat_nodes:
        #     # print(mat_node,mat_node.type)
        #     if mat_node.type == 'TEX_IMAGE':
        #         img_node = mat_node
        #         break
        '''

        if img_node is None:
            print(
                f"No image found for collection: {col}, on the first object.")

        else:

            print("\t\tFound Image. Saving Image")
            img = img_node.image
            img.name = f"{col}_LilyTexImage"
            img_path = f"{LILY_IMAGE_FILE_PATH}{img.name}.bmp"
            img.filepath_raw = img_path
            img.save()

            join_object_group(objs=objs, name=complete_obj_name)

            assign_lily_texture_to_object(
                obj_name=obj.name, img_filepath=img_path)

    # if more than 1 column then join sections together
    if (len(col_names) > 1):
        join_lily_models_together(col_names=col_names)

    print("Finished Lily Texture Packer on collections\n")

    return col_names[0]


def join_lily_models_together(col_names: list[str]):

    print("\nStarting join_lily_models_together")

    objs_list = [
        obj for col in col_names for obj in bpy.data.collections.get(col).objects]

    join_object_group(objs=objs_list, name=complete_obj_name)

    print("Finished join_lily_models_together\n")

    return


def join_object_group(objs: list, name: str = None):

    print("\nStarting join_object_group, objs: ", objs, " name: ", name)

    # DESELECT ALL OBJS
    bpy.ops.object.select_all(action='DESELECT')

    for ob in objs:
        ob.select_set(True)

    # set first object as active
    bpy.context.view_layer.objects.active = bpy.data.objects[objs[0].name]

    # join all objects into first object of selected_obj_name list
    bpy.ops.object.join()

    if name:
        objs[0].name = name
        objs[0].data.name = name

    # DESELECT ALL OBJS
    bpy.ops.object.select_all(action='DESELECT')

    print("Finished join_object_group\n")
    return


def assign_lily_texture_to_object(obj_name: str, img_filepath: str, mat_number: str = 1):

    mat_time_start = time.time()

    # get current context mode
    current_context_mode = bpy.context.active_object.mode

    # switch to object mode if not
    if (current_context_mode != 'OBJECT'):
        # set context mode to object
        bpy.ops.object.mode_set(mode='OBJECT')

    # log start
    print('\nStarting assign_lily_texture_to_object')

    # Remove materials from obj
    # bpy.data.objects.get(obj_name).data.materials.clear()
    materials = list(bpy.data.objects.get(obj_name).data.materials)
    for mat in materials:
        del mat
    bpy.data.objects.get(obj_name).data.materials.clear()

    # create new material
    new_material = bpy.data.materials.new(
        name=f"High_Poly_Lily_Texture_Mat{mat_number}"
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

    # load image
    img = bpy.data.images.load(filepath=img_filepath)

    tex_image_node = nodes.new(type="ShaderNodeTexImage")
    tex_image_node.location = (-450, 0)
    tex_image_node.name = f'High_Poly_Lily_Tex_Node_{mat_number}'
    tex_image_node.image = img

    # attach material
    new_material.node_tree.links.new(
        bsdf_node.inputs[0], tex_image_node.outputs[0])

    # append new material
    bpy.data.objects.get(
        obj_name).data.materials.append(new_material)

    # switch to back to previous mode if not in object
    if (current_context_mode != 'OBJECT'):
        # back to whatever mode we were in
        bpy.ops.object.mode_set(mode=current_context_mode)

    # output material time
    print("\nIt Took assign_lily_texture_to_object:", time.strftime(
        "%H hours, %M minutes and %S seconds to Complete", time.gmtime(time.time()-mat_time_start)))

    return


def get_max_image_size():
    objs = bpy.context.scene.objects

    max_image_size = 0
    for obj in objs:
        image = get_image_for_obj(obj)

        # if no image found skip obj
        if image is None:
            continue

        current_max_res = max(image.size[0], image.size[1])

        if current_max_res > max_image_size:
            max_image_size = current_max_res

    print(f'Max image size is: {max_image_size}')
    return max_image_size


def get_image_for_obj(obj):

    # as lily texture capture only assumes one material for obj use first slot
    mat = obj.material_slots[0].material
    # check material exists and use nodes
    if mat and mat.use_nodes:
        bdsf_node = mat.node_tree.nodes['Principled BSDF']
        input_socket = bdsf_node.inputs[0]

        try:
            # get the link that inputs into the bsdf and into the socket this will be the image link
            node_link = next(link for link in mat.node_tree.links if link.to_node ==
                             bdsf_node and link.to_socket == input_socket)

            # image node
            image_node = node_link.from_node

            # check its the image texture node
            if image_node.type == 'TEX_IMAGE':
                # return image
                return image_node.image

        except Exception as err:
            print(
                f"Unable to image texture from object: {obj.name}. Exception raised: {err}")
            # return none as no image was retrievable
            return None


if __name__ == '__main__':

    # retrieved and tweaked from https://blender.stackexchange.com/questions/33603/importing-python-modules-and-text-files credit to Cardboy0
    original_path = pathlib.Path(bpy.data.filepath)
    parent_path = original_path.parent

    # remember, paths only work if they're strings
    str_parent_path = str(parent_path.resolve())
    # print(str_parent_path)
    # print(original_path)
    if str_parent_path not in sys.path:
        sys.path.append(str_parent_path)
    print(f'{parent_path}\\Scripts')
    if f'{parent_path}\\Scripts' not in sys.path:
        sys.path.append(f'{parent_path}\\Scripts')

    # building the correct __package__ name
    relative_path = original_path.parent.relative_to(parent_path)
    # print(relative_path)
    with_dots = '.'.join(relative_path.parts)
    # print(with_dots)
    __package__ = with_dots
    from Scripts import *
    from constants import *
    from shared_common_methods import *  # this works here but not else where

    main()
