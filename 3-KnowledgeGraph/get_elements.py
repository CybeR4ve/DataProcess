import json
import jsonlines
import os

def get_actual_schema_elements(entities_file, graph_data_file):
    entity_types = set()
    relation_types = set() # 对应 entity-entity 关系类型 (predicate)
    event_types = set()    # 对应 Event 节点的 eventType 属性值
    argument_roles = set() # 对应 Event-Entity 关系类型 (argument role)

    # 从 entities.json 获取实体类型
    try:
        with open(entities_file, 'r', encoding='utf-8') as f:
            entities = json.load(f)
            for entity in entities:
                if 'type' in entity and entity['type']:
                    entity_types.add(entity['type'])
    except FileNotFoundError:
        print(f"警告: 实体文件未找到: {entities_file}")
    except Exception as e:
        print(f"读取实体文件时出错: {e}")


    # 从 graph_data.jsonl 获取关系类型、事件类型和论元角色
    try:
        with jsonlines.open(graph_data_file, 'r') as reader:
            for record in reader:
                # 获取实体间关系类型
                relations = record.get("relations", [])
                for rel in relations:
                    if 'type' in rel and rel['type']:
                        relation_types.add(rel['type'])

                # 获取事件类型和论元角色
                events = record.get("events", [])
                for event in events:
                    if 'event_type' in event and event['event_type']: # 这是 Event 节点的属性 eventType
                        event_types.add(event['event_type'])
                    arguments = event.get("arguments", [])
                    for arg in arguments:
                        if 'role' in arg and arg['role']:
                             argument_roles.add(arg['role'])

    except FileNotFoundError:
        print(f"警告: 图谱数据文件未找到: {graph_data_file}")
    except Exception as e:
        print(f"读取图谱数据文件时出错: {e}")

    return sorted(list(entity_types)), sorted(list(relation_types)), sorted(list(event_types)), sorted(list(argument_roles))

# --- 在您的导入或实体统一化脚本运行后执行 ---
if __name__ == "__main__":
    # 请确保这里的路径指向您生成好的文件
    ENTITIES_JSON_FILE = "cleaned_entities_by_freq.json" # 实体文件路径
    GRAPH_DATA_JSONL_FILE = "cleaned_graph_data_by_freq.jsonl" # 图谱数据文件路径

    actual_entity_types, actual_relation_types, actual_event_types, actual_argument_roles = get_actual_schema_elements(ENTITIES_JSON_FILE, GRAPH_DATA_JSONL_FILE)

    print("\n--- 实际图谱模式元素 ---")
    print("实体类型:", actual_entity_types)
    print("实体间关系类型 (谓语):", actual_relation_types)
    print("事件类型:", actual_event_types) # 这个应该与您固定的列表一致
    print("事件论元角色 (关系类型):", actual_argument_roles)

    # 您可以使用这些打印出来的列表来填充您的 Prompt