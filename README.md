# 金融新闻知识图谱构建系统

该项目是一个完整的金融新闻知识图谱构建系统，从新闻数据爬取到知识图谱的最终生成。整个流程分为三个主要阶段：数据爬取、模型微调预测，以及知识图谱构建。

## 项目结构

```
|-- 1-Crawler/                    # 数据爬取阶段
|   |-- crawler.py                # 新浪财经新闻爬虫
|   |-- sina_data.csv             # 爬取的新闻数据
|
|-- 2-Finetuning/                 # 模型微调与预测阶段
|   |-- 1-dataset/                # 数据集处理
|   |   |-- SPO/                  # 知识三元组数据集
|   |   |-- EE/                   # 事件抽取数据集
|   |   |-- trim_json.py          # JSON文件修剪工具
|   |   |-- count_json_objects.py # JSON对象计数工具
|   |
|   |-- 2-evaluating/             # 模型评估
|   |   |-- evaluate_IE.py        # 信息抽取评估
|   |   |-- evaluate_EE.py        # 事件抽取评估
|   |
|   |-- 3-prediction/             # 模型预测结果处理
|   |   |-- merge.py              # 合并预测结果
|   |   |-- filter_merged_data.py # 过滤合并数据
|   |   |-- convert/              # 结果转换工具
|   |   |-- ie_predictions.jsonl  # 信息抽取预测结果
|   |   |-- ee_predictions.jsonl  # 事件抽取预测结果
|   |   |-- merged_results.jsonl  # 合并后的结果
|   |   |-- filtered_merged_results.jsonl # 过滤后的结果
|   |
|   |-- 4-consolidating/          # 数据整合
|   |   |-- consolidating.py      # 实体统一与重构
|   |   |-- clean_extra_data.py   # 额外数据清理
|   |   |-- unified_entities.json # 统一化的实体列表
|   |   |-- graph_data_with_ids.jsonl # 使用ID引用的图谱数据
|   |
|   |-- logs/                     # 训练和评估日志
|
|-- 3-KnowledgeGraph/             # 知识图谱构建阶段
|   |-- import.py                 # Neo4j导入脚本
|   |-- get_elements.py           # 图谱元素获取
|   |-- get_frequency.py          # 实体频率统计
|   |-- cleaned_entities_by_freq.json    # 频率过滤后的实体
|   |-- cleaned_graph_data_by_freq.jsonl # 频率过滤后的图谱数据
```

## 项目流程

### 1. 数据爬取阶段 (1-Crawler)

- **crawler.py**: 爬取新浪财经7x24小时新闻数据
  - 使用HTTP请求获取新浪财经新闻数据
  - 解析JSON响应，提取新闻内容和发布时间
  - 将数据保存到CSV文件中
  - 支持断点续爬和增量爬取

### 2. 模型微调与预测阶段 (2-Finetuning)

#### 2.1 数据集处理 (1-dataset)
- 处理和准备用于模型微调的数据集
- **trim_json.py**: 裁剪大型JSON文件为训练需要的大小
- **count_json_objects.py**: 统计JSON文件中的对象数量
- 包含两类数据集：
  - SPO目录: 知识三元组抽取数据集(主语-谓语-宾语)
  - EE目录: 事件抽取数据集

#### 2.2 模型评估 (2-evaluating)
- **evaluate_IE.py**: 评估信息抽取模型性能
- **evaluate_EE.py**: 评估事件抽取模型性能

#### 2.3 预测结果处理 (3-prediction)
- **merge.py**: 合并信息抽取和事件抽取的预测结果
  - 读取原始CSV文件中的文本和时间戳
  - 读取知识三元组和事件抽取预测结果
  - 按行合并结果并输出到新的JSONL文件
- **filter_merged_data.py**: 过滤和清洗合并后的数据
- 存储预测结果:
  - ie_predictions.jsonl: 信息抽取预测结果
  - ee_predictions.jsonl: 事件抽取预测结果
  - merged_results.jsonl: 合并后的结果
  - filtered_merged_results.jsonl: 过滤后的结果

#### 2.4 数据整合 (4-consolidating)
- **consolidating.py**: 
  - 统一化实体标识
  - 构建实体映射表
  - 重构数据使用实体ID引用
  - 输出最终的实体列表和图谱数据
- **clean_extra_data.py**: 清理额外数据和过滤低频实体
- 输出结果:
  - unified_entities.json: 统一化的实体列表
  - graph_data_with_ids.jsonl: 使用ID引用的图谱数据

### 3. 知识图谱构建阶段 (3-KnowledgeGraph)

- **get_frequency.py**: 统计实体和关系的频率
- **get_elements.py**: 从图谱数据中提取元素
- **import.py**: 
  - 将处理后的数据导入Neo4j图数据库
  - 创建实体节点和关系
  - 构建事件节点及其与实体的关系
  - 设置数据库约束和索引
- 最终数据:
  - cleaned_entities_by_freq.json: 频率过滤后的实体列表
  - cleaned_graph_data_by_freq.jsonl: 频率过滤后的图谱数据

## 使用方法

1. **爬取数据**:
   ```
   cd 1-Crawler
   python crawler.py
   ```

2. **处理数据集**:
   ```
   cd 2-Finetuning/1-dataset
   python trim_json.py
   ```

3. **模型预测结果合并**:
   ```
   cd 2-Finetuning/3-prediction
   python merge.py
   ```

4. **实体统一化与重构**:
   ```
   cd 2-Finetuning/4-consolidating
   python consolidating.py
   ```

5. **导入Neo4j数据库**:
   ```
   cd 3-KnowledgeGraph
   python import.py
   ```

## 技术栈

- Python 3.6+
- Neo4j图数据库
- 依赖库: requests, jsonlines, neo4j-driver, csv, json

## 注意事项

- 确保Neo4j数据库已安装并运行
- 默认Neo4j连接配置: bolt://localhost:7687，用户名neo4j，密码12345678
- 大型数据文件如sina_data.csv不包含在代码仓库中 