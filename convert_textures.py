import json
import shutil
from pathlib import Path

from PIL import Image

from zenkit import Texture


def convert(extract_path, convert_path):
    tex_file_path_list = list(Path(extract_path).rglob(f'*.TEX'))

    for tex_file_path in tex_file_path_list:
        relative_path = str(tex_file_path.relative_to(extract_path))
        if relative_path[-4:] == '.TEX':
            relative_path = relative_path[:-4]
        if relative_path[-2:] == '-C':
            relative_path = relative_path[:-2]

        save_path = convert_path / (relative_path + '.TGA')

        texture = Texture.load(tex_file_path)

        save_path.parent.mkdir(exist_ok=True, parents=True)

        image = Image.new('RGBA', (texture.width, texture.height))
        image.frombytes(texture.mipmap_rgba(0))
        image.save(save_path)

        print(f'converted: {relative_path}.TEX')


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

    convert(extract_path, convert_path)


if __name__ == '__main__':
    main()
