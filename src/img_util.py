from typing import List, Tuple
from pathlib import Path

from PIL import Image,  ImageDraw, ImageFilter, ImageOps


TEMP_PATH = Path("data/img")


def get_center(img_a: tuple[int, int], img_b: tuple[int, int], offset=(0, 0)):
    """获取可以使 img_b 在 img_a 中居中的 img_b 左上角坐标

    Args:
        img_a (tuple[int,int]): img_a 的大小 

        img_b (tuple[int,int]): img_b 的大小

        offset (tuple, optional): 偏移量. Defaults to (0, 0).

    """
    return ((img_a[0]-img_b[0])//2+offset[0], (img_a[1]-img_b[1])//2+offset[1])


def get_mask(img_size: tuple[int, int], xy_list: List[tuple[int, int, int, int]], offset: Tuple[int, int], radius: int, m:int):
    """获取裁剪蒙版图层

    Args:
        img_size (tuple[int,int]): 原始图像的尺寸

        pos (tuple[int,int,int,int]): 蒙版四角坐标

        r (int, optional): 蒙版圆角半径.

    """

    alpha = Image.new('L', img_size, 255)
    draw = ImageDraw.Draw(alpha)
    for xy in xy_list:
        pos = (xy[0]*m+offset[0], xy[1]*m+offset[1],
               xy[2]*m+offset[0], xy[3]*m+offset[1])

        draw.rounded_rectangle(pos, fill="black", radius=radius)

    alpha = ImageOps.invert(alpha)

    # alpha.save('cache/img/alpha.jpg', quality=100)
    return alpha


# def get_shadow(img_size: tuple[int, int], ex: tuple[int, int]):
#     """获取 shadow 蒙版图层

#     Args:
#         img_size (tuple[int,int]):  产生阴影的图层的尺寸 

#         ex (float, optional): 拓展尺寸（左右/上下）

#     """

#     shadow = Image.new(
#         'L', (int(img_size[0]+ex[0]), int(img_size[1]+ex[1])), 255)

#     l = Image.linear_gradient('L').resize((shadow.width, shadow.height//2))
#     shadow.paste(l)
#     shadow.paste(l.transpose(Image.ROTATE_180), (0, shadow.height//2))

#     shadow = ImageChops.darker(shadow,
#                                shadow.copy().transpose(Image.ROTATE_90).resize((shadow.width, shadow.height)))

#     # 给阴影加个圆角
#     s = Image.new('L', shadow.size)
#     s.paste(shadow, mask=get_mask(shadow.size, shadow.getbbox(), 60))

#     # s.save('cache/img/shadow.jpg', quality=100)
#     return s


def draw_blur_pic(input_img,
                  xy_list: List[Tuple[int, int, int, int]],
                  offset: Tuple[int, int] = (0, 0),
                  radius: int = 15,
                  blur_radius=30,
                  color: str = 'white',
                  brightness: int = 210,
                  m: int = 1
                  ):
    """绘制高斯模糊的圆角矩形

    Args:
        input_img (Image): 输入图片
        xy_list (List[Tuple[int, int, int, int]]): 需要绘制矩形的坐标(x1,y1,x2,y2)列表
        offset (Tuple[int, int], optional): 整体偏移量 (x, y). Defaults to (0, 0).
        radius (int, optional): 圆角半径. Defaults to 15.
        blur_radius (int, optional): 模糊半径. Defaults to 30.
        color (str, optional): 颜色（黑/白）. Defaults to 'white'.
        brightness (int, optional): 亮度. Defaults to 210.
        m (int, optional): _description_. Defaults to 1.

    """
    if m !=1:
        input_img = input_img.resize((input_img.width*m, input_img.height*m))
        m = m//2

    img = input_img.filter(ImageFilter.GaussianBlur(10))
    blur_img = img.filter(ImageFilter.GaussianBlur(blur_radius))

    # 画阴影
    # shadow = get_shadow((xy[2]-xy[0],xy[3]-xy[1]), shadow_size)
    # img.paste(Image.new('RGBA', shadow.size),
    #           (xy[0]-shadow_size[0]//2, xy[1]-shadow_size[1]//2),
    #           shadow)

    # 模糊层加一层变亮/变暗
    blur_img.paste(Image.new('RGBA', img.size, color),
                   mask=Image.new('L', img.size, brightness))
    # 画模糊层
    img.paste(blur_img, mask=get_mask(blur_img.size, xy_list, offset, radius=radius, m=m))
    # 画边框
    outline_color = '#9d9e9f'
    if color == 'black':
        outline_color = '#121417'
    for xy in xy_list:
        draw = ImageDraw.Draw(img)
        pos = (xy[0]*m+offset[0], xy[1]*m+offset[1],
               xy[2]*m+offset[0], xy[3]*m+offset[1])
        draw.rounded_rectangle(pos, outline=outline_color, width=1, radius=radius)

    return img
