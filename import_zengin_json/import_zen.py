import json
from pathlib import Path
import importlib.util
import math

import bpy
import bmesh
from mathutils import Matrix, Quaternion, Vector


load_materials_module = None
load_mesh_module = None
utils_module = None


def import_module(module_name):
    module_path_list = []
    module_path_list.append(Path(module_name + '.py'))
    module_path_list.append(Path.cwd() / (module_name + '.py'))
    module_path_list.append(Path.cwd() / 'import_zengin_json' / (module_name + '.py'))
    for module_path in module_path_list:
        if module_path.exists():
            # Create a module spec from the given path
            spec = importlib.util.spec_from_file_location(module_name, module_path)

            # Load the module from the created spec
            module = importlib.util.module_from_spec(spec)

            # Execute the module to make its attributes accessible
            spec.loader.exec_module(module)

            # Return the imported module
            return module

    return None


def create_mesh_texture_depend(base_mesh_obj, name, material_name_list, mode):
    mesh_obj = base_mesh_obj.copy()
    mesh_obj.name = name
    mesh_obj.data = base_mesh_obj.data.copy()
    bpy.context.collection.objects.link(mesh_obj)

    material_index_list = []
    for index, material in enumerate(mesh_obj.data.materials):
        material_name = material.name.upper().replace('.TGA', '')
        if material_name in material_name_list:
            material_index_list.append(index)

    mesh_b = bmesh.new()
    mesh_b.from_mesh(mesh_obj.data)
    mesh_b.faces.ensure_lookup_table()

    faces_with_material = set()
    for face in mesh_b.faces:
        if face.material_index in material_index_list:
            faces_with_material.add(face)

    verts_with_material = set()
    for face in faces_with_material:
        for vertex in face.verts:
            verts_with_material.add(vertex)

    faces_without_material = set()
    for face in mesh_b.faces:
        if face.material_index not in material_index_list:
            faces_without_material.add(face)

    verts_without_material = set()
    for face in faces_without_material:
        for vertex in face.verts:
            verts_without_material.add(vertex)

    if mode == 'EXCLUDE':
        if len(faces_without_material) == 0:
            mesh_b.free()
            bpy.context.scene.collection.objects.unlink(mesh_obj)
            return None

        verts_with_material.difference_update(verts_without_material)
        bmesh.ops.delete(mesh_b, geom=list(faces_with_material), context='FACES_ONLY')
        bmesh.ops.delete(mesh_b, geom=list(verts_with_material), context='VERTS')
    elif mode == 'INCLUDE':
        if len(faces_with_material) == 0:
            mesh_b.free()
            bpy.context.scene.collection.objects.unlink(mesh_obj)
            return None

        verts_without_material.difference_update(verts_with_material)
        bmesh.ops.delete(mesh_b, geom=list(faces_without_material), context='FACES_ONLY')
        bmesh.ops.delete(mesh_b, geom=list(verts_without_material), context='VERTS')
    else:
        mesh_b.free()
        bpy.context.scene.collection.objects.unlink(mesh_obj)
        print(f'wrong mode: {mode}')
        return None

    mesh_b.faces.ensure_lookup_table()

    edges_with_face = set()
    for face in mesh_b.faces:
        for edge in face.edges:
            edges_with_face.add(edge)

    edges_all = set()
    for edge in mesh_b.edges:
        edges_all.add(edge)

    edges_without_face = []
    for edge in edges_all:
        if edge not in edges_with_face:
            edges_without_face.append(edge)

    bmesh.ops.delete(mesh_b, geom=edges_without_face, context='EDGES')

    mesh_b.to_mesh(mesh_obj.data)
    mesh_b.free()

    mesh_obj.select_set(True)
    bpy.context.view_layer.objects.active = mesh_obj

    bpy.ops.object.material_slot_remove_unused()

    bpy.context.view_layer.objects.active = None
    mesh_obj.select_set(False)

    return mesh_obj


