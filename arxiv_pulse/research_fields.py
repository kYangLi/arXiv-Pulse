"""
arXiv 研究领域定义模块
用于交互式配置和横幅生成
"""

RESEARCH_FIELDS = {
    "condensed_matter": {
        "name": "凝聚态物理",
        "query": "condensed matter physics AND cat:cond-mat.*",
        "description": "包括超导、强关联电子、介观系统、材料科学等",
        "keywords": ["condensed matter physics", "cond-mat"],
    },
    "astro_physics": {
        "name": "天体物理",
        "query": "cat:astro-ph.*",
        "description": "天体物理学、宇宙学、天体观测等",
        "keywords": ["astro-ph"],
    },
    "high_energy_physics": {
        "name": "高能物理（粒子物理）",
        "query": "cat:hep-ph.* OR cat:hep-ex.* OR cat:hep-th.* OR cat:hep-lat.*",
        "description": "粒子物理、高能物理理论与实验",
        "keywords": ["hep-ph", "hep-ex", "hep-th", "hep-lat"],
    },
    "nuclear_physics": {
        "name": "核物理",
        "query": "cat:nucl-th.* OR cat:nucl-ex.*",
        "description": "核物理理论与实验",
        "keywords": ["nucl-th", "nucl-ex"],
    },
    "general_relativity": {
        "name": "广义相对论与宇宙学",
        "query": "cat:gr-qc.*",
        "description": "引力理论、宇宙学、黑洞物理",
        "keywords": ["gr-qc"],
    },
    "quantum_physics": {
        "name": "量子物理",
        "query": "cat:quant-ph.*",
        "description": "量子信息、量子计算、量子基础",
        "keywords": ["quant-ph"],
    },
    "computational_physics": {
        "name": "计算物理",
        "query": "cat:physics.comp-ph",
        "description": "数值计算方法在物理中的应用",
        "keywords": ["physics.comp-ph"],
    },
    "chemical_physics": {
        "name": "化学物理",
        "query": "cat:physics.chem-ph",
        "description": "化学过程的物理基础",
        "keywords": ["physics.chem-ph"],
    },
    "physics_other": {
        "name": "物理学（其他）",
        "query": "cat:physics:* NOT cat:physics.comp-ph NOT cat:physics.chem-ph",
        "description": "其他物理学领域",
        "keywords": ["physics:"],
    },
    "nonlinear_science": {
        "name": "非线性科学",
        "query": "cat:nlin.*",
        "description": "非线性动力学、复杂系统、混沌理论",
        "keywords": ["nlin"],
    },
    "mathematical_physics": {
        "name": "数学物理",
        "query": "cat:math-ph.*",
        "description": "物理问题的数学方法",
        "keywords": ["math-ph"],
    },
    "dft": {
        "name": "密度泛函理论 (DFT)",
        "query": '(ti:"density functional" OR abs:"density functional") AND (cat:physics.comp-ph OR cat:cond-mat.mtrl-sci OR cat:physics.chem-ph)',
        "description": "第一性原理计算、材料设计",
        "keywords": ["density functional"],
    },
    "first_principles": {
        "name": "第一性原理计算",
        "query": '(ti:"first principles" OR abs:"first principles" OR ti:"ab initio" OR abs:"ab initio") AND (cat:physics.comp-ph OR cat:cond-mat.mtrl-sci)',
        "description": "从头计算、量子化学方法",
        "keywords": ["first principles", "ab initio"],
    },
    "quantum_chemistry": {
        "name": "量子化学",
        "query": '(ti:"quantum chemistry" OR abs:"quantum chemistry") AND (cat:physics.chem-ph OR cat:physics.comp-ph)',
        "description": "量子化学方法与计算",
        "keywords": ["quantum chemistry"],
    },
    "force_fields": {
        "name": "力场与分子动力学",
        "query": '(ti:"force field" OR abs:"force field") AND (cat:physics.comp-ph OR cat:cond-mat.soft OR cat:physics.chem-ph)',
        "description": "力场开发、分子动力学模拟",
        "keywords": ["force field"],
    },
    "molecular_dynamics": {
        "name": "分子动力学",
        "query": '(ti:"molecular dynamics" OR abs:"molecular dynamics") AND (cat:physics.comp-ph OR cat:cond-mat.soft OR cat:physics.chem-ph)',
        "description": "分子动力学模拟技术",
        "keywords": ["molecular dynamics"],
    },
    "computational_materials": {
        "name": "计算材料科学",
        "query": 'cat:cond-mat.mtrl-sci AND (ti:"computational" OR abs:"computational" OR ti:"simulation" OR abs:"simulation")',
        "description": "材料计算与模拟",
        "keywords": ["computational materials", "materials science"],
    },
    "mathematics": {
        "name": "数学",
        "query": "cat:math.* AND NOT cat:math-ph.*",
        "description": "纯数学与应用数学",
        "keywords": ["cat:math."],
    },
    "numerical_analysis": {
        "name": "数值分析",
        "query": "cat:math.NA",
        "description": "数值计算方法与算法",
        "keywords": ["math.NA"],
    },
    "optimization_control": {
        "name": "优化与控制",
        "query": "cat:math.OC",
        "description": "数学优化、最优控制理论",
        "keywords": ["math.OC"],
    },
    "statistics_math": {
        "name": "统计学（数学）",
        "query": "cat:math.ST",
        "description": "数理统计理论",
        "keywords": ["math.ST"],
    },
    "machine_learning": {
        "name": "机器学习",
        "query": '(ti:"machine learning" OR abs:"machine learning") AND (cat:physics.comp-ph OR cat:cond-mat.mtrl-sci OR cat:physics.chem-ph OR cat:cs.* OR cat:stat.*)',
        "description": "机器学习在物理和材料科学中的应用",
        "keywords": ["machine learning"],
    },
    "artificial_intelligence": {
        "name": "人工智能",
        "query": "cat:cs.AI OR cat:cs.LG OR cat:cs.NE",
        "description": "人工智能、机器学习、神经网络",
        "keywords": ["cs.AI", "cs.LG", "cs.NE"],
    },
    "computer_vision": {
        "name": "计算机视觉",
        "query": "cat:cs.CV",
        "description": "图像处理、计算机视觉",
        "keywords": ["cs.CV"],
    },
    "natural_language": {
        "name": "自然语言处理",
        "query": "cat:cs.CL",
        "description": "计算语言学、自然语言处理",
        "keywords": ["cs.CL"],
    },
    "computer_science_other": {
        "name": "计算机科学（其他）",
        "query": "cat:cs.* NOT cat:cs.AI NOT cat:cs.LG NOT cat:cs.NE NOT cat:cs.CV NOT cat:cs.CL",
        "description": "其他计算机科学领域",
        "keywords": ["cat:cs."],
    },
    "statistics": {
        "name": "统计学",
        "query": "cat:stat.*",
        "description": "统计学理论与应用",
        "keywords": ["cat:stat."],
    },
    "statistical_learning": {
        "name": "统计学习",
        "query": "cat:stat.ML",
        "description": "统计学习方法与应用",
        "keywords": ["stat.ML"],
    },
    "quantitative_biology": {
        "name": "定量生物学",
        "query": "cat:q-bio.*",
        "description": "生物信息学、系统生物学、定量生物方法",
        "keywords": ["q-bio"],
    },
    "quantitative_finance": {
        "name": "定量金融",
        "query": "cat:q-fin.*",
        "description": "金融数学、金融工程、计量金融",
        "keywords": ["q-fin"],
    },
    "electrical_engineering": {
        "name": "电子工程与系统科学",
        "query": "cat:eess.*",
        "description": "信号处理、控制系统、电子工程",
        "keywords": ["eess"],
    },
    "economics": {
        "name": "经济学",
        "query": "cat:econ.*",
        "description": "经济学理论、计量经济学",
        "keywords": ["econ"],
    },
}

DEFAULT_BANNER_FIELDS = ["凝聚态物理", "密度泛函理论", "机器学习", "力场"]
