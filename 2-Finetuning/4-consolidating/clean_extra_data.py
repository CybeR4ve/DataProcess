import json
import jsonlines
import os
from collections import Counter

# --- Configuration ---
FREQUENCY_THRESHOLD = 100 # You can change this value

# --- Cleaning Function ---
def clean_data_by_frequency(entities_input_filepath: str, graph_data_input_filepath: str, cleaned_entities_output_filepath: str, cleaned_graph_data_output_filepath: str, threshold: int = FREQUENCY_THRESHOLD):
    """
    根据元素在数据中出现的频率，过滤掉低频的实体类型、关系、事件和论元角色。

    Args:
        entities_input_filepath: 统一化实体列表输入JSON文件路径。
        graph_data_input_filepath: 使用实体ID引用重构后的图谱数据输入JSONL文件路径。
        cleaned_entities_output_filepath: 清洗后实体列表输出JSON文件路径。
        cleaned_graph_data_output_filepath: 清洗后图谱数据输出JSONL文件路径。
        threshold: 频率阈值。低于此频率的元素将被过滤。
    """
    print(f"正在根据频率阈值 ({threshold}) 清洗数据...")
    print(f"实体输入文件: {entities_input_filepath}")
    print(f"图谱数据输入文件: {graph_data_input_filepath}")
    print(f"清洗后实体输出: {cleaned_entities_output_filepath}")
    print(f"清洗后图谱数据输出: {cleaned_graph_data_output_filepath}")

    # --- Step 1: Calculate Frequencies ---
    print("\nStep 1: 统计模式元素频率...")
    entity_type_counts = Counter()
    relation_type_counts = Counter()
    event_type_counts = Counter()
    argument_role_counts = Counter()
    all_records_for_second_pass = [] # Store records for the second pass

    try:
        with open(entities_input_filepath, 'r', encoding='utf-8') as f:
            entities = json.load(f)
            for entity in entities:
                entity_type = entity.get('type')
                if entity_type:
                    entity_type_counts[entity_type] += 1

        with jsonlines.open(graph_data_input_filepath, 'r') as reader:
            for record in reader:
                all_records_for_second_pass.append(record) # Store record

                relations = record.get("relations", [])
                for rel in relations:
                    rel_type = rel.get("type")
                    if rel_type:
                        relation_type_counts[rel_type] += 1

                events = record.get("events", [])
                for event in events:
                    # Use 'event_type' (lowercase t) based on previous fix/discussion
                    event_type = event.get("event_type")
                    if event_type:
                        event_type_counts[event_type] += 1

                    arguments = event.get("arguments", [])
                    for arg in arguments:
                        role = arg.get("role")
                        if role:
                            argument_role_counts[role] += 1

    except FileNotFoundError as e:
        print(f"错误: 输入文件未找到 - {e}")
        return
    except Exception as e:
        print(f"统计频率时发生错误: {e}")
        return

    # --- Step 2: Define Frequency-Based Whitelists ---
    print("\nStep 2: 定义频率白名单...")
    valid_entity_types = {item for item, count in entity_type_counts.items() if count >= threshold}
    valid_relation_types = {item for item, count in relation_type_counts.items() if count >= threshold}
    valid_event_types = {item for item, count in event_type_counts.items() if count >= threshold}
    valid_argument_roles = {item for item, count in argument_role_counts.items() if count >= threshold}

    print(f"基于阈值 {threshold}，确定的有效模式元素数量:")
    print(f"  实体类型: {len(valid_entity_types)}")
    print(f"  关系类型: {len(valid_relation_types)}")
    print(f"  事件类型: {len(valid_event_types)}")
    print(f"  论元角色: {len(valid_argument_roles)}")

    # --- Step 3: Clean Entities based on Type Whitelist ---
    print("\nStep 3: 清洗实体...")
    valid_entity_ids = set()
    cleaned_entities_list = []
    # Re-load entities file or use the 'entities' variable from Step 1 if held in memory
    # Assuming entities list from Step 1 is small enough to hold in memory
    try:
        with open(entities_input_filepath, 'r', encoding='utf-8') as f:
             entities = json.load(f) # Re-load just in case Step 1 didn't store it

        for entity in entities:
            if entity.get('type') in valid_entity_types:
                cleaned_entities_list.append(entity)
                valid_entity_ids.add(entity.get('id')) # Collect IDs of valid entities

        with open(cleaned_entities_output_filepath, 'w', encoding='utf-8') as f:
            json.dump(cleaned_entities_list, f, ensure_ascii=False, indent=2)

        print(f"实体清洗完成。保留 {len(cleaned_entities_list)} / {len(entities)} 个实体。")
        print(f"清洗后实体列表已保存到 {cleaned_entities_output_filepath}")

    except FileNotFoundError:
        print(f"错误: 实体输入文件未找到 (二次读取) - {entities_input_filepath}")
        return
    except Exception as e:
        print(f"清洗实体时发生错误 (二次处理): {e}")
        return


    # --- Step 4: Clean Graph Data (Relations and Events) based on Whitelists and valid Entity IDs ---
    print("\nStep 4: 清洗关系和事件...")
    cleaned_record_count = 0

    try:
        with jsonlines.open(cleaned_graph_data_output_filepath, 'w') as writer:
            for record in all_records_for_second_pass: # Use records stored from Step 1

                original_relations = record.get("relations", [])
                cleaned_relations = []
                for rel in original_relations:
                    # Keep relation only if its type is valid AND head/tail entities are valid
                    rel_type = rel.get("type")
                    head_id = rel.get("head")
                    tail_id = rel.get("tail")

                    if rel_type in valid_relation_types and head_id in valid_entity_ids and tail_id in valid_entity_ids:
                        cleaned_relations.append(rel)

                original_events = record.get("events", [])
                cleaned_events = []
                for event in original_events:
                    # Use 'event_type' (lowercase t)
                    event_type = event.get("event_type")

                    if event_type in valid_event_types: # Keep event only if its eventType is valid
                        cleaned_arguments = []
                        arguments = event.get("arguments", [])
                        for arg in arguments:
                            # Keep argument only if its role is valid AND the referenced entity is valid (if linked)
                            role = arg.get("role")
                            ref_entity_id = arg.get("ref_entity_id")

                            if role in valid_argument_roles:
                                 # If argument is linked to an entity, check if that entity is valid
                                 if ref_entity_id is not None:
                                      if ref_entity_id in valid_entity_ids:
                                           cleaned_arguments.append(arg)
                                 else:
                                      # If argument is NOT linked to an entity, keep it if its role is valid
                                      cleaned_arguments.append(arg) # Keep unlinked argument with valid role

                        # Add cleaned arguments to the event
                        cleaned_event = event.copy() # Preserve original event properties
                        cleaned_event["arguments"] = cleaned_arguments
                        cleaned_events.append(cleaned_event)


                # Write the cleaned record structure
                cleaned_record = {
                    "timestamp": record.get("timestamp"),
                    "text": record.get("text"),
                    "relations": cleaned_relations,
                    "events": cleaned_events
                }
                writer.write(cleaned_record)
                cleaned_record_count += 1


        print(f"关系和事件清洗完成。处理 {cleaned_record_count} 条记录。")
        print(f"清洗后图谱数据已保存到 {cleaned_graph_data_output_filepath}")


    except FileNotFoundError:
        print(f"错误: 图谱数据输入文件未找到 (二次读取) - {graph_data_input_filepath}")
        return
    except Exception as e:
        print(f"清洗关系或事件时发生错误 (二次处理): {e}")
        return

print(f"\n数据清洗流程结束。阈值: {FREQUENCY_THRESHOLD}")

if __name__ == "__main__":
# 确保这些文件是您运行实体统一化脚本后的输出文件
    ENTITIES_INPUT = "unified_entities.json"
    GRAPH_DATA_INPUT = "graph_data_with_ids.jsonl"
# 设置清洗后的输出文件路径
    CLEANED_ENTITIES_OUTPUT = "cleaned_entities_by_freq.json"
    CLEANED_GRAPH_DATA_OUTPUT = "cleaned_graph_data_by_freq.jsonl"
# 设置频率阈值 (例如，100)
    CLEANING_THRESHOLD = 100
# 运行清洗脚本
    clean_data_by_frequency(ENTITIES_INPUT, GRAPH_DATA_INPUT, CLEANED_ENTITIES_OUTPUT, CLEANED_GRAPH_DATA_OUTPUT, threshold=CLEANING_THRESHOLD)
