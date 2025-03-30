import json
import shutil
from importlib.resources import read_text
from pathlib import Path
import subprocess

from zenkit import World, VirtualObject, VobType
from zenkit import MovableObject, InteractiveObject, Container, Door, Fire, SoundMaterialType
from zenkit import Trigger, TriggerList, TriggerScript, TriggerChangeLevel, TriggerWorldStart, TriggerUntouch
from zenkit import Mover, MoverBehavior, MoverSpeedType, TriggerBatchMode, TriggerListTarget
from zenkit import Sound, SoundDaytime
from zenkit import ModelScript, AnimationFlags, AnimationDirection

import helpers

vob_index = 0


def rf(f):
    return round(f, 4)


def pasrse_vob(vob_list):
    # https://auronen.cokoliv.eu/gmc/zengin/worlds/Classes/zCVob/#__tabbed_1_2

    global vob_index

    vob_dict_list = []
    for vob in vob_list:

        # print(vob)

        class_name = vob.__class__.__name__
        rot = [vob.rotation.columns[0][0], vob.rotation.columns[1][0], vob.rotation.columns[2][0],
               vob.rotation.columns[0][1], vob.rotation.columns[1][1], vob.rotation.columns[2][1],
               vob.rotation.columns[0][2], vob.rotation.columns[1][2], vob.rotation.columns[2][2]]
        rot = [rf(f) for f in rot]

        pos = [rf(vob.position.x), rf(vob.position.y), rf(vob.position.z)]

        bbox_min = [rf(vob.bbox.min.x - vob.position.x), rf(vob.bbox.min.y - vob.position.y), rf(vob.bbox.min.z - vob.position.z)]
        bbox_max = [rf(vob.bbox.max.x - vob.position.x), rf(vob.bbox.max.y - vob.position.y), rf(vob.bbox.max.z - vob.position.z)]

        vob_index = vob_index + 1
        vob_dict = {}
        vob_dict['id'] = vob_index
        vob_dict['type'] = vob.type.name
        # Internals
        # 'pack': 0,
        if len(vob.preset_name) != 0:
            vob_dict['presetName'] = vob.preset_name
        if bbox_min != [0.0, 0.0, 0.0] or bbox_max != [0.0, 0.0, 0.0]:
            vob_dict['bbox3DWS'] = {'min': bbox_min, 'max': bbox_max}
        if rot != [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]:
            vob_dict['trafoOSToWSRot'] = rot
        vob_dict['trafoOSToWSPos'] = pos
        # Vob
        if len(vob.name) != 0:
            vob_dict['vobName'] = vob.name
        if len(vob.visual.name) != 0:
            vob_dict['visual'] = {'name': vob.visual.name.split('.')[0], 'type': vob.visual.type.name}
        if not vob.show_visual:
            vob_dict['showVisual'] = vob.show_visual

        # ValueError: 254 is not a valid SpriteAlignment
        sprite_camera_facing_mode_name = 'NONE'
        try:
            sprite_camera_facing_mode_name = vob.sprite_camera_facing_mode.name
        except ValueError as error:
            print(f'[WORLD] WARNING: Vob(id={vob_index}) have wrong value in parameter [visualCamAlign], set default value to "NONE". Error: "{error}"')
        if sprite_camera_facing_mode_name != 'NONE':
            vob_dict['visualCamAlign'] = sprite_camera_facing_mode_name

        # 3 is not a valid AnimationType
        anim_mode_name = 'NONE'
        try:
            anim_mode_name = vob.anim_mode.name
        except ValueError as error:
            print(f'[WORLD] WARNING: Vob(id={vob_index}) have wrong value in parameter [visualAniMode], set default value to "NONE". Error: "{error}"')
        if anim_mode_name != 'NONE':
            vob_dict['visualAniMode'] = anim_mode_name

        if rf(vob.anim_strength) != 0.0:
            vob_dict['visualAniModeStrength'] = rf(vob.anim_strength)
        if rf(vob.far_clip_scale) != 1.0:
            vob_dict['vobFarClipZScale'] = rf(vob.far_clip_scale)
        if vob.cd_static != False:
            vob_dict['cdStatic'] = vob.cd_static
        if vob.cd_dynamic != False:
            vob_dict['cdDyn'] = vob.cd_dynamic
        if vob.vob_static != False:
            vob_dict['staticVob'] = vob.vob_static
        if vob.dynamic_shadows.name != 'NONE':
            vob_dict['dynShadow'] = vob.dynamic_shadows.name
        if vob.bias != 1:
            vob_dict['zbias'] = vob.bias
        if vob.ambient != False:
            vob_dict['isAmbient'] = vob.ambient

        # if isinstance(vob, MovableObject) or issubclass(vob, MovableObject):
        #     print(f'class or subclass of MovableObject, {vob.type.name}')

        # if hasattr(vob, '__class__'):
        #     # print(f'{vob} has attr __class__')
        #     pass
        # else:
        #     print(f'{vob} no have attr __class__')

        if class_name == 'VirtualObject':
            pass
        elif class_name == 'Item':
            vob_dict['itemInstance'] = vob.instance
        elif issubclass(type(vob), MovableObject):
            vob_dict['focusName'] = vob.name
            vob_dict['hitpoints'] = vob.hp
            vob_dict['damage'] = vob.damage
            vob_dict['moveable'] = vob.movable
            vob_dict['takeable'] = vob.takable
            vob_dict['focusOverride'] = vob.focus_override
            vob_dict['soundMaterial'] = vob.material.name
            vob_dict['visualDestroyed'] = vob.visual_destroyed
            vob_dict['owner'] = vob.owner
            vob_dict['ownerGuild'] = vob.owner_guild
            if issubclass(type(vob), InteractiveObject):
                vob_dict['stateNum'] = vob.state
                vob_dict['triggerTarget'] = vob.target
                vob_dict['useWithItem'] = vob.item
                vob_dict['conditionFunc'] = vob.condition_function
                vob_dict['onStateFunc'] = vob.on_state_change_function
                vob_dict['rewind'] = vob.rewind
                if vob_dict['type'] == 'oCMobBed':
                    pass
                elif issubclass(type(vob), Fire):
                    vob_dict['fireSlot'] = vob.slot
                    vob_dict['fireVobtreeName'] = vob.vob_tree
                elif vob_dict['type'] == 'oCMobLadder':
                    pass
                elif (vob_dict['type'] == 'oCMobLockable' or
                      issubclass(type(vob), Container) or
                      issubclass(type(vob), Door)):
                    vob_dict['locked'] = vob.is_locked
                    vob_dict['keyInstance'] = vob.key
                    vob_dict['pickLockStr'] = vob.pick_string
                    if issubclass(type(vob), Container):
                        vob_dict['contents'] = vob.contents
                    elif issubclass(type(vob), Door):
                        pass
                elif vob_dict['type'] == 'oCMobSwitch':
                    pass
                elif vob_dict['type'] == 'oCMobWheel':
                    pass
                elif class_name == 'InteractiveObject':
                    pass
                else:
                    print(f'WARNING!!! VOB DON\'T PARSED ({class_name})')
            elif class_name == 'MovableObject':
                pass
            else:
                print(f'WARNING!!! VOB DON\'T PARSED ({class_name})')
        elif class_name == 'Animate':
            vob_dict['start_on'] = vob.start_on
            vob_dict['is_running'] = vob.is_running
        elif class_name == 'LensFlare':
            vob_dict['effect'] = vob.effect
        elif class_name == 'ParticleEffectController':
            vob_dict['effect_name'] = vob.effect_name
            vob_dict['kill_when_done'] = vob.kill_when_done
            vob_dict['initially_running'] = vob.initially_running
        elif class_name == 'MessageFilter':
            vob_dict['target'] = vob.target
            vob_dict['on_trigger'] = vob.on_trigger
            vob_dict['on_untrigger'] = vob.on_untrigger
        elif class_name == 'CodeMaster':
            vob_dict['target'] = vob.target
            vob_dict['ordered'] = vob.ordered
            vob_dict['first_false_is_failure'] = vob.first_false_is_failure
            vob_dict['failure_target'] = vob.failure_target
            vob_dict['untriggered_cancels'] = vob.untriggered_cancels
            slaves = []
            for slave in vob.slaves:
                if isinstance(vob.slaves, str):
                    slaves.append(slave)
                elif slave.__class__.__name__ == 'ZkString':
                    slaves.append(slave.value)
            vob_dict['slaves'] = slaves
        elif class_name == 'MoverController':
            vob_dict['target'] = vob.target
            vob_dict['message'] = vob.message
            vob_dict['key'] = vob.key
        elif class_name == 'TouchDamage':
            vob_dict['damage'] = vob.damage
            vob_dict['is_barrier'] = vob.is_barrier
            vob_dict['is_blunt'] = vob.is_blunt
            vob_dict['is_edge'] = vob.is_edge
            vob_dict['is_fire'] = vob.is_fire
            vob_dict['is_fly'] = vob.is_fly
            vob_dict['is_magic'] = vob.is_magic
            vob_dict['is_point'] = vob.is_point
            vob_dict['is_fall'] = vob.is_fall
            vob_dict['repeat_delay_seconds'] = vob.repeat_delay_seconds
            vob_dict['volume_scale'] = vob.volume_scale
            vob_dict['collision_type'] = vob.collision_type
        elif class_name == 'Earthquake':
            vob_dict['radius'] = vob.radius
            vob_dict['duration'] = vob.duration
            amplitude = [rf(vob.amplitude.x), rf(vob.amplitude.y), rf(vob.amplitude.z)]
            vob_dict['amplitude'] = amplitude
        elif class_name == 'CutsceneCamera':
            vob_dict['trajectory_for'] = vob.trajectory_for
            vob_dict['target_trajectory_for'] = vob.target_trajectory_for
            vob_dict['loop_mode'] = vob.loop_mode
            vob_dict['lerp_mode'] = vob.lerp_mode
            vob_dict['ignore_for_vob_rotation'] = vob.ignore_for_vob_rotation
            vob_dict['ignore_for_vob_rotation_target'] = vob.ignore_for_vob_rotation_target
            vob_dict['adapt'] = vob.adapt
            vob_dict['ease_first'] = vob.ease_first
            vob_dict['ease_last'] = vob.ease_last
            vob_dict['total_duration'] = vob.total_duration
            vob_dict['auto_focus_vob'] = vob.auto_focus_vob
            vob_dict['auto_player_movable'] = vob.auto_player_movable
            vob_dict['auto_untrigger_last'] = vob.auto_untrigger_last
            vob_dict['auto_untrigger_last_delay'] = vob.auto_untrigger_last_delay
            vob_dict['position_count'] = vob.position_count
            vob_dict['is_paused'] = vob.is_paused
            vob_dict['is_started'] = vob.is_started
            vob_dict['goto_time_mode'] = vob.goto_time_mode
            vob_dict['time'] = vob.time
            vob_dict['frames'] = pasrse_vob(vob.frames)
        elif class_name == 'CameraTrajectoryFrame':
            vob_dict['time'] = vob.time
            vob_dict['roll_angle'] = vob.roll_angle
            vob_dict['fov_scale'] = vob.fov_scale
            vob_dict['motion_type'] = vob.motion_type
            vob_dict['motion_type_fov'] = vob.motion_type_fov
            vob_dict['motion_type_roll'] = vob.motion_type_roll
            vob_dict['motion_type_time_scale'] = vob.motion_type_time_scale
            vob_dict['tension'] = vob.tension
            vob_dict['cam_bias'] = vob.cam_bias
            vob_dict['continuity'] = vob.continuity
            vob_dict['time_scale'] = vob.time_scale
            vob_dict['time_fixed'] = vob.time_fixed
            original_pose = [vob.original_pose.columns[0][0], vob.original_pose.columns[1][0], vob.original_pose.columns[2][0], vob.original_pose.columns[3][0],
                             vob.original_pose.columns[0][1], vob.original_pose.columns[1][1], vob.original_pose.columns[2][1], vob.original_pose.columns[3][1],
                             vob.original_pose.columns[0][2], vob.original_pose.columns[1][2], vob.original_pose.columns[2][2], vob.original_pose.columns[3][2],
                             vob.original_pose.columns[0][3], vob.original_pose.columns[1][3], vob.original_pose.columns[2][3], vob.original_pose.columns[3][3]]
            original_pose = [rf(f) for f in original_pose]
            vob_dict['original_pose'] = original_pose
        elif class_name == 'Light':
            vob_dict['preset'] = vob.preset
            vob_dict['light_type'] = vob.light_type
            vob_dict['range'] = vob.range
            vob_dict['color'] = [vob.color.r, vob.color.g, vob.color.b, vob.color.a]
            vob_dict['cone_angle'] = vob.cone_angle
            vob_dict['is_static'] = vob.is_static
            vob_dict['quality'] = vob.quality
            vob_dict['lensflare_fx'] = vob.lensflare_fx
            vob_dict['on'] = vob.on
            vob_dict['range_animation_scale'] = vob.range_animation_scale
            vob_dict['range_animation_fps'] = vob.range_animation_fps
            vob_dict['range_animation_smooth'] = vob.range_animation_smooth
            color_animation = []
            for vob_ca in vob.color_animation:
                color_animation.append([vob_ca.r, vob_ca.g, vob_ca.b, vob_ca.a])
            vob_dict['color_animation'] = color_animation
            vob_dict['color_animation_fps'] = rf(vob.color_animation_fps)
            vob_dict['color_animation_smooth'] = vob.color_animation_smooth
            vob_dict['can_move'] = vob.can_move
        elif issubclass(type(vob), Sound):
            vob_dict['volume'] = vob.volume
            vob_dict['mode'] = vob.mode
            vob_dict['random_delay'] = vob.random_delay
            vob_dict['random_delay_var'] = vob.random_delay_var
            vob_dict['initially_playing'] = vob.initially_playing
            vob_dict['ambient3d'] = vob.ambient3d
            vob_dict['obstruction'] = vob.obstruction
            vob_dict['cone_angle'] = vob.cone_angle
            vob_dict['volume_type'] = vob.volume_type
            vob_dict['radius'] = vob.radius
            vob_dict['sound_name'] = vob.sound_name
            vob_dict['is_running'] = vob.is_running
            vob_dict['is_allowed_to_run'] = vob.is_allowed_to_run
            if issubclass(type(vob), SoundDaytime):
                vob_dict['start_time'] = vob.start_time
                vob_dict['end_time'] = vob.end_time
                vob_dict['sound_name_daytime'] = vob.sound_name_daytime
            elif class_name == 'Sound':
                pass
            else:
                print(f'WARNING!!! VOB DON\'T PARSED ({class_name})')
        elif issubclass(type(vob), Trigger):
            vob_dict['target'] = vob.target
            vob_dict['start_enabled'] = vob.start_enabled
            vob_dict['send_untrigger'] = vob.send_untrigger
            vob_dict['react_to_on_trigger'] = vob.react_to_on_trigger
            vob_dict['react_to_on_touch'] = vob.react_to_on_touch
            vob_dict['react_to_on_damage'] = vob.react_to_on_damage
            vob_dict['respond_to_object'] = vob.respond_to_object
            vob_dict['respond_to_pc'] = vob.respond_to_pc
            vob_dict['respond_to_npc'] = vob.respond_to_npc
            vob_dict['vob_target'] = vob.vob_target
            vob_dict['max_activation_count'] = vob.max_activation_count
            vob_dict['retrigger_delay_seconds'] = vob.retrigger_delay_seconds
            vob_dict['damage_threshold'] = vob.damage_threshold
            vob_dict['fire_delay_seconds'] = vob.fire_delay_seconds
            vob_dict['next_time_triggerable'] = vob.next_time_triggerable
            vob_dict['other_vob'] = vob.other_vob
            vob_dict['count_can_be_activated'] = vob.count_can_be_activated
            vob_dict['is_enabled'] = vob.is_enabled
            if issubclass(type(vob), Mover):
                vob_dict['behavior'] = vob.behavior
                vob_dict['touch_blocker_damage'] = vob.touch_blocker_damage
                vob_dict['stay_open_time_seconds'] = vob.stay_open_time_seconds
                vob_dict['is_locked'] = vob.is_locked
                vob_dict['auto_link'] = vob.auto_link
                vob_dict['auto_rotate'] = vob.auto_rotate
                vob_dict['speed'] = vob.speed
                vob_dict['lerp_type'] = vob.lerp_type
                vob_dict['speed_type'] = vob.speed_type
                vob_dict['act_key_pos_delta'] = [rf(vob.act_key_pos_delta.x), rf(vob.act_key_pos_delta.y), rf(vob.act_key_pos_delta.z)]
                vob_dict['act_keyframe_f'] = vob.act_keyframe_f
                vob_dict['act_keyframe'] = vob.act_keyframe
                vob_dict['next_keyframe'] = vob.next_keyframe
                vob_dict['move_speed_unit'] = vob.move_speed_unit
                vob_dict['advance_dir'] = vob.advance_dir
                vob_dict['trigger_event_count'] = vob.trigger_event_count
                vob_dict['stay_open_time_dest'] = vob.stay_open_time_dest
                vob_dict['sfx_open_start'] = vob.sfx_open_start
                vob_dict['sfx_open_end'] = vob.sfx_open_end
                vob_dict['sfx_transitioning'] = vob.sfx_transitioning
                vob_dict['sfx_close_start'] = vob.sfx_close_start
                vob_dict['sfx_close_end'] = vob.sfx_close_end
                vob_dict['sfx_lock'] = vob.sfx_lock
                vob_dict['sfx_unlock'] = vob.sfx_unlock
                vob_dict['sfx_use_locked'] = vob.sfx_use_locked
                key_frames = []
                for vob_kf in vob.keyframes:
                    position = [rf(vob_kf.position.x), rf(vob_kf.position.y), rf(vob_kf.position.z)]
                    rotation = [rf(vob_kf.rotation.w), rf(vob_kf.rotation.x), rf(vob_kf.rotation.y), rf(vob_kf.rotation.z)]
                    key_frames.append({'position': position, 'rotation': rotation})
                vob_dict['keyframes'] = key_frames
            elif issubclass(type(vob), TriggerList):
                vob_dict['mode'] = vob.mode
                vob_dict['act_target'] = vob.act_target
                vob_dict['send_on_trigger'] = vob.send_on_trigger
                targets = []
                for vob_t in vob.targets:
                    targets.append({'name': vob_t.name, 'delay_seconds': vob_t.delay_seconds})
                vob_dict['targets'] = targets
            elif issubclass(type(vob), TriggerScript):
                vob_dict['function'] = vob.function
            elif issubclass(type(vob), TriggerChangeLevel):
                vob_dict['level_name'] = vob.level_name
                vob_dict['start_vob'] = vob.start_vob
            elif class_name == 'Trigger':
                pass
            else:
                print(f'WARNING!!! VOB DON\'T PARSED ({class_name})')
        elif class_name == 'TriggerWorldStart':
            vob_dict['target'] = vob.target
            vob_dict['fire_once'] = vob.fire_once
            vob_dict['has_fired'] = vob.has_fired
        elif class_name == 'ZoneMusic':
            vob_dict['is_enabled'] = vob.is_enabled
            vob_dict['priority'] = vob.priority
            vob_dict['is_ellipsoid'] = vob.is_ellipsoid
            vob_dict['reverb'] = vob.reverb
            vob_dict['is_loop'] = vob.is_loop
            vob_dict['local_enabled'] = vob.local_enabled
            vob_dict['day_entrance_done'] = vob.day_entrance_done
            vob_dict['night_entrance_done'] = vob.night_entrance_done
        elif class_name == 'ZoneFog':
            vob_dict['range_center'] = vob.range_center
            vob_dict['inner_range_percentage'] = vob.inner_range_percentage
            vob_dict['color'] = [vob.color.r, vob.color.g, vob.color.b, vob.color.a]
            vob_dict['fade_out_sky'] = vob.fade_out_sky
            vob_dict['override_color'] = vob.override_color
        elif class_name == 'ZoneFarPlane':
            vob_dict['vob_far_plane_z'] = vob.vob_far_plane_z
            vob_dict['inner_range_percentage'] = vob.inner_range_percentage
        else:
            print(f'WARNING!!! VOB DON\'T PARSED ({class_name})')
            pass


        # # !! WORK!!!!
        # if vob_dict['name'] == 'oCMobDoor':
        #     pass
        # elif vob_dict['name'] == 'oCMobDoor':
        #     pass
        # elif vob_dict['name'] == 'oCMobDoor':
        #     pass
        # elif vob_dict['name'] == 'oCMobBed':
        #     pass
        # elif vob_dict['name'] == 'oCMobFire':
        #     vob_dict['fireSlot'] = vob.slot
        #     vob_dict['fireVobtreeName'] = vob.vob_tree
        # elif vob_dict['name'] == 'oCMobLadder':
        #     pass
        # elif vob_dict['name'] == 'oCMobLockable'
        # elif vob_dict['name'] == 'oCMobContainer':
        #     vob_dict['locked'] = vob.is_locked
        #     vob_dict['keyInstance'] = vob.key
        #     vob_dict['pickLockStr'] = vob.pick_string
        #     vob_dict['contents'] = vob.contents
        #     vob_dict['items'] = vob.items
        # elif vob_dict['name'] == 'oCMobDoor':
        #     pass
        # elif vob_dict['name'] == 'oCMobSwitch':
        #     pass
        # elif vob_dict['name'] == 'oCMobWheel':
        #     pass
        # else:
        #     print(f'unhandled vob type: {vob_dict["name"]}')

        children = pasrse_vob(vob.children)
        if len(children) > 0:
            vob_dict['children'] = children

        vob_dict_list.append(vob_dict)

    return vob_dict_list


