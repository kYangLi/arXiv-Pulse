"""
Category service - 分类解释服务
"""

from arxiv_pulse.constants import get_all_categories

_CATEGORY_NAMES = {
    "cs.AI": ("人工智能", "Artificial Intelligence"),
    "cs.CL": ("计算语言学", "Computation and Language"),
    "cs.CR": ("密码学与安全", "Cryptography and Security"),
    "cs.CV": ("计算机视觉", "Computer Vision"),
    "cs.LG": ("机器学习", "Machine Learning"),
    "cs.NE": ("神经网络", "Neural and Evolutionary Computing"),
    "cs.SE": ("软件工程", "Software Engineering"),
    "cs.PL": ("编程语言", "Programming Languages"),
    "cs.DC": ("分布式计算", "Distributed, Parallel, and Cluster Computing"),
    "cs.DS": ("数据结构与算法", "Data Structures and Algorithms"),
    "cs.IT": ("信息论", "Information Theory"),
    "cs.SY": ("系统与控制", "Systems and Control"),
    "cond-mat": ("凝聚态物理", "Condensed Matter"),
    "cond-mat.mtrl-sci": ("材料科学", "Materials Science"),
    "cond-mat.str-el": ("强关联电子系统", "Strongly Correlated Electrons"),
    "cond-mat.supr-con": ("超导", "Superconductivity"),
    "cond-mat.mes-hall": ("介观系统与量子霍尔效应", "Mesoscopic Systems and Quantum Hall Effect"),
    "cond-mat.soft": ("软凝聚态物质", "Soft Condensed Matter"),
    "cond-mat.dis-nn": ("无序系统与神经网络", "Disordered Systems and Neural Networks"),
    "cond-mat.stat-mech": ("统计力学", "Statistical Mechanics"),
    "cond-mat.quant-gas": ("量子气体", "Quantum Gases"),
    "physics": ("物理学", "Physics"),
    "physics.comp-ph": ("计算物理", "Computational Physics"),
    "physics.chem-ph": ("化学物理", "Chemical Physics"),
    "physics.data-an": ("数据分析", "Data Analysis, Statistics and Probability"),
    "physics.ins-det": ("仪器与探测器", "Instrumentation and Detectors"),
    "math": ("数学", "Mathematics"),
    "math.NA": ("数值分析", "Numerical Analysis"),
    "math.OC": ("优化与控制", "Optimization and Control"),
    "math.ST": ("统计", "Statistics"),
    "q-bio": ("定量生物学", "Quantitative Biology"),
    "q-bio.BM": ("生物分子", "Biomolecules"),
    "q-bio.QM": ("定量方法", "Quantitative Methods"),
    "q-fin": ("定量金融", "Quantitative Finance"),
    "stat": ("统计学", "Statistics"),
    "stat.ML": ("机器学习", "Machine Learning"),
    "stat.AP": ("应用", "Applications"),
    "stat.CO": ("计算", "Computation"),
    "stat.ME": ("方法学", "Methodology"),
    "stat.OT": ("其他", "Other"),
    "stat.TH": ("理论", "Theory"),
}


def get_category_explanations(category_code: str) -> dict[str, str]:
    """
    获取分类代码的中文和英文解释

    Returns:
        dict: {"zh": "中文 (英文)", "en": "英文"}
    """
    if not category_code:
        return {"zh": "", "en": ""}

    categories = [c.strip() for c in category_code.split(",")]
    zh_parts = []
    en_parts = []

    for cat in categories:
        zh_name, en_name = _get_single_category_names(cat)
        zh_parts.append(zh_name)
        en_parts.append(en_name)

    return {"zh": "; ".join(zh_parts), "en": "; ".join(en_parts)}


def _get_single_category_names(cat: str) -> tuple[str, str]:
    """获取单个分类的中英文名称，返回 (中文名称, 英文名称)"""
    if cat in _CATEGORY_NAMES:
        zh_name, en_name = _CATEGORY_NAMES[cat]
        return f"{zh_name} ({en_name})", en_name

    main_cat = cat.split(".")[0] if "." in cat else cat
    if main_cat in _CATEGORY_NAMES:
        zh_main, en_main = _CATEGORY_NAMES[main_cat]
        return f"{cat} ({zh_main})", f"{cat} ({en_main})"

    all_cats = get_all_categories()
    if cat in all_cats:
        info = all_cats[cat]
        zh_name = info.get("name", cat)
        en_name = info.get("name_en", cat)
        return f"{zh_name} ({en_name})", en_name

    return cat, cat
