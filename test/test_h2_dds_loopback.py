#!/usr/bin/env python
"""本机 DDS 回环自测：同一进程内发布并订阅自定义话题，验证本机 DDS 栈正常。

使用自定义话题 rt/diag_test，不触碰机器人的 rt/lowstate / rt/lowcmd，安全无副作用。
"""
import sys
import time
import argparse

from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelPublisher, ChannelSubscriber
from unitree_sdk2py.idl.default import unitree_hg_msg_dds__LowState_
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowState_

TOPIC = "rt/diag_test"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", type=int, default=0)
    parser.add_argument("--iface", default=None)
    parser.add_argument("--duration", type=float, default=5.0)
    args = parser.parse_args()

    if args.iface:
        ChannelFactoryInitialize(args.domain, args.iface)
    else:
        ChannelFactoryInitialize(args.domain)

    got = {"n": 0}

    def handler(msg):
        got["n"] += 1
        if got["n"] == 1:
            print("[loopback] received own sample -> DDS stack OK")

    pub = ChannelPublisher(TOPIC, LowState_)
    pub.Init()
    sub = ChannelSubscriber(TOPIC, LowState_)
    sub.Init(handler, 10)
    time.sleep(0.5)  # let discovery settle

    sample = unitree_hg_msg_dds__LowState_()
    sample.mode_machine = 7
    sample.motor_state[0].q = 1.234
    for _ in range(int(args.duration * 10)):
        pub.Write(sample)
        if got["n"] > 0:
            break
        time.sleep(0.1)

    if got["n"] > 0:
        print(f"[loopback] OK: received {got['n']} sample(s).")
        return 0
    print("[loopback] FAIL: could not receive own published sample.")
    print("       说明本机 DDS 配置有问题（domain / 网卡 / CycloneDDS 安装）。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
