import math

from mathutils import Matrix, Quaternion, Vector

import bpy


def get_bone_data(animation_dict, bone_name, frame):
    return_list = [[], []]

    for node_name, node_data in animation_dict['frames'].items():
        if node_name.upper() == bone_name.upper():
            if 'translation' in node_data and len(node_data['translation']) > frame:
                return_list[0] = node_data['translation'][frame]
            if 'rotation' in node_data and len(node_data['rotation']) > frame:
                return_list[1] = node_data['rotation'][frame]

    return return_list


def set_animation(armature_obj, armature, node_dict, animation_dict, rotation_mode_euler, bone_name, frame):
    pos, rot = get_bone_data(animation_dict, bone_name, frame)
    have_pos = False
    have_rot = False

    if len(pos) == 3:
        have_pos = True
    if len(rot) == 4:
        have_rot = True

    if have_rot:
        rot = [rot[2], rot[3], rot[0], rot[1]]

    bone_name_original = bone_name
    bone_name = bone_name.upper()

    if have_pos:
        if bone_name in node_dict and node_dict[bone_name]:
            pos = Vector([f / 100.0 for f in pos])

            node_matrix_translation = Matrix.Translation(node_dict[bone_name]['translation']).to_4x4()
            node_matrix_rotation = node_dict[bone_name]['rotation'].to_matrix().to_4x4()
            node_matrix = node_matrix_translation @ node_matrix_rotation

            frame_matrix_translation = Matrix.Translation(pos).to_4x4()
            frame_matrix_rotation = Quaternion(rot).to_matrix().to_4x4()
            frame_matrix = frame_matrix_translation @ frame_matrix_rotation

            # convert global coordinate to local
            m1 = node_matrix.inverted() @ frame_matrix
            pos = m1.to_translation()
            pos = Vector([-pos.z, pos.x, pos.y])

        # print(f'rot in pos calc: {get_euler_string(m1)}')

    rot_quat = Quaternion()
    if have_rot:
        rot_quat = Quaternion(rot)

        if bone_name in node_dict and node_dict[bone_name] and 'rotation' in node_dict[bone_name]:
            rot_quat = rot_quat @ node_dict[bone_name]['rotation']

        rot_quat = Quaternion(Vector([rot_quat.w, -rot_quat.z, rot_quat.x, rot_quat.y]))

    animation_data = armature_obj.animation_data

    if rotation_mode_euler:
        curve_path_pos = f'pose.bones["{bone_name_original}"].location'
        curve_path_rot = f'pose.bones["{bone_name_original}"].rotation_euler'

        curve_pos = [None, None, None]
        curve_rot = [None, None, None]

        for fc in animation_data.action.fcurves:
            if fc.data_path == curve_path_pos:
                curve_pos[fc.array_index] = fc
            elif fc.data_path == curve_path_rot:
                curve_rot[fc.array_index] = fc

        if have_pos:
            for i in range(len(curve_pos)):
                if not curve_pos[i]:
                    curve_pos[i] = animation_data.action.fcurves.new(curve_path_pos, index=i, action_group=bone_name_original)
                curve_pos[i].keyframe_points.insert(frame, pos[i])
                curve_pos[i].keyframe_points[-1].interpolation = 'LINEAR'

        if have_rot:
            rot_euler = rot_quat.to_euler()

            for i in range(len(curve_rot)):
                if curve_rot[i] is None:
                    curve_rot[i] = animation_data.action.fcurves.new(curve_path_rot, index=i, action_group=bone_name_original)
                curve_rot[i].keyframe_points.insert(frame, rot_euler[i])
                curve_rot[i].keyframe_points[-1].interpolation = 'LINEAR'
    else:
        curve_path_pos = f'pose.bones["{bone_name_original}"].location'
        curve_path_rot = f'pose.bones["{bone_name_original}"].rotation_quaternion'

        curve_pos = [None, None, None]
        curve_rot = [None, None, None, None]

        for fc in animation_data.action.fcurves:
            if fc.data_path == curve_path_pos:
                curve_pos[fc.array_index] = fc
            elif fc.data_path == curve_path_rot:
                curve_rot[fc.array_index] = fc

        if have_pos:
            for i in range(len(curve_pos)):
                if not curve_pos[i]:
                    curve_pos[i] = animation_data.action.fcurves.new(curve_path_pos, index=i, action_group=bone_name_original)
                curve_pos[i].keyframe_points.insert(frame, pos[i])
                curve_pos[i].keyframe_points[-1].interpolation = 'LINEAR'

        if have_rot:
            for i in range(len(curve_rot)):
                if curve_rot[i] is None:
                    curve_rot[i] = animation_data.action.fcurves.new(curve_path_rot, index=i, action_group=bone_name_original)
                curve_rot[i].keyframe_points.insert(frame, rot_quat[i])
                curve_rot[i].keyframe_points[-1].interpolation = 'LINEAR'


def create_animation(armature_obj, armature, node_dict, animation_dict, rotation_mode_euler=True):
    frame_count = int(animation_dict['frame_count'])
    assert frame_count >= 1

    scene = bpy.context.scene
    scene.render.fps = int(animation_dict['fps'])
    scene.frame_start = 0
    scene.frame_end = frame_count - 1
    scene.frame_set(0)

    animation_data = armature_obj.animation_data
    if animation_data is None:
        animation_data = armature_obj.animation_data_create()

    if animation_data.action:
        bpy.data.actions.remove(animation_data.action, do_unlink=True)

    animation_data.action = bpy.data.actions.new(f'{armature_obj.name}Action')

    for frame in range(frame_count):
        # print(f'{frame=}')
        for pose_bone in armature_obj.pose.bones:
            bone_name = pose_bone.name
            # print(f'{pose_bone=}')
            if rotation_mode_euler:
                pose_bone.rotation_mode = 'XYZ'
            else:
                pose_bone.rotation_mode = 'QUATERNION'
            set_animation(armature_obj, armature, node_dict, animation_dict, rotation_mode_euler, bone_name, frame)