def split_mesh(mesh_obj, mesh, zengin_materials):
    water_texture_list = []
    no_collision_texture_list = []
    portal_texture_list = []
    sector_texture_list = []
    ghostoccluder_texture_list = []
    sunblocker_texture_list = []
    collision_texture_list = []
    for material in zengin_materials:
        material_name = material['name'].upper().replace('.TGA', '')
        # if or elif???
        if material['matGroup'] == 'WATER':
            water_texture_list.append(material_name)
        elif material['noCollDet']:
            no_collision_texture_list.append(material_name)
        elif material_name.startswith('P:') or material_name.startswith('PI:') or material_name.startswith('PN:'):
            portal_texture_list.append(material_name)
        elif material_name.startswith('S:'):
            sector_texture_list.append(material_name)
        elif material_name == 'GHOSTOCCLUDER':
            ghostoccluder_texture_list.append(material_name)
        elif material_name.startswith('SUN_BLOCKER'):
            sunblocker_texture_list.append(material_name)
        else:
            collision_texture_list.append(material_name)

    create_mesh_texture_depend(mesh_obj, 'WATER', water_texture_list, 'INCLUDE')
    create_mesh_texture_depend(mesh_obj, 'PORTAL', portal_texture_list, 'INCLUDE')

    # https://github.com/postm1/SpacerNET_Union/commit/bdcb6dae4bd37442ca9698d6e81769e8ba909fe6
    create_mesh_texture_depend(mesh_obj, 'SECTOR', sector_texture_list, 'INCLUDE')

    create_mesh_texture_depend(mesh_obj, 'GHOSTOCCLUDER', ghostoccluder_texture_list, 'INCLUDE')
    create_mesh_texture_depend(mesh_obj, 'SUN_BLOCKER', sunblocker_texture_list, 'INCLUDE')
    create_mesh_texture_depend(mesh_obj, 'COLLISION', collision_texture_list, 'INCLUDE')
    create_mesh_texture_depend(mesh_obj, 'NO_COLLISION', no_collision_texture_list, 'INCLUDE')

    bpy.context.scene.collection.objects.unlink(mesh_obj)
    # bpy.ops.outliner.orphans_purge(do_recursive=True)


def create_zen_mesh(name, mesh_dict, materials_by_index, use_gothic_normals=False):
    global load_mesh_module

    assert 'positions' in mesh_dict
    assert 'polygons' in mesh_dict

    if len(mesh_dict['positions']) < 3 or len(mesh_dict['polygons']) <= 0:
        return None, None

    if load_mesh_module is None:
        load_mesh_module = import_module('load_mesh')

    assert load_mesh_module is not None

    vertex_list = mesh_dict['positions']
    face_list = []
    normal_list = []
    uv_list = []

    face_material_index_list = []

    polygons = mesh_dict['polygons']
    texture = mesh_dict['texture']
    normals = mesh_dict['normals']

    for polygon in polygons:
        face = polygon['position_indices']
        face_material_index_list.append(polygon['material_index'])
        feature_indices = polygon['feature_indices']
        normal = []
        uv = []
        for feature_index in feature_indices:
            normal_x, normal_y, normal_z = normals[feature_index]
            normal.append([-normal_x, -normal_y, -normal_z])
            uv_x, uv_y = texture[feature_index]
            uv.append([uv_x, -uv_y])
            # normal.append(normals[feature_index])
            # uv.append(texture[feature_index])
        face_list.append(face)
        normal_list.append(normal)
        uv_list.append(uv)

    # for some worlds normals broken =(
    if not use_gothic_normals:
        normal_list = None

    mesh_obj, mesh = load_mesh_module.create_mesh_v2(name, vertex_list, face_list, normal_list=normal_list,
        uv_list=uv_list, blender_materials=materials_by_index, face_material_index_list=face_material_index_list)

    return mesh_obj, mesh


