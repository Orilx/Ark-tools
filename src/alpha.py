from pathlib import Path

from PIL import Image


def gen(base_path, name, file_name):
    avg_img_path = base_path / "face" / f"{file_name}.png"
    avg_alpha_path = base_path / "face" / f"{file_name}[alpha].png"
    avg_img = Image.open(avg_img_path)
    avg_alpha = Image.open(avg_alpha_path).convert(mode='L')

    base_img = Image.new('RGBA', size=avg_img.size)
    base_img.paste(avg_img, mask=avg_alpha)

    save_path: Path = avg_img_path.parent.parent.parent.parent / "out" / name

    base_img.save(save_path / f'{file_name}.png', quality=100)


base_path = Path("cache/ark_tools/unpack_1695805718")

gen(base_path, "avg_190_clour_1", "6$1")
