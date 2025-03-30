import json
import shutil
from pathlib import Path

import convert_textures
import convert_model_hierarchy
import convert_model_scripts
import convert_model
import convert_model_mesh
import convert_morph_mesh
import convert_multiresolution_mesh
import convert_model_animations
import convert_worlds
import helpers


def find_latest_blender():
    system_disc_list = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'J']
    for system_disc in system_disc_list:
        blender_foundation_folder_path = Path(system_disc + ':/Program Files/Blender Foundation')
        if not blender_foundation_folder_path.exists():
            continue

        blender_folder_path_list = list(blender_foundation_folder_path.glob(f'*'))
        blender_folder_path_list = sorted([path for path in blender_folder_path_list if path.is_dir()])

        if len(blender_folder_path_list):
            return blender_folder_path_list[-1]

    return ''


def convert():
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
    if not blender_executable_file_path.exists():
        blender_folder = find_latest_blender()
        blender_executable_file_path = Path(blender_folder) / 'blender.exe'
        if not blender_executable_file_path.exists():
            print(f'ERROR: can\'t find blender executable file.')
            return
        else:
            print(f'WARNING: Blender folder don\'t setup in config, used blender with path: {blender_folder}')

    shutil.rmtree(intermediate_path, ignore_errors=True)
    intermediate_path.mkdir(parents=True, exist_ok=True)

    shutil.rmtree(convert_path, ignore_errors=True)
    convert_path.mkdir(parents=True, exist_ok=True)

    convert_textures.convert(extract_path, convert_path)

    convert_model_hierarchy.convert(extract_path, intermediate_path, convert_path)

    convert_model_scripts.convert(extract_path, intermediate_path, convert_path)

    blender_script_file_path = Path.cwd() / 'import_zengin_json' / 'import_mdl.py'
    convert_model.convert(extract_path, intermediate_path, convert_path, blender_executable_file_path, blender_script_file_path)

    # model mesh must be after "model hierarchy" and after "model"
    blender_script_file_path = Path.cwd() / 'import_zengin_json' / 'import_mdm.py'
    convert_model_mesh.convert(extract_path, intermediate_path, convert_path, blender_executable_file_path, blender_script_file_path)

    blender_script_file_path = Path.cwd() / 'import_zengin_json' / 'import_mmb.py'
    convert_morph_mesh.convert(extract_path, intermediate_path, convert_path, blender_executable_file_path, blender_script_file_path)

    blender_script_file_path = Path.cwd() / 'import_zengin_json' / 'import_mrm.py'
    convert_multiresolution_mesh.convert(extract_path, intermediate_path, convert_path, blender_executable_file_path, blender_script_file_path)

    blender_script_file_path = Path.cwd() / 'import_zengin_json' / 'import_man.py'
    convert_model_animations.convert(extract_path, intermediate_path, convert_path, blender_executable_file_path, blender_script_file_path)

    blender_script_file_path = Path.cwd() / 'import_zengin_json' / 'import_zen.py'
    convert_worlds.convert(extract_path, intermediate_path, convert_path, blender_executable_file_path, blender_script_file_path)


if __name__ == '__main__':
    convert()
