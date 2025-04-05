# GoothicHub Scripts

**This code is designed to extract all resources from the game on the zengin engine,
and convert them into a readable format, such as ".blender" or ".fbx" or ".gltf""**

**The program requires the latest version of blender to work**
https://www.blender.org/download/

## How to use:
1. Edit config file.
2. Run extract all .bat file.
3. Run convert all .bat file.

## Config setting:
vdf_folder - path to folder with .vdf/.mod files. For example: "C:/GAMES/Archolos/Data/" <br/>
extract_folder - path to extract folder.<br/>
intermediate_folder - path to intermediate folder.<br/>
convert_folder - path to convert folder.<br/>
blender_folder - path to blender folder. For example: "C:/Program Files/Blender Foundation/Blender 4.3/"<br/>
export_format - format for convert files. For example: "GLB", "GLTF_SEPARATE", "FBX", "BLEND"<br/>
use_gothic_normals - use or not use original normals<br/>
rename_bones - is to rename bones for normal name<br/>
add_root_bone - is to add root bone<br/>
split_world - is to split world to parts like water, collision, portals...<br/>