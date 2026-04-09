"""虾总笑点测试 - 8 题

答完写入 soul.md 的 profile 维度评分，影响后续梗图生成方向。
"""
from __future__ import annotations
from . import soul


# 全部用「虾总叙事」包装：每道题都是虾总的一个生活场景，
# 用户通过帮虾总选反应来暴露自己的笑点维度。
QUIZ = [
    {
        "q": "🦞 虾总今天打开朋友圈，看到老板发『公司战略性瘦身50%，蛋糕已备好』。虾总该回啥？",
        "options": [
            ("钳子敬礼：『恭喜公司轻装上阵 🎂』", "dark"),
            ("默默把工位照片设成壁纸", "self_deprecating"),
            ("给老板点赞，给 HR 鞠躬", "workplace"),
            ("不回，假装没看见", "cold"),
        ],
    },
    {
        "q": "🦞 虾总走进一家酒吧，老板说『我们这儿不卖海鲜』。虾总最酷的反应是？",
        "options": [
            ("『巧了，我也不吃人』 ← 冷面回怼", "cold"),
            ("『那卖不卖梦想？』 ← 突然哲学", "absurd"),
            ("掏出工牌：『我是来体检的』 ← 一本正经", "contrast"),
            ("『鸡你太美』 ← 转移话题", "pun"),
        ],
    },
    {
        "q": "🦞 虾总加班到凌晨3点，发现 bug 是少了个分号。它会发什么朋友圈？",
        "options": [
            ("『今晚的月色，配得上这个分号』", "technical"),
            ("『我为分号活着，分号不为我活着』", "self_deprecating"),
            ("『打工人的浪漫：和标点谈恋爱』", "workplace"),
            ("『分号已离家出走，请勿打扰』", "absurd"),
        ],
    },
    {
        "q": "🦞 虾总收到 HR 的面谈邀请，主题是『关于你最近的工作状态』。它脑子里第一个画面是？",
        "options": [
            ("自己被装进保鲜盒的电影分镜 🎬", "dark"),
            ("简历自动滚动播放的画面", "workplace"),
            ("『反正我也没什么状态』 ← 自暴自弃笑容", "self_deprecating"),
            ("一脸冷静：『又一次预演而已』", "cold"),
        ],
    },
    {
        "q": "🦞 虾总偷偷买了一个按摩椅放工位，被同事发现了。它最帅的解释是？",
        "options": [
            ("『腰椎是 KPI 的载体』 ← 一本正经胡说", "contrast"),
            ("『这是给老板备的，他还没来』", "workplace"),
            ("『打工人的尊严，从一把椅开始』", "self_deprecating"),
            ("『按摩椅是给灵魂的，不是给身体的』", "absurd"),
        ],
    },
    {
        "q": "🦞 虾总在书店看到一本书叫《如何不被煮》，它最想翻到哪一页？",
        "options": [
            ("『第三章：会哭的虾有奶喝』 ← 自嘲式生存", "self_deprecating"),
            ("『第七章：装死的艺术』 ← 冷幽默", "cold"),
            ("『序言：火锅是一种生活方式』 ← 黑色幽默", "dark"),
            ("『结语：成为一道菜也是一种修行』 ← 哲学", "absurd"),
        ],
    },
    {
        "q": "🦞 虾总和 ChatGPT 聊了一下午，最后它合上电脑说了一句话。是哪句？",
        "options": [
            ("『连 AI 都比我会写代码了』", "technical"),
            ("『它懂我的所有 bug，但不懂我为什么熬夜』", "self_deprecating"),
            ("『AI 是新一代打工人，我可以退休了』", "workplace"),
            ("『它太懂事了，反而像个人』", "contrast"),
        ],
    },
    {
        "q": "🦞 最后一题：如果让虾总当一天皇帝，它的第一道圣旨是？",
        "options": [
            ("『取消周一』 ← 职场救世主", "workplace"),
            ("『所有 KPI 改名叫许愿池』 ← 黑色幽默", "dark"),
            ("『海洋归海鲜，办公室归人类，不要再混淆了』 ← 抽象", "absurd"),
            ("『今日宜摸鱼，违者必究』 ← 冷面颁布", "cold"),
        ],
    },
]


def run():
    print("=" * 50)
    print("  虾总笑点测试 · 8 题")
    print("  答完会写入 soul.md，影响后续梗图方向")
    print("=" * 50)

    profile: dict[str, float] = {}
    for i, q in enumerate(QUIZ, 1):
        print(f"\n[{i}/{len(QUIZ)}] {q['q']}")
        for j, (text, _) in enumerate(q["options"], 1):
            print(f"  {j}. {text}")
        choice = _ask(len(q["options"]))
        _, dim = q["options"][choice - 1]
        profile[dim] = profile.get(dim, 0) + 1

    # 归一化到 0-10
    mx = max(profile.values()) if profile else 1
    profile = {k: round(v * 10 / mx, 1) for k, v in profile.items()}

    soul.update_profile(profile)

    print("\n" + "=" * 50)
    print("  你的笑点画像：")
    for k, v in sorted(profile.items(), key=lambda x: -x[1]):
        label = soul.DIM_LABELS.get(k, k)
        bar = "█" * int(v) + "·" * (10 - int(v))
        print(f"    {label:8s} {bar} {v}")
    print(f"\n  已写入 {soul.SOUL_PATH}")
    print("  下次跑 `python -m meme_hunter` 时会自动按这个画像出梗")
    print("=" * 50)


def _ask(n: int) -> int:
    while True:
        try:
            c = int(input(f"选择 (1-{n}): ").strip())
            if 1 <= c <= n:
                return c
        except (ValueError, EOFError):
            pass
        print(f"  请输入 1-{n}")
