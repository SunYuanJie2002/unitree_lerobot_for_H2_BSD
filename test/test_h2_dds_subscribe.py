#!/usr/bin/env python
"""诊断脚本：订阅 H2 的 rt/lowstate，验证 DDS 通信链路是否可达。

只订阅、不发布任何指令，不会动机器人，可安全运行。

用法:
    # 自动确定网卡
    python test_h2_dds_subscribe.py

    # 显式指定网卡（推荐，多网卡 / VPN 环境下更可靠）
    python test_h2_dds_subscribe.py --iface wlx480eec290d7b

    # 指定 domain（仿真用 domain 1）
    python test_h2_dds_subscribe.py --domain 1
"""
import sys
import time
import argparse

from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelSubscriber
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowState_


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", type=int, default=0, help="DDS domain id (real robot=0, sim=1)")
    parser.add_argument("--iface", default=None, help="network interface name, e.g. wlx480eec290d7b / enp130s0 / eth0")
    parser.add_argument("--duration", type=float, default=10.0, help="how long to wait for first sample (s)")
    parser.add_argument("--topic", default="rt/lowstate")
    args = parser.parse_args()

    if args.iface:
        print(f"[diag] ChannelFactoryInitialize(domain={args.domain}, iface='{args.iface}')")
        ChannelFactoryInitialize(args.domain, args.iface)
    else:
        print(f"[diag] ChannelFactoryInitialize(domain={args.domain}, autodetermine)")
        ChannelFactoryInitialize(args.domain)

    state = {"n": 0}

    def handler(msg):
        state["n"] += 1
        if state["n"] == 1:
            print("[diag] FIRST lowstate received!")
            print(f"        mode_machine = {msg.mode_machine}")
            for i in range(min(6, len(msg.motor_state))):
                st = msg.motor_state[i]
                print(f"        motor[{i}] q={st.q:.3f} dq={st.dq:.3f}")

    sub = ChannelSubscriber(args.topic, LowState_)
    sub.Init(handler, 10)
    print(f"[diag] subscribed to '{args.topic}' (domain={args.domain}) ...")
    print(f"[diag] waiting up to {args.duration}s for first sample ...")

    start = time.time()
    while time.time() - start < args.duration and state["n"] == 0:
        time.sleep(0.2)

    if state["n"] > 0:
        print(f"[diag] OK: received {state['n']} sample(s) on '{args.topic}'.")
        return 0

    print(f"[diag] FAIL: no data on '{args.topic}' within {args.duration}s.")
    print("       可能原因:")
    print("       1. 机器人未上电 / 运控未开启（lowstate 未发布）")
    print("       2. domain 不匹配（实机 0，仿真 1）")
    print("       3. 网卡选错（本机有 VPN/多网卡，试试 --iface <网卡名>）")
    print("       4. 机器人与电脑网络不通（ping 192.168.123.161 测试）")
    return 1


if __name__ == "__main__":
    sys.exit(main())