def parse_waypoints(way_net):
    way_point_dict_list = []
    for way_point in way_net.points:
        way_point_dict = {'wpName': way_point.name,
                          'waterDepth': way_point.water_depth,
                          'underWater': way_point.under_water,
                          'position': [rf(way_point.position.z),
                                       rf(way_point.position.x),
                                       rf(way_point.position.y)],
                          'direction': [rf(way_point.direction.x),
                                       rf(way_point.direction.y),
                                       rf(way_point.direction.z)],
                          'freePoint': way_point.free_point,
                          'links': []}

        way_point_dict_list.append(way_point_dict)

    for edge in way_net.edges:
        way_point_dict_list[edge.a]['links'].append(way_point_dict_list[edge.b]['wpName'])

    return way_point_dict_list


def parse_mesh(mesh, bsp_tree):
    name = ''
    try:
        name = mesh.name
    except:
        pass

    bbox_min = [mesh.bounding_box.min.x, mesh.bounding_box.min.y, mesh.bounding_box.min.z]
    bbox_min = [rf(f) for f in bbox_min]
    bbox_max = [mesh.bounding_box.max.x, mesh.bounding_box.max.y, mesh.bounding_box.max.z]
    bbox_max = [rf(f) for f in bbox_max]

    positions = []
    for position in mesh.positions:
        position = [position.x, position.y, position.z]
        position = [rf(v) for v in position]
        positions.append(position)

    uv = []
    normals = []
    for feature in mesh.features:
        feature_uv = [rf(feature.texture.x), rf(feature.texture.y)]
        feature_normal = [rf(feature.normal.x), rf(feature.normal.y), rf(feature.normal.z)]  # I think normals is ok...
        uv.append(feature_uv)
        normals.append(feature_normal)

    faces = []
    for polygon in mesh.polygons:
        face = {}
        face['material_index'] = polygon.material_index
        face['position_indices'] = polygon.position_indices
        face['feature_indices'] = polygon.feature_indices

        # uv = []
        # for feature_index in polygon.feature_indices:
        #     uv.append(mesh_data['uv'][feature_index + 1])
        # face['uv_indices'].append(uv)

        faces.append(face)

    mesh_data = {'name': name,
                 'datetime': '',
                 'bounding_box': {'min': bbox_min, 'max': bbox_max},
                 # 'oriented_bbox': '',
                 # 'light_map': [],
                 'positions': positions,
                 'texture': uv,
                 'normals': normals,
                 'polygons': faces}

    return mesh_data


