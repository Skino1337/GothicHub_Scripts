import bpy


def create_materials(zengin_materials, texture_path_dict, verbose=False):
    def image_has_alpha(img):
        b = 32 if img.is_float else 8
        return (img.depth == 2 * b or   # Grayscale+Alpha
                img.depth == 4 * b)     # RGB+Alpha

    materials_by_index = dict()

    assert len(zengin_materials) > 0
    assert len(texture_path_dict) > 0

    for zengin_material in zengin_materials:
        material_name = zengin_material['name'].upper()
        if material_name in bpy.data.materials:
            materials_by_index[zengin_material['index']] = bpy.data.materials[material_name]
            continue

        zengin_texture_name = None
        if len(zengin_material['texture']) > 0:
            zengin_texture_name = zengin_material['texture'].upper()
        elif len(zengin_material['name']) > 0:
            zengin_texture_name = zengin_material['name'].upper()
        else:
            # assert False, 'zengin_texture_name is None'
            continue
        image = None
        if zengin_texture_name in texture_path_dict:
            image = bpy.data.images.load(texture_path_dict[zengin_texture_name], check_existing=True)
            image.source = 'FILE'
            image.filepath = texture_path_dict[zengin_texture_name]

            # well, if u can fix textures (at least as an option) that would be good,
            # because texture = just material property in vob file, not real path
            # so it can save material-texture field even if there is not file

            # if not image:
            #     print(f'if not image: {image=}')
        else:
            texture_name = zengin_texture_name.upper().split(':')[0]
            if texture_name not in ['P', 'PI', 'PN', 'S', 'GHOSTOCCLUDER', 'SUN_BLOCKER']:
                print(f'[MATERIAL] WARNING: Texture not found: "{zengin_texture_name}"')

        material = bpy.data.materials.new(name=material_name)
        material.use_nodes = True
        material.diffuse_color = [c / 255 for c in zengin_material['color']]

        nodes = material.node_tree.nodes

        principled_bsdf = nodes.get('Principled BSDF')
        if principled_bsdf is None:
            principled_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
        principled_bsdf.location = (400, 0)
        principled_bsdf.inputs['Metallic'].default_value = 1.0
        principled_bsdf.inputs['Roughness'].default_value = 1.0

        if 'Specular IOR Level' in principled_bsdf.inputs:
            principled_bsdf.inputs['Specular IOR Level'].default_value = 0.0

        material_output = nodes.get('Material Output')
        if material_output is None:
            material_output = nodes.new(type='ShaderNodeOutputMaterial')
        material_output.location = (800, 0)

        links = material.node_tree.links
        links.new(principled_bsdf.outputs['BSDF'], material_output.inputs['Surface'])

        # @TODO: node_pbsdf.inputs['Transmission'].default_value = 0.5 # 1 is fully transparent
        # @TODO: node_pbsdf.inputs['Alpha'].default_value = 1 # 1 is opaque, 0 is invisible

        if image:
            tex_image = nodes.new('ShaderNodeTexImage')
            tex_image.location = (0, 0)
            tex_image.image = image

            links.new(tex_image.outputs['Color'], principled_bsdf.inputs['Base Color'])

            if image_has_alpha(image):
                links.new(tex_image.outputs['Alpha'], principled_bsdf.inputs['Alpha'])
                material.show_transparent_back = False
                material.blend_method = 'CLIP'
                if hasattr(material, 'shadow_method'):
                    material.shadow_method = 'CLIP'
                material['biplanar'] = True
        else:
            principled_bsdf.inputs['Base Color'].default_value = zengin_material['color']

        materials_by_index[zengin_material['index']] = material

    return materials_by_index
