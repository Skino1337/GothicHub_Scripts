def rf(f):
    return round(f, 2)


def parse_materials(material_list):
    # https://github.com/GothicKit/ZenKit/blob/main/src/Material.cc
    # https://auronen.cokoliv.eu/gmc/zengin/worlds/Classes/zCMaterial/

    index = 0
    material_dict_list = []
    for material in material_list:
        material_dict = {}
        # G1
        material_dict['index'] = index
        material_dict['name'] = material.name.upper()
        material_dict['matGroup'] = material.group.name
        material_dict['color'] = [material.color.r, material.color.g, material.color.b, material.color.a]
        material_dict['smoothAngle'] = rf(material.smooth_angle)
        material_dict['texture'] = material.texture.upper().rsplit('.', 1)[0]
        material_dict['texScale'] = [rf(material.texture_scale[0]), rf(material.texture_scale[1])]
        material_dict['texAniFPS'] = rf(material.texture_animation_fps)


        # ValueError: 32 is not a valid AnimationMapping
        texture_animation_mapping = 'NONE'
        try:
            texture_animation_mapping = material.texture_animation_mapping.name
        except ValueError as error:
            print(f'[MATERIAL] WARNING: Material have wrong value in parameter [texAniMapMode], set default value to "NONE". Error: "{error}"')
        if texture_animation_mapping != 'NONE':
            material_dict['texAniMapMode'] = texture_animation_mapping


        material_dict['texAniMapDir'] = [rf(material.texture_animation_mapping_direction[0]),
                                         rf(material.texture_animation_mapping_direction[1])]
        material_dict['noCollDet'] = material.disable_collision
        material_dict['noLightmap'] = material.disable_lightmap
        material_dict['lodDontCollapse'] = material.dont_collapse
        material_dict['detailObject'] = material.detail_object
        material_dict['defaultMapping'] = [rf(material.default_mapping.x), rf(material.default_mapping.y)]
        # G2
        material_dict['detailObjectScale'] = rf(material.detail_object_scale)
        material_dict['forceOccluder'] = material.force_occluder
        material_dict['environmentalMapping'] = material.environment_mapping
        material_dict['environmentalMappingStrength'] = rf(material.environment_mapping_strength)


        # ValueError: 255 is not a valid WaveMode
        wave_mode = 'NONE'
        try:
            wave_mode = material.wave_mode.name
        except ValueError as error:
            print(f'[MATERIAL] WARNING: Material have wrong value in parameter [waveMode], set default value to "NONE". Error: "{error}"')
        if wave_mode != 'NONE':
            material_dict['waveMode'] = wave_mode


        # ValueError: 32 is not a valid WaveSpeed
        wave_speed = 'NONE'
        try:
            wave_speed = material.wave_speed.name
        except ValueError as error:
            print(f'[MATERIAL] WARNING: Material have wrong value in parameter [waveSpeed], set default value to "NONE". Error: "{error}"')
        if wave_speed != 'NONE':
            material_dict['waveSpeed'] = wave_speed


        material_dict['waveMaxAmplitude'] = rf(material.wave_amplitude)
        material_dict['waveGridSize'] = rf(material.wave_grid_size)
        material_dict['ignoreSunLight'] = material.ignore_sun
        # G1

        # ValueError: 32 is not a valid AnimationMapping
        alpha_function = 'DEFAULT'
        try:
            alpha_function = material.alpha_function.name
        except ValueError as error:
            print(f'[MATERIAL] WARNING: Material have wrong value in parameter [alphaFunc], set default value to "DEFAULT". Error: "{error}"')
        material_dict['alphaFunc'] = alpha_function

        material_dict_list.append(material_dict)

        index += 1

    return material_dict_list


def rename_bone(bone_name):
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
        name = 'old_root'

    print(f'bone rename: {bone_name} => {name}')

    return name


def run_blender(blender_executable_file_path, blender_script_file_path):
    import subprocess

    # https://blender.stackexchange.com/questions/6817/how-to-pass-command-line-arguments-to-a-blender-python-script

    arguments = [blender_executable_file_path]
    # arguments.extend(['--background'])
    # arguments.extend(['--factory-startup'])
    arguments.extend(['--python', blender_script_file_path])
    process = subprocess.Popen(arguments,
                               # stdout=subprocess.PIPE,
                               # stderr=subprocess.PIPE,
                               # stdin=subprocess.PIPE,
                               encoding='utf-8')
    process.wait()
