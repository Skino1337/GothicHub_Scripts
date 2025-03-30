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


def import_morph_mesh(mmb_json_data, texture_folder_list):
    global import_mrm_module

    assert 'multiresolution_mesh' in mmb_json_data
    assert 'animations' in mmb_json_data

    if import_mrm_module is None:
        import_mrm_module = import_module('import_mrm')

    assert import_mrm_module is not None

    matrix_rotation_x = Matrix.Rotation(math.radians(90.0), 4, 'X').to_4x4()
    matrix_mirror_y = Matrix.Scale(-1.0, 4, Vector([0.0, 1.0, 0.0]))

    mesh_obj, mesh = import_mrm_module.import_multiresolution_mesh(mmb_json_data['multiresolution_mesh'], texture_folder_list)

    # Rotate and mirror mesh
    mesh.transform(matrix_rotation_x)
    mesh.transform(matrix_mirror_y)

    # Shape keys
    shape_key_basis = mesh_obj.shape_key_add(name='Basis')
    shape_key_basis.interpolation = 'KEY_LINEAR'
    mesh.shape_keys.use_relative = True

    shape_key_index = 0
    for animation in mmb_json_data['animations']:
        vertices = animation['vertices']
        samples = animation['samples']

        assert len(samples) % len(vertices) == 0
        assert max(vertices) < len(mesh.vertices)

        for frame_index, frame in enumerate(range(len(samples) // len(vertices))):
            shape_key_name = f'{shape_key_index:02d}_{animation["name"]}_{frame_index:02d}'
            shape_key_index = shape_key_index + 1

            shape_key = mesh_obj.shape_key_add(name=shape_key_name)
            shape_key.interpolation = 'KEY_LINEAR'
            for i, vertex_index in enumerate(vertices):
                vertex = samples[(len(vertices) * frame_index) + i]
                vertex = Vector([f * 0.01 for f in vertex])
                vertex = matrix_rotation_x @ vertex
                vertex = matrix_mirror_y @ vertex
                shape_key.data[vertex_index].co += vertex

    # Animation
    scene = bpy.context.scene
    scene.frame_start = 0
    scene.frame_end = shape_key_index - 1
    scene.frame_set(0)

    animation_data = mesh.shape_keys.animation_data
    if not animation_data:
        animation_data = mesh.shape_keys.animation_data_create()

    if animation_data.action:
        bpy.data.actions.remove(animation_data.action, do_unlink=True)

    animation_data.action = bpy.data.actions.new(f'{mesh_obj.name}Action')

    for key_block_index, key_block in enumerate(mesh.shape_keys.key_blocks[1:]):
        key_block.value = 0
        key_block.keyframe_insert(data_path='value', frame=key_block_index - 1)

        key_block.value = 1
        key_block.keyframe_insert(data_path='value', frame=key_block_index)

        key_block.value = 0
        key_block.keyframe_insert(data_path='value', frame=key_block_index + 1)

    return mesh_obj, mesh


def import_morph_mesh_from_json(mmb_json_data, texture_folder_list):
    global utils_module

    if utils_module is None:
        utils_module = import_module('utils')

    assert utils_module is not None

    utils_module.reset_scene()

    mesh_obj, mesh = import_morph_mesh(mmb_json_data, texture_folder_list)


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

    mmb_json_file_path_list = list(Path(intermediate_path).rglob(f'*.MMB.json'))
    for mmb_json_file_path in mmb_json_file_path_list:
        file_name = mmb_json_file_path.stem.upper().replace('.MMB', '').replace('.JSON', '')
        relative_path = mmb_json_file_path.relative_to(intermediate_path).parent
        relative_path = Path(str(relative_path).replace('_Anims', '_Meshes'))

        # if 'HUM_HEAD_BABE' != file_name:
        #     continue
        #
        # if 'HUM_HEAD_BABE' not in str(mmb_json_file_path):
        #     continue
        #
        # if 'VDF_Anims' not in str(mmb_json_file_path):
        #     continue
        #
        # if 'Gothic II' not in str(mmb_json_file_path):
        #     continue

        mmb_json_data = mmb_json_file_path.read_text()
        mmb_json_dict = json.loads(mmb_json_data)

        import_morph_mesh_from_json(mmb_json_dict, texture_folder_list)

        morph_mesh_script = dict()
        morph_mesh_script['type'] = 'morph_mesh_script'
        morph_mesh_script['animations'] = mmb_json_dict['animations'][:]
        for animation_index in range(len(morph_mesh_script['animations'])):
            morph_mesh_script['animations'][animation_index].pop('vertices', None)
            morph_mesh_script['animations'][animation_index].pop('samples', None)

        # Save
        save_folder_path = convert_path / relative_path / file_name
        save_folder_path.mkdir(exist_ok=True, parents=True)

        json_data = json.dumps(morph_mesh_script, indent=4, ensure_ascii=False)
        save_path_mms = save_folder_path / (file_name + '.MMS.json')
        save_path_mms.write_text(json_data, encoding='utf-8')

        save_path_file = save_folder_path / file_name
        utils_module.export(save_path_file, config)

        print(f'converted: {relative_path / file_name}.MMB')

    # close blender
    exit()


def init():
    if __name__ != '__main__':
        return

    config_file_path = Path('config.json')
    if config_file_path.exists():
        load_from_gothic_hub_scripts(config_file_path)


init()
