import json
from pathlib import Path
import importlib.util
import math

import bpy
from mathutils import Matrix, Quaternion, Vector


load_armature_module = None
load_mesh_module = None
load_materials_module = None
import_mrm_module = None
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


def import_model_mesh_from_json(mdm_json_data, texture_folder_list, rename_bones=False, add_root_bone=False, use_gothic_normals=False):
    global load_armature_module, import_mrm_module, utils_module

    assert 'hierarchy' in mdm_json_data
    assert 'mesh' in mdm_json_data

    model_hierarchy_dict = mdm_json_data['hierarchy']
    model_mesh_dict = mdm_json_data['mesh']

    assert 'meshes' in model_mesh_dict
    assert 'attachments' in model_mesh_dict

    if load_armature_module is None:
        load_armature_module = import_module('load_armature')

    if import_mrm_module is None:
        import_mrm_module = import_module('import_mrm')

    if utils_module is None:
        utils_module = import_module('utils')

    assert load_armature_module is not None
    assert import_mrm_module is not None
    assert utils_module is not None

    utils_module.reset_scene()

    armature_obj, armature, node_dict = load_armature_module.create_armature(model_hierarchy_dict)

    if armature_obj:
        if rename_bones:
            utils_module.rename_armature_bones(armature_obj)

        if add_root_bone:
            utils_module.add_root_bone(armature_obj)

    # same code in import_mdl =(

    if len(model_mesh_dict['meshes']) > 0:
        # some armour have split mesh
        for index, mesh_dict in enumerate(model_mesh_dict['meshes']):
            if 'multi_resolution_mesh' not in mesh_dict:
                continue

            mesh_name = 'Mesh' if index == 0 else f'Mesh{index}'
            multi_resolution_mesh = mesh_dict['multi_resolution_mesh']
            mesh_obj, mesh = import_mrm_module.import_multiresolution_mesh(multi_resolution_mesh, texture_folder_list,
                                                                           use_gothic_normals=use_gothic_normals,
                                                                           mesh_name=mesh_name)

            if armature_obj:
                mesh_obj.parent = armature_obj

                armature_modifier = mesh_obj.modifiers.new(armature_obj.name, 'ARMATURE')
                armature_modifier.object = armature_obj
                armature_modifier.use_vertex_groups = True

                # Create vertex group

                soft_skin_weight_list = mesh_dict['soft_skin_weight']

                for vertex_index, soft_skin_weight in enumerate(soft_skin_weight_list):
                    for soft_skin_weight_bone in soft_skin_weight:
                        node_index = soft_skin_weight_bone['node_index']
                        model_hierarchy_node = model_hierarchy_dict['nodes'][node_index]
                        vertex_group_name = model_hierarchy_node['name']
                        if rename_bones:
                            vertex_group_name = utils_module.rename_bone(vertex_group_name)

                        vertex_group = None
                        if vertex_group_name in mesh_obj.vertex_groups:
                            vertex_group = mesh_obj.vertex_groups[vertex_group_name]
                        else:
                            vertex_group = mesh_obj.vertex_groups.new(name=vertex_group_name)
                        vertex_group.add([vertex_index], soft_skin_weight_bone['weight'], 'ADD')

                # Rotate and mirror mesh
                matrix_rotation_x = Matrix.Rotation(math.radians(90.0), 4, 'X').to_4x4()
                matrix_mirror_y = Matrix.Scale(-1.0, 4, Vector([1.0, 0.0, 0.0]))

                mesh.transform(matrix_rotation_x)
                mesh.transform(matrix_mirror_y)

    if len(model_mesh_dict['attachments']) > 0:
        for attachment in model_mesh_dict['attachments']:
            for attachment_key, attachment_value in attachment.items():
                if rename_bones:
                    attachment_key = utils_module.rename_bone(attachment_key)

                mesh_obj, mesh = import_mrm_module.import_multiresolution_mesh(attachment_value, texture_folder_list,
                                                                               use_gothic_normals=use_gothic_normals)
                mesh_obj.name = f'Mesh_{attachment_key}'
                mesh.name = mesh_obj.name

                matrix_rotation_x = Matrix.Rotation(math.radians(90.0), 4, 'X').to_4x4()
                matrix_mirror_y = Matrix.Scale(-1.0, 4, Vector([0.0, 1.0, 0.0]))
                mesh.transform(matrix_rotation_x)
                mesh.transform(matrix_mirror_y)

                if armature_obj and attachment_key in armature.bones:
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

    mdm_json_file_path_list = list(Path(intermediate_path).rglob(f'*.MDM.json'))
    for mdm_json_file_path in mdm_json_file_path_list:
        # only mdl file include double format coz same name with mdm
        file_name = mdm_json_file_path.stem.upper().replace('.MDM', '').replace('.JSON', '')
        relative_path = mdm_json_file_path.relative_to(intermediate_path).parent
        relative_path = Path(str(relative_path).replace('_Anims', '_Meshes'))

        # if 'ARMOR_BDT_M' not in str(mdm_json_file_path):
        #     continue

        # if 'VDF_Anims' not in str(mdm_json_file_path):
        #     continue
        #
        # if 'Gothic II' not in str(mdm_json_file_path):
        #     continue

        # if 'Gothic II' not in str(mdm_json_file_path):  # Addon, Gothic II,
        #     continue

        # if 'HUM_BODY_NAKED0' not in str(mdm_json_file_path):  # CHESTBIG_ADD_STONE_LOCKED
        #     continue

        # print(f'{relative_path=}')
        # print(f'{mdm_json_file_path=}')

        mdm_json_data = mdm_json_file_path.read_text()
        mdm_json_dict = json.loads(mdm_json_data)
        # try:
        #     mdm_json_dict = json.loads(mdm_json_data)
        # except:
        #     print(mdm_json_file_path)
        #     return

        import_model_mesh_from_json(mdm_json_dict, texture_folder_list,
                                    rename_bones=config['rename_bones'],
                                    add_root_bone=config['add_root_bone'],
                                    use_gothic_normals=config['use_gothic_normals'])

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
