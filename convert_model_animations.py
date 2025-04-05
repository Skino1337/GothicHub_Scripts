import json
import shutil
from pathlib import Path
import subprocess

from mathutils import Matrix, Quaternion, Vector

from zenkit import ModelAnimation

import helpers


def rf(f, accuracy=4):
    return round(f, accuracy)


def parse_man(model_animation, mdh_dict):
    asc_name = str(model_animation.source_path).split('\\')[-1]

    if model_animation.checksum != mdh_dict['checksum']:
        return None

    animation_data = {'checksum': model_animation.checksum,
                      'frame_count': model_animation.frame_count,
                      'fps': model_animation.fps,
                      'fps_source': model_animation.fps_source,
                      'layer': model_animation.layer,
                      'source_script': {}, 'frames': {}}

    bone_offset = 0
    frame_offset = 0
    for sample_index, sample in enumerate(model_animation.samples):
        if bone_offset >= len(model_animation.node_indices):
            bone_offset = 0
            frame_offset = frame_offset + 1

        bone_index = model_animation.node_indices[bone_offset]

        bone_name = mdh_dict['nodes'][bone_index]['name']
        if bone_name not in animation_data['frames']:
            animation_data['frames'][bone_name] = {}

        translation = [sample.position.x, sample.position.y, sample.position.z]
        rotation = [sample.rotation.x, sample.rotation.y, sample.rotation.z, sample.rotation.w]

        translation = [rf(f) for f in translation]
        rotation = [rf(f) for f in rotation]

        if 'translation' not in animation_data['frames'][bone_name]:
            animation_data['frames'][bone_name]['translation'] = []

        animation_data['frames'][bone_name]['translation'].append(translation)

        if 'rotation' not in animation_data['frames'][bone_name]:
            animation_data['frames'][bone_name]['rotation'] = []
        animation_data['frames'][bone_name]['rotation'].append(rotation)

        bone_offset = bone_offset + 1

    return animation_data


def convert(extract_path, intermediate_path, convert_path, blender_executable_file_path, blender_script_file_path):
    man_file_path_list = list(Path(extract_path).rglob(f'*.MAN'))
    for man_file_path in man_file_path_list:
        relative_path = man_file_path.relative_to(extract_path)

        game_type_folder = str(relative_path).split('/')[0]
        game_type_folder = game_type_folder.split('\\')[0]

        # if 'HUMANS' not in str(man_file_path):
        #     continue
        #
        # if 'VDF_Anims' not in str(man_file_path):
        #     continue

        model_animation = ModelAnimation.load(man_file_path)
        checksum = model_animation.checksum

        # order is import
        folder_path_list = ['Mod', 'Addon', 'Gothic II', 'Gothic']
        for folder_path in folder_path_list[:]:
            if folder_path.upper() != game_type_folder.upper():
                folder_path_list.remove(folder_path)
            else:
                break

        model_hierarchy_dict = None
        for folder_path in folder_path_list:
            mdh_file_path_list = list(Path(intermediate_path / folder_path).rglob(f'*.MDH.json'))
            for temp_mdh_file_path in mdh_file_path_list:
                mdh_data = temp_mdh_file_path.read_text()
                mdh_dict = json.loads(mdh_data)
                if 'checksum' in mdh_dict and mdh_dict['checksum'] == checksum:
                    model_hierarchy_dict = mdh_dict
                    break
            if model_hierarchy_dict:
                break

        if model_hierarchy_dict is None:
            print(f'[MODEL ANIMATION] ERROR: can\'t find model hierarchy for {relative_path / man_file_path.stem}.MAN')
            continue

        man_data = parse_man(model_animation, model_hierarchy_dict)
        man_data = {'hierarchy': model_hierarchy_dict, 'animation': man_data}

        save_path = intermediate_path / (str(relative_path) + '.json')
        save_path.parent.mkdir(exist_ok=True, parents=True)

        json_data = json.dumps(man_data, indent=4, ensure_ascii=False, sort_keys=False, default=str)
        save_path.write_text(json_data, encoding='utf-8')

        print(f'prepared: {relative_path}')

    if __name__ != '__main__':
        print(f'[MODEL ANIMATION] Start convert MAN via blender')
        helpers.run_blender(blender_executable_file_path, blender_script_file_path)
        print(f'[MODEL ANIMATION] End convert MAN via blender')


def main():
    config_file_path = Path('config.json')
    if not config_file_path.exists():
        print(f'ERROR: can\'t find config file [{config_file_path}].')
        return
    config_data = config_file_path.read_text()
    config = json.loads(config_data)

    extract_path = Path(config['extract_folder'])
    if not extract_path.is_absolute():
        extract_path = Path.cwd() / extract_path
    intermediate_path = Path(config['intermediate_folder'])
    if not intermediate_path.is_absolute():
        intermediate_path = Path.cwd() / intermediate_path
    convert_path = Path(config['convert_folder'])
    if not convert_path.is_absolute():
        convert_path = Path.cwd() / convert_path

    if not extract_path.exists():
        print(f'ERROR: folder "{extract_path}" not exist!')
        return

    blender_executable_file_path = Path(config['blender_folder']) / 'blender.exe'
    blender_script_file_path = Path.cwd() / 'import_zengin_json' / 'import_man.py'

    convert(extract_path, intermediate_path, convert_path, blender_executable_file_path, blender_script_file_path)

    helpers.run_blender(blender_executable_file_path, blender_script_file_path)


if __name__ == '__main__':
    main()
