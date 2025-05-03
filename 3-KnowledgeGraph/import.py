from neo4j import GraphDatabase, basic_auth
import json
import jsonlines
import os

# --- Neo4j 连接配置 ---
URI = "bolt://localhost:7687" # Neo4j 数据库的 URI
AUTH = basic_auth("neo4j", "12345678") # 替换为您的 Neo4j 用户名和密码

# --- 数据文件路径 ---
ENTITIES_FILE = "unified_entities.json" # 统一化实体列表文件
GRAPH_DATA_FILE = "graph_data_with_ids.jsonl" # 重构后的图谱数据文件

# --- 清空数据库函数 ---
def clear_database(tx):
    """清空Neo4j数据库中的所有节点和关系"""
    query = "MATCH (n) DETACH DELETE n"
    tx.run(query)
    print("数据库已清空。")

# --- Neo4j 操作函数 ---
def add_entity_node(tx, entity):
    """在Neo4j中创建或匹配实体节点"""
    # 使用 MERGE 来确保即使脚本运行多次，同一个实体ID也只创建一个节点
    # entityId 作为唯一标识非常重要，通常会为其创建索引
    query = """
    MERGE (n:Entity {entityId: $entityId})
    SET n.name = $name, n.type = $type
    """
    # 如果实体类型作为标签，则可以在 MERGE 中添加标签
    # query = """
    # MERGE (n:Entity:`""" + entity.get('type', 'Unknown') + """` {entityId: $entityId})
    # SET n.name = $name // 如果类型作为标签，这里可以不存 type 属性
    # """
    # 注意：动态标签不直接支持 $参数，需要拼接字符串，注意注入风险或使用 APOC

    tx.run(query, entityId=entity.get('id'), name=entity.get('text'), type=entity.get('type')) # 使用参数化查询

def add_relation(tx, relation):
    """在Neo4j中创建实体间关系"""
    query = """
    MATCH (h:Entity {entityId: $headId})
    MATCH (t:Entity {entityId: $tailId})
    MERGE (h)-[r:`""" + relation.get('type', 'UNKNOWN_REL') + """`]->(t)
    // 如果关系有属性，可以在这里 SET r.property = $property
    """
    # 动态关系类型也需要拼接字符串，注意注入风险或使用 APOC
    tx.run(query, headId=relation.get('head'), tailId=relation.get('tail'))

def add_event_and_relations(tx, record):
    """在Neo4j中创建事件节点及其与实体的关系"""
    timestamp = record.get("timestamp")
    original_text = record.get("text")
    events = record.get("events", []) # 获取事件列表

    # 为事件节点生成一个唯一ID的前缀或基础（实际应用中可能需要更健壮的ID策略）
    # 这里可以考虑使用 record 的某种标识 + 索引作为 eventId 的一部分

    for i, event in enumerate(events):
        # --- 第一个检查：确保 event 是字典 ---
        if not isinstance(event, dict):
            print(f"警告: 记录 (时间戳: {record.get('timestamp')}, 前100字: {record.get('text', '')[:100]}) 中事件列表包含非字典项 (索引 {i})，类型为 {type(event)}，内容: {event}。跳过该项。")
            continue
        # --- 结束第一个检查 ---

        event_type = event.get("event_type", "UnknownEvent")

        # --- 处理 trigger 字段 ---
        trigger_raw_value = event.get("trigger", None) # 获取 trigger 字段的原始值，如果不存在则为 None
        trigger_text = "" # 默认为空字符串

        if isinstance(trigger_raw_value, dict):
            # 如果 trigger 字段的值是字典 (即期望的 {"text": "..."} 格式)
            trigger_text = trigger_raw_value.get("text", "")
            # print(f"信息: 记录 (...) 中事件 (...) 成功处理字典格式的 trigger。") # 导入顺利后可注释掉这类信息

        elif trigger_raw_value is not None:
            # 如果 trigger 字段的值不是 None 且不是字典 (即它是字符串、数字等)
            # 这覆盖了模型输出 "trigger": "字符串" 的情况
            trigger_text = str(trigger_raw_value) # 将其转换为字符串作为触发词文本
            # print(f"信息: 记录 (...) 中事件 (...) 成功处理非字典格式的 trigger，内容: {trigger_raw_value}。") # 导入顺利后可注释掉这类信息

        # else: trigger_raw_value 是 None, trigger_text 保持为 ""

        # 之前那个总是出现的警告可以删掉了，因为我们现在正确处理了字符串格式
        # print(f"警告: 记录 (...) 中事件 (...) 的 'trigger' 字段不是字典...") # <-- 删除或注释掉这行


        # 为事件节点生成一个唯一ID
        import uuid # 确保 uuid 库已导入
        event_node_id = f"event_{uuid.uuid4()}"

        # 创建事件节点 (使用获取到的 trigger_text)
        query_event_node = """
        MERGE (e:Event {eventId: $eventId})
        SET e.eventType = $eventType, e.timestampStr = $timestamp, e.triggerText = $triggerText, e.originalText = $originalText
        """

        tx.run(query_event_node, eventId=event_node_id, eventType=event_type, timestamp=timestamp, triggerText=trigger_text, originalText=original_text)

        # --- 创建事件与实体的关系 (论元)，这里保持不变，因为它处理的是 arguments 列表 ---
        arguments = event.get("arguments", [])
        for arg in arguments:
             # --- 第二个检查：确保论元项是字典 ---
            if not isinstance(arg, dict):
                print(f"警告: 记录 (时间戳: {record.get('timestamp')}, 事件ID: {event_node_id}) 的论元列表包含非字典项，内容: {arg}。跳过该项。")
                continue
            # --- 结束第三个检查 ---
            # ... (处理论元，查找 ref_entity_id，创建关系的代码保持不变) ...
            role = arg.get("role", "UnknownRole")
            ref_entity_id = arg.get("ref_entity_id")
            arg_text = arg.get("argument", "")

            if ref_entity_id:
                 query_create_arg_rel = """
                MATCH (e:Event {eventId: $eventId})
                MATCH (p:Entity {entityId: $entityId})
                MERGE (e)-[r:`""" + role + """`]->(p)
                SET r.argumentText = $argumentText
                """
                 try:
                    tx.run(query_create_arg_rel, eventId=event_node_id, entityId=ref_entity_id, argumentText=arg_text)
                 except Exception as rel_e:
                    print(f"错误: 记录 (时间戳: {record.get('timestamp')}, 事件ID: {event_node_id}) 为论元 {arg_text} (ID: {ref_entity_id}) 创建关系时出错: {rel_e}")



