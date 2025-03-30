import json
import shutil
from importlib.resources import read_text
from pathlib import Path
import subprocess

from zenkit import MorphMesh

from convert_multiresolution_mesh import parse_multiresolution_mesh
import helpers




def rf(f):
    return round(f, 4)


def parse_morph_mesh(morph_mesh: MorphMesh):
    morph_mesh_dict = {'name': '', 'multiresolution_mesh': {}, 'morph_positions': [], 'animations': []}
    name = morph_mesh.name
    # sources = morph_mesh.sources[0].file

    morph_mesh_dict['name'] = name

    # print(f'{name=}')
    # print(f'{sources=}')

    for morph_position in morph_mesh.morph_positions:
        morph_position = [morph_position.x, morph_position.y, morph_position.z]
        morph_position = [rf(f) for f in morph_position]
        morph_mesh_dict['morph_positions'].append(morph_position)

    for animation in morph_mesh.animations:
        animation_dict = dict()
        animation_dict['name'] = animation.name
        animation_dict['layer'] = animation.layer
        animation_dict['blend_in'] = rf(animation.blend_in * 10.0)
        animation_dict['duration'] = rf(animation.duration.total_seconds() / 1000.0)
        animation_dict['blend_out'] = rf(animation.blend_out * 10.0)
        animation_dict['flags'] = animation.flags
        animation_dict['frame_count'] = animation.frame_count
        animation_dict['speed'] = int(animation.speed * 1000.0)

        animation_dict['vertices'] = animation.vertices
        sample_list = []
        for sample in animation.samples:
            sample = [sample.x, sample.y, sample.z]
            sample = [rf(f) for f in sample]
            sample_list.append(sample)
        animation_dict['samples'] = sample_list


        morph_mesh_dict['animations'].append(animation_dict)

    morph_mesh_dict['multiresolution_mesh'] = parse_multiresolution_mesh(morph_mesh.mesh)

    return morph_mesh_dict


def convert(extract_path, intermediate_path, convert_path, blender_executable_file_path, blender_script_file_path):
    mmb_file_path_list = list(Path(extract_path).rglob(f'*.MMB'))

    for mmb_file_path in mmb_file_path_list:
        relative_path = mmb_file_path.relative_to(extract_path).parent  # / zen_file_path.stem

        # if 'Gothic II' not in str(mmb_file_path):
        #     continue
        #
        # if 'ITRW_BOW_L_01' not in str(mmb_file_path):
        #     continue

        morph_mesh = None
        try:
            morph_mesh = MorphMesh.load(mmb_file_path)
        except:
            print(f'[MORPH MESH] ERROR: can\'t open: {relative_path / mmb_file_path.stem}.MMB')
            continue


        morph_mesh_dict = parse_morph_mesh(morph_mesh)

        json_data = json.dumps(morph_mesh_dict, indent=4, ensure_ascii=False)

        save_path = intermediate_path / relative_path
        save_path.mkdir(exist_ok=True, parents=True)

        save_path = save_path / (mmb_file_path.stem + '.MMB.json')
        save_path.write_text(json_data, encoding='utf-8')

        print(f'prepared: {relative_path / mmb_file_path.stem}.MMB')

    if __name__ != '__main__':
        print(f'[MORPH MESH] Start convert MMB via blender')
        helpers.run_blender(blender_executable_file_path, blender_script_file_path)
        print(f'[MORPH MESH] End convert MMB via blender')


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
    blender_script_file_path = Path.cwd() / 'import_zengin_json' / 'import_mmb.py'

    convert(extract_path, intermediate_path, convert_path, blender_executable_file_path, blender_script_file_path)

    helpers.run_blender(blender_executable_file_path, blender_script_file_path)


if __name__ == '__main__':
    main()
