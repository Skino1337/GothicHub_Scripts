import math
from mathutils import Matrix, Quaternion, Vector
import array

import bpy
import bmesh
from bpy_extras.io_utils import unpack_list
import numpy as np



import random


# https://github.com/scorpion81/blender-addons/blob/master/io_scene_obj/import_obj.py
# https://projects.blender.org/blender/blender/src/commit/de3c473ebb167ef6f1f8aca699b7419a00485520/scripts/addons_core/io_scene_fbx/import_fbx.py#L1793
# https://projects.blender.org/blender/blender -> scripts/addons_core/io_scene_fbx/import_fbx.py

# faster with np
#
#
# def create_mesh(mesh_dict, mesh_name, mesh_materials, use_normals=True, verbose=True):
#     assert 'vertices' in mesh_dict
#     assert 'faces' in mesh_dict
#
#     verts_dict = mesh_dict['vertices']
#     faces_dict = mesh_dict['faces']
#
#     uv_dict = mesh_dict['uv']
#     normals_dict = mesh_dict['normals']
#
#     vertex_list = []
#     for vertex in verts_dict:
#         vertex_list.append([axis / 100.0 for axis in vertex])
#     face_list = []
#     loops_count = 0
#     loop_uv_list = []
#     loop_normal_list = []
#     for face in faces_dict:
#         vertex_indices = face['vertex_indices']
#         face_list.append(vertex_indices)
#         loops_count = loops_count + len(vertex_indices)
#         for feature_index in face['feature_indices']:
#             uv = uv_dict[feature_index]
#             uv = uv[0], -uv[1]
#             loop_uv_list.append(uv)
#
#             normal = normals_dict[feature_index]
#             normal_normalized_vector = Vector([normal[0], normal[1], normal[2]]).normalized()
#             normal = [normal_normalized_vector[0], normal_normalized_vector[1], normal_normalized_vector[2]]
#             loop_normal_list.append(normal)
#
#     # print(f'verts: {len(vertex_list)}')
#     # print(f'faces: {len(face_list)}')
#     # print(f'loop normal count: {len(loop_normal_list)}')
#     # print(f'loop uv count: {len(loop_uv_list)}')
#
#     mesh = bpy.data.meshes.new(mesh_name)
#     # mesh.use_auto_smooth = True
#
#     mesh.vertices.add(len(vertex_list))
#     mesh.loops.add(loops_count)
#     mesh.polygons.add(len(face_list))
#
#     mesh.vertices.foreach_set('co', unpack_list(vertex_list))
#
#     loops_vert_idx = []
#     faces_loop_start = []
#     faces_loop_total = []
#     lidx = 0
#     for face_index, face in enumerate(face_list):
#         vidx = face
#         nbr_vidx = len(vidx)
#         loops_vert_idx.extend(vidx)
#         faces_loop_start.append(lidx)
#         faces_loop_total.append(nbr_vidx)
#         lidx += nbr_vidx
#
#     mesh.loops.foreach_set('vertex_index', loops_vert_idx)
#     mesh.polygons.foreach_set('loop_start', faces_loop_start)
#     mesh.polygons.foreach_set('loop_total', faces_loop_total)
#
#     for material_index, material in mesh_materials.items():
#         mesh.materials.append(material)
#
#     uv_layer = mesh.uv_layers.new(name='texture', do_init=False)
#     for polygon in mesh.polygons:
#         polygon.material_index = faces_dict[polygon.index]['material_index']
#     for loop_index, loop in enumerate(mesh.loops):
#         uv_layer.data[loop_index].uv = loop_uv_list[loop_index]
#
#     if use_normals:
#         mesh.attributes.new('temp_custom_normals', 'FLOAT_VECTOR', 'CORNER')
#         assert len(loop_normal_list) == len(mesh.attributes['temp_custom_normals'].data)
#         for loop_normal, float_vector_attribute in zip(loop_normal_list, mesh.attributes['temp_custom_normals'].data):
#             float_vector_attribute.vector = loop_normal
#
#     mesh.validate(verbose=False, clean_customdata=False)  # *Very* important to not remove lnors here!
#     mesh.update(calc_edges=False)
#
#     if use_normals:
#         clnors = np.empty(len(mesh.loops) * 3, dtype=np.single)
#         mesh.attributes['temp_custom_normals'].data.foreach_get('vector', clnors)
#         mesh.polygons.foreach_set('use_smooth', [True] * len(mesh.polygons))
#         mesh.normals_split_custom_set(tuple(zip(*(iter(clnors.data),) * 3)))
#
#         mesh.attributes.remove(mesh.attributes['temp_custom_normals'])
#
#     if verbose:
#         print(f'Mesh created, verts={len(mesh.vertices)}, faces={len(mesh.polygons)}')  # bones
#
#     mesh_obj = bpy.data.objects.new(mesh.name, mesh)
#     bpy.context.collection.objects.link(mesh_obj)
#
#     return mesh_obj, mesh
#
#
# def create_mesh_old(mesh_dict, mesh_name, mesh_materials, use_normals=False, verbose=True):
#     assert 'vertices' in mesh_dict
#     assert 'faces' in mesh_dict
#
#     verts_dict = mesh_dict['vertices']
#     uv_dict = mesh_dict['uv']
#     normals_dict = mesh_dict['normals']
#     faces_dict = mesh_dict['faces']
#     faces_vertex_indices = [face['vertex_indices'] for face in faces_dict]
#
#     vertex_list = []
#     for vertex in verts_dict:
#         vertex_list.append([axis / 100.0 for axis in vertex])
#
#     print(f'verts count: {len(vertex_list)}')
#     print(f'normals count: {len(normals_dict)}')
#
#     loop_normal_list = []
#     for face in faces_dict:
#         for feature_index in face['feature_indices']:
#             normal = normals_dict[feature_index]
#             normal_normalized_vector = Vector([normal[0], normal[1], normal[2]]).normalized()
#             normal = [normal_normalized_vector[0], normal_normalized_vector[1], normal_normalized_vector[2]]
#             loop_normal_list.append(normal)
#
#     mesh = bpy.data.meshes.new(mesh_name)
#     mesh.from_pydata(vertex_list, [], faces_vertex_indices)
#     # mesh.update(calc_edges=True)
#
#     if use_normals:
#         assert len(loop_normal_list) == len(mesh.attributes['temp_custom_normals'].data)
#         mesh.attributes.new('temp_custom_normals', 'FLOAT_VECTOR', 'CORNER')
#         for loop_normal, float_vector_attribute in zip(loop_normal_list, mesh.attributes['temp_custom_normals'].data):
#             float_vector_attribute.vector = loop_normal
#
#         clnors = np.empty(len(mesh.loops) * 3, dtype=np.single)
#         mesh.attributes['temp_custom_normals'].data.foreach_get('vector', clnors)
#         mesh.polygons.foreach_set('use_smooth', [True] * len(mesh.polygons))
#         mesh.normals_split_custom_set(tuple(zip(*(iter(clnors.data),) * 3)))
#
#         mesh.attributes.remove(mesh.attributes['temp_custom_normals'])
#
#     mesh_obj = bpy.data.objects.new(mesh.name, mesh)
#     bpy.context.collection.objects.link(mesh_obj)
#
#     # mesh_obj.select_set(True)
#     # mesh_obj.data.materials.append(material)
#
#     # bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
#
#     for material_index, material in mesh_materials.items():
#         mesh_obj.data.materials.append(material)
#
#     mesh_b = bmesh.new()
#     mesh_b.from_mesh(mesh_obj.data)
#
#     mesh_obj.select_set(True)
#     bpy.context.view_layer.objects.active = mesh_obj
#     bpy.ops.object.mode_set(mode='EDIT', toggle=False)
#
#     bpy.ops.mesh.select_all(action='DESELECT')
#
#     uv_layer = mesh_b.loops.layers.uv.active or mesh_b.loops.layers.uv.new()
#     for face in mesh_b.faces:
#         face.material_index = faces_dict[face.index]['material_index']
#         for loop_index, loop in enumerate(face.loops):
#             uv_x, uv_y = uv_dict[faces_dict[face.index]['feature_indices'][loop_index]]
#             loop[uv_layer].uv = uv_x, -uv_y
#
#     # shade_smooth()
#
#     mesh_obj.select_set(False)
#     bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
#
#     mesh_b.to_mesh(mesh_obj.data)
#
#     mesh.validate(verbose=False, clean_customdata=True)
#     mesh.update(calc_edges=False)
#
#     if verbose:
#         print(f'Mesh created, verts={len(mesh_b.verts)}, faces={len(mesh_b.faces)}')  # bones
#
#     return mesh_obj, mesh
#


