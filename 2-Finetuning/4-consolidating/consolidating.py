import json
import jsonlines
import os

def consolidate_entities_simple(filtered_jsonl_filepath: str, entities_output_filepath: str, graph_data_output_filepath: str):
    """
    根据“同名实体视为同一实体”的简单规则，统一化实体并重构数据。

    Args:
        filtered_jsonl_filepath: 过滤后的合并结果JSONL文件路径。
        entities_output_filepath: 统一化后的实体列表输出JSON文件路径。
        graph_data_output_filepath: 使用实体ID引用重构后的图谱数据输出JSONL文件路径。
    """
    print(f"正在进行实体统一化...")
    print(f"输入文件: {filtered_jsonl_filepath}")
    print(f"统一化实体列表输出: {entities_output_filepath}")
    print(f"重构图谱数据输出: {graph_data_output_filepath}")

    entity_map = {} # 映射 {实体文本: {"id": ..., "primary_type": ...}}
    next_entity_id = 0
    all_records = [] # 存储所有记录以便进行第二遍处理

    # --- 第一遍: 构建实体映射表 ---
    print("第一遍: 构建实体映射表...")
    try:
        with jsonlines.open(filtered_jsonl_filepath, 'r') as reader:
            for record in reader:
                all_records.append(record) # 存储记录

                # 从 knowledge_triples 中提取实体提及 (subject, object)
                triples = record.get("knowledge_triples", [])
                for triple in triples:
                    subject_text = triple.get("subject")
                    subject_type = triple.get("subject_type") # 使用 SPO 中的类型
                    object_text = triple.get("object")
                    object_type = triple.get("object_type") # 使用 SPO 中的类型

                    if subject_text and subject_text not in entity_map:
                        entity_map[subject_text] = {"id": f"e{next_entity_id}", "primary_type": subject_type}
                        next_entity_id += 1
                    if object_text and object_text not in entity_map:
                         # 检查宾语和主语是否是同一个文本，如果是，使用同一个 ID
                        if object_text in entity_map:
                             # 如果宾语文本已经作为主语或其他宾语出现过，使用现有 ID 和类型
                             pass # 保持原有的 map 条目
                        else:
                            entity_map[object_text] = {"id": f"e{next_entity_id}", "primary_type": object_type}
                            next_entity_id += 1

                # 从 events 中提取实体提及 (argument) - 这些没有类型，只用于链接到已识别的实体
                events = record.get("events", [])
                for event in events:
                    arguments = event.get("arguments", [])
                    for arg in arguments:
                        arg_text = arg.get("argument")
                        # 如果论元文本在三元组中作为实体出现过，它就会在 entity_map 里
                        # 这一遍我们只填充 map，不处理论元

    except FileNotFoundError:
        print(f"错误: 输入文件未找到 - {filtered_jsonl_filepath}")
        return
    except Exception as e:
        print(f"构建实体映射表时发生错误: {e}")
        return

    # --- 生成最终的实体列表 ---
    final_entities_list = []
    for text, info in entity_map.items():
        final_entities_list.append({
            "id": info["id"],
            "text": text,
            "type": info.get("primary_type", "Unknown") # 如果SPO里没有类型，给个默认值
            # 可以在这里尝试从多个来源汇总类型，但简单方法就用第一个
        })
    print(f"识别出 {len(final_entities_list)} 个唯一实体。")

    # 将最终实体列表写入 JSON 文件
    try:
        with open(entities_output_filepath, 'w', encoding='utf-8') as f:
            json.dump(final_entities_list, f, ensure_ascii=False, indent=2)
        print(f"统一化实体列表已保存到 {entities_output_filepath}")
    except Exception as e:
        print(f"保存实体列表时发生错误: {e}")


    # --- 第二遍: 重构数据使用实体ID引用 ---
    print("\n第二遍: 重构数据使用实体ID引用...")
    try:
        with jsonlines.open(graph_data_output_filepath, 'w') as writer:
            for record in all_records: # 使用存储在内存中的记录

                # 重构 relations 列表
                original_triples = record.get("knowledge_triples", [])
                reconstructed_relations = []
                for triple in original_triples:
                    subject_text = triple.get("subject")
                    object_text = triple.get("object")
                    predicate_type = triple.get("predicate")

                    # 查找对应的实体ID
                    subject_info = entity_map.get(subject_text)
                    object_info = entity_map.get(object_text)

                    if subject_info and object_info and predicate_type:
                         reconstructed_relations.append({
                            # 实体间关系使用 head/tail ID 引用
                            "head": subject_info["id"],
                            "tail": object_info["id"],
                            "type": predicate_type
                         })
                    elif subject_text or object_text or predicate_type:
                         print(f"警告: 无法为三元组 {triple} 找到所有对应的实体ID，跳过该关系。")


                # 重构 events 列表
                original_events = record.get("events", [])
                reconstructed_events = []
                for event in original_events:
                    # 复制事件本身的信息
                    reconstructed_event = event.copy()
                    # 重构论元列表，添加 ref_entity_id
                    reconstructed_arguments = []
                    arguments = event.get("arguments", [])
                    for arg in arguments:
                        arg_text = arg.get("argument")
                        # 复制论元本身的信息
                        reconstructed_arg = arg.copy()

                        # 查找论元文本对应的实体ID
                        arg_entity_info = entity_map.get(arg_text)

                        if arg_entity_info:
                            # 如果论元文本在实体映射表中找到，添加实体ID引用
                            reconstructed_arg["ref_entity_id"] = arg_entity_info["id"]
                            # 注意：原始论元中没有位置信息，这里也无法添加。如果需要位置，需要在抽取或之前步骤中处理。
                        # else: 论元文本不在实体映射表中 (例如数字、普通名词、未抽全的实体)，不添加 ref_entity_id

                        reconstructed_arguments.append(reconstructed_arg)

                    reconstructed_event["arguments"] = reconstructed_arguments
                    reconstructed_events.append(reconstructed_event)


                # 构建重构后的记录
                reconstructed_record = {
                    "timestamp": record.get("timestamp"), # 保留时间戳
                    "text": record.get("text"),           # 保留原文
                    "relations": reconstructed_relations, # 使用重构后的关系列表 (包含实体间关系)
                    "events": reconstructed_events       # 使用重构后的事件列表 (论元可能包含实体ID引用)
                    # 注意：这里将 knowledge_triples 字段名改为了 relations
                }

                # 写入输出文件
                writer.write(reconstructed_record)

        print(f"\n图谱数据重构完成。")
        print(f"重构后的图谱数据保存在 {graph_data_output_filepath}")

    except FileNotFoundError:
        print(f"错误: 输入文件未找到 - {filtered_jsonl_filepath}")
    except Exception as e:
        print(f"重构数据时发生错误: {e}")


