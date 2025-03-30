import json
from pathlib import Path
import importlib.util

import bpy


load_armature_module = None
load_animation_module = None
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


def import_man_from_hierarchy_and_animation(hierarchy_dict, animation_dict, rename_bones=True, add_root_bone=True):
    global load_armature_module, load_animation_module, utils_module

    if load_armature_module is None:
        load_armature_module = import_module('load_armature')

    if load_animation_module is None:
        load_animation_module = import_module('load_animation')

    if utils_module is None:
        utils_module = import_module('utils')

    assert load_armature_module is not None
    assert load_animation_module is not None
    assert utils_module is not None

    utils_module.reset_scene()

    armature_obj, armature, node_dict = load_armature_module.create_armature(hierarchy_dict)
    load_animation_module.create_animation(armature_obj, armature, node_dict, animation_dict)

    if rename_bones:
        utils_module.rename_armature_bones(armature_obj)

    if add_root_bone:
        utils_module.add_root_bone(armature_obj)


def load_from_gothic_hub_scripts(config_file_path):
    global utils_module

    bpy.context.preferences.view.show_splash = False

    config_data = config_file_path.read_text()
    config = json.loads(config_data)

    if utils_module is None:
        utils_module = import_module('utils')

    assert utils_module is not None

    extract_path, intermediate_path, convert_path = utils_module.get_eic_paths(config)

    man_json_file_path_list = list(Path(intermediate_path).rglob(f'*.MAN.json'))
    for man_json_file_path in man_json_file_path_list:
        file_name = man_json_file_path.stem.upper().replace('.MAN', '').replace('.JSON', '')
        relative_path = man_json_file_path.relative_to(intermediate_path).parent

        # if 'HUMANS\\T_JUMPB' not in str(man_json_file_path):
        #     continue
        #
        # if 'VDF_Anims' not in str(man_json_file_path):
        #     continue

        man_json_data = Path(man_json_file_path).read_text()
        man_json_dict = json.loads(man_json_data)

        assert 'hierarchy' in man_json_dict
        assert 'animation' in man_json_dict

        import_man_from_hierarchy_and_animation(man_json_dict['hierarchy'], man_json_dict['animation'],
                                                rename_bones=config['rename_bones'],
                                                add_root_bone=config['add_root_bone'])

        # Save
        save_folder_path = convert_path / relative_path
        save_folder_path.mkdir(exist_ok=True, parents=True)

        utils_module.export(save_folder_path / file_name, config)

        print(f'converted: {relative_path / file_name}.MAN')

    # close blender
    exit()


def init():
    config_file_path = Path('config.json')
    if config_file_path.exists():
        load_from_gothic_hub_scripts(config_file_path)


init()
