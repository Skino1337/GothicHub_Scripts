import json
import shutil
from pathlib import Path

from zenkit import DaedalusScript


def convert(extract_path, convert_path):
    # https://github.com/GothicKit/ZenKit/blob/main/tests/TestDaedalusScript.cc
    # https://worldofplayers.ru/threads/12256/page-146
    # https://worldofplayers.ru/threads/42582/page-6


    tex_file_path_list = list(Path(extract_path).rglob(f'*.DAT'))

    for tex_file_path in tex_file_path_list:
        print(tex_file_path)

        # script = DaedalusScript.load(tex_file_path)


def main():
    config_file_path = Path('config.json')
    config_data = config_file_path.read_text()
    config = json.loads(config_data)

    extract_path = Path(config['vdf_folder']) / Path(config['extract_folder'])
    convert_path = Path(config['vdf_folder']) / Path(config['convert_folder'])

    if not extract_path.exists():
        print(f'ERROR: folder "{extract_path}" not exist!')
        return

    shutil.rmtree(convert_path, ignore_errors=True)
    convert_path.mkdir()

    convert(extract_path, convert_path)


if __name__ == '__main__':
    main()
