import re # 导入正则表达式模块
import json
from collections import Counter

def parse_events(json_string):
    """
    解析 JSON 字符串为事件列表。
    处理可能的解析错误和数据格式问题。
    """
    try:
        events = json.loads(json_string)
        # 确保解析结果是列表
        if not isinstance(events, list):
            print(f"Warning: Expected a list of events, but got {type(events)}. Returning empty list.")
            return []
        # 验证每个元素是否是字典且包含必要的键
        valid_events = []
        for event in events:
            if isinstance(event, dict) and all(key in event for key in ["event_type", "trigger", "arguments"]):
                # 进一步验证 arguments 是列表
                if isinstance(event["arguments"], list):
                    valid_events.append(event)
                else:
                     print(f"Warning: Invalid event format found (arguments not a list): {event}. Skipping.")
            else:
                print(f"Warning: Invalid event format found: {event}. Skipping.")
        return valid_events
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON string: {json_string[:100]}... Error: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred while parsing events: {e}")
        return []

def normalize_text(text):
    """
    规范化文本：移除空格和标点，转小写。
    """
    if not isinstance(text, str):
        return ""
    # 移除空格和常见标点符号，保留中文、英文、数字
    text = re.sub(r'[^\w]+', '', text).lower()
    return text

def argument_to_comparable_form(argument):
    """
    将论元字典转换为可比较的形式（如元组）。
    在转换前对文本字段进行规范化。
    """
    if not isinstance(argument, dict):
        return None

    # 规范化角色和论元内容
    normalized_role = normalize_text(argument.get("role", ""))
    normalized_argument_content = normalize_text(argument.get("argument", ""))

    # 返回一个元组作为可比较形式
    return (normalized_role, normalized_argument_content)

def calculate_metrics_for_example_argument_based(predicted_events, labeled_events):
    """
    计算单个示例的论元级别的 TP, FP, FN。
    首先匹配事件类型和触发词，然后在匹配的事件对内计算论元指标。
    """
    total_arg_tp = 0
    total_arg_fp = 0
    total_arg_fn = 0

    # 将标签事件转换为可查找的结构，以便快速匹配
    # 使用 (normalized_event_type, normalized_trigger) 作为键
    labeled_event_map = {}
    for labeled_event in labeled_events:
        normalized_event_type = normalize_text(labeled_event.get("event_type", ""))
        normalized_trigger = normalize_text(labeled_event.get("trigger", ""))
        key = (normalized_event_type, normalized_trigger)
        if key not in labeled_event_map:
            labeled_event_map[key] = []
        labeled_event_map[key].append(labeled_event)

    # 标记已使用的标签事件，避免重复匹配
    used_labeled_events = set()

    # 遍历预测事件
    for predicted_event in predicted_events:
        normalized_pred_type = normalize_text(predicted_event.get("event_type", ""))
        normalized_pred_trigger = normalize_text(predicted_event.get("trigger", ""))
        pred_key = (normalized_pred_type, normalized_pred_trigger)

        # 查找匹配的标签事件
        matching_labeled_events = labeled_event_map.get(pred_key, [])

        # 找到一个未使用的匹配标签事件
        matched_labeled_event = None
        for labeled_evt in matching_labeled_events:
            # 创建一个唯一的标识符来检查是否已使用
            # 简单地使用事件对象本身作为标识符（Python对象的identity）
            if id(labeled_evt) not in used_labeled_events:
                 matched_labeled_event = labeled_evt
                 used_labeled_events.add(id(labeled_evt))
                 break # 找到第一个匹配且未使用的即可

        # 如果找到了匹配的标签事件
        if matched_labeled_event:
            # 将预测和标签的论元列表转换为规范化后的可比较形式的集合
            predicted_arg_set = {argument_to_comparable_form(arg) for arg in predicted_event.get("arguments", []) if argument_to_comparable_form(arg) is not None}
            labeled_arg_set = {argument_to_comparable_form(arg) for arg in matched_labeled_event.get("arguments", []) if argument_to_comparable_form(arg) is not None}

            # 计算当前匹配事件对内的论元 TP, FP, FN
            arg_tp_set = predicted_arg_set.intersection(labeled_arg_set)
            arg_tp = len(arg_tp_set)

            arg_fp_set = predicted_arg_set - labeled_arg_set
            arg_fp = len(arg_fp_set)

            arg_fn_set = labeled_arg_set - predicted_arg_set
            arg_fn = len(arg_fn_set)

            total_arg_tp += arg_tp
            total_arg_fp += arg_fp
            total_arg_fn += arg_fn

        else:
            # 如果没有找到匹配的标签事件，则预测事件的所有论元都是 FP
            predicted_arg_count = len([arg for arg in predicted_event.get("arguments", []) if argument_to_comparable_form(arg) is not None])
            total_arg_fp += predicted_arg_count

    # 遍历标签事件，计算未被匹配的事件的论元作为 FN
    for labeled_event in labeled_events:
         if id(labeled_event) not in used_labeled_events:
            # 如果标签事件没有被匹配，则其所有论元都是 FN
            labeled_arg_count = len([arg for arg in labeled_event.get("arguments", []) if argument_to_comparable_form(arg) is not None])
            total_arg_fn += labeled_arg_count


    return total_arg_tp, total_arg_fp, total_arg_fn

