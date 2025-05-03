import json

def convert_data(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        data = []
        for line in f:
            try:
                item = json.loads(line.strip())
                data.append(item)
            except json.JSONDecodeError as e:
                print(f"解析以下行时出错: {line[:100]}...")
                print(f"错误信息: {e}")
                continue

    new_data = []
    for item in data:
        text = item['text']
        spo_list = item['spo_list']
        
        # 提取出新的 output 格式
        output_list = []
        for spo in spo_list:
            output_item = {
                "subject": spo['subject'],
                "subject_type": spo['subject_type']["@value"] if isinstance(spo['subject_type'], dict) else spo['subject_type'],
                "predicate": spo['predicate'],
                "object": spo['object']["@value"] if isinstance(spo['object'], dict) else spo['object'],
                "object_type": spo['object_type']["@value"] if isinstance(spo['object_type'], dict) else spo['object_type']
            }
            output_list.append(output_item)
        
        # 构建新的一条样本
        new_item = {
            "instruction": "请从以下文本中抽取知识三元组，包含实体（含类型）、属性（含类型）与实体之间的关系（含类型）。",
            "input": text,
            "output": json.dumps(output_list, ensure_ascii=False)  # 直接变成字符串
        }
        new_data.append(new_item)

    # 保存新文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)

    print(f"转换完成，共处理 {len(new_data)} 条数据。输出文件：{output_file}")

if __name__ == "__main__":
    input_path = "dev_data.json"    # 原始大json路径
    output_path = "dev_ie_data.json"  # 转换后输出的路径
    convert_data(input_path, output_path)
