import re
import matplotlib.pyplot as plt
from pathlib import Path

log_path = Path("/home/bosideng/pi05_training_30k.log")
output_dir = Path("/home/bosideng/unitree_lerobot/unitree_lerobot/outputs/GrabAndPutDownToDifferentPos/pi05_training_30k")
output_dir.mkdir(parents=True, exist_ok=True)

steps = []
losses = []

# 正则：匹配 step: 后跟数字或数字+K
step_pattern = re.compile(r"step:(\d+K?)")
loss_pattern = re.compile(r"loss:([\d.]+)")

last_valid_step = None

with open(log_path, "r") as f:
    for line in f:
        step_match = step_pattern.search(line)
        loss_match = loss_pattern.search(line)
        if not (step_match and loss_match):
            continue

        step_str = step_match.group(1)
        # 转换 step
        if step_str.endswith("K"):
            try:
                step_val = int(step_str[:-1]) * 1000
            except ValueError:
                continue
        else:
            step_val = int(step_str)

        loss_val = float(loss_match.group(1))

        # 如果当前 step 值不大于上一个有效 step，则按步长 10 递增
        if last_valid_step is not None and step_val <= last_valid_step:
            step_val = last_valid_step + 10
        last_valid_step = step_val

        steps.append(step_val)
        losses.append(loss_val)

if not steps:
    print("未找到 loss 数据，请检查日志路径和格式。")
else:
    plt.figure(figsize=(10, 5))
    plt.plot(steps, losses, linewidth=1, alpha=0.7)
    plt.xlabel("Step")
    plt.ylabel("Loss")
    plt.title("Training Loss(PI 0.5)")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    save_path = output_dir / "loss_plot.png"
    plt.savefig(save_path, dpi=150)
    print(f"Loss 图已保存至: {save_path}")
    print(f"共提取 {len(steps)} 个数据点，最后一步 = {steps[-1]}")