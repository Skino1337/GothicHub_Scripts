import json
from pathlib import Path
import importlib.util
import math

import bpy
from mathutils import Matrix, Quaternion, Vector


load_mesh_module = None
load_materials_module = None
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


def import_multiresolution_mesh(multiresolution_mesh_dict, texture_folder_list):
    global load_mesh_module, load_materials_module, utils_module

    assert 'positions' in multiresolution_mesh_dict
    assert 'submeshes' in multiresolution_mesh_dict

    # sometimes have empty files
    if len(multiresolution_mesh_dict['positions']) < 3 or len(multiresolution_mesh_dict['submeshes']) <= 0:
        return None, None

    if load_mesh_module is None:
        load_mesh_module = import_module('load_mesh')

    if load_materials_module is None:
        load_materials_module = import_module('load_materials')

    if utils_module is None:
        utils_module = import_module('utils')

    assert load_mesh_module is not None
    assert load_materials_module is not None
    assert utils_module is not None

    vertex_list = multiresolution_mesh_dict['positions']
    face_list = []
    normal_list = []
    uv_list = []
    face_material_index_list = []

    for submesh_index, submesh in enumerate(multiresolution_mesh_dict['submeshes']):
        triangles = submesh['triangles']
        wedges = submesh['wedges']

        for triangle_index, triangle in enumerate(triangles):
            face = []
            normal = []
            uv = []
            for wedge_index in triangle:
                wedge = wedges[wedge_index]
                face.append(wedge['positions_index'])
                normal_x, normal_y, normal_z = wedge['normal']
                normal.append([-normal_x, -normal_y, -normal_z])
                uv_x, uv_y = wedge['texture']
                uv.append([uv_x, -uv_y])
            face_list.append(face)
            normal_list.append(normal)
            uv_list.append(uv)

            face_material_index_list.append(submesh_index)

    materials_by_index = None
    if 'materials' in multiresolution_mesh_dict:
        materials_dict = multiresolution_mesh_dict['materials']
        texture_path_dict = utils_module.get_texture_path_dict(texture_folder_list)
        materials_by_index = load_materials_module.create_materials(materials_dict, texture_path_dict)

    mesh_obj, mesh = load_mesh_module.create_mesh_v2('Mesh', vertex_list, face_list, normal_list=normal_list,
        uv_list=uv_list, blender_materials=materials_by_index, face_material_index_list=face_material_index_list)

    return mesh_obj, mesh


def import_multiresolution_mesh_from_json(mrm_json_data, texture_folder_list):
    global utils_module

    if utils_module is None:
        utils_module = import_module('utils')

    assert utils_module is not None

    utils_module.reset_scene()

    mesh_obj, mesh = import_multiresolution_mesh(mrm_json_data, texture_folder_list)
    if not mesh:
        return

    # Rotate and mirror mesh
    matrix_rotation_x = Matrix.Rotation(math.radians(90.0), 4, 'X').to_4x4()
    mesh.transform(matrix_rotation_x)

    matrix_mirror_y = Matrix.Scale(-1.0, 4, Vector([0.0, 1.0, 0.0]))
    mesh.transform(matrix_mirror_y)


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

    mrm_json_file_path_list = list(Path(intermediate_path).rglob(f'*.MRM.json'))
    for mrm_json_file_path in mrm_json_file_path_list:
        file_name = mrm_json_file_path.stem.upper().replace('.MRM', '').replace('.JSON', '')
        relative_path = mrm_json_file_path.relative_to(intermediate_path).parent

        # if 'NW_HARBOUR_BARREL_01' not in str(mrm_json_file_path):
        #     continue
        #
        # if 'VDF_Meshes' not in str(mrm_json_file_path):
        #     continue
        #
        # if 'Gothic II' not in str(mrm_json_file_path):
        #     continue


        # if 'MOD_KM_Meshes' not in str(mrm_json_file_path):  # Gothic II
        #     continue

        # if '1H_HAMMER_GODENDAR' not in str(mrm_json_file_path):  # NW_HARBOUR_BARREL_01
        #     continue

        mrm_json_data = mrm_json_file_path.read_text()
        mrm_json_dict = json.loads(mrm_json_data)

        import_multiresolution_mesh_from_json(mrm_json_dict, texture_folder_list)

        # Save
        save_folder_path = convert_path / relative_path
        save_folder_path.mkdir(exist_ok=True, parents=True)

        utils_module.export(save_folder_path / file_name, config)

        print(f'converted: {relative_path / file_name}.MRM')

    # close blender
    exit()


def init():
    if __name__ != '__main__':
        return

    config_file_path = Path('config.json')
    if config_file_path.exists():
        load_from_gothic_hub_scripts(config_file_path)


init()
