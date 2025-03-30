import json
import shutil
from importlib.resources import read_text
from pathlib import Path
import subprocess
import math

from zenkit import MultiResolutionMesh

import helpers


def rf(f):
    return round(f, 4)


def parse_multiresolution_mesh(multiresolution_mesh: MultiResolutionMesh):
    multi_resolution_mesh_dict = {'positions': [], 'submeshes': []}

    materials_dict = helpers.parse_materials(multiresolution_mesh.material)
    if materials_dict:
        multi_resolution_mesh_dict['materials'] = materials_dict

    for position in multiresolution_mesh.positions:
        position = [position.x, position.y, position.z]
        position = [rf(f) for f in position]
        multi_resolution_mesh_dict['positions'].append(position)

    for submesh in multiresolution_mesh.submeshes:
        submesh_dict = {'triangles': [], 'wedges': []}

        for triangle in submesh.triangles:
            submesh_dict['triangles'].append(triangle.wedges)

        for wedge in submesh.wedges:
            normal = [wedge.normal.x, wedge.normal.y, wedge.normal.z]
            normal = [rf(f) for f in normal]
            texture = [wedge.texture.x, wedge.texture.y]
            texture = [0.5 if math.isnan(f) else f for f in texture]
            texture = [rf(f) for f in texture]
            positions_index = wedge.index

            wedge_dict = {'positions_index': positions_index, 'normal': normal, 'texture': texture}
            submesh_dict['wedges'].append(wedge_dict)

        # for triangle_plane_index in submesh.triangle_plane_indices:
        #     if 'triangle_plane_indices' not in submesh_dict:
        #         submesh_dict['triangle_plane_indices'] = []
        #     submesh_dict['triangle_plane_indices'].append(triangle_plane_index)
        #
        # for triangle_plane in submesh.triangle_planes:
        #     if 'triangle_plane' not in submesh_dict:
        #         submesh_dict['triangle_plane'] = []
        #     submesh_dict['triangle_plane'].append(triangle_plane)
        #
        # for triangle_edge in submesh.triangle_edges:
        #     if 'triangle_edges' not in submesh_dict:
        #         submesh_dict['triangle_edges'] = []
        #     submesh_dict['triangle_edges'].append(triangle_edge.edges)

        multi_resolution_mesh_dict['submeshes'].append(submesh_dict)

    return multi_resolution_mesh_dict


def convert(extract_path, intermediate_path, convert_path, blender_executable_file_path, blender_script_file_path):
    mrm_file_path_list = list(Path(extract_path).rglob(f'*.MRM'))

    for mrm_file_path in mrm_file_path_list:
        relative_path = mrm_file_path.relative_to(extract_path).parent  # / zen_file_path.stem

        # if 'VDF_Meshes_Addon' not in str(mrm_file_path):  # Gothic II
        #     continue

        # if '1H_HAMMER_GODENDAR' not in str(mrm_file_path):  # NW_HARBOUR_BARREL_01
        #     continue

        multiresolution_mesh = None
        try:
            multiresolution_mesh = MultiResolutionMesh.load(mrm_file_path)
        except:
            print(f'[MULTIRESOLUTION MESH] ERROR: can\'t open: {relative_path / mrm_file_path.stem}.MRM')
            continue


        multiresolution_mesh_dict = parse_multiresolution_mesh(multiresolution_mesh)

        json_data = json.dumps(multiresolution_mesh_dict, indent=4, ensure_ascii=False)

        save_path = intermediate_path / relative_path
        save_path.mkdir(exist_ok=True, parents=True)

        save_path = save_path / (mrm_file_path.stem + '.MRM.json')
        save_path.write_text(json_data, encoding='utf-8')

        print(f'prepared: {relative_path / mrm_file_path.stem}.MRM')

    if __name__ != '__main__':
        print(f'[MULTIRESOLUTION MESH] Start convert MRM via blender')
        helpers.run_blender(blender_executable_file_path, blender_script_file_path)
        print(f'[MULTIRESOLUTION MESH] End convert MRM via blender')


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
    blender_script_file_path = Path.cwd() / 'import_zengin_json' / 'import_mrm.py'

    convert(extract_path, intermediate_path, convert_path, blender_executable_file_path, blender_script_file_path)

    helpers.run_blender(blender_executable_file_path, blender_script_file_path)


if __name__ == '__main__':
    main()
