import json

def trim_json_file(input_file, output_file, max_lines=20000):
    """
    读取JSON文件并只保留前max_lines行
    
    Args:
        input_file (str): 输入JSON文件路径
        output_file (str): 输出JSON文件路径
        max_lines (int): 要保留的最大行数
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            # 读取前max_lines行
            lines = []
            for i, line in enumerate(f):
                if i >= max_lines:
                    break
                lines.append(line.strip())
        
        # 写入新文件
        with open(output_file, 'w', encoding='utf-8') as f:
            for line in lines:
                f.write(line + '\n')
        
        print(f'成功处理文件！保留了前{len(lines)}行数据。')
        
    except Exception as e:
        print(f'处理文件时出错：{str(e)}')

if __name__ == '__main__':
    # 使用示例
    input_file = 'EE/dev_ie_data.json'  # 替换为你的输入文件路径
    output_file = 'dev_ie_data20000.json'  # 替换为你的输出文件路径
    trim_json_file(input_file, output_file) 