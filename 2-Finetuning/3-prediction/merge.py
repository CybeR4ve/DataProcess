import csv
import json
import jsonlines # 需要安装这个库：pip install jsonlines
import os

def merge_extraction_results(csv_filepath: str, triples_jsonl_filepath: str, events_jsonl_filepath: str, output_jsonl_filepath: str):
    """
    读取CSV文件中的文本和时间戳，以及两个JSONL文件中的抽取结果，按行合并后输出到新的JSONL文件。

    Args:
        csv_filepath: 包含原始文本和时间戳的CSV文件路径。
        triples_jsonl_filepath: 包含知识三元组抽取结果的JSONL文件路径 (结果在predict字段)。
        events_jsonl_filepath: 包含事件抽取结果的JSONL文件路径 (结果在predict字段)。
        output_jsonl_filepath: 合并结果输出的JSONL文件路径。
    """
    print(f"正在合并结果...")
    print(f"CSV源文件: {csv_filepath}")
    print(f"三元组JSONL源文件: {triples_jsonl_filepath}")
    print(f"事件JSONL源文件: {events_jsonl_filepath}")
    print(f"输出文件: {output_jsonl_filepath}")

    # 使用 jsonlines 库方便处理 JSONL 文件
    # 使用 csv.DictReader 自动处理 CSV 头部，按列名访问数据
    try:
        with open(csv_filepath, 'r', encoding='utf-8') as csvfile, \
             jsonlines.open(triples_jsonl_filepath, 'r') as triples_reader, \
             jsonlines.open(events_jsonl_filepath, 'r') as events_reader, \
             jsonlines.open(output_jsonl_filepath, 'w') as writer:

            csv_reader = csv.DictReader(csvfile)

            # 检查 CSV 是否包含所需的列名
            if 'create_time' not in csv_reader.fieldnames or 'rich_text' not in csv_reader.fieldnames:
                raise ValueError(f"CSV文件需要包含 'create_time' 和 'rich_text' 列。找到的列名: {csv_reader.fieldnames}")

            # 逐行读取并合并
            record_count = 0
            try:
                # 同时迭代三个读取器
                for csv_row, triple_line, event_line in zip(csv_reader, triples_reader, events_reader):
                    record_count += 1
                    
                    # 从CSV获取时间和文本
                    timestamp = csv_row['create_time']
                    original_text = csv_row['rich_text']

                    # 从三元组JSONL获取结果
                    triple_predict_str = triple_line.get('predict', '[]') # 获取predict字段，如果不存在或为None则默认为空列表的字符串表示
                    try:
                        knowledge_triples = json.loads(triple_predict_str)
                        if not isinstance(knowledge_triples, list): # 简单的类型检查
                             print(f"警告: 行 {record_count} 三元组预测结果非JSON列表: {triple_predict_str[:200]}...")
                             knowledge_triples = [] # 结构不对时视为空
                    except json.JSONDecodeError:
                        print(f"错误: 行 {record_count} 三元组预测结果JSON解析失败: {triple_predict_str[:200]}...")
                        knowledge_triples = [] # 解析失败时视为空

                    # 从事件JSONL获取结果
                    event_predict_str = event_line.get('predict', '[]') # 获取predict字段
                    try:
                        events = json.loads(event_predict_str)
                        if not isinstance(events, list): # 简单的类型检查
                             print(f"警告: 行 {record_count} 事件预测结果非JSON列表: {event_predict_str[:200]}...")
                             events = [] # 结构不对时视为空
                    except json.JSONDecodeError:
                        print(f"错误: 行 {record_count} 事件预测结果JSON解析失败: {event_predict_str[:200]}...")
                        events = [] # 解析失败时视为空

                    # 构建合并后的结果字典
                    merged_record = {
                        "timestamp": timestamp,
                        "text": original_text,
                        "knowledge_triples": knowledge_triples,
                        "events": events
                    }

                    # 写入输出文件
                    writer.write(merged_record)

            except StopIteration:
                # zip 会在最短的迭代器结束时停止，这通常意味着文件行数不完全对齐
                print("\n警告: 输入文件行数可能不完全对齐。合并在最短文件结束时停止。")


            print(f"\n合并完成。共处理 {record_count} 条记录。结果保存在 {output_jsonl_filepath}")

    except FileNotFoundError as e:
        print(f"错误: 文件未找到 - {e}")
    except Exception as e:
        print(f"合并过程中发生错误: {e}")

