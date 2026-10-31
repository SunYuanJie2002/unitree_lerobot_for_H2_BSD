# H2 机器人适配 LeRobot 工作汇总

> 基于 XR Teleoperate（已适配 H2）将 H2 支持移植到 Unitree LeRobot，参照已有的 G1 适配模式完成。

---

## 一、适配背景

- **原始状态**：LeRobot 已适配 G1（G1_29 / G1_23），XR Teleoperate 已适配 G1 + H2
- **适配目标**：使 LeRobot 支持宇树 H2 人形机器人 + 强脑五指灵巧手的策略评估
- **适配策略**：底层控制代码（Arm Controller + IK）从 XR 直接移植，应用层（Eval 脚本 + Config）参照 G1 模式创建

---

## 二、文件变更清单

### 🆕 新建文件

| 文件路径 | 说明 |
|----------|------|
| `eval_robot/assets/h2/H2.urdf` | H2 机器人 URDF 模型 |
| `eval_robot/assets/h2/meshes/*.stl` | H2 32 个 STL 网格部件 |
| `eval_robot/eval_h2.py` | H2 实机策略评估脚本 |
| `eval_robot/eval_h2_dataset.py` | H2 数据集离线评估脚本 |
| `eval_robot/eval_h2_sim.py` | H2 仿真评估脚本 |     

### ✏️ 修改文件

| 文件路径 | 修改内容 |
|----------|----------|
| `eval_robot/robot_control/robot_arm.py` | 新增 `H2_ArmController`、`H2_JointIndex`、`H2_JointArmIndex`、`H2_LowState`、`H2_Num_Motors` |
| `eval_robot/robot_control/robot_arm_ik.py` | 新增 `H2_ArmIK` 逆运动学求解器 |
| `eval_robot/robot_control/mobile_control.py` | 标注 H2 兼容性，新增通用别名 `Robot_Mobile_Lift_Controller` |
| `eval_robot/make_robot.py` | 注册 `ARM_CONFIG["H2"]`，导入 H2 控制器，使用通用移动控制别名 |

### ✅ 已验证无需修改

| 模块 | 原因 |
|------|------|
| `robot_hand_brainco.py`（强脑五指灵巧手） | 已完整适配，6 DOF，关节索引 0-5，与 XR 一致 |
| `robot_hand_unitree.py`（宇树 dex3/dex1） | 通用 DDS 接口，与 H2 兼容 |
| `robot_hand_inspire.py`（因时灵巧手） | 同上 |
| `image_server/`（图像采集） | 与机器人型号无关 |
| `replay_robot.py` | 通过 `ARM_CONFIG` 自动分发，无需修改 |

---

## 三、核心技术细节

### 3.1 H2 手臂控制参数

| 参数 | G1_29 | H2 | 说明 |
|------|-------|-----|------|
| 总电机数 | 35 | 35 | |
| 手臂 DOF | 14 | 14 | 双臂各 7 关节 |
| DDS 协议 | `hg_LowCmd` / `hg_LowState` | 相同 | `unitree_hg` |
| `kp_high` | 300 | 300 | 强关节刚度 |
| `kd_high` | 3 | **5** | 强关节阻尼 |
| `kp_low` | 80 | **140** | 弱关节刚度 |
| `kd_low` | 3 | 3 | 弱关节阻尼 |
| `kp_wrist` | 40 | **50** | 腕关节刚度 |
| `kd_wrist` | 1.5 | **2** | 腕关节阻尼 |

### 3.2 H2 关节索引

```
全身关节 (0-34):
├── 左腿 (0-5):   hip_pitch, hip_roll, hip_yaw, knee, ankle_pitch, ankle_roll
├── 右腿 (6-11):  hip_pitch, hip_roll, hip_yaw, knee, ankle_pitch, ankle_roll
├── 腰部 (12-14): waist_yaw, waist_roll, waist_pitch
├── 左臂 (15-21): shoulder_pitch, shoulder_roll, shoulder_yaw, elbow,
│                  wrist_roll, wrist_pitch, wrist_yaw
├── 右臂 (22-28): shoulder_pitch, shoulder_roll, shoulder_yaw, elbow,
│                  wrist_roll, wrist_pitch, wrist_yaw
├── 头部 (29-30): head_pitch, head_yaw
└── 保留 (31-34)
```

