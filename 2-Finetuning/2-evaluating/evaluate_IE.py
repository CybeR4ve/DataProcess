import re # 导入正则表达式模块
import json
from collections import Counter

def parse_triples(json_string):
    """
    解析 JSON 字符串为三元组列表。
    处理可能的解析错误和数据格式问题。
    """
    try:
        triples = json.loads(json_string)
        # 确保解析结果是列表
        if not isinstance(triples, list):
            print(f"Warning: Expected a list of triples, but got {type(triples)}. Returning empty list.")
            return []
        # 验证每个元素是否是字典且包含必要的键
        valid_triples = []
        for triple in triples:
            if isinstance(triple, dict) and all(key in triple for key in ["subject", "subject_type", "predicate", "object", "object_type"]):
                valid_triples.append(triple)
            else:
                print(f"Warning: Invalid triple format found: {triple}. Skipping.")
        return valid_triples
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON string: {json_string[:100]}... Error: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred while parsing triples: {e}")
        return []

def normalize_text(text):
    """
    规范化文本：移除空格和标点，转小写。
    """
    if not isinstance(text, str):
        return ""
    # 移除空格和常见标点符号
    text = re.sub(r'[\s\W]+', '', text).lower()
    return text

def triple_to_comparable_form(triple):
    """
    将三元组字典转换为可比较的形式（如元组），用于集合操作。
    在转换前对文本字段进行规范化。
    使用 frozenset 是为了处理字典内部键值对顺序不定的情况。
    """
    if not isinstance(triple, dict):
        return None

    # 对文本字段进行规范化
    normalized_triple = {
        "subject": normalize_text(triple.get("subject", "")),
        "subject_type": triple.get("subject_type", ""),
        "predicate": normalize_text(triple.get("predicate", "")),
        "object": normalize_text(triple.get("object", "")),
        "object_type": triple.get("object_type", "")
    }

    # 将规范化后的字典转换为 frozenset
    return frozenset(normalized_triple.items())


def calculate_metrics_for_example(predicted_triples, labeled_triples):
    """
    计算单个示例的 TP, FP, FN。
    使用规范化后的三元组进行匹配。
    """
    # 将预测和标签三元组转换为规范化后的可比较形式的集合
    predicted_set = {triple_to_comparable_form(t) for t in predicted_triples if triple_to_comparable_form(t) is not None}
    labeled_set = {triple_to_comparable_form(t) for t in labeled_triples if triple_to_comparable_form(t) is not None}

    # 计算真阳性 (TP): 预测和标签中都存在的
    tp_set = predicted_set.intersection(labeled_set)
    tp = len(tp_set)

    # 计算假阳性 (FP): 预测中有，但标签中没有的
    fp_set = predicted_set - labeled_set
    fp = len(fp_set)

    # 计算假阴性 (FN): 标签中有，但预测中没有的
    fn_set = labeled_set - predicted_set
    fn = len(fn_set)

    return tp, fp, fn

def calculate_overall_f1(jsonl_filepath):
    """
    读取 JSONL 文件，计算总体的精确率、召回率和 F1 分数。
    """
    total_tp = 0
    total_fp = 0
    total_fn = 0
    example_count = 0

    try:
        with open(jsonl_filepath, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    prompt = data.get("prompt", "") # 获取 prompt，虽然计算不需要，但可以用于调试
                    predict_json = data.get("predict", "[]") # 默认空列表字符串
                    label_json = data.get("label", "[]")     # 默认空列表字符串

                    predicted_triples = parse_triples(predict_json)
                    labeled_triples = parse_triples(label_json)

                    tp, fp, fn = calculate_metrics_for_example(predicted_triples, labeled_triples)

                    total_tp += tp
                    total_fp += fp
                    total_fn += fn
                    example_count += 1

                except json.JSONDecodeError as e:
                    print(f"Skipping line due to JSON parsing error: {line[:100]}... Error: {e}")
                except Exception as e:
                    print(f"Skipping line due to unexpected error: {e}")


    except FileNotFoundError:
        print(f"Error: File not found at {jsonl_filepath}")
        return None
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        return None

    # 计算总体的精确率、召回率和 F1
    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    return {
        "total_examples": example_count,
        "total_tp": total_tp,
        "total_fp": total_fp,
        "total_fn": total_fn,
        "precision": precision,
        "recall": recall,
        "f1_score": f1
    }

# 示例用法：
# 假设您的 JSONL 文件名为 'data.jsonl'
# 您可以将您提供的示例数据保存到 'data.jsonl' 文件中
# 然后运行以下代码：

if __name__ == "__main__":
    jsonl_file = '../dataset/SPO/IE_eval_predictions.jsonl' # 替换为您的文件路径
    results = calculate_overall_f1(jsonl_file)

if results:
    print("\n--- Overall Metrics ---")
    print(f"Total Examples: {results['total_examples']}")
    print(f"Total True Positives (TP): {results['total_tp']}")
    print(f"Total False Positives (FP): {results['total_fp']}")
    print(f"Total False Negatives (FN): {results['total_fn']}")
    print(f"Precision: {results['precision']:.4f}")
    print(f"Recall:    {results['recall']:.4f}")
    print(f"F1 Score:  {results['f1_score']:.4f}")
