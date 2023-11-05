import re
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

from warterprint import code128_image
from img_util import draw_blur_pic, get_center, get_mask


def upscale(save_path: Path):
    print('进行超分处理...')
    tool_path = "./tools/realcugan/realcugan-ncnn-vulkan.exe"
    cmd = f"{tool_path} -m models-nose -n 0 -i {save_path.absolute()} -o {save_path.absolute()}"
    process = subprocess.Popen(
        cmd.split(" "), stdout=subprocess.PIPE, universal_newlines=True)
    # 实时读取stdout
    assert process.stdout
    for line in process.stdout:
        print(line, end='')
    # 等待命令执行完毕
    process.wait()
    print('处理完成.')
    return Image.open(save_path)


def gen_face(img_path: Path, crop_lb_x: int, crop_lb_y: int, crop_width: int, bg_path: Path):

    face_block_width = 200
    gap_width = 8
    unit_width = face_block_width + gap_width
    file_groups = {}

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
    for cate, files in file_groups.items():
        print(f'正在处理：{img_path.name}_{cate}.png')
        pic_cnt = len(files)

        # 根据数量判断三个一排还是四个一排
        g_x = 4 if pic_cnt > 15 else 3
        g_y = pic_cnt // g_x
        if pic_cnt % g_x != 0:
            g_y += 1

        # 水印
        # code_img = code128_image('5rOw5ouJ5peF56S+')
        # code_img = code_img.resize((code_img.width, base_img.height))
        # code_mask = Image.new('L', size=code_img.size, color='#181818')
        # base_img.paste(code_img, box=((base_img.width-code_img.width)//2, 0), mask=code_mask)

        # 主体人物
        full_ori = Image.open(img_path/f"1${cate}.png")

        full_ori = full_ori.resize((1000, 1000), resample=Image.LANCZOS)
        full_ori_block_width = full_ori.width + gap_width*4
        full_ori_block_height = full_ori.height + gap_width*4
        full_pos = get_center(
            (full_ori_block_width, full_ori_block_height), full_ori.size)

        # 需要绘制背景块的坐标列表（x1,y1,x2,y2）
        blur_list = []
        # 主体人物背景块的坐标
        blur_list.append((0, 0, full_ori_block_width, full_ori_block_height))

        # 表情差分处理
        # 裁切坐标（左上和右下）
        # 有的立绘的头顶紧贴着上边框，这里留出 20px 方便调整
        crop_box = ((crop_lb_x, crop_lb_y+20,
                     crop_lb_x+crop_width, crop_lb_y+20+crop_width))
        # 创建放置表情差分的透明底图
        face_img = Image.new('RGBA', size=(g_x*unit_width, g_y*unit_width))
        # 依次打开差分图片，粘贴到底图
        for i in range(pic_cnt):
            f = Image.new('RGBA', (full_ori.height, full_ori.height))
            f.paste(Image.open(img_path/f"{i+1}${cate}.png"), (0, 20))
            f = f.crop(crop_box).resize(
                (face_block_width, face_block_width), resample=Image.LANCZOS)
            face_img.alpha_composite(
                f, (unit_width*(i % g_x), unit_width*(i // g_x)))

            # 表情差分背景块的坐标
            blur_list.append((full_ori_block_width + gap_width + unit_width*(i % g_x), unit_width*(i // g_x),
                              full_ori_block_width + gap_width + unit_width*(i % g_x)+face_block_width, unit_width*(i // g_x)+face_block_width))

        # 最后一行空白处理
        space = pic_cnt % g_x
        if space != 0:
            space_width = (g_x-space)*face_block_width+(g_x-space-1)*gap_width
            blur_list.append((full_ori_block_width + gap_width + unit_width*space, unit_width*(pic_cnt // g_x),
                             full_ori_block_width + gap_width + space_width+unit_width*space, face_block_width+unit_width*(pic_cnt // g_x)))

        # 创建透明底的全图，下一步超分使用
        t_bg_width = full_ori_block_width + face_img.width
        t_bg_height = max(full_ori_block_height, face_img.height)

        t_bg = Image.new('RGBA', (t_bg_width, t_bg_height))
        t_bg.alpha_composite(full_ori, full_pos)
        t_bg.alpha_composite(face_img, (full_ori_block_width + gap_width, 0))

        save_path = img_path.parent/f"{img_path.name}_{cate}.png"
        t_bg.save(save_path)

        # 对拼好的透明底差分进行超分处理
        t = upscale(save_path)

        # TODO 处理方式改进
        m = 4
        bg = Image.open(bg_path)

        tt = Image.new('RGBA', t.size)
        tt.paste(t, mask=get_mask(t.size, blur_list, (0, 0), radius=16, m=2))
        offset = get_center((bg.width*m, bg.height*m), t.size)
        # 绘制背景块
        bg = draw_blur_pic(bg, blur_list, radius=16,
                           offset=offset, color='white', m=m)
        bg.alpha_composite(tt, offset)

        # 画边框
        for xy in blur_list:
            draw = ImageDraw.Draw(bg)
            pos = (xy[0]*2+offset[0], xy[1]*2+offset[1],
                   xy[2]*2+offset[0], xy[3]*2+offset[1])
            draw.rounded_rectangle(pos, outline='#9d9e9f', width=1, radius=16)

        # 保存
        bg.save(save_path)
        print('拼接完成.')

# bg_path = Path('data/img') / '44_g8_towersquare.png'
# directory_path = Path("out/avg_npc_1124_1")

# crop_lb_x = 430
# crop_lb_y = -20
# crop_width = 200

# gen_face(directory_path, crop_lb_x, crop_lb_y, crop_width, bg_path)