# mesh_b = bmesh.new()
# mesh_b.from_mesh(mesh)
#
# for vertex in mesh_b.verts:
#     print(vertex.normal)
#     vertex.normal = Vector([0.0, 1.0, 0.0])
#     print(vertex.normal)
#     print('---')

# for face in mesh_b.faces:
#     if random.random() < 0.5:
#         face.normal_flip()
#
# for face in mesh_b.faces:
#     average_corner_normal = Vector([0.0, 0.0, 0.0])
#     for corner_normal in normal_list[face.index]:
#         average_corner_normal += Vector(corner_normal)
#     average_corner_normal = average_corner_normal / len(normal_list[face.index])
#
#     dot = average_corner_normal.dot(face.normal)
#
#     print(f'{average_corner_normal=}')
#     print(f'{face.normal=}')
#     print(f'{dot=}')
#     print(f'---')
#
#     if dot < 0:
#         face.normal_flip()


# if normal_list:
#     loop_normal_list = []  # @todo: list comp
#     for face_normal_list in normal_list:
#         for normal in face_normal_list:
#             loop_normal_list.append(normal)
#
#     mesh.attributes.new('temp_custom_normals', 'FLOAT_VECTOR', 'CORNER')
#     assert len(loop_normal_list) == len(mesh.attributes['temp_custom_normals'].data)
#     for loop_normal, float_vector_attribute in zip(loop_normal_list, mesh.attributes['temp_custom_normals'].data):
#         float_vector_attribute.vector = loop_normal
#
# # autofix all critical mesh problems, but save mesh custom attributes!
# mesh.validate(verbose=False, clean_customdata=False)



