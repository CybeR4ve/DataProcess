import jsonlines
import os

def filter_merged_data(input_jsonl_filepath: str, output_jsonl_filepath: str):
    """
    读取合并后的JSONL文件，过滤掉events或knowledge_triples列表为空的记录，输出到新的JSONL文件。

    Args:
        input_jsonl_filepath: 合并后的JSONL文件路径。
        output_jsonl_filepath: 过滤后输出的JSONL文件路径。
    """
    print(f"正在过滤数据...")
    print(f"输入文件: {input_jsonl_filepath}")
    print(f"输出文件: {output_jsonl_filepath}")

    kept_count = 0
    skipped_count = 0

    try:
        with jsonlines.open(input_jsonl_filepath, 'r') as reader, \
             jsonlines.open(output_jsonl_filepath, 'w') as writer:

            for record in reader:
                # 检查 knowledge_triples 列表是否非空
                has_triples = record.get("knowledge_triples") is not None and isinstance(record["knowledge_triples"], list) and len(record["knowledge_triples"]) > 0

                # 检查 events 列表是否非空
                has_events = record.get("events") is not None and isinstance(record["events"], list) and len(record["events"]) > 0

                # 如果 triples 和 events 列表都非空，则保留该记录
                if has_triples and has_events:
                    writer.write(record)
                    kept_count += 1
                else:
                    skipped_count += 1

        print(f"\n过滤完成。")
        print(f"保留记录数: {kept_count}")
        print(f"跳过记录数 (缺少三元组或事件): {skipped_count}")
        print(f"过滤结果保存在 {output_jsonl_filepath}")

    except FileNotFoundError:
        print(f"错误: 输入文件未找到 - {input_jsonl_filepath}")
    except Exception as e:
        print(f"过滤过程中发生错误: {e}")

# --- 示例使用 ---
if __name__ == "__main__":
    # 假设上一步合并的输出文件是这个
    MERGED_INPUT_FILE = "merged_extraction_results.jsonl"
    FILTERED_OUTPUT_FILE = "filtered_merged_results.jsonl"

    # 注意：请确保 MERGED_INPUT_FILE 存在并且是上一步合并脚本的输出

    # 运行过滤脚本
    filter_merged_data(MERGED_INPUT_FILE, FILTERED_OUTPUT_FILE)

    # --- 打印一部分过滤后的结果以供检查 ---
    if os.path.exists(FILTERED_OUTPUT_FILE):
         print(f"\n--- 过滤后的结果 (前 3 条) ---")
         try:
             with jsonlines.open(FILTERED_OUTPUT_FILE, 'r') as reader:
                 for i, obj in enumerate(reader):
                     print(json.dumps(obj, ensure_ascii=False, indent=2))
                     if i >= 2: # 只打印前3条
                         break
         except Exception as e:
             print(f"无法读取过滤后的文件: {e}")
    else:
        print(f"过滤后的输出文件 {FILTERED_OUTPUT_FILE} 不存在。")