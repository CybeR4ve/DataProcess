import json

def count_json_objects(file_path):
    """
    统计JSON数组中的对象数量
    
    Args:
        file_path (str): JSON文件路径
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # 读取整个文件内容并解析为JSON
            data = json.load(f)
            
            # 检查是否为列表类型
            if isinstance(data, list):
                count = len(data)
                print(f'JSON数组中共有 {count} 个对象')
                return count
            else:
                print('文件内容不是JSON数组格式')
                return 0
        
    except json.JSONDecodeError as e:
        print(f'JSON解析错误：{str(e)}')
        return 0
    except Exception as e:
        print(f'处理文件时出错：{str(e)}')
        return 0

if __name__ == '__main__':
    # 使用示例
    file_path = 'EE/converted_event_dataset.json'  # 替换为你的JSON文件路径
    count_json_objects(file_path) 