# --- 主导入函数 ---
def import_data_to_neo4j(uri, auth, entities_file, graph_data_file, clear_db=False):
    driver = None
    try:
        # 连接到 Neo4j 数据库
        driver = GraphDatabase.driver(uri, auth=auth)
        driver.verify_connectivity()
        print("成功连接到 Neo4j 数据库。")

        # 如果需要，清空数据库
        if clear_db:
            with driver.session() as session:
                session.execute_write(clear_database)

        # 步骤 1: 创建 Entity 节点的唯一性约束 (强烈推荐在导入前做)
        # 如果 Entity 标签不存在，MERGE 会创建它
        with driver.session() as session:
            session.execute_write(lambda tx: tx.run("CREATE CONSTRAINT IF NOT EXISTS for (n:Entity) REQUIRE n.entityId IS UNIQUE"))
            session.execute_write(lambda tx: tx.run("CREATE INDEX IF NOT EXISTS for (n:Entity) ON (n.name)")) # 可选：为 name 创建索引以加速查询

        # 步骤 2: 导入 Entity 节点
        print("\n开始导入实体节点...")
        with open(entities_file, 'r', encoding='utf-8') as f:
            entities = json.load(f)
            with driver.session() as session:
                # 分批导入以提高效率
                batch_size = 1000
                for i in range(0, len(entities), batch_size):
                    batch = entities[i:i+batch_size]
                    session.execute_write(lambda tx: [add_entity_node(tx, entity) for entity in batch])
                    print(f"已导入 {min(i + batch_size, len(entities))} / {len(entities)} 个实体节点。")
        print("实体节点导入完成。")


        # 步骤 3: 导入关系和事件
        print("\n开始导入关系和事件...")
        with jsonlines.open(graph_data_file, 'r') as reader:
            # 分批导入记录，每批处理多个记录中的关系和事件
            batch_size = 50 # 每批处理的记录数
            record_batch = []
            record_count = 0

            with driver.session() as session:
                for record in reader:
                    record_batch.append(record)
                    record_count += 1

                    if len(record_batch) >= batch_size:
                        # 处理当前批次
                        for rec in record_batch:
                            session.execute_write(lambda tx: [add_relation(tx, rel) for rel in rec.get("relations", [])])
                            session.execute_write(lambda tx: add_event_and_relations(tx, rec)) # 事件是每条记录独立处理
                        record_batch = [] # 清空批次
                        print(f"已处理 {record_count} 条记录...")

                # 处理最后一批剩余的记录
                if record_batch:
                     for rec in record_batch:
                        session.execute_write(lambda tx: [add_relation(tx, rel) for rel in rec.get("relations", [])])
                        session.execute_write(lambda tx: add_event_and_relations(tx, rec))
                     print(f"已处理 {record_count} 条记录 (完成)。")

        print("关系和事件导入完成。")

    except FileNotFoundError:
        print("错误: 数据文件未找到。请检查路径是否正确。")
    except Exception as e:
        print(f"导入数据时发生错误: {e}")
        if driver:
            driver.close()
            print("数据库连接已关闭。")
        raise # 重新抛出异常以便调试

    finally:
        if driver:
            driver.close()
            print("数据库连接已关闭。")

# --- 示例运行导入脚本 ---
if __name__ == "__main__":
    # 请将这些文件路径替换为您实际生成的文件路径
    ENTITIES_JSON_FILE = "cleaned_entities_by_freq.json"
    GRAPH_DATA_JSONL_FILE = "cleaned_graph_data_by_freq.jsonl"

    # 请确保 Neo4j 数据库正在运行，并且您已经创建了用户和设置了密码
    # 如果您修改了默认的 URI 或认证信息，请更新上面的 URI 和 AUTH 变量

    # 创建模拟数据文件 (如果不存在) 用于测试脚本
    if not os.path.exists(ENTITIES_JSON_FILE) or not os.path.exists(GRAPH_DATA_JSONL_FILE):
         print("\n请先运行合并和实体统一化脚本生成数据文件。")
         print(f"预期文件: {ENTITIES_JSON_FILE}, {GRAPH_DATA_JSONL_FILE}")
    else:
         # 设置 clear_db=True 将在导入前清空数据库
         import_data_to_neo4j(URI, AUTH, ENTITIES_JSON_FILE, GRAPH_DATA_JSONL_FILE, clear_db=True)