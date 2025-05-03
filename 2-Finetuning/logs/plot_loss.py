import json
import matplotlib.pyplot as plt

# 读取日志文件
train_losses = []
eval_losses = []
train_steps = []
eval_steps = []

with open('ee/trainer_log_ee_all_1.jsonl', 'r') as f:
    for line in f:
        data = json.loads(line)
        if 'loss' in data and 'eval_loss' not in data:
            train_losses.append(data['loss'])
            train_steps.append(data['current_steps'])
        elif 'eval_loss' in data:
            eval_losses.append(data['eval_loss'])
            eval_steps.append(data['current_steps'])

# 创建图表
plt.figure(figsize=(10, 6))
plt.plot(train_steps, train_losses, label='Training Loss', color='blue', alpha=0.6)
plt.plot(eval_steps, eval_losses, label='Validation Loss', color='red', marker='o')

plt.xlabel('Steps')
plt.ylabel('Loss')
plt.title('Training and Validation Loss')
plt.legend()
plt.grid(True)

# 保存图表
plt.savefig('loss_curves1.png')
plt.close() 