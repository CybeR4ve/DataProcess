import json
import jsonlines
import os
from collections import Counter

def analyze_schema_frequency(entities_file: str, graph_data_file: str):
    """
    统计提取出的实体类型、关系类型、事件类型、论元角色的频率并按频率排序。

    Args:
        entities_file: 统一化实体列表JSON文件路径。
        graph_data_file: 使用实体ID引用重构后的图谱数据JSONL文件路径。
    """
    print(f"正在统计模式元素频率...")
    print(f"实体文件: {entities_file}")
    print(f"图谱数据文件: {graph_data_file}")

    # 初始化 Counter 对象
    entity_type_counts = Counter()
    relation_type_counts = Counter()
    event_type_counts = Counter()
    argument_role_counts = Counter()

    # --- 统计频率 ---
    # 从 entities.json 统计实体类型频率
    try:
        with open(entities_file, 'r', encoding='utf-8') as f:
            entities = json.load(f)
            for entity in entities:
                entity_type = entity.get('type')
                if entity_type: # 只统计非空类型
                    entity_type_counts[entity_type] += 1
        print(f"已统计 {len(entities)} 个实体的类型。")
    except FileNotFoundError:
        print(f"警告: 实体文件未找到: {entities_file}")
    except Exception as e:
        print(f"读取实体文件或统计实体类型时出错: {e}")

    # 从 graph_data.jsonl 统计关系类型、事件类型和论元角色频率
    try:
        with jsonlines.open(graph_data_file, 'r') as reader:
            record_count = 0
            for record in reader:
                record_count += 1
                # 统计实体间关系类型频率
                relations = record.get("relations", [])
                for rel in relations:
                    rel_type = rel.get("type")
                    if rel_type: # 只统计非空类型
                        relation_type_counts[rel_type] += 1

                # 统计事件类型频率
                events = record.get("events", [])
                for event in events:
                    # 注意这里查找的是 event_type (小写 t)，与清洗脚本中的修复一致
                    event_type = event.get("event_type")
                    if event_type: # 只统计非空类型
                        event_type_counts[event_type] += 1

                    # 统计论元角色频率
                    arguments = event.get("arguments", [])
                    for arg in arguments:
                        role = arg.get("role")
                        if role: # 只统计非空角色
                            argument_role_counts[role] += 1
            print(f"已处理 {record_count} 条记录，统计关系、事件和论元频率。")

    except FileNotFoundError:
        print(f"警告: 图谱数据文件未找到: {graph_data_file}")
    except Exception as e:
        print(f"读取图谱数据文件或统计关系/事件/论元时出错: {e}")

    # --- 按频率排序并打印结果 ---
    print("\n--- 模式元素频率统计结果 (按频率降序) ---")

    print("\n实体类型及其频率:")
    if entity_type_counts:
        for item, count in entity_type_counts.most_common():
            print(f"  '{item}': {count}")
    else:
        print("  (未统计到实体类型)")

    print("\n实体间关系类型 (谓语) 及其频率:")
    if relation_type_counts:
        for item, count in relation_type_counts.most_common():
            print(f"  '{item}': {count}")
    else:
         print("  (未统计到实体间关系类型)")

    print("\n事件类型 (eventType) 及其频率:")
    if event_type_counts:
        # 根据您之前提供的固定事件类型列表，这里应该包含那些类型及其频率
        for item, count in event_type_counts.most_common():
            print(f"  '{item}': {count}")
    else:
        print("  (未统计到事件类型)")


    print("\n事件论元角色 (关系类型) 及其频率:")
    if argument_role_counts:
        for item, count in argument_role_counts.most_common():
            print(f"  '{item}': {count}")
    else:
        print("  (未统计到事件论元角色)")

    print("\n--- 统计完成 ---")


# --- 示例使用 ---
if __name__ == "__main__":
    # 确保这些文件是您运行实体统一化脚本后的输出文件
    ENTITIES_JSON_FILE = "cleaned_entities_by_freq.json"
    GRAPH_DATA_JSONL_FILE = "cleaned_graph_data_by_freq.jsonl"

    # 运行频率统计脚本
    analyze_schema_frequency(ENTITIES_JSON_FILE, GRAPH_DATA_JSONL_FILE)