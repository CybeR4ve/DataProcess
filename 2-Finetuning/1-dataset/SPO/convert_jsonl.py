import json

def convert_jsonl_data(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f_in:
        with open(output_file, 'w', encoding='utf-8') as f_out:
            for line in f_in:
                try:
                    item = json.loads(line.strip())
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
                    
                    # 构建新的一条样本，只包含input和output
                    new_item = {
                        "instruction": "请从以下文本中抽取知识三元组，包含实体（含类型）、属性（含类型）与实体之间的关系（含类型）。",
                        "input": text,
                        "output": json.dumps(output_list, ensure_ascii=False)
                    }
                    
                    # 写入到输出文件，每条记录一行
                    f_out.write(json.dumps(new_item, ensure_ascii=False) + '\n')
                except json.JSONDecodeError as e:
                    print(f"解析以下行时出错: {line[:100]}...")
                    print(f"错误信息: {e}")
                    continue

    print(f"转换完成。输出文件：{output_file}")

if __name__ == "__main__":
    input_path = "ie_val_dataset.jsonl"
    output_path = "ie_val_dataset_converted_forbase.jsonl"
    convert_jsonl_data(input_path, output_path) 