# --- 示例使用 ---
if __name__ == "__main__":
    # 假设你的文件名为以下
    CSV_FILE = "sina_data_results.csv"
    TRIPLES_JSONL_FILE = "ie_predictions.jsonl"
    EVENTS_JSONL_FILE = "ee_predictions.jsonl"
    OUTPUT_MERGED_JSONL_FILE = "merged_results.jsonl"

    # --- 创建一些模拟文件用于测试 ---
    # 你需要替换为你实际的文件
    if not os.path.exists(CSV_FILE):
        print(f"创建模拟 {CSV_FILE} 文件...")
        with open(CSV_FILE, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['create_time', 'rich_text', 'other_column']) # CSV头部
            writer.writerow(['2025/4/26 2:43', '北约秘书长吕特会见了特朗普...', '...'])
            writer.writerow(['2025/4/26 2:35', '特朗普：“俄罗斯与乌克兰局势...', '...'])
            writer.writerow(['2025/4/26 2:33', '美国总统特朗普：乌克兰尚未签...', '...'])
    else:
         print(f"使用现有 {CSV_FILE} 文件。")

    if not os.path.exists(TRIPLES_JSONL_FILE):
        print(f"创建模拟 {TRIPLES_JSONL_FILE} 文件...")
        with jsonlines.open(TRIPLES_JSONL_FILE, 'w') as writer:
            writer.write({"prompt": "...", "predict": "[{\"subject\": \"吕特\", \"predicate\": \"职务\", \"object\": \"秘书长\"}]", "label": ""})
            writer.write({"prompt": "...", "predict": "[{\"subject\": \"特朗普\", \"predicate\": \"国籍\", \"object\": \"美国\"}]", "label": ""})
            writer.write({"prompt": "...", "predict": "[{\"subject\": \"特朗普\", \"predicate\": \"职务\", \"object\": \"总统\"}]", "label": ""})
    else:
         print(f"使用现有 {TRIPLES_JSONL_FILE} 文件。")

    if not os.path.exists(EVENTS_JSONL_FILE):
        print(f"创建模拟 {EVENTS_JSONL_FILE} 文件...")
        with jsonlines.open(EVENTS_JSONL_FILE, 'w') as writer:
            writer.write({"prompt": "...", "predict": "[{\"event_type\": \"会见\", \"trigger\": \"会见\", \"arguments\": [{\"role\": \"参与方\", \"argument\": \"吕特\"}, {\"role\": \"参与方\", \"argument\": \"特朗普\"}]}]", "label": ""})
            writer.write({"prompt": "...", "predict": "[{\"event_type\": \"评价\", \"trigger\": \"明朗\", \"arguments\": [{\"role\": \"对象\", \"argument\": \"局势\"}]}]", "label": ""})
            writer.write({"prompt": "...", "predict": "[{\"event_type\": \"签署\", \"trigger\": \"签署\", \"arguments\": [{\"role\": \"签署方\", \"argument\": \"乌克兰\"}, {\"role\": \"文件\", \"argument\": \"稀土协议\"}]}]", "label": ""})
    else:
         print(f"使用现有 {EVENTS_JSONL_FILE} 文件。")
    # --- 运行合并脚本 ---

    merge_extraction_results(CSV_FILE, TRIPLES_JSONL_FILE, EVENTS_JSONL_FILE, OUTPUT_MERGED_JSONL_FILE)

    # --- 打印一部分合并后的结果以供检查 ---
    if os.path.exists(OUTPUT_MERGED_JSONL_FILE):
        print(f"\n--- 合并后的结果 (前 3 条) ---")
        try:
            with jsonlines.open(OUTPUT_MERGED_JSONL_FILE, 'r') as reader:
                for i, obj in enumerate(reader):
                    print(json.dumps(obj, ensure_ascii=False, indent=2))
                    if i >= 2: # 只打印前3条
                        break
        except Exception as e:
            print(f"无法读取合并后的文件: {e}")