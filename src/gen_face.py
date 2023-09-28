import re
import subprocess
from pathlib import Path
from typing import List

from natsort import natsorted
from PIL import Image

from warterprint import code128_image


def gen_face(directory_path, crop_lb_x, crop_lb_y, crop_width):

    width = 250
    gap_width = 8
    unit_width = width + gap_width

    img_path = Path(directory_path)
    file_groups = {}

    save_list: List[Path] = []

    for file_path in img_path.glob("*.png"):
        file_name = file_path.name

        # 使用正则表达式提取分类数字
        match = re.search(r"\$(\d+)\.png", file_name)
        if match:
            cate = int(match.group(1))
            if cate not in file_groups:
                file_groups[cate] = []
            file_groups[cate].append(file_name)

    # 按分类处理差分
    for cate, files in natsorted(file_groups.items()):
        pic_cnt = len(files)

        # 根据数量判断三个一排还是四个一排
        g_x = 4 if pic_cnt > 12 else 3
        g_y = pic_cnt // g_x
        if pic_cnt % g_x != 0:
            g_y += 1

        # 裁切坐标（左上和右下）
        crop_box = ((crop_lb_x, crop_lb_y+20,
                    crop_lb_x+crop_width, crop_lb_y+20+crop_width))
        # 创建一个不包含左上边框的底图
        base_img_size = (g_x*unit_width, g_y*unit_width)
        base_img = Image.new('RGBA', size=base_img_size, color='black')
        # 白色背景
        white_base = Image.new('RGBA', size=(width, width), color='white')

        # 依次打开差分，粘贴到底图
        for i in range(pic_cnt):
            f = Image.new('RGBA', (1024, 1044))
            f.paste(Image.open(img_path/f"{i+1}${cate}.png"), (0, 20))
            f = f.crop(crop_box).resize((width, width))

            pos_box = (unit_width*(i % g_x), unit_width*(i // g_x))
            base_img.paste(white_base, pos_box)
            base_img.alpha_composite(f, pos_box)

        # 最底部空白处理
        space = pic_cnt % g_x
        if space != 0:
            space_width = (g_x-space)*width+(g_x-space-1)*gap_width
            base_img.paste(white_base.resize((space_width, width)),
                           (unit_width*space, unit_width*(pic_cnt // g_x)))
        # 保存图片
        save_path = img_path.parent/f"{img_path.name}_{cate}.png"
        t = Image.new("RGB", (g_x*unit_width+gap_width,
                      g_y*unit_width+gap_width))
        # 水印
        code_img = code128_image('5rOw5ouJ5peF56S+')
        code_img = code_img.resize((code_img.width, t.height))
        code_mask = Image.new('L', size=code_img.size, color='#181818')
        t.paste(code_img, box=((t.width-code_img.width)//2, 0), mask=code_mask)

        t.paste(base_img, (gap_width, gap_width))
        t.save(save_path)
        save_list.append(save_path)

    return save_list


# 要遍历的目录路径
directory_path = "cache/out/avg_190_clour_1"

crop_lb_x = 365
crop_lb_y = 0
crop_width = 250

path_list = gen_face(directory_path, crop_lb_x, crop_lb_y, crop_width)

# 超分处理

tool_path = "./tools/realcugan/realcugan-ncnn-vulkan.exe"

for p in path_list:
    cmd = f"{tool_path} -n 1 -i {p.absolute()} -o {p.absolute()}"

# stdout = subprocess.run(cmd.split(" "), capture_output=True).stdout
    # print(subprocess.run(cmd.split(" "), capture_output=True).stdout.decode())
    print("run command:", cmd)

    process = subprocess.Popen(
        cmd.split(" "), stdout=subprocess.PIPE, universal_newlines=True)

    # 实时读取stdout
    for line in process.stdout:
        print(line, end='')

    # 等待命令执行完毕
    process.wait()
    print()
