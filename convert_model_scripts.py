import json
import shutil
from pathlib import Path

from zenkit import ModelScript, AnimationFlags, AnimationDirection


def parse_msb(model_script):
    # https://github.com/GothicKit/ZenKit/blob/main/src/ModelScript.cc

    msb_data = {'group_name': '',
                'skeleton': {'name': '', 'mesh_disabled': True},
                'mesh': [],
                # 'socket': [],
                'animation': [],
                'animation_alias': [],
                'animation_blend': [],
                'animation_combine': [],
                'animation_disable': []}

    msb_data['skeleton']['name'] = model_script.skeleton_name.replace('.ASC', '').replace('.asc', '')
    msb_data['skeleton']['mesh_disabled'] = model_script.skeleton_mesh_disabled

    msb_data['mesh'] = [mesh_name.replace('.ASC', '').replace('.asc', '') for mesh_name in model_script.meshes]

    msb_data['animation_disable'] = model_script.disabled_animations

    for animation in model_script.animations:
        flags = [flag.name for flag in AnimationFlags if animation.flags & flag.value]
        direction = 'FORWARD' if AnimationDirection.FORWARD == animation.direction else 'BACKWARD'

        events = []
        for event in animation.event_tags:
            # args is not released for now(((
            event_dict = {'type': 'EVENT_TAG',
                          'frame': event.frame,
                          'frames': event.frames,
                          'tag': event.type.name,
                          'slot': event.slot,
                          'item': event.item,
                          'fight_mode': event.fight_mode.name,
                          'is_attached': event.is_attached}
            events.append(event_dict)

        for camera_tremor in animation.camera_tremors:
            event_dict = {'type': 'EVENT_CAMERA_TREMOR',
                          'frame': camera_tremor.frame,
                          'field1': camera_tremor.field1,
                          'field2': camera_tremor.field2,
                          'field3': camera_tremor.field3,
                          'field4': camera_tremor.field4}
            events.append(event_dict)

        for sound_effect in animation.sound_effects:
            event_dict = {'type': 'EVENT_SFX',
                          'frame': sound_effect.frame,
                          'name': sound_effect.name,
                          'range': sound_effect.range,
                          'empty_slot': sound_effect.empty_slot}
            events.append(event_dict)

        for sound_effect_ground in animation.sound_effects_ground:
            event_dict = {'type': 'EVENT_SFX_GROUND',
                          'frame': sound_effect_ground.frame,
                          'name': sound_effect_ground.name,
                          'range': sound_effect_ground.range,
                          'empty_slot': sound_effect_ground.empty_slot}
            events.append(event_dict)

        for particle_effect in animation.particle_effects:
            event_dict = {'type': 'EVENT_PFX',
                          'frame': particle_effect.frame,
                          'index': particle_effect.index,
                          'name': particle_effect.name,
                          'position': particle_effect.position,
                          'is_attached': particle_effect.is_attached}
            events.append(event_dict)

        for particle_effect_stop in animation.particle_effects_stop:
            event_dict = {'type': 'EVENT_PFX_STOP',
                          'frame': particle_effect_stop.frame,
                          'index': particle_effect_stop.index}
            events.append(event_dict)

        for morph_animation in animation.morph_animations:
            event_dict = {'type': 'EVENT_MM_ANI',
                          'frame': morph_animation.frame,
                          'animation': morph_animation.animation,
                          'node': morph_animation.node}
            events.append(event_dict)

        animation_dict = {'name': animation.name,
                          'layer': animation.layer,
                          'next': animation.next,
                          'blend_id': round(animation.blend_in, 2),
                          'blend_out': round(animation.blend_out, 2),
                          'flags': flags,
                          'model': animation.model,
                          'direction': direction,
                          'first_frame': animation.first_frame,
                          'last_frame': animation.last_frame,
                          'fps': round(animation.fps, 2),
                          'speed': round(animation.speed, 2),
                          'cvs': round(animation.collision_volume_scale, 2),
                          'events': events}

        msb_data['animation'].append(animation_dict)

    for animation_aliase in model_script.animation_aliases:
        flags = [flag.name for flag in AnimationFlags if animation_aliase.flags & flag.value]
        direction = 'FORWARD' if AnimationDirection.FORWARD == animation_aliase.direction else 'BACKWARD'

        animation_alias_dict = {'name': animation_aliase.name,
                                'layer': animation_aliase.layer,
                                'next': animation_aliase.next,
                                'blend_id': round(animation_aliase.blend_in, 2),
                                'blend_out': round(animation_aliase.blend_out, 2),
                                'flags': flags,
                                'alias': animation_aliase.alias,
                                'direction': direction}

        msb_data['animation_alias'].append(animation_alias_dict)

    for animation_blend in model_script.animation_blends:
        animation_blend_dict = {'name': animation_blend.name,
                                'next': animation_blend.next,
                                'blend_in': round(animation_blend.blend_in, 2),
                                'blend_out': round(animation_blend.blend_out, 2)}

        msb_data['animation_blend'].append(animation_blend_dict)

    for animation_combine in model_script.animation_combines:
        flags = [flag.name for flag in AnimationFlags if animation_combine.flags & flag.value]
        animation_combine_dict = {'name': animation_combine.name,
                                  'layer': animation_combine.layer,
                                  'next': animation_combine.next,
                                  'blend_in': round(animation_combine.blend_in, 2),
                                  'blend_out': round(animation_combine.blend_out, 2),
                                  'flags': flags,
                                  'model': animation_combine.model,
                                  'last_frame': animation_combine.last_frame}

        msb_data['animation_combine'].append(animation_combine_dict)

    return msb_data


def convert(extract_path, intermediate_path, convert_path):
    msb_file_path_list = list(Path(extract_path).rglob(f'*.MSB'))

    for msb_file_path in msb_file_path_list:
        relative_path = msb_file_path.relative_to(extract_path)
        save_path = convert_path / (str(relative_path) + '.json')
        save_path.parent.mkdir(exist_ok=True, parents=True)

        model_script = ModelScript.load(msb_file_path)
        msb_data = parse_msb(model_script)
        group_name = msb_file_path.stem.upper().split('_')[0]
        msb_data['group_name'] = group_name

        json_data = json.dumps(msb_data, indent=4, ensure_ascii=False)
        save_path.write_text(json_data, encoding='utf-8')

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
