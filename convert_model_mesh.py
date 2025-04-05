import json
import shutil
from importlib.resources import read_text
from pathlib import Path
import subprocess

from zenkit import ModelMesh, MultiResolutionMesh, SoftSkinMesh, SoftSkinWeight

from convert_multiresolution_mesh import parse_multiresolution_mesh
import helpers


def rf(f):
    return round(f, 4)


def check_mdh_compatibility(model_hierarchy_dict, model_mesh_dict):
    if 'nodes' not in model_hierarchy_dict or len(model_hierarchy_dict['nodes']) <= 0:
        return False

    if 'meshes' in model_mesh_dict and len(model_mesh_dict['meshes']) > 0:
        model_hierarchy_nodes_len = len(model_hierarchy_dict['nodes'])
        for mesh_list in model_mesh_dict['meshes']:
            for mesh in mesh_list:
                if 'soft_skin_weight' not in mesh or len(mesh['soft_skin_weight']) <= 0:
                    continue

                for soft_skin_weight_list_list in mesh['soft_skin_weight']:
                    for soft_skin_weight_list in soft_skin_weight_list_list:
                        for soft_skin_weight in soft_skin_weight_list:
                            if 'node_index' not in soft_skin_weight:
                                continue

                            if soft_skin_weight['node_index'] >= model_hierarchy_nodes_len:
                                return False

    if 'attachments' in model_mesh_dict and len(model_mesh_dict['attachments']) > 0:
        nodes_name_list = []
        for node in model_hierarchy_dict['nodes']:
            if 'name' in node:
                nodes_name_list.append(node['name'].upper())

        for attachment_list in model_mesh_dict['attachments']:
            for attachment_name in attachment_list:
                if attachment_name.upper() not in nodes_name_list:
                    return False

    return True


def parse_model_mesh(model_mesh: ModelMesh):
    checksum = model_mesh.checksum

    attachment_list = []
    for attachment_key, attachment_value in model_mesh.attachments.items():
        attachment_dict = parse_multiresolution_mesh(attachment_value)
        attachment_dict = {attachment_key: attachment_dict}
        attachment_list.append(attachment_dict)

    meshes = []
    for mesh in model_mesh.meshes:
        mesh_dict = {'multi_resolution_mesh': {}, 'soft_skin_weight': [], 'nodes': []}

        mesh_dict['multi_resolution_mesh'] = parse_multiresolution_mesh(mesh.mesh)

        # materials_dict = helpers.parse_materials(multi_resolution_mesh.material)
        # if materials_dict:
        #     multi_resolution_mesh_dict['materials'] = materials_dict
        #
        # for position in multi_resolution_mesh.positions:
        #     position = [position.x, position.y, position.z]
        #     position = [rf(f) for f in position]
        #     multi_resolution_mesh_dict['positions'].append(position)
        #
        # for submesh in multi_resolution_mesh.submeshes:
        #     submesh_dict = {'triangles': [], 'wedges': []}
        #
        #     for triangle in submesh.triangles:
        #         submesh_dict['triangles'].append(triangle.wedges)
        #
        #     for wedge in submesh.wedges:
        #         normal = [wedge.normal.x, wedge.normal.y, wedge.normal.z]
        #         normal = [rf(f) for f in normal]
        #         uv = [wedge.texture.x, wedge.texture.y]
        #         uv = [rf(f) for f in uv]
        #         vertex_index = wedge.index
        #
        #         wedge_dict = {'vertex_index': vertex_index, 'normal': normal, 'uv': uv}
        #         submesh_dict['wedges'].append(wedge_dict)
        #
        #     for triangle_plane_index in submesh.triangle_plane_indices:
        #         if 'triangle_plane_indices' not in submesh_dict:
        #             submesh_dict['triangle_plane_indices'] = []
        #         submesh_dict['triangle_plane_indices'].append(triangle_plane_index)
        #
        #     for triangle_plane in submesh.triangle_planes:
        #         if 'triangle_plane' not in submesh_dict:
        #             submesh_dict['triangle_plane'] = []
        #         submesh_dict['triangle_plane'].append(triangle_plane)
        #
        #     # ERR
        #     # for edge in submesh.edges:
        #     # if 'edges' not in submesh_dict:
        #     #     submesh_dict['edges'] = []
        #     #     submesh_dict['edges'].append(edge.edges)
        #
        #     for triangle_edge in submesh.triangle_edges:
        #         if 'triangle_edges' not in submesh_dict:
        #             submesh_dict['triangle_edges'] = []
        #         submesh_dict['triangle_edges'].append(triangle_edge.edges)
        #
        #     multi_resolution_mesh_dict['submeshes'].append(submesh_dict)
        #
        # mesh_dict['multi_resolution_mesh'] = multi_resolution_mesh_dict

        for soft_skin_weight_list in mesh.weights:
            temp_soft_skin_weight_list = []
            for soft_skin_weight in soft_skin_weight_list:
                weight = rf(soft_skin_weight.weight)
                position = [soft_skin_weight.position.x, soft_skin_weight.position.y, soft_skin_weight.position.z]
                position = [rf(f) for f in position]
                node_index = soft_skin_weight.index
                soft_skin_weight_dict = {'node_index': node_index, 'weight': weight, 'position': position}
                temp_soft_skin_weight_list.append(soft_skin_weight_dict)
            mesh_dict['soft_skin_weight'].append(temp_soft_skin_weight_list)

        for node in mesh.nodes:
            mesh_dict['nodes'].append(node)

        meshes.append(mesh_dict)

    model_mesh_dict = {'checksum': checksum, 'attachments': attachment_list, 'meshes': meshes}

    return model_mesh_dict


