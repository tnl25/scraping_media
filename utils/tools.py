# tools.py
import os
import re
import shutil
import json
from collections import Counter
from datetime import datetime, timezone


def make_dir(path: str):
    if not os.path.exists(path):
        os.mkdir(path)
    return os.path.normpath(path)
    
def save_dict(info: dict, name: str, dir_name: str = 'dist', stamp: bool = False):
    if not info:
        return None
    
    timestamp = datetime.now(timezone.utc).strftime(r'%Y-%m-%dT%H-%M-%S-%fZ')   

    path = make_dir(dir_name)
    filename = os.path.join(path, f"{name}.json")
    
    if stamp:
        filename = os.path.join(path, f"{name}-{timestamp}.json")
               
    with open(filename, 'w') as f:
        json.dump(info, f, indent=4)
        print(f'file saved {filename}')

def rm_dir(name: str):
    shutil.rmtree(name)

def assert_camelCase(info: dict) -> None:
    if isinstance(info, dict):
        for key in list(info.keys()):
            if key[0].isupper():
                raise ValueError(f'key {key} start with upper')
            
            if isinstance(info[key], (dict, list)):
                assert_camelCase(info[key])
    
    elif isinstance(info, list):
        for item in info:
            assert_camelCase(item)

def read_settings(file_path: str = "settings.json") -> dict:
    
    if not os.path.isfile(file_path):
        raise ValueError(f"Couldn't find settings file: {file_path}")
    
    try:
        with open(file_path, 'r') as f:
            settings = json.load(f)
    except Exception as e:
        raise ValueError(f'Could not read setting.json: {e}')
    
    return settings

def clean_cache(directory: str = '.') -> None:
    for root, dirs, files in os.walk(directory, topdown=False):
        # delete __pycache__
        if '__pycache__' in dirs:
            pycache_dir = os.path.join(root, '__pycache__')
            print(f"Delete dir: {pycache_dir}")
            shutil.rmtree(pycache_dir)
        
        # Delete .pyc y .pyo
        for file in files:
            if file.endswith(('.pyc', '.pyo')):
                file_path = os.path.join(root, file)
                print(f"Delete file: {file_path}")
                os.remove(file_path)

    print("Limpieza de cache completada.")


def mostcommon_Bykey(data: list[dict], key: str) -> dict:
    counter = Counter(i.get(key) for i in data)
    common = counter.most_common(2)
    if not common:
        raise ValueError('Most common not found')
    if len(common) > 1:
        if common[0][1] == common[1][1]:
            raise ValueError('Two most common found')
    
    common_id = common[0][0]
    return next(i for i in data if i.get(key) == common_id)

def mostcommon(data: list[dict]) -> dict:
    counter = Counter(json.dumps(i, sort_keys=True) for i in data)
    common = counter.most_common(2)
    
    if not common:
        raise ValueError('most common not found')
    
    if len(common) > 1:
        if common[0][1] == common[1][1]:
            raise ValueError('Two most common found')
    
    common_json = common[0][0]
    return next(i for i in data if json.dumps(i, sort_keys=True) == common_json)

def find_tags(text: str) -> list[str]:
        pattern = r'#\w+'
        return re.findall(pattern, text)
