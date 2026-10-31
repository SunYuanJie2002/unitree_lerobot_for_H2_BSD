# import safetensors.torch

# path = "/home/bosideng/models/pi05_base/model.safetensors"
# sd = safetensors.torch.load_file(path)
# keys = sorted(sd.keys())

# # 查找所有包含 'embed' 或 'token' 的键
# embed_keys = [k for k in keys if "embed" in k.lower()]
# print("Keys containing 'embed':")
# for k in embed_keys:
#     print(f"  {k}")

# # 检查是否包含 'model.paligemma_with_expert.paligemma.model.language_model.embed_tokens.weight'
# target = "model.paligemma_with_expert.paligemma.model.language_model.embed_tokens.weight"
# if target in keys:
#     print(f"\n✅ 找到目标键: {target}")
# else:
#     print(f"\n❌ 未找到目标键: {target}")
#     # 查找相似键
#     similar = [k for k in keys if "language_model" in k and "embed" in k]
#     if similar:
#         print("可能的相似键:")
#         for k in similar:
#             print(f"  {k}")

from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained("/home/bosideng/models/paligemma_tokenizer")
print(tok("你好"))