G1_29 对比：索引 0-28 完全一致，G1_29 的 29-34 为 not_used，H2 的 29-30 为 head 关节。

### 3.3 H2 IK 求解器

- **算法**：基于 Pinocchio 动力学库 + CasADi IPOPT 非线性优化
- **模型**：加载 `assets/h2/H2.urdf`，锁定双腿 + 腰部 + 头部关节，仅优化 14 个手臂关节
- **末端执行器**：`left_wrist_yaw_joint` / `right_wrist_yaw_joint` + 偏移 `[0.05, 0, 0]`
- **代价函数**：`50 × 平移误差 + 1.0 × 旋转误差 + 0.02 × 正则化 + 0.1 × 平滑`
- **平滑滤波**：加权移动平均 `[0.4, 0.3, 0.2, 0.1]`

---

## 四、使用方式

```bash
# H2 实机评估（默认 arm=H2, ee=brainco）
python eval_h2.py --repo_id your/dataset --arm H2 --ee brainco

# 仿真评估
python eval_h2_sim.py --repo_id your/dataset --arm H2 --sim

# 数据集离线评估（绘制 ground truth vs predicted 对比图）
python eval_h2_dataset.py --repo_id your/dataset

# 也可通过原有 G1 脚本 + 命令行参数指定 H2
python eval_g1.py --arm H2 --ee brainco ...
```

### 命令行参数说明

| 参数 | 可选值 | 默认值 | 说明 |
|------|--------|--------|------|
| `--arm` | `G1_29`, `G1_23`, `H2` | `H2`（eval_h2.py） | 手臂控制器 |
| `--ee` | `dex3`, `dex1`, `inspire1`, `brainco` | `dex3` | 末端执行器 |
| `--motion` | flag | `False` | 启用运动控制模式 |
| `--sim` | flag | `False` | 启用仿真模式 |
| `--frequency` | float | `30.0` | 控制频率 (Hz) |
| `--visualization` | flag | `False` | 启用 Rerun 可视化 |

---

## 五、数据来源对照

| LeRobot 内容 | XR Teleoperate 来源 |
|-------------|---------------------|
| `H2_ArmController` | `teleop/robot_control/robot_arm.py` L1124-1420 |
| `H2_ArmIK` | `teleop/robot_control/robot_arm_ik.py` L1202-1494 |
| `H2.urdf` + meshes | `assets/h2/` 完整目录 |
| `H2_JointIndex` / `H2_JointArmIndex` | 同上 `robot_arm.py` L1336-1420 |
| `Robot_Mobile_Lift_Controller` 别名 | 基于 XR `motion_switcher.py` 中 G1/H2 共用 `LocoClient` 的事实 |
| `eval_h2.py` 等应用层脚本 | 参照 LeRobot 原有 `eval_g1.py` 模式自建（XR 无对应） |

---

## 六、目录结构

```
unitree_lerobot/eval_robot/
├── assets/
│   ├── g1/              # G1 资源（原有）
│   ├── h2/              # H2 资源（🆕 从 XR 复制）
│   │   ├── H2.urdf
│   │   └── meshes/      # 32 个 STL
│   ├── brainco_hand/    # 强脑灵巧手（原有，与 XR 一致）
│   ├── unitree_hand/    # 宇树灵巧手（原有）
│   └── inspire_hand/    # 因时灵巧手（原有）
├── robot_control/
│   ├── robot_arm.py     # 手臂控制器（✏️ 新增 H2）
│   ├── robot_arm_ik.py  # 逆运动学（✏️ 新增 H2）
│   ├── robot_hand_brainco.py   # 强脑手（✅ 已就绪）
│   ├── robot_hand_unitree.py   # 宇树手（✅ 已就绪）
│   ├── robot_hand_inspire.py   # 因时手（✅ 已就绪）
│   └── mobile_control.py       # 移动底座（✏️ 兼容标注）
├── make_robot.py        # 机器人接口工厂（✏️ 注册 H2）
├── eval_g1.py           # G1 评估（原有）
├── eval_h2.py           # H2 评估（🆕 新建）
├── eval_h2_dataset.py   # H2 数据集评估（🆕 新建）
├── eval_h2_sim.py       # H2 仿真评估（🆕 新建）
└── replay_robot.py      # 回放（✅ 通用）
```
