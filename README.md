# unitree_lerobot for H2

这是一个基于宇树官方
[unitree_lerobot](https://github.com/unitreerobotics/unitree_lerobot)
项目改造的版本。

本项目保留官方项目原有的数据转换、LeRobot 训练、策略评估、仿真验证、
数据集回放以及多种灵巧手支持，同时增加了对 **Unitree H2 人形机器人**
的适配，重点支持 H2 双臂和 BrainCo 五指灵巧手。

> 本仓库只发布代码、配置、机器人模型资源和部署文档，不包含训练数据、
> 模型权重、checkpoint 或运行日志。使用者需要准备自己的数据集和策略模型。

## 功能概览

- Unitree 数据采集结果转换为 LeRobot 数据集
- ACT、Diffusion、Pi0/Pi05、GR00T 等策略的训练入口
- G1 原有的真机、仿真、离线评估和数据回放功能
- H2 双臂 DDS 控制器和 Pinocchio/CasADi IK 求解器
- H2 URDF 与网格资源
- H2 + BrainCo、Unitree、Inspire 等末端执行器接口
- H2 真机评估、仿真评估和离线策略评估
- H2 DDS 通信诊断脚本

## 目录说明

```text
unitree_lerobot/
├── lerobot/                         # LeRobot 子模块，训练框架
├── unitree_lerobot/
│   ├── eval_robot/                  # 真机/仿真评估与机器人控制
│   │   ├── assets/h2/               # H2 URDF 和 meshes
│   │   ├── eval_h2.py               # H2 真机策略评估
│   │   ├── eval_h2_sim.py           # H2 仿真策略评估
│   │   ├── eval_h2_dataset.py       # H2 离线数据集评估
│   │   └── robot_control/           # 手臂、IK、灵巧手控制器
│   └── utils/                       # 数据转换和公共工具
├── test/                            # DDS 和功能诊断脚本
├── H2_ADAPTATION_SUMMARY.md         # H2 适配细节
└── 使用说明.md                       # 本地部署运维说明
```

## 安装环境

推荐 Ubuntu 22.04、Python 3.10 和 Conda：

```bash
git clone --recurse-submodules \
  https://github.com/SunYuanJie2002/unitree_lerobot_for_H2_BSD.git
cd unitree_lerobot_for_H2_BSD

conda create -y -n unitree_lerobot python=3.10
conda activate unitree_lerobot

conda install -y pinocchio -c conda-forge
conda install -y ffmpeg=7.1.1 -c conda-forge

cd lerobot
pip install -e .
cd ..
pip install -e .
```

安装 Unitree DDS Python SDK：

```bash
git clone https://github.com/unitreerobotics/unitree_sdk2_python.git
cd unitree_sdk2_python
pip install -e .
pip install cyclonedds
cd ..
```

如果仓库已经下载但子模块为空：

```bash
git submodule update --init --recursive
```

## 数据转换和训练

本项目不提供数据集。可以使用自己的 Unitree/遥操作数据，按照
`utils/convert_unitree_json_to_lerobot.py` 中的配置进行转换。

H2 BrainCo 数据使用：

```bash
python unitree_lerobot/utils/convert_unitree_json_to_lerobot.py \
  --raw-dir /path/to/raw_dataset \
  --repo-id your_name/h2_task \
  --robot_type Unitree_H2_Brainco
```

具体参数以脚本当前版本的 `--help` 输出为准：

```bash
python unitree_lerobot/utils/convert_unitree_json_to_lerobot.py --help
```

训练时使用仓库内的 LeRobot 训练入口，并将 `--dataset.repo_id`、
`--dataset.root` 和策略参数替换为自己的数据集与训练配置。例如：

```bash
python lerobot/src/lerobot/scripts/lerobot_train.py \
  --dataset.repo_id=your_name/h2_task \
  --policy.type=act \
  --output_dir=outputs/h2_act
```

## H2 真机部署

### 1. 真机部署前提

1. H2 已上电并处于允许控制的状态。
2. 运行推理的电脑与 H2 使用同一网络和 DDS domain。
3. 机器人端图传 `image_server` 已启动。
4. 已准备与数据集观测维度匹配的策略模型和数据集元信息。
5. 已确认 `unitree_sdk2py`、`cyclonedds`、`pinocchio`、PyTorch 和
   LeRobot 可以在当前 Conda 环境导入。

先运行只读 DDS 诊断，不会向机器人发送控制指令：

```bash
python test/test_h2_dds_subscribe.py
```

多网卡环境可以指定网卡：

```bash
python test/test_h2_dds_subscribe.py \
  --iface <network_interface> \
  --domain 0
```

### 2. 启动 H2 策略评估

默认 H2 手臂控制器为 `H2`，BrainCo 五指手使用 `brainco`：

```bash
python unitree_lerobot/eval_robot/eval_h2.py \
  --repo_id your_name/h2_task \
  --root /path/to/h2_task \
  --arm H2 \
  --ee brainco \
  --policy.path /path/to/pretrained_model
```

常用参数：

| 参数 | 说明 |
| --- | --- |
| `--repo_id` | LeRobot 数据集仓库 ID |
| `--root` | 本地数据集目录 |
| `--policy.path` | 训练好的策略目录 |
| `--arm H2` | 使用 H2 手臂控制器 |
| `--ee brainco` | 使用 BrainCo 五指手；也支持 `dex3`、`dex1`、`inspire1` |
| `--image_host` | 图传服务器地址 |
| `--frequency 30` | 控制频率，默认 30 Hz |
| `--motion` | 启用运动控制模式时使用 |

程序初始化时会要求输入 `s`。确认机器人姿态、网络和急停条件后再输入，
机械臂才会移动到数据集初始姿态并开始闭环推理。

### 3. H2 离线评估

不连接真机时，可以对数据集运行策略并绘制预测动作对比：

```bash
python unitree_lerobot/eval_robot/eval_h2_dataset.py \
  --repo_id your_name/h2_task \
  --root /path/to/h2_task \
  --policy.path /path/to/pretrained_model
```

### 4. H2 仿真评估

在已配置 Unitree 仿真环境和 domain 1 的情况下：

```bash
python unitree_lerobot/eval_robot/eval_h2_sim.py \
  --repo_id your_name/h2_task \
  --policy.path /path/to/pretrained_model \
  --arm H2 \
  --ee brainco \
  --sim
```

## H2 适配说明

H2 适配的控制链路包括：

- `H2_ArmController`：H2 35 电机状态和双臂 14 DOF 控制
- H2 官方 `rt/arm_sdk` 控制话题
- `H2_ArmIK`：基于 H2 URDF 的双臂逆运动学
- H2 专用关节索引、阻尼/刚度参数和状态映射
- `Unitree_H2_Brainco` 数据转换配置

更多关节索引、控制参数、URDF 和文件变更说明见
[H2_ADAPTATION_SUMMARY.md](./H2_ADAPTATION_SUMMARY.md)。

## 安全提醒

- 首次真机运行必须先执行 DDS 只读诊断。
- 确认急停、机器人姿态和控制权限后再输入 `s`。
- 不要直接使用未经验证的策略模型或错误的 `--root` 数据集。
- 真机运行时保持急停装置可用，并准备随时断开控制。

## 上游项目和许可证

本项目基于官方
[unitreerobotics/unitree_lerobot](https://github.com/unitreerobotics/unitree_lerobot)
进行改造。LeRobot 子模块、Unitree SDK、机器人模型和其他第三方组件
分别遵循其原始项目许可证；请在分发和二次开发时保留相关版权和许可证文件。

本仓库的 H2 适配代码与文档遵循仓库中的许可证文件。
