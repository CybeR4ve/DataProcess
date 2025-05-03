import requests
import json
import time
import re
import datetime
import random
import csv
import os
from requests.adapters import HTTPAdapter

# 创建CSV文件并写入表头
def create_csv_file(filename):
    file_exists = os.path.isfile(filename)
    with open(filename, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['id', 'create_time', 'rich_text'])
    return filename

# 写入数据到CSV文件
def write_to_csv(filename, data):
    with open(filename, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(data)

def get_json_data(base_url, headers):
    s = requests.Session()
    s.mount('http://', HTTPAdapter(max_retries=3))
    s.mount('https://', HTTPAdapter(max_retries=3))
    print(time.strftime('%Y-%m-%d %H:%M:%S'))
 
    try:
        response = requests.get(base_url, timeout=5, headers=headers)
        html = response.text
        # print(html)
        html_cl = html[12:-14]
        false = False
        true = True
        null = None
        html_json = eval(html_cl)
        json_str = json.dumps(html_json)
        results = json.loads(json_str)
        data = results['result']['data']['feed']['list']
    except Exception as e:
        print('get_json_str未收录错误类型，请检查网络通断,错误位置：', e)
        time.sleep(5)
        get_json_data(base_url, headers)
    else:
        return data

# 读取已爬取的ID列表
def get_existing_ids(filename):
    if not os.path.isfile(filename):
        return []
    
    existing_ids = []
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)  # 跳过表头
        for row in reader:
            if row:  # 确保行不为空
                existing_ids.append(row[0])
    return existing_ids

# 主程序
def main():
    # 创建CSV文件
    csv_filename = 'sina_data.csv'
    create_csv_file(csv_filename)
    
    page = 0
    
    while True:
        try:
            page += 1
            print(page)
            referer_url = "http://finance.sina.com.cn/7x24/?tag=102"
            cookie = "UOR=www.baidu.com,tech.sina.com.cn,; SINAGLOBAL=114.84.181.236_1579684610.152568; UM_distinctid=16fcc8a8b704c8-0a1d2def9ca4c6-33365a06-15f900-16fcc8a8b718f1; lxlrttp=1578733570; gr_user_id=2736e487-ee25-4d52-a1eb-c232ac3d58d6; grwng_uid=d762fe92-912b-4ea8-9a24-127a43143ebf; __gads=ID=d79f786106eb99a1:T=1582016329:S=ALNI_MZoErH_0nNZiM3D4E36pqMrbHHOZA; Apache=114.84.181.236_1582267433.457262; ULV=1582626620968:6:4:1:114.84.181.236_1582267433.457262:1582164462661; ZHIBO-SINA-COM-CN=; SUB=_2AkMpBPEzf8NxqwJRmfoWz2_ga4R2zQzEieKfWADoJRMyHRl-yD92qm05tRB6AoTf3EaJ7Bg2UU4l1CDZXUBCzEuJv3mP; SUBP=0033WrSXqPxfM72-Ws9jqgMF55529P9D9WhqhhGsPWdPjar0R99pFT8s"
            headers = {
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Connection": "keep-alive",
                "Cookie": cookie,
                "Host": "zhibo.sina.com.cn",
                "Referer": referer_url,
                "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36"
            }
            base_url = "http://zhibo.sina.com.cn/api/zhibo/feed?callback=jQuery0&page=%s"%page+"&page_size=20&zhibo_id=152&tag_id=0&dire=f&dpc=1&pagesize=20&_=0%20Request%20Method:GET%27"
            data = get_json_data(base_url, headers)
            
            # 获取已爬取的ID列表
            existing_ids = get_existing_ids(csv_filename)
            
            for i in data:
                id = i['id']
                create_time = i['create_time']
                rich_text = i['rich_text']
                
                # 检查ID是否已存在
                if id not in existing_ids:
                    print(id, create_time, rich_text)
                    try:
                        # 写入CSV文件
                        write_to_csv(csv_filename, [id, create_time, rich_text])
                        existing_ids.append(id)  # 更新已爬取ID列表
                    except Exception as e:
                        print(e)
                        continue
            
            time.sleep(random.randint(1, 3))
        except Exception as e:
            print(e)
            continue

if __name__ == "__main__":
    main()
