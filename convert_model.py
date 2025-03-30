import json
import shutil
from importlib.resources import read_text
from pathlib import Path
import subprocess
from decimal import Decimal

from zenkit import Model

from convert_model_hierarchy import parse_mdh
from convert_model_mesh import parse_model_mesh
import helpers


def rf(f):
    return round(f, 4)


def parse_model(model: Model):
    model_hierarchy_dict = parse_mdh(model.hierarchy)
    model_mesh_dict = parse_model_mesh(model.mesh)

    model_dict = {'hierarchy': model_hierarchy_dict, 'mesh': model_mesh_dict}

    return model_dict


def convert(extract_path, intermediate_path, convert_path, blender_executable_file_path, blender_script_file_path):
    mdl_file_path_list = list(Path(extract_path).rglob(f'*.MDL'))

    for mdl_file_path in mdl_file_path_list:
        relative_path = mdl_file_path.relative_to(extract_path).parent  # / zen_file_path.stem

        # if 'Gothic II' not in str(mdl_file_path):  # Gothic II
        #     continue

        # if 'CR2_BODY' not in str(mdl_file_path):  # NW_HARBOUR_BARREL_01, CHESTBIG_OCCHESTMEDIUM, BARBQ_SCAV
        #     continue

        model = None
        try:
            model = Model.load(mdl_file_path)
        except:
            print(f'[MODEL] ERROR: can\'t open: {relative_path / mdl_file_path.stem}.MDL')
            continue

        model_dict = parse_model(model)

        json_data = json.dumps(model_dict, indent=4, ensure_ascii=False)

        save_path = intermediate_path / relative_path
        save_path.mkdir(exist_ok=True, parents=True)

        save_path = save_path / (mdl_file_path.stem + '.MDL.json')
        save_path.write_text(json_data, encoding='utf-8')

        print(f'prepared: {relative_path / mdl_file_path.stem}.MDL')

    if __name__ != '__main__':
        print(f'[MODEL] Start convert MDL via blender')
        helpers.run_blender(blender_executable_file_path, blender_script_file_path)
        print(f'[MODEL] End convert MDL via blender')


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
    blender_script_file_path = Path.cwd() / 'import_zengin_json' / 'import_mdl.py'

    convert(extract_path, intermediate_path, convert_path, blender_executable_file_path, blender_script_file_path)

    helpers.run_blender(blender_executable_file_path, blender_script_file_path)


if __name__ == '__main__':
    main()
