import zipfile
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

from PIL import Image, ImageDraw

from unpacker import ArkUnPacker

# def gen_package(input_path: Union[str, Path], output_path: Union[str, Path], file_name: str) -> Path:
#     if isinstance(input_path, str):
#         input_path = Path(input_path)
#     if isinstance(output_path, str):
#         output_path = Path(output_path)

#     file_path = output_path / f"{file_name}.zip"

#     with zipfile.ZipFile(file_path, mode="w") as archive:
#         for files in input_path.rglob('*'):
#             archive.write(files, arcname=files.name)

#     return file_path

def gen_avg_chararts(source_file: str, file_name: str) -> List[Path]:
    """生成人物差分

    Args:
        url (str): 群文件 url
        source_file (str): 下载文件名

    Returns:
        List[Path]: 生成图片的地址列表
    """
    # await download_file(url=url, path='cache/download/' + source_file)

    d = ArkUnPacker(source_file, 'cache/ark_tools/').export_avg_chararts()
    # print(d)
    base_path = d["output_path"]
    type_cnt = d["type_cnt"]

    result_list = []
    for it in range(type_cnt):
        img_type = it + 1
        # 各种路径
        avg_img_path = base_path / "full" / f"{file_name}${img_type}.png"
        avg_alpha_path = base_path / "full" / \
            f"{file_name}${img_type}[alpha].png"

        save_path: Path = avg_img_path.parent.parent.parent.parent / "out" / file_name
        if not save_path.exists():
            save_path.mkdir()

        pos_info = d["pos_info"][it]
        # 打开图片
        avg_img = Image.open(avg_img_path)
        avg_alpha = Image.open(avg_alpha_path).convert(mode='L')

        base_img = Image.new('RGBA', size=avg_img.size)
        base_img.paste(avg_img, mask=avg_alpha)

        # 确定有差分
        if pos_info["face_size_x"] != 0:
            alpha_set = []
            face_size = (pos_info["face_size_x"], pos_info["face_size_y"])
            for i in d["pics"]["face"]:
                # print(i)
                if i.endswith(f"[alpha].png"):
                    alpha_set.append(i.replace('[alpha].png', ''))
            # print(alpha_set)
            for i in d["pics"]["face"]:
                if not i.endswith(f"{img_type}.png"):
                    continue
                if i.split('.')[0] in alpha_set:
                    f_alpha_path = base_path / "face" / \
                        f"{i.split('.')[0]}[alpha].png"
                else:
                    f_alpha_path = base_path / "face" / \
                        f"{img_type}$[alpha].png"

                f_path = base_path / "face" / i

                f_alpha = Image.open(f_alpha_path).resize(
                    face_size).convert(mode='L')
                f1 = Image.open(f_path).resize(face_size)
                head = Image.new('RGBA', f1.size)

                head.paste(f1, mask=f_alpha)
                f1.save(save_path / "head" / i, quality=100)

                base_img.paste(head, box=(
                    pos_info["face_pos_x"], pos_info["face_pos_y"]))
                result_list.append(save_path / i)
                base_img.save(save_path / i, quality=100)

                # natsorted(result_list)
        else:
            base_img.save(save_path / avg_img_path.name, quality=100)
            result_list.append(save_path / avg_img_path.name)
    # gen_package('cache/ark_avg/out', 'cache/ark_avg/zip_files', source_file)

    return result_list

# import os

# for root, dirs, files in os.walk(Path('data/ab/')):
#     for file_name in files:
#         # generate file_path
#         # file_path = os.path.join(root, file_name)
#         gen_avg_chararts('data/ab/'+file_name, file_name.replace(".ab",""))


gen_avg_chararts('cache/input/avg_190_clour_1.ab', 'avg_190_clour_1')
# {'output_path': WindowsPath('cache/ark_tools/unpack_1695804954'),
#  'type_cnt': 1,
#  'pics': {'full': ['avg_190_clour_1$1[alpha].png', 'avg_190_clour_1$1.png'],
#           'face': ['6$1[alpha].png', '6$1.png', '8$1.png', '3$1.png', '3$1[alpha].png', '4$1.png', '4$1[alpha].png', '7$1.png', '1$1.png', '10$1.png', '9$1.png', '1$[alpha].png', '5$1.png', '2$1.png']}, 'pos_info': [{'face_size_x': 117, 'face_size_y': 131, 'face_pos_x': 408, 'face_pos_y': 93}]}


async def gen_CG(url: str, source_file: str) -> List[Path]:
    """提取 CG 图片

    Args:
        url (str): 群文件 url
        source_file (str): 下载文件名

    Returns:
        List[Path]: 生成图片的地址列表
    """
    # await download_file(url=url, path='cache/download/' + source_file)

    d = ArkUnPacker('cache/download/' + source_file,
                    'cache/ark_tools/').export_avg_chararts()

    # gen_package('cache/ark_avg/out', 'cache/ark_avg/zip_files', source_file_name)

    return d["pics"]


# def extract_package(file_path: Path, extract_path: Path) -> Tuple[str, List[str]]:
#     avg_img_name = ''
#     img_list = []
#     with zipfile.ZipFile(file_path, mode="r") as archive:
#         for file_info in archive.infolist():
#             f_name = file_info.filename
#             # 检查文件路径是否以指定目录开头
#             if f_name.startswith('Texture2D/'):
#                 if not f_name.replace('Texture2D/', ''):
#                     continue
#                 if f_name.endswith('[alpha].png'):
#                     continue

#                 if f_name.startswith('Texture2D/avg'):
#                     avg_img_name = f_name
#                 else:
#                     img_list.append(f_name.replace('Texture2D/', ''))
#         archive.extractall(extract_path)
#     return avg_img_name, img_list
