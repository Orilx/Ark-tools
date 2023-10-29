import time
from pathlib import Path
from typing import Any, Dict
from natsort import natsorted
import UnityPy


class ArkUnPacker:
    def __init__(self, input_file: str | bytes, output_path: str = 'cache/out/'):
        self.env = UnityPy.load(input_file)
        self.output_path = Path(output_path) / f'unpack_{int(time.time())}'

        if not self.output_path.exists():
            self.output_path.mkdir()

        self.result = {
            "output_path": self.output_path,
            "type_cnt": 0,
            "pics":  {
                "full": [],
                "face": [],
                "face_alpha": []
            },
            "pos_info": []
        }

    def save_Texture2D(self, data):
        """保存素材图片（立绘差分的原始和遮罩图片、CG、插图等）

        Args:
            data (_type_): Texture2D
        """

        if not self.output_path.exists():
            self.output_path.mkdir()

        if data.m_Width != 0:
            pic_type = 1
            if data.name.startswith('avg'):
                img_path = self.output_path / 'full'
            else:
                img_path = self.output_path / 'face'
                pic_type = 0

            if not img_path.exists():
                img_path.mkdir()

            out_file = img_path / f"{data.name}.png"

            try:
                data.image.save(out_file)

                if pic_type:
                    if not out_file.name.endswith("[alpha].png"):
                        self.result["pics"]["full"].append(out_file.name)
                        self.result["type_cnt"] += 1
                else:
                    if not out_file.name.endswith("[alpha].png"):
                        self.result["pics"]["face"].append(out_file.name)
                    else:
                        self.result["pics"]["face_alpha"].append(
                            out_file.name.replace('[alpha].png', ''))

            except Exception as e:
                pass

    def get_pos_info(self, mono):
        """获取差分图像的变形参数

        Args:
            mono (_type_): MonoBehaviour
        """
        if mono.serialized_type.nodes:
            if spriteGroups := mono.read_typetree().get("spriteGroups"):
                for p in spriteGroups:
                    self.result["pos_info"].append(
                        {"face_size_x": int(p["faceSize"]["x"]),
                         "face_size_y": int(p["faceSize"]["y"]),
                         "face_pos_x": int(p["facePos"]["x"]),
                         "face_pos_y": int(p["facePos"]["y"])})

    # def export_skin(self) -> Dict[str, Any]:
    #     """获取时装的原始和遮罩图片

    #     Returns:
    #         Dict[str, Any]: _description_
    #     """
    #     for path, obj in self.env.container.items():
    #         # 定位到包含 2048 x 2048 图像的 Container
    #         # if path.endswith('_material.mat') and not path.endswith('b_material.mat'):
    #         #     if path.endswith('.prefab') and not path.endswith('b.prefab'):
    #         if path.split('/')[-1].startswith('illust_'):
    #             print('=====')
    #             print(path)
    #             try:
    #                 for key, texEnv in obj.read().m_SavedProperties.m_TexEnvs.items():  # type: ignore
    #                     if not texEnv.m_Texture:
    #                         continue
    #                     # 提取图片
    #                     tex = texEnv.m_Texture.read()
    #                     texName = f"{tex.m_Name if tex.m_Name else key}.png"
    #                     print(texName)

    #                 # self.result["pics"].append(self.output_path / texName)
    #                 # with self.env.fs.open(self.output_path / texName, "wb") as f:
    #                 #     tex.read().image.save(f)
    #             except:
    #                 pass
    #     return self.result

    methods = {
        'Texture2D': save_Texture2D,
        'MonoBehaviour': get_pos_info,
    }

    def export_avg_chararts(self) -> Dict[str, Any]:
        """获取剧情立绘差分的原始图片、遮罩图片和差分图像的变形参数

        Returns:
            Dict[str, Any]: _description_
        """
        for obj in self.env.objects:
            func = self.methods.get(obj.type.name)

            if not func:
                # print('Unknown type:' + type_name)
                continue

            assert func
            func(self, obj.read())

        self.result["pics"]["face_alpha"] = natsorted(
            self.result["pics"]["face_alpha"])
        return self.result

    # def export_CG(self) -> Dict[str, Any]:
    #     """导出 CG

    #     Returns:
    #         Dict[str, Any]: _description_
    #     """
    #     for obj in self.env.objects:
    #         if obj.type.name == 'Texture2D':
    #             self.save_Texture2D(obj.read())
    #     return self.result
