"""LitePet —— 一个常驻桌面、会走会说话、关掉再打开还记得你的小宠物。

模块划分：
    brain    纯逻辑：时段判断、台词、好感度（可单测，不依赖 GUI）
    memory   JSON 持久化：位置、好感度、聊天历史、上次见面时间
    sprite   QPainter 绘制的猫（无外部图片依赖，支持换配色）
    window   窗口与交互：走动、拖拽、点击、菜单、快捷键、定时提醒
    main     命令行入口
"""

__version__ = "1.0.0"
__all__ = ["brain", "memory", "sprite", "window", "main"]