def convert(extract_path, intermediate_path, convert_path, blender_executable_file_path, blender_script_file_path):
    mdm_file_path_list = list(Path(extract_path).rglob(f'*.MDM'))

    for mdm_file_path in mdm_file_path_list:
        filename = mdm_file_path.stem
        relative_path = mdm_file_path.relative_to(extract_path).parent  # / zen_file_path.stem

        game_type_folder = str(relative_path).split('/')[0]
        game_type_folder = game_type_folder.split('\\')[0]

        # if 'Gothic II' not in str(mdm_file_path):  # Addon, Gothic II,
        #     continue

        # if 'FIREPLACE_HIGH2' not in str(mdm_file_path):  # CHESTBIG_ADD_STONE_LOCKED, CHESTBIG_OCCHESTMEDIUM, GOL_BODY
        #     continue

        # if 'HUM_BODY_NAKED0' not in str(mdm_file_path):  # Addon, Gothic II,
        #     continue

        model_mesh = None
        try:
            model_mesh = ModelMesh.load(mdm_file_path)
        except:
            print(f'[MODEL MESH] ERROR: can\'t open: {relative_path / mdm_file_path.stem}.MDM')
            continue

        # mdh_file_path = intermediate_path / relative_path.parent / Path(str(relative_path.parent.name) + '.MDH.json')
        # if not mdh_file_path.exists():
        #     print(f'[MODEL MESH] ERROR: file "{mdh_file_path}" not exist, can\'t convert {relative_path}')
        #     continue

        model_mesh_dict = parse_model_mesh(model_mesh)
        assert 'checksum' in model_mesh_dict

        checksum = model_mesh_dict['checksum']

        model_hierarchy_dict = None

        # print(f'{checksum=}')

        # order is import
        folder_path_list = ['Mod', 'Addon', 'Gothic II', 'Gothic']
        for folder_path in folder_path_list[:]:
            if folder_path.upper() != game_type_folder.upper():
                folder_path_list.remove(folder_path)
            else:
                break

        if checksum != 0:
            # try to find model hierarchy by checksum
            for folder_path in folder_path_list:
                mdh_file_path_list = list(Path(intermediate_path / folder_path).rglob(f'*.MDH.json'))
                for mdh_file_path in mdh_file_path_list:
                    mdh_data = mdh_file_path.read_text()
                    mdh_dict = json.loads(mdh_data)
                    if 'checksum' in mdh_dict and mdh_dict['checksum'] == checksum:
                        model_hierarchy_dict = mdh_dict
                        break
                if model_hierarchy_dict:
                    break
        else:
            # MDL -> MDH (param name) -> MDH (file name)

            # try to find model hierarchy from .MDL with same name
            if model_hierarchy_dict is None:
                for folder_path in folder_path_list:
                    mdl_file_path_list = list(Path(intermediate_path / folder_path).rglob(f'{filename}.MDL.json'))
                    for mdl_file_path in mdl_file_path_list:
                        mdl_data = mdl_file_path.read_text()
                        mdl_dict = json.loads(mdl_data)
                        if 'hierarchy' in mdl_dict and check_mdh_compatibility(mdl_dict['hierarchy'], model_mesh_dict):
                            print(f'[MODEL MESH] WARNING: {relative_path / mdm_file_path.stem}.MDM using model hierarchy from {mdl_file_path}')
                            model_hierarchy_dict = mdl_dict['hierarchy']
                            break
                    if model_hierarchy_dict:
                        break

            # try to find model hierarchy from any .MDH with same name (in param)
            if model_hierarchy_dict is None:
                for folder_path in folder_path_list:
                    mdh_file_path_list = list(Path(intermediate_path / folder_path).rglob(f'*.MDH.json'))
                    for mdh_file_path in mdh_file_path_list:
                        mdh_data = mdh_file_path.read_text()
                        mdh_dict = json.loads(mdh_data)
                        if mdh_dict['name'].upper() == mdm_file_path.stem.upper():
                            if check_mdh_compatibility(mdh_dict, model_mesh_dict):
                                print(f'[MODEL MESH] WARNING: {relative_path / mdm_file_path.stem}.MDM using model hierarchy finding by name param (not by checksum) {mdh_file_path}')
                                model_hierarchy_dict = mdh_dict
                                break
                    if model_hierarchy_dict:
                        break

            # try to find model hierarchy from any .MDH with same name (by filename)
            if model_hierarchy_dict is None:
                for folder_path in folder_path_list:
                    mdh_file_path_list = list(Path(intermediate_path / folder_path).rglob(f'*.MDH.json'))
                    for mdh_file_path in mdh_file_path_list:
                        mdh_data = mdh_file_path.read_text()
                        mdh_dict = json.loads(mdh_data)
                        if mdh_file_path.stem.split('.')[0].upper() == mdm_file_path.stem.upper():
                            if check_mdh_compatibility(mdh_dict, model_mesh_dict):
                                print(f'[MODEL MESH] WARNING: {relative_path / mdm_file_path.stem}.MDM using model hierarchy finding by file name (not by checksum) {mdh_file_path}')
                                model_hierarchy_dict = mdh_dict
                                break
                    if model_hierarchy_dict:
                        break

        if model_hierarchy_dict is None:
            model_hierarchy_dict = dict()
            print(f'[MODEL MESH] ERROR: can\'t find model hierarchy for {relative_path / mdm_file_path.stem}.MDM')

        model_dict = {'hierarchy': model_hierarchy_dict, 'mesh': model_mesh_dict}
        json_data = json.dumps(model_dict, indent=4, ensure_ascii=False)

        save_path = intermediate_path / relative_path
        save_path.mkdir(exist_ok=True, parents=True)

        save_path_model_mesh = save_path / (mdm_file_path.stem + '.MDM.json')
        save_path_model_mesh.write_text(json_data, encoding='utf-8')

        print(f'prepared: {relative_path / mdm_file_path.stem}.MDM')

    if __name__ != '__main__':
        print(f'[MODEL MESH] Start convert MDM via blender')
        helpers.run_blender(blender_executable_file_path, blender_script_file_path)
        print(f'[MODEL MESH] End convert MDM via blender')


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
    blender_script_file_path = Path.cwd() / 'import_zengin_json' / 'import_mdm.py'

    convert(extract_path, intermediate_path, convert_path, blender_executable_file_path, blender_script_file_path)

    helpers.run_blender(blender_executable_file_path, blender_script_file_path)


if __name__ == '__main__':
    main()
