import json
import shutil
from pathlib import Path

from mathutils import Matrix, Quaternion, Vector

from zenkit import ModelHierarchy


def rf(f, accuracy=4):
    return round(f, accuracy)


def parse_mdh(model_hierarchy, rename_bone_function=None):
    skeleton_name = ""
    try:
        skeleton_name = model_hierarchy.source_path
    except:
        print(f'[MODEL HIERARCHY] can\'t read source_path, set empty string.')
    skeleton_name = skeleton_name.split('\\')[-1].split('.')[0]

    root_translation = [model_hierarchy.root_translation.x, model_hierarchy.root_translation.y, model_hierarchy.root_translation.z]
    root_translation = [rf(f) for f in root_translation]

    bbox_min = [model_hierarchy.bbox.min.x, model_hierarchy.bbox.min.y, model_hierarchy.bbox.min.z]
    bbox_min = [rf(f) for f in bbox_min]
    bbox_max = [model_hierarchy.bbox.max.x, model_hierarchy.bbox.max.y, model_hierarchy.bbox.max.z]
    bbox_max = [rf(f) for f in bbox_max]

    collision_bbox_min = [model_hierarchy.collision_bbox.min.x, model_hierarchy.collision_bbox.min.y, model_hierarchy.collision_bbox.min.z]
    collision_bbox_min = [rf(f) for f in collision_bbox_min]
    collision_bbox_max = [model_hierarchy.collision_bbox.max.x, model_hierarchy.collision_bbox.max.y, model_hierarchy.collision_bbox.max.z]
    collision_bbox_max = [rf(f) for f in collision_bbox_max]

    date = 0
    try:
        date = model_hierarchy.source_date.total_seconds()
    except:
        pass

    skeleton_data = {'checksum': model_hierarchy.checksum,
                     'name': skeleton_name,
                     'root_translation': root_translation,
                     'bbox': {'min': bbox_min, 'max': bbox_max},
                     'collision_bbox': {'min': collision_bbox_min, 'max': collision_bbox_max},
                     'nodes': []}

    for i, model_node in enumerate(model_hierarchy.nodes):
        column_0 = model_node.transform.columns[0]
        column_1 = model_node.transform.columns[1]
        column_2 = model_node.transform.columns[2]
        column_3 = model_node.transform.columns[3]

        transform_mat = Matrix.Identity(4)
        transform_mat.col[0] = [column_0.x, column_0.y, column_0.z, column_0.w]
        transform_mat.col[1] = [column_1.x, column_1.y, column_1.z, column_1.w]
        transform_mat.col[2] = [column_2.x, column_2.y, column_2.z, column_2.w]
        transform_mat.col[3] = [column_3.x, column_3.y, column_3.z, column_3.w]

        translation, rotation, scale = transform_mat.decompose()
        translation = [rf(f) for f in translation]
        rotation = [rf(f) for f in rotation]

        for j in range(len(scale)):
            if 0.9998 < scale[j] < 1.0001:
                scale[j] = 1.0

        node_name_renamed = model_node.name
        if rename_bone_function:
            node_name_renamed = rename_bone_function(model_node.name)

        node = {'name': node_name_renamed, 'parent_index': model_node.parent, 'parent_name': '',
                'translation': [translation[0], translation[1], translation[2]],
                'rotation': [rotation[0], rotation[1], rotation[2], rotation[3]],
                'scale': [scale[0], scale[1], scale[2]]}

        skeleton_data['nodes'].append(node)

    for index, _ in enumerate(list(skeleton_data['nodes'])):
        parent_index = skeleton_data['nodes'][index]['parent_index']
        parent_name = ''
        if parent_index >= 0:
            parent_name = skeleton_data['nodes'][parent_index]['name']
        skeleton_data['nodes'][index]['parent_name'] = parent_name

    return skeleton_data


def convert(extract_path, intermediate_path, convert_path):
    mdh_file_path_list = list(Path(extract_path).rglob(f'*.MDH'))

    for mdh_file_path in mdh_file_path_list:
        relative_path = mdh_file_path.relative_to(extract_path)
        # save_path_convert = convert_path / (str(relative_path) + '.json')
        # save_path_convert.parent.mkdir(exist_ok=True, parents=True)
        save_path_intermediate = intermediate_path / (str(relative_path) + '.json')
        save_path_intermediate.parent.mkdir(exist_ok=True, parents=True)

        model_hierarchy = ModelHierarchy.load(mdh_file_path)
        mdh_data = parse_mdh(model_hierarchy)

        json_data = json.dumps(mdh_data, indent=4, ensure_ascii=False, sort_keys=False, default=str)
        # save_path_convert.write_text(json_data, encoding='utf-8')
        save_path_intermediate.write_text(json_data, encoding='utf-8')

        print(f'prepared: {relative_path}')


def main():
    config_file_path = Path('config.json')
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

    # shutil.rmtree(convert_path, ignore_errors=True)
    # convert_path.mkdir()

    convert(extract_path, intermediate_path, convert_path)


if __name__ == '__main__':
    main()