def create_mesh_v2(name, vertex_list, face_list,
                   normal_list=None, uv_list=None, blender_materials=None, face_material_index_list=None,
                   remove_unused_material=True, scale=0.01):
    scaled_vertex_list = []
    for vertex in vertex_list:
        scaled_vertex = [f * scale for f in vertex]
        scaled_vertex_list.append(scaled_vertex)

    # Mesh
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(scaled_vertex_list, [], face_list)

    # Texture
    if uv_list and blender_materials and face_material_index_list:
        for material_index, material in blender_materials.items():
            mesh.materials.append(material)

        mesh_b = bmesh.new()
        mesh_b.from_mesh(mesh)

        uv_layer = mesh_b.loops.layers.uv.active or mesh_b.loops.layers.uv.new()
        for face in mesh_b.faces:
            face.material_index = face_material_index_list[face.index]
            for loop_local_index, loop in enumerate(face.loops):
                face_uv_list = uv_list[face.index]
                uv_x, uv_y = face_uv_list[loop_local_index]
                loop[uv_layer].uv = uv_x, uv_y

        mesh_b.to_mesh(mesh)
        mesh_b.free()

    # Use smooth anyway
    mesh.polygons.foreach_set('use_smooth', [True] * len(mesh.polygons))

    # Normals
    if normal_list:
        assert len(mesh.polygons) == len(normal_list)

        loop_normal_list = []
        for face_normal in normal_list:
            for normal in face_normal:
                loop_normal_list.append(normal)

        assert len(mesh.loops) == len(loop_normal_list)

        mesh.normals_split_custom_set(loop_normal_list)

    mesh_obj = bpy.data.objects.new(mesh.name, mesh)
    bpy.context.collection.objects.link(mesh_obj)

    if remove_unused_material:
        mesh_obj.select_set(True)
        bpy.context.view_layer.objects.active = mesh_obj

        bpy.ops.object.material_slot_remove_unused()

        bpy.context.view_layer.objects.active = None
        mesh_obj.select_set(False)

    return mesh_obj, mesh
