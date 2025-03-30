import json
import shutil
from pathlib import Path

from zenkit import Vfs, VfsOverwriteBehavior, GameVersion


def save_file(vfs, node, path):
    if node.is_dir():
        subpath = path + node.name + '/'
        # print(f'path {Path(subpath)}')
        for node_children in node.children:
            save_file(vfs, node_children, subpath)
    if node.is_file():
        node_name = node.name
        file_format, file_name = node_name[::-1].split('.', 1)
        file_name = file_name[::-1]
        file_format = file_format[::-1]
        file_to_save = Path(path)

        if file_format == 'MAN' and '-' in file_name:
            folder_name, file_name = file_name.split('-')
            file_to_save = file_to_save / folder_name / (file_name + '.' + file_format)
        elif file_format == 'MSB' or file_format == 'MDH':
            file_to_save = file_to_save / file_name / (file_name + '.' + file_format)
        else:
            file_to_save = file_to_save / node_name

        file_to_save.parent.mkdir(exist_ok=True, parents=True)
        file_to_save.write_bytes(node.data)


def extract():
    config_file_path = Path('config.json')
    if not config_file_path.exists():
        print(f'ERROR: can\'t find config file [{config_file_path}].')
        return
    config_data = config_file_path.read_text()
    config = json.loads(config_data)

    vdf_folder_path = Path(config['vdf_folder'])
    if not vdf_folder_path.exists():
        print(f'ERROR: folder [{vdf_folder_path}] not exist.')
        return

    extract_path = Path(config['extract_folder'])
    if not extract_path.is_absolute():
        extract_path = Path.cwd() / extract_path

    vdf_file_path_list = list(vdf_folder_path.glob(f'*.vdf'))
    vdf_file_path_list.extend(list(vdf_folder_path.glob(f'*.mod')))
    if len(vdf_file_path_list) == 0:
        print(f'ERROR: folder [{vdf_folder_path}] don\'t contain any .vdf/.mod files.')
        return

    shutil.rmtree(extract_path, ignore_errors=True)
    extract_path.mkdir(parents=True, exist_ok=True)

    for vfs_file in vdf_file_path_list:
        vfs_file_name = vfs_file.stem
        prefix = ''
        if 'VDF' in vfs_file.suffix.upper():
            prefix = 'VDF_'
        elif 'MOD' in vfs_file.suffix.upper():
            prefix = 'MOD_'

        print(f'[EXTRACT] Extract files from: {vfs_file}')

        vfs = Vfs()
        vfs.mount_disk(vfs_file, clobber=VfsOverwriteBehavior.OLDER)

        # how we can get gothic version from vfs?
        game_version = GameVersion.GOTHIC2

        game_type_folder = 'Game'
        if game_version == GameVersion.GOTHIC1:
            game_type_folder = 'Gothic'
        elif game_version == GameVersion.GOTHIC2:
            game_type_folder = 'Gothic II'
        if 'ADDON' in vfs_file_name.upper():
            game_type_folder = 'Addon'
        elif prefix == 'MOD_':
            game_type_folder = 'Mod'

        save_path = extract_path / game_type_folder / (prefix + vfs_file_name)

        save_file(vfs, vfs.root, str(save_path))


if __name__ == '__main__':
    extract()
