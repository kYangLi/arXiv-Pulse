"""
Chinese translations for arXiv Pulse backend.
"""

ZH_DICT: dict = {
    # Common
    "common": {
        "success": "成功",
        "error": "错误",
        "loading": "加载中...",
        "saving": "保存中...",
        "done": "完成",
        "cancel": "取消",
        "confirm": "确认",
        "delete": "删除",
        "edit": "编辑",
        "save": "保存",
    },
    # API messages
    "api": {
        "config": {
            "saved": "配置已保存",
            "save_failed": "保存失败",
            "not_initialized": "系统未初始化",
            "api_key_required": "API Key 为必填项",
            "model_required": "模型名称为必填项",
        },
        "papers": {
            "not_found": "论文未找到",
            "search_empty": "请输入搜索关键词",
            "searching": "正在搜索...",
            "syncing": "正在同步...",
            "sync_done": "同步完成",
            "no_new_papers": "没有新论文",
            "papers_added": "已添加 {count} 篇论文",
            "updating": "正在更新...",
            "update_done": "更新完成",
            "translating": "正在翻译...",
            "summarizing": "正在总结...",
        },
        "collections": {
            "created": "论文集已创建",
            "updated": "论文集已更新",
            "deleted": "论文集已删除",
            "not_found": "论文集未找到",
            "name_required": "名称为必填项",
            "paper_added": "论文已添加到论文集",
            "paper_removed": "论文已从论文集移除",
            "search_placeholder": "搜索论文...",
            "sort_by": "排序方式",
            "sort_published": "发表时间",
            "sort_added": "加入时间",
            "sort_asc": "升序",
            "sort_desc": "降序",
            "ai_search": "AI 检索",
            "ai_search_placeholder": "描述你想找的论文，如：关于电池材料 DFT 计算的",
            "ai_searching": "AI 正在检索...",
            "ai_no_result": "未找到匹配的论文",
            "ai_result": "找到 {count} 篇匹配论文",
            "no_search_result": "未找到匹配的论文，试试 AI 检索？",
        },
        "chat": {
            "thinking": "思考中...",
            "processing": "处理中...",
            "no_session": "会话不存在",
            "session_created": "会话已创建",
            "session_deleted": "会话已删除",
            "message_sent": "消息已发送",
        },
        "export": {
            "exporting": "正在导出...",
            "export_done": "导出完成",
            "no_papers": "没有论文可导出",
        },
    },
    # SSE progress messages
    "progress": {
        "connecting": "连接中...",
        "connected": "已连接",
        "fetching_papers": "获取论文中...",
        "papers_fetched": "已获取 {count} 篇论文",
        "processing_papers": "处理论文中...",
        "paper_processed": "已处理 {current}/{total}",
        "ai_analyzing": "AI 分析中...",
        "translating_title": "翻译标题...",
        "translating_abstract": "翻译摘要...",
        "generating_summary": "生成总结...",
        "extracting_figure": "提取图片...",
        "done": "完成",
        "error": "出错了: {error}",
    },
    # Sync task messages
    "sync": {
        "starting": "开始同步...",
        "checking_updates": "检查更新...",
        "downloading": "下载论文中...",
        "processing": "处理论文中...",
        "completed": "同步完成",
        "failed": "同步失败",
        "no_papers": "没有找到新论文",
        "papers_synced": "已同步 {count} 篇论文",
    },
    # Chat messages
    "chat": {
        "welcome": "你好！我是 AI 助手，可以帮你分析论文、回答问题。有什么可以帮你的吗？",
        "system_prompt": """你是一个专业的学术研究助手，帮助用户分析 arXiv 论文。

你可以：
- 总结论文的核心内容和贡献
- 解释论文中的技术概念和方法
- 比较不同论文的异同
- 回答用户关于论文的问题
- 提供研究建议

请用专业但易懂的语言回答，必要时引用论文原文。""",
        "no_context": "请先选择一篇论文进行分析。",
        "paper_context": "当前分析的论文：{title}",
    },
    # Research fields (for API responses)
    "fields": {
        "condensed_matter": "凝聚态物理",
        "dft": "密度泛函理论 (DFT)",
        "machine_learning": "机器学习",
        "force_fields": "力场与分子动力学",
        "first_principles": "第一性原理计算",
        "quantum_physics": "量子物理",
        "computational_physics": "计算物理",
        "chemical_physics": "化学物理",
        "molecular_dynamics": "分子动力学",
        "computational_materials": "计算材料科学",
        "quantum_chemistry": "量子化学",
        "astrophysics": "天体物理",
        "high_energy": "高能物理",
        "nuclear_physics": "核物理",
        "artificial_intelligence": "人工智能",
        "numerical_analysis": "数值分析",
        "statistics": "统计学",
        "quantitative_biology": "定量生物学",
        "electrical_engineering": "电子工程",
        "mathematical_physics": "数学物理",
    },
    # Category explanations
    "categories": {
        "cond-mat.mes-hall": "介观物理与纳米系统",
        "cond-mat.mtrl-sci": "材料科学",
        "cond-mat.other": "其他凝聚态物理",
        "cond-mat.quant-gas": "量子气体",
        "cond-mat.soft": "软物质物理",
        "cond-mat.stat-mech": "统计力学",
        "cond-mat.str-el": "强关联电子",
        "cond-mat.supr-con": "超导",
        "physics.chem-ph": "化学物理",
        "physics.comp-ph": "计算物理",
        "quant-ph": "量子物理",
        "cs.LG": "机器学习",
        "cs.AI": "人工智能",
        "cs.NE": "神经网络与进化计算",
    },
    # Time related
    "time": {
        "just_now": "刚刚",
        "minutes_ago": "{n} 分钟前",
        "hours_ago": "{n} 小时前",
        "days_ago": "{n} 天前",
        "yesterday": "昨天",
        "never": "从未",
    },
    # Status
    "status": {
        "running": "运行中",
        "completed": "已完成",
        "failed": "失败",
        "pending": "等待中",
        "cancelled": "已取消",
    },
}