def calculate_overall_f1_argument_based(jsonl_filepath):
    """
    读取 JSONL 文件，计算总体的论元级别精确率、召回率和 F1 分数。
    """
    total_arg_tp = 0
    total_arg_fp = 0
    total_arg_fn = 0
    example_count = 0

    try:
        with open(jsonl_filepath, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    # 获取 prompt，虽然计算不需要，但可以用于调试
                    prompt = data.get("prompt", "")
                    # 获取 predict 和 label，默认空列表字符串
                    predict_json = data.get("predict", "[]")
                    label_json = data.get("label", "[]")

                    predicted_events = parse_events(predict_json)
                    labeled_events = parse_events(label_json)

                    arg_tp, arg_fp, arg_fn = calculate_metrics_for_example_argument_based(predicted_events, labeled_events)

                    total_arg_tp += arg_tp
                    total_arg_fp += arg_fp
                    total_arg_fn += arg_fn
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

    # 计算总体的论元级别精确率、召回率和 F1
    precision = total_arg_tp / (total_arg_tp + total_arg_fp) if (total_arg_tp + total_arg_fp) > 0 else 0
    recall = total_arg_tp / (total_arg_tp + total_arg_fn) if (total_arg_tp + total_arg_fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    return {
        "total_examples": example_count,
        "total_argument_tp": total_arg_tp,
        "total_argument_fp": total_arg_fp,
        "total_argument_fn": total_arg_fn,
        "argument_precision": precision,
        "argument_recall": recall,
        "argument_f1_score": f1
    }

# 示例用法：
# 假设您的 JSONL 文件名为 'event_results.jsonl'
# 您可以将您提供的示例数据保存到 'event_results.jsonl' 文件中
# 然后运行以下代码：

if __name__ == "__main__":
    # 请将 'event_results.jsonl' 替换为您实际的文件路径
    jsonl_file = '../dataset/EE/EE_eval_predictions.jsonl'
    results = calculate_overall_f1_argument_based(jsonl_file)

    if results:
        print("\n--- Overall Argument-based Metrics ---")
        print(f"Total Examples: {results['total_examples']}")
        print(f"Total Argument True Positives (TP): {results['total_argument_tp']}")
        print(f"Total Argument False Positives (FP): {results['total_argument_fp']}")
        print(f"Total Argument False Negatives (FN): {results['total_argument_fn']}")
        print(f"Argument Precision: {results['argument_precision']:.4f}")
        print(f"Argument Recall:    {results['argument_recall']:.4f}")
        print(f"Argument F1 Score:  {results['argument_f1_score']:.4f}")