# --- 示例使用 (接在过滤代码的示例后面) ---
if __name__ == "__main__":
     # ... (过滤代码的示例部分) ...
     # filter_merged_data(MERGED_INPUT_FILE, FILTERED_OUTPUT_FILE)

     # --- 运行实体统一化和重构脚本 ---
     FILTERED_OUTPUT_FILE = "../prediction/filtered_merged_results.jsonl"
     ENTITIES_OUTPUT_FILE = "unified_entities.json"
     GRAPH_DATA_OUTPUT_FILE = "graph_data_with_ids.jsonl"

     # 确保 FILTERED_OUTPUT_FILE 是上一步过滤的输出文件
     consolidate_entities_simple(FILTERED_OUTPUT_FILE, ENTITIES_OUTPUT_FILE, GRAPH_DATA_OUTPUT_FILE)

     # --- 打印一部分最终重构后的图谱数据以供检查 ---
     if os.path.exists(GRAPH_DATA_OUTPUT_FILE):
          print(f"\n--- 最终重构后的图谱数据 (前 3 条) ---")
          try:
              with jsonlines.open(GRAPH_DATA_OUTPUT_FILE, 'r') as reader:
                  for i, obj in enumerate(reader):
                      print(json.dumps(obj, ensure_ascii=False, indent=2))
                      if i >= 2: # 只打印前3条
                          break
          except Exception as e:
              print(f"无法读取重构后的文件: {e}")

     # 打印生成的实体列表文件内容
     if os.path.exists(ENTITIES_OUTPUT_FILE):
          print(f"\n--- 统一化实体列表文件内容 ---")
          try:
              with open(ENTITIES_OUTPUT_FILE, 'r', encoding='utf-8') as f:
                  entities_content = json.load(f)
                  print(json.dumps(entities_content, ensure_ascii=False, indent=2))
          except Exception as e:
              print(f"无法读取实体列表文件: {e}")