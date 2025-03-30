import json
from pathlib import Path
import importlib.util
import math

import bpy
from mathutils import Matrix, Quaternion, Vector


import_mrm_module = None
load_armature_module = None
load_mesh_module = None
load_materials_module = None
utils_module = None


def import_module(module_name):
    module_path_list = []
    module_path_list.append(Path(module_name + '.py'))
    module_path_list.append(Path.cwd() / str(module_name + '.py'))
    module_path_list.append(Path.cwd() / 'import_zengin_json' / str(module_name + '.py'))
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


def import_model(mdl_json_data, texture_folder_list, rename_bones=False, add_root_bone=False):
    global load_armature_module, import_mrm_module, utils_module

    if load_armature_module is None:
        load_armature_module = import_module('load_armature')

    if import_mrm_module is None:
        import_mrm_module = import_module('import_mrm')

    if utils_module is None:
        utils_module = import_module('utils')

    assert load_armature_module is not None
    assert import_mrm_module is not None
    assert utils_module is not None

    assert 'hierarchy' in mdl_json_data
    assert 'mesh' in mdl_json_data

    hierarchy_dict = mdl_json_data['hierarchy']
    mesh_dict = mdl_json_data['mesh']

    utils_module.reset_scene()

    armature_obj, armature, node_dict = load_armature_module.create_armature(hierarchy_dict)
    if rename_bones:
        utils_module.rename_armature_bones(armature_obj)

    if add_root_bone:
        utils_module.add_root_bone(armature_obj)

    # same code in import_mdm =(

    if len(mesh_dict['meshes']) > 0:
        assert 'multi_resolution_mesh' in mesh_dict['meshes'][0]

        multi_resolution_mesh = mesh_dict['meshes'][0]['multi_resolution_mesh']
        mesh_obj, mesh = import_mrm_module.import_multiresolution_mesh(multi_resolution_mesh, texture_folder_list)

        if armature_obj:
            mesh_obj.parent = armature_obj

            armature_modifier = mesh_obj.modifiers.new(armature_obj.name, 'ARMATURE')
            armature_modifier.object = armature_obj
            armature_modifier.use_vertex_groups = True

            # Create vertex group

            soft_skin_weight_list = mesh_dict['meshes'][0]['soft_skin_weight']

            for veterx_index, soft_skin_weight in enumerate(soft_skin_weight_list):
                for soft_skin_weight_bone in soft_skin_weight:
                    node_index = soft_skin_weight_bone['node_index']
                    model_hierarchy_node = hierarchy_dict['nodes'][node_index]
                    vertex_group_name = model_hierarchy_node['name']
                    vertex_group = None
                    if vertex_group_name in mesh_obj.vertex_groups:
                        vertex_group = mesh_obj.vertex_groups[vertex_group_name]
                    else:
                        vertex_group = mesh_obj.vertex_groups.new(name=vertex_group_name)
                    vertex_group.add([veterx_index], soft_skin_weight_bone['weight'], 'ADD')

            # Rotate and mirror mesh
            matrix_rotation_x = Matrix.Rotation(math.radians(90.0), 4, 'X').to_4x4()
            matrix_mirror_y = Matrix.Scale(-1.0, 4, Vector([1.0, 0.0, 0.0]))
            mesh.transform(matrix_rotation_x)
            mesh.transform(matrix_mirror_y)

    if len(mesh_dict['attachments']) > 0:
        for attachment in mesh_dict['attachments']:
            for attachment_key, attachment_value in attachment.items():
                if rename_bones:
                    attachment_key = utils_module.rename_bone(attachment_key)

                mesh_obj, mesh = import_mrm_module.import_multiresolution_mesh(attachment_value, texture_folder_list)
                mesh_obj.name = f'Mesh_{attachment_key}'
                mesh.name = mesh_obj.name

                matrix_rotation_x = Matrix.Rotation(math.radians(90.0), 4, 'X').to_4x4()
                matrix_mirror_y = Matrix.Scale(-1.0, 4, Vector([0.0, 1.0, 0.0]))
                mesh.transform(matrix_rotation_x)
                mesh.transform(matrix_mirror_y)

                if armature_obj:
                    # attach
                    mesh_obj.parent = armature_obj
                    mesh_obj.parent_bone = attachment_key
                    mesh_obj.parent_type = 'BONE'

                    # fix base bone rotation (see bone default rotation) (vertex dimension, not object)
                    matrix_rotation_z = Matrix.Rotation(math.radians(90.0), 4, 'Z').to_4x4()
                    mesh.transform(matrix_rotation_z)

                    # fix bone head/tail feature
                    bone = armature.bones[attachment_key]
                    mesh_obj.location.y -= bone.length


def import_model_from_json(mdl_json_data, texture_folder_list, rename_bones=False, add_root_bone=False):
    global utils_module

    if utils_module is None:
        utils_module = import_module('utils')

    assert utils_module is not None

    utils_module.reset_scene()

    import_model(mdl_json_data, texture_folder_list, rename_bones=False, add_root_bone=False)


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

    mdl_json_file_path_list = list(Path(intermediate_path).rglob(f'*.MDL.json'))
    for mdl_json_file_path in mdl_json_file_path_list:
        file_name = mdl_json_file_path.stem.upper().replace('.JSON', '')
        relative_path = mdl_json_file_path.relative_to(intermediate_path).parent
        relative_path = Path(str(relative_path).replace('_Anims', '_Meshes'))

        # if 'BARBQ_SCAV' not in str(mdl_json_file_path):
        #     continue
        #
        # # if 'VDF_Anims' not in str(mdl_json_file_path):
        # #     continue
        #
        # if 'Gothic II' not in str(mdl_json_file_path):
        #     continue

        mdl_json_data = mdl_json_file_path.read_text()
        mdl_json_dict = json.loads(mdl_json_data)

        import_model_from_json(mdl_json_dict, texture_folder_list, rename_bones=config['rename_bones'], add_root_bone=config['add_root_bone'])

        # Save
        save_folder_path = convert_path / relative_path
        save_folder_path.mkdir(exist_ok=True, parents=True)

        utils_module.export(save_folder_path / file_name, config)

        print(f'converted: {relative_path / file_name}')

    # close blender
    exit()


def init():
    config_file_path = Path('config.json')
    if config_file_path.exists():
        load_from_gothic_hub_scripts(config_file_path)


init()