def import_zen_from_mesh_and_materials(mesh_dict, materials_dict, texture_folder_list, split_world=False, use_gothic_normals=False):
    global load_materials_module, load_mesh_module, utils_module

    if load_materials_module is None:
        load_materials_module = import_module('load_materials')

    if load_mesh_module is None:
        load_mesh_module = import_module('load_mesh')

    if utils_module is None:
        utils_module = import_module('utils')

    assert load_materials_module is not None
    assert load_mesh_module is not None
    assert utils_module is not None

    texture_path_dict = utils_module.get_texture_path_dict(texture_folder_list)

    utils_module.reset_scene()

    materials_by_index = load_materials_module.create_materials(materials_dict, texture_path_dict)
    mesh_obj, mesh = create_zen_mesh('World', mesh_dict, materials_by_index, use_gothic_normals=use_gothic_normals)
    if not mesh:
        return False

    # don't know how to transform to correct coordinates...

    matrix_rotation_x = Matrix.Rotation(math.radians(90.0), 4, 'X').to_4x4()
    mesh_obj.data.transform(matrix_rotation_x)
    mesh_obj.data.update()

    matrix_mirror_y = Matrix.Scale(-1.0, 4, Vector([0.0, 1.0, 0.0]))
    mesh_obj.data.transform(matrix_mirror_y)
    mesh_obj.data.update()

    mesh_obj.select_set(True)
    bpy.context.view_layer.objects.active = mesh_obj

    bpy.ops.object.material_slot_remove_unused()

    bpy.context.view_layer.objects.active = None
    mesh_obj.select_set(False)

    if split_world:
        split_mesh(mesh_obj, mesh, materials_dict)

    return True


def import_zen_from_json(path_to_zen_json_file, texture_folder_list):
    zen_json_data = Path(path_to_zen_json_file).read_text()
    zen_json_dict = json.loads(zen_json_data)

    assert 'mesh' in zen_json_dict
    assert 'materials' in zen_json_dict

    mesh_dict = zen_json_dict['mesh']
    materials_dict = zen_json_dict['materials']

    import_zen_from_mesh_and_materials(mesh_dict, materials_dict, texture_folder_list)


def load_from_gothic_hub_scripts(config_file_path):
    global utils_module

    bpy.context.preferences.view.show_splash = False

    config_data = config_file_path.read_text()
    config = json.loads(config_data)

    if utils_module is None:
        utils_module = import_module('utils')

    assert utils_module is not None

    extract_path, intermediate_path, convert_path = utils_module.get_eic_paths(config)

    texture_folder_list = utils_module.get_texture_folder_list(convert_path)

    zen_json_file_path_list = list(Path(intermediate_path).rglob(f'*.ZEN.json'))
    for zen_json_file_path in zen_json_file_path_list:
        # if 'ARCHOLOS_SEWERS' not in str(zen_json_file_path.name):  # ARCHOLOS_SEWERS ARCHOLOS_MAINLAND ARCHOLOS_SILVERMINE
        #     continue

        relative_path = zen_json_file_path.relative_to(intermediate_path).parent

        world_name = zen_json_file_path.stem.upper().replace('.ZEN', '').replace('.JSON', '')
        # save_folder = convert_path / 'Worlds' / world_name
        save_folder = convert_path / relative_path / world_name
        save_folder.mkdir(exist_ok=True, parents=True)

        # relative_path = zen_file_path.relative_to(extract_path).parent
        # save_path = intermediate_path / relative_path

        zen_json_data = Path(zen_json_file_path).read_text()
        zen_json_dict = json.loads(zen_json_data)

        assert 'mesh' in zen_json_dict
        assert 'materials' in zen_json_dict

        mesh_dict = zen_json_dict['mesh']
        materials_dict = zen_json_dict['materials']

        import_zen_from_mesh_and_materials(mesh_dict, materials_dict, texture_folder_list,
                                           split_world=config['split_world'],
                                           use_gothic_normals=config['use_gothic_normals'])

        json_data = json.dumps(materials_dict, indent=4, ensure_ascii=False)
        save_path_materials = save_folder / 'materials.json'
        save_path_materials.write_text(json_data, encoding='utf-8')

        json_data = json.dumps(zen_json_dict['vobs'], indent=4, ensure_ascii=False)
        save_path_vobs = save_folder / 'vobs.json'
        save_path_vobs.write_text(json_data, encoding='utf-8')

        json_data = json.dumps(zen_json_dict['waypoints'], indent=4, ensure_ascii=False)
        save_path_waypoints = save_folder / 'waypoints.json'
        save_path_waypoints.write_text(json_data, encoding='utf-8')

        utils_module.export(save_folder / world_name, config)

        print(f'converted: {relative_path / world_name}.ZEN')

    # close blender
    exit()


def init():
    config_file_path = Path('config.json')
    if config_file_path.exists():
        load_from_gothic_hub_scripts(config_file_path)


init()
