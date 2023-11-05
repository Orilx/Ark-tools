from typing import List
import requests
import json
from pathlib import Path


def diff(old_set: List, new_set: List):
    
    # 转换为集合
    set1 = set(json.dumps(i) for i in old_set)
    set2 = set(json.dumps(i) for i in new_set)

    # 获取不同部分
    diff_set = [json.loads(i) for i in set1.symmetric_difference(set2)]

    return diff_set


def download_res(resVersion: str, resName: str, dl_path: str):
    res_url = f"https://ak.hycdn.cn/assetbundle/official/Android/assets/{resVersion}/{dl_path}_{resName}.dat"
    print(f"正在下载：{resName}")
    print(res_url)
    
    out_path = cachePath / "download" / dl_path
    if not out_path.exists():
        out_path.mkdir()
        
    response = requests.get(res_url)
    if response.status_code == 200:
        with open(out_path / f"{resName}.zip", "wb") as file:
            file.write(response.content)
            print("下载完成")
    else:
        print("下载文件时出错：", response.status_code)


cachePath = Path('cache')
dataPath = Path('data/game_data')

# 获取版本号
version_api = 'https://ak-conf.hypergryph.com/config/prod/official/Android/version'
print(f'获取当前版本信息...')
resVersion = requests.get(version_api).json()["resVersion"]
print(f'当前版本号：{resVersion}')

# 检查本地是否有缓存的版本文件列表
curr_ver_info = {}
curr_ver_file = dataPath / "version_info" / f"{resVersion}.json"
if curr_ver_file.exists():
    with open(curr_ver_file, "r") as file:
        curr_ver_info = json.load(file)
else:
    print(f'下载版本文件列表...')
    # 获取文件列表
    hot_update_list = f"https://ak.hycdn.cn/assetbundle/official/Android/assets/{resVersion}/hot_update_list.json"
    curr_ver_info = requests.get(hot_update_list).json()
    print(f'下载完成.')

    with open(curr_ver_file, "w") as file:
        json.dump(curr_ver_info, file)

curr_avg_imgs = []
curr_avg_bg = []
curr_avg_characters = []
curr_characarts = []
curr_skinpack = []

for item in curr_ver_info["abInfos"]:
    name = item["name"]
    if name.startswith("chararts/"):
        curr_characarts.append({"name": name, "hash": item["hash"]})
    elif name.startswith("skinpack/"):
        curr_skinpack.append({"name": name, "hash": item["hash"]})
    elif name.startswith("avg/characters/"):
        curr_avg_characters.append({"name": name, "hash": item["hash"]})
    elif name.startswith("avg/imgs/"):
        curr_avg_imgs.append({"name": name, "hash": item["hash"]})
    elif name.startswith("avg/bg/"):
        curr_avg_bg.append({"name": name, "hash": item["hash"]})

def dl_save(res_type:str, curr_res:List):
    old_res = []
    with open(dataPath / f"old_{res_type}.json", "r") as file:
        old_res = json.load(file)
    # 所有有修改的文件列表
    diff_set = diff(old_res, curr_res)
    download_list = list(set([i["name"].split('/')[-1][:-3] for i in diff_set]))
    for resName in download_list:
        download_res(resVersion, resName, res_type)

    with open(dataPath / f"old_{res_type}.json", "w") as file:
        json.dump(curr_res, file)

# 下载文件

# 剧情背景和 CG
dl_save("avg_imgs", curr_avg_imgs)
dl_save("avg_bg", curr_avg_bg)

# 干员立绘
dl_save("chararts", curr_characarts)

# 干员时装
dl_save("skinpack", curr_skinpack)

# 立绘差分
dl_save("avg_characters", curr_avg_characters)