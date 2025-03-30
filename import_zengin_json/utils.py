from pathlib import Path
from mathutils import Vector

import shutil

import bpy


def rename_bone(bone_name, root_name='root'):
    name = bone_name

    name = name.strip()
    name = name.lower()
    name = name.replace(' ', '_')
    name = name.replace('-', '_')

    name = name.replace('_l_', '_left_')
    name = name.replace('_r_', '_right_')

    name = name.replace('zs_', 'socket_')

    name = name.replace('bip01', '')
    name = name.strip('_')

    if len(name) == 0:
        name = root_name

    return name


def rename_armature_bones(armature_obj):
    for pbone in armature_obj.pose.bones:
        pbone.name = rename_bone(pbone.name)


def add_root_bone(armature_obj, root_name='root'):
    root_pose_bone = None
    for pose_bone in armature_obj.pose.bones:
        if pose_bone.parent is None and len(pose_bone.children) > 0:
            root_pose_bone = pose_bone
            break

    # no root bone
    if root_pose_bone is None:
        return

    # check for already have root bone
    if root_pose_bone.head.length < 0.01 and root_pose_bone.tail.x < 0.01 and root_pose_bone.tail.y < 0.01:
        return

    if root_pose_bone.name == root_name:
        root_pose_bone.name = root_pose_bone.name + '1'

    # create new bone available only in armature edit mode
    armature_obj.select_set(True)
    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)

    # create new bones
    root_edit_bone_new = armature_obj.data.edit_bones.new(root_name)
    root_edit_bone_new.head = (0.0, 0.0, 0.0)
    root_edit_bone_new.tail = (0.0, 0.0, 0.1)

    # set relations
    armature_obj.data.edit_bones[root_pose_bone.name].parent = root_edit_bone_new

    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    armature_obj.select_set(False)
    bpy.context.view_layer.objects.active = None

    # copy animation data from old root to new root
    if armature_obj.animation_data and armature_obj.animation_data.action:
        action = armature_obj.animation_data.action

        # add fcurves to root
        action.fcurves.new(f'pose.bones["{root_name}"].location', index=0, action_group=root_name)  # x
        action.fcurves.new(f'pose.bones["{root_name}"].location', index=1, action_group=root_name)  # y
        action.fcurves.new(f'pose.bones["{root_name}"].location', index=2, action_group=root_name)  # z

        old_root_x_fcurve = action.fcurves.find(f'pose.bones["{root_pose_bone.name}"].location', index=0)
        old_root_y_fcurve = action.fcurves.find(f'pose.bones["{root_pose_bone.name}"].location', index=1)
        # old_root_z_fcurve = action.fcurves.find(f'pose.bones["{root_pose_bone.name}"].location', index=2)

        root_x_fcurve = action.fcurves.find(f'pose.bones["{root_name}"].location', index=0)
        # root_y_fcurve = action.fcurves.find(f'pose.bones["{root_name}"].location', index=1)
        root_z_fcurve = action.fcurves.find(f'pose.bones["{root_name}"].location', index=2)

        if old_root_x_fcurve and root_x_fcurve:
            for point in old_root_x_fcurve.keyframe_points:  # x = -x
                root_x_fcurve.keyframe_points.insert(frame=point.co[0], value=point.co[1] * -1)
            action.fcurves.remove(old_root_x_fcurve)

        if old_root_y_fcurve and root_z_fcurve:
            for point in old_root_y_fcurve.keyframe_points:  # z = y
                root_z_fcurve.keyframe_points.insert(frame=point.co[0], value=point.co[1])
            action.fcurves.remove(old_root_y_fcurve)


def reset_scene():
    for material in bpy.data.materials:
        bpy.data.materials.remove(material)

    scene = bpy.context.scene

    for child_collection in scene.collection.children:
        scene.collection.children.unlink(child_collection)

    for child_object in scene.collection.objects:
        scene.collection.objects.unlink(child_object)

    bpy.ops.outliner.orphans_purge(do_recursive=True)


def get_texture_folder_list(convert_path):
    texture_folder_list = []
    if (convert_path / 'VDF_Textures').exists():
        texture_folder_list.append(str(convert_path / 'VDF_Textures'))
    if (convert_path / 'VDF_Textures_Addon').exists():
        texture_folder_list.append(str(convert_path / 'VDF_Textures_Addon'))

    for path in Path(convert_path).glob('*'):
        if not path.is_dir():
            continue
        if str(path) in texture_folder_list:
            continue

        texture_folder_list.append(str(path))

    return texture_folder_list


def get_texture_path_dict(texture_folder_list, texture_format='tga'):
    texture_path_dict = {}
    for texture_folder in texture_folder_list:
        for path in Path(texture_folder).rglob(f'*.{texture_format}'):  # case_sensitive=False
            texture_path_dict[path.stem.upper()] = str(path)

    return texture_path_dict


def get_eic_paths(config):
    extract_path = Path(config['extract_folder'])
    if not extract_path.is_absolute():
        extract_path = Path.cwd() / extract_path
    intermediate_path = Path(config['intermediate_folder'])
    if not intermediate_path.is_absolute():
        intermediate_path = Path.cwd() / intermediate_path
    convert_path = Path(config['convert_folder'])
    if not convert_path.is_absolute():
        convert_path = Path.cwd() / convert_path

    return extract_path, intermediate_path, convert_path


def export(file_path, config):
    export_format = ''
    if 'export_format' in config:
        export_format = config['export_format']

    # https://docs.blender.org/api/current/bpy.ops.export_scene.html
    if export_format.upper() == 'GLB':
        bpy.ops.export_scene.gltf(
            filepath=str(file_path),
            # export_normals=True,
            check_existing=False,
            export_format='GLB',
            # export_image_format='NONE',
            # export_keep_originals=True,
            export_texture_dir='../GLTF_Textures',
            export_image_quality=100,
            export_frame_range=True,
            export_anim_slide_to_zero=True,
        )

        # texture_folder_path = file_path.parent.parent / 'GLTF_Textures'
        # shutil.rmtree(texture_folder_path, ignore_errors=True)
    elif export_format.upper() == 'GLTF_SEPARATE':
        bpy.ops.export_scene.gltf(
            filepath=str(file_path),
            # export_normals=False,
            check_existing=False,
            export_format='GLTF_SEPARATE',
            # export_image_format='NONE',
            # export_keep_originals=True,
            export_texture_dir='../GLTF_Textures',
            export_image_quality=100
            # use_visible=True,
            # export_frame_range=True,
            # export_anim_slide_to_zero=True,
        )

        # texture_folder_path = file_path.parent.parent / 'GLTF_Textures'
        # shutil.rmtree(texture_folder_path, ignore_errors=True)
    elif export_format.upper() == 'FBX':
        bpy.ops.export_scene.fbx(
            filepath=str(file_path) + '.fbx',
            check_existing=False,
        )
    else:
        bpy.ops.wm.save_as_mainfile(filepath=str(file_path) + '.blend')
