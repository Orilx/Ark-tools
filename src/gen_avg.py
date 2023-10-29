import zipfile
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union
import shutil
from PIL import Image

from unpacker import ArkUnPacker


def gen_avg_chararts(unpack_info: Dict) -> List[Path]:
    """生成人物差分

    Args:
        url (str): 群文件 url
        source_file (str): 下载文件名

    Returns:
        List[Path]: 生成图片的地址列表
    """
    base_path = unpack_info["output_path"]
    type_cnt = unpack_info["type_cnt"]
    face_alpha_set = unpack_info["pics"]["face_alpha"]
    file_name = unpack_info["pics"]["full"][0].split('$')[0]
    result_list = []

    for avg_type in range(type_cnt):
        avg_type_name = avg_type + 1
        # 各种路径
        avg_img_path = base_path / "full" / f"{file_name}${avg_type_name}.png"
        avg_alpha_path = base_path / "full" / \
            f"{file_name}${avg_type_name}[alpha].png"

        # TODO 清理屎山
        save_path: Path = avg_img_path.parent.parent.parent.parent / "out" / file_name
        if not save_path.exists():
            save_path.mkdir()

        pos_info = unpack_info["pos_info"][avg_type]
        face_size = (pos_info["face_size_x"], pos_info["face_size_y"])
        face_pos = (pos_info["face_pos_x"], pos_info["face_pos_y"])

        # 确定有差分
        # if pos_info["face_size_x"] != 0:
        if face_list := unpack_info["pics"]["face"]:
            for i in face_list:
                if not i.endswith(f'{avg_type_name}.png'):
                    continue
                # 打开图片
                avg_img = Image.open(avg_img_path)
                avg_alpha = Image.open(avg_alpha_path).convert(mode='L')

                base_img = Image.new('RGBA', size=avg_img.size)
                base_img.paste(avg_img, mask=avg_alpha)

                # 脸部遮罩路径
                f_alpha_path = ''
                for alpha in face_alpha_set:
                    if i.startswith(alpha):
                        f_alpha_path = base_path / \
                            "face" / f"{alpha}[alpha].png"
                # 没有指定遮罩的时候使用默认遮罩
                if not f_alpha_path:
                    f_alpha_path = base_path / "face" / \
                        f"{avg_type_name}$[alpha].png"

                f_alpha = Image.open(f_alpha_path).convert(mode='L')
                f = Image.open(base_path / "face" / i)

                head = Image.new('RGBA', f.size)
                head.paste(f, mask=f_alpha)

                if head.width == 128:
                    head = head.resize(face_size)
                    base_img.paste(head, box=face_pos)
                # 处理脸部差分变成全身立绘的情况
                else:
                    base_img.paste(head)

                base_img.save(save_path / i, quality=100)
                result_list.append(save_path / i)
        else:
            avg_img = Image.open(avg_img_path)
            avg_alpha = Image.open(avg_alpha_path).convert(mode='L')
            base_img = Image.new('RGBA', size=avg_img.size)
            base_img.paste(avg_img, mask=avg_alpha)
            base_img.save(save_path / avg_img_path.name, quality=100)
            result_list.append(save_path / avg_img_path.name)
    # 删除缓存文件
    shutil.rmtree(base_path)
    return result_list


def extract_package(file_path: Path) -> bytes:
    content = b""
    with zipfile.ZipFile(file_path, mode="r") as f:
        with f.open(f.infolist()[0].filename) as ab:
            content = ab.read()
    return content


source_file = extract_package(
    Path("cache/download/avg_characters/avg_4088_hodrer_1.zip"))

unpack_info = ArkUnPacker(source_file).export_avg_chararts()

gen_avg_chararts(unpack_info)