def convert(extract_path, intermediate_path, convert_path, blender_executable_file_path, blender_script_file_path):
    zen_file_path_list = list(Path(extract_path).rglob(f'*.ZEN'))

    for zen_file_path in zen_file_path_list:
        relative_path = zen_file_path.relative_to(extract_path).parent  # / zen_file_path.stem

        # if 'NEWWORLD.ZEN' not in str(zen_file_path):  # ARCHOLOS_SEWERS
        #     continue

        print(f'[WORLD] Start parse file: [{relative_path / zen_file_path.stem}.ZEN]')

        world = None
        try:
            world = World.load(zen_file_path)
        except:
            print(f'[WORLD] ERROR: can\'t open: {relative_path / zen_file_path.stem}.ZEN')
            continue

        mesh_dict = parse_mesh(world.mesh, world.bsp_tree)
        waypoints_dict = parse_waypoints(world.way_net)
        materials_dict = helpers.parse_materials(world.mesh.materials)
        vob_dict = pasrse_vob(world.root_objects)

        # print(f'{len(world.root_objects)=}')

        world_dict = {'mesh': mesh_dict, 'vobs': vob_dict, 'materials': materials_dict, 'waypoints': waypoints_dict}
        json_data = json.dumps(world_dict, indent=4, ensure_ascii=False)

        save_path = intermediate_path / relative_path
        save_path.mkdir(exist_ok=True, parents=True)

        save_path_world = save_path / (zen_file_path.stem + '.ZEN.json')
        save_path_world.write_text(json_data, encoding='utf-8')

        print(f'[WORLD] End parse file: [{relative_path / zen_file_path.stem}.ZEN]')

    if __name__ != '__main__':
        print(f'[WORLD] Start convert ZEN via blender')
        helpers.run_blender(blender_executable_file_path, blender_script_file_path)
        print(f'[WORLD] End convert ZEN via blender')


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

    blender_executable_file_path = Path(config['blender_folder']) / 'blender.exe'
    blender_script_file_path = Path.cwd() / 'import_zengin_json' / 'import_zen.py'

    convert(extract_path, intermediate_path, convert_path, blender_executable_file_path, blender_script_file_path)

    helpers.run_blender(blender_executable_file_path, blender_script_file_path)


if __name__ == '__main__':
    main()
