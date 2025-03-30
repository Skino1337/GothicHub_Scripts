import math

from mathutils import Matrix, Quaternion, Vector

import bpy


def rename_bones(hierarchy_dict):
    for index, node in enumerate(hierarchy_dict['nodes']):
        if len(node['name']) > 0:
            pass


def get_parent_node_data(node_dict, node_name):
    for n_name, n_data in node_dict.items():
        if node_name == n_name:
            if n_data['parent_name'] and n_data['parent_name'] in node_dict:
                return node_dict[n_data['parent_name']]

    return None


def get_child_node_data(node_dict, node_name, tag=None):
    for n_name, n_data in node_dict.items():
        if node_name == n_data['parent_name']:
            if tag:
                if tag in n_name:
                    return n_data
            else:
                return n_data

    return None


def bound_tail(head, tail, limit):
    is_raise = head > tail
    if is_raise:
        if limit >= head:
            return tail
        return max(tail, limit)
    else:
        if limit <= head:
            return tail
        return min(tail, limit)


def create_armature(hierarchy_dict, scale=0.01):
    if 'nodes' not in hierarchy_dict or len(hierarchy_dict['nodes']) <= 0:
        return None, None, None

    armature = bpy.data.armatures.new('Armature')
    # armature.display_type = 'STICK'
    armature_obj = bpy.data.objects.new(armature.name, armature)
    bpy.context.collection.objects.link(armature_obj)

    armature.show_names = True
    armature.show_axes = True

    # ---

    # select and set active
    armature_obj.select_set(True)
    bpy.context.view_layer.objects.active = armature_obj

    # bone edits only in edit mode
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)

    node_dict = dict()
    for index, node in enumerate(hierarchy_dict['nodes']):
        name = node['name']
        translation = Vector([f * scale for f in node['translation']])
        rotation = Quaternion(node['rotation'])
        parent_name = node['parent_name']

        if index == 0:
            root_translation = Vector([f * scale for f in hierarchy_dict['root_translation']])
            translation = translation + root_translation

        parent_transform_translation = Vector([0, 0, 0])
        parent_transform_rotation = Quaternion()
        parent_transform_matrix = Matrix().Identity(4)

        if parent_name and parent_name in node_dict:
            if 'transform_translation' in node_dict[parent_name]:
                parent_transform_translation = node_dict[parent_name]['transform_translation']
            if 'transform_rotation' in node_dict[parent_name]:
                parent_transform_rotation = node_dict[parent_name]['transform_rotation']
            if 'transform_matrix' in node_dict[parent_name]:
                parent_transform_matrix = node_dict[parent_name]['transform_matrix']

        transform_translation = parent_transform_rotation @ translation
        transform_translation = parent_transform_translation + transform_translation
        transform_rotation = parent_transform_rotation @ rotation

        transform_matrix = Matrix.Translation(translation) @ rotation.to_matrix().to_4x4()
        transform_matrix = parent_transform_matrix @ transform_matrix

        node_dict[name] = {'parent_name': parent_name, 'translation': translation, 'rotation': rotation,
                           'transform_translation': transform_translation, 'transform_rotation': transform_rotation,
                           'transform_matrix': transform_matrix}

    # create bones for skeleton
    for node_name, node_data in node_dict.items():
        bone = armature_obj.data.edit_bones.new(node_name)
        bone.head = [0, 0, 0]
        length = 0.1
        child_node_data = get_child_node_data(node_dict, node_name)
        if child_node_data:
            length = (node_data['transform_translation'] - child_node_data['transform_translation']).length
            length = max(length, 0.1)
        bone.tail = [length, 0, 0]

        # for animated mesh
        bone.use_deform = True

        # bound without this don't work
        bone.transform(node_data['transform_rotation'].to_matrix())
        bone.translate(node_data['transform_translation'])

        if child_node_data:
            x_bound = bound_tail(bone.head.x, bone.tail.x, child_node_data['transform_translation'].x)
            y_bound = bound_tail(bone.head.y, bone.tail.y, child_node_data['transform_translation'].y)
            z_bound = bound_tail(bone.head.z, bone.tail.z, child_node_data['transform_translation'].z)

            bone.length = abs((node_data['transform_translation'] - Vector([x_bound, y_bound, z_bound])).length)
        else:
            bbox_min = hierarchy_dict['bbox']['min']
            bbox_min = Vector([f * scale for f in bbox_min])
            bbox_max = hierarchy_dict['bbox']['max']
            bbox_max = Vector([f * scale for f in bbox_max])
            # bbox have very little values...
            parent_node_data = get_parent_node_data(node_dict, node_name)
            if parent_node_data and 'bone' in parent_node_data and parent_node_data['bone']:
                bone.length = parent_node_data['bone'].length / 2

        node_dict[node_name]['bone'] = bone
        if 'parent_name' in node_dict[node_name] and node_dict[node_name]['parent_name']:
            parent_name = node_dict[node_name]['parent_name']
            if 'bone' in node_dict[parent_name]:
                bone.parent = node_dict[parent_name]['bone']

    for node_name, node_data in node_dict.items():
        # asc style bone (main rotation axis)
        # translation_matrix = Matrix.Translation(node_data['transform_pos']).to_4x4()
        # rotation_matrix = node_data['transform_rot'].to_matrix().to_4x4()
        # transform_matrix = translation_matrix @ rotation_matrix
        transform_matrix = node_data['transform_matrix']

        default_bone_matrix = Matrix.Rotation(math.radians(-90.0), 4, 'Z').to_4x4()

        bone_matrix = transform_matrix @ default_bone_matrix

        # asc style bone (roll)
        bone_matrix = bone_matrix @ Matrix.Rotation(math.radians(90.0), 4, 'Y').to_4x4()

        # stay on foot
        bone_matrix = Matrix.Rotation(math.radians(90), 4, 'X').to_4x4() @ bone_matrix

        if 'bone' in node_dict[node_name] and node_dict[node_name]['bone']:
            bone = node_dict[node_name]['bone']
            bone.matrix = bone_matrix

            # mirror bug? fix
            bone.head = [-bone.head.x, bone.head.y, bone.head.z]
            bone.tail = [-bone.tail.x, bone.tail.y, bone.tail.z]
            bone.roll = (bone.roll * -1.0) + math.radians(180.0)

            bone_matrix = bone.matrix

        node_dict[node_name]['bone_matrix'] = bone_matrix

    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

    armature_obj.select_set(False)
    bpy.context.view_layer.objects.active = None

    return armature_obj, armature, node_dict
