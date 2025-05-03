import json

def convert_event_data(input_file, output_file):
    data = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip() # 移除行首尾空白，包括换行符
            if not line: # 跳过空行
                continue
            try:
                item = json.loads(line)
                data.append(item)
            except json.JSONDecodeError as e:
                print(f"解析以下行时出错: {line[:100]}...")
                print(f"错误信息: {e}")
                continue

    new_data = []
    for item in data:
        # 确保 'text' 键存在
        if 'text' not in item:
            print(f"跳过缺少 'text' 键的项: {item}")
            continue

        text = item['text']
        event_list = item.get('event_list', [])

        # 提取出新的 output 格式
        output_list = []
        for event in event_list:
            # 确保 'event_type' 和 'trigger' 键存在或提供默认值
            output_item = {
                "event_type": event.get('event_type', ''),
                "trigger": event.get('trigger', ''),
                "arguments": []
            }

            for argument in event.get('arguments', []):
                 # 确保 'role' 和 'argument' 键存在或提供默认值
                arg_item = {
                    "role": argument.get('role', ''),
                    "argument": argument.get('argument', '')
                }
                output_item["arguments"].append(arg_item)

            output_list.append(output_item)

        # 构建新的一条样本
        # output 内容直接变成字符串，符合你的原始代码逻辑
        new_item = {
            "instruction": "请从以下文本中抽取所有事件，包含事件类型、触发词和论元角色及其内容。",
            "input": text,
            "output": json.dumps(output_list, ensure_ascii=False)
        }
        new_data.append(new_item)

    # 保存新文件 - 修改这里以实现每行一个 JSON 对象
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in new_data:
            # 将每个字典序列化为一行 JSON 字符串，并写入文件
            f.write(json.dumps(item, ensure_ascii=False) + '\n')


    print(f"转换完成，共处理 {len(new_data)} 条数据。输出文件：{output_file}")

if __name__ == "__main__":
    input_path = "EE_train_dataset.jsonl"    # 原始event格式路径
    output_path = "Converted_EE_train_dataset.jsonl" # 转换后输出路径
    convert_event_data(input_path, output_path)