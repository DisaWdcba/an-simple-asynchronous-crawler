import os
import requests
import time
import random
import string
import hashlib
import logging
import threading
from pynput import keyboard

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def calculate_file_hash(file_path):
    """计算文件哈希值"""
    hasher = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()
    except Exception as e:
        logging.error(f"计算文件哈希值时出错: {e}")
        return None

def check_duplicates_in_directory(directory):
    """检查文件夹中的重复文件"""
    hashes = {}
    duplicates = []
    
    for file_name in os.listdir(directory):
        file_path = os.path.join(directory, file_name)
        if os.path.isfile(file_path):
            file_hash = calculate_file_hash(file_path)
            if file_hash is None:
                continue
            
            if file_hash in hashes:
                logging.warning(f"发现重复文件: {file_path} 和 {hashes[file_hash]}")
                duplicates.append((file_path, hashes[file_hash]))
            else:
                hashes[file_hash] = file_path
    
    return duplicates

def remove_duplicate_files(duplicates):
    """删除重复文件，只保留第一个文件"""
    for dup in duplicates:
        try:
            logging.info(f"删除重复文件: {dup[0]}")
            os.remove(dup[0])
        except Exception as e:
            logging.error(f"删除文件 {dup[0]} 时出错: {e}")

def download_image(url, save_directory, stop_flag, max_attempts=400, sleep_interval=1):
    """下载图片并保存到指定目录"""
    os.makedirs(save_directory, exist_ok=True)
    for i in range(max_attempts):  # 默认执行 400 次下载请求
        if stop_flag.is_set():
            logging.info("下载被用户中断")
            break
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                while True:
                    random_name = ''.join(random.choices(string.ascii_letters + string.digits, k=10)) + '.jpg'
                    save_path = os.path.join(save_directory, random_name)
                    if not os.path.exists(save_path):  
                        break
                
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                logging.info(f"第{i+1}次下载成功，图片已保存为 {save_path}")
            
            else:
                logging.warning(f"第{i+1}次下载失败，状态码：{response.status_code}")
        
        except requests.RequestException as e:
            logging.error(f"第{i+1}次下载失败，网络错误: {e}")
        
        for _ in range(int(sleep_interval * 10)):
            if stop_flag.is_set():
                break
            time.sleep(0.1)
    

    logging.info("正在检查文件夹中的重复文件...")
    duplicates = check_duplicates_in_directory(save_directory)
    
    if duplicates:
        logging.info("发现重复文件，正在删除重复文件...")
        remove_duplicate_files(duplicates)
    else:
        logging.info("没有发现重复文件。")

def on_press(key, stop_flag):
    """监听键盘"""
    try:
        if key.char == '1':
            stop_flag.set()
            print("\n正在停止...")
    except AttributeError:
        pass

def listen_for_stop(stop_flag):
    """键盘监听"""
    with keyboard.Listener(on_press=lambda key: on_press(key, stop_flag)) as listener:
        listener.join()

def main():

    image_url = "https://www.loliapi.com/bg/" 
    save_directory = "./Saved_Pic"
    
    stop_flag = threading.Event()
    input_thread = threading.Thread(target=listen_for_stop, args=(stop_flag,), daemon=True)
    input_thread.start()
    logging.info("开始下载图片...")
    download_image(image_url, save_directory, stop_flag)
    logging.info("下载任务完成。")

if __name__ == "__main__":
    main()
