"""
arXiv 官方分类体系
基于 https://arxiv.org/category_taxonomy
"""

ARXIV_CATEGORIES = {
    "physics": {
        "id": "physics",
        "name": "物理学",
        "name_en": "Physics",
        "children": {
            "astro-ph": {
                "id": "astro-ph",
                "name": "天体物理",
                "name_en": "Astrophysics",
                "children": {
                    "astro-ph.CO": {
                        "id": "astro-ph.CO",
                        "name": "宇宙学与非星系天体物理",
                        "name_en": "Cosmology and Nongalactic Astrophysics",
                    },
                    "astro-ph.EP": {
                        "id": "astro-ph.EP",
                        "name": "地球与行星天体物理",
                        "name_en": "Earth and Planetary Astrophysics",
                    },
                    "astro-ph.GA": {
                        "id": "astro-ph.GA",
                        "name": "银河系天体物理",
                        "name_en": "Astrophysics of Galaxies",
                    },
                    "astro-ph.HE": {
                        "id": "astro-ph.HE",
                        "name": "高能天体物理",
                        "name_en": "High Energy Astrophysical Phenomena",
                    },
                    "astro-ph.IM": {
                        "id": "astro-ph.IM",
                        "name": "天体物理仪器与方法",
                        "name_en": "Instrumentation and Methods for Astrophysics",
                    },
                    "astro-ph.SR": {
                        "id": "astro-ph.SR",
                        "name": "太阳与恒星天体物理",
                        "name_en": "Solar and Stellar Astrophysics",
                    },
                },
            },
            "cond-mat": {
                "id": "cond-mat",
                "name": "凝聚态物理",
                "name_en": "Condensed Matter",
                "recommended": True,
                "children": {
                    "cond-mat.dis-nn": {
                        "id": "cond-mat.dis-nn",
                        "name": "无序系统与神经网络",
                        "name_en": "Disordered Systems and Neural Networks",
                    },
                    "cond-mat.mes-hall": {
                        "id": "cond-mat.mes-hall",
                        "name": "介观与纳米物理",
                        "name_en": "Mesoscale and Nanoscale Physics",
                    },
                    "cond-mat.mtrl-sci": {
                        "id": "cond-mat.mtrl-sci",
                        "name": "材料科学",
                        "name_en": "Materials Science",
                        "recommended": True,
                    },
                    "cond-mat.other": {
                        "id": "cond-mat.other",
                        "name": "凝聚态物理其他",
                        "name_en": "Other Condensed Matter",
                    },
                    "cond-mat.quant-gas": {"id": "cond-mat.quant-gas", "name": "量子气体", "name_en": "Quantum Gases"},
                    "cond-mat.soft": {
                        "id": "cond-mat.soft",
                        "name": "软凝聚态物理",
                        "name_en": "Soft Condensed Matter",
                    },
                    "cond-mat.stat-mech": {
                        "id": "cond-mat.stat-mech",
                        "name": "统计力学",
                        "name_en": "Statistical Mechanics",
                    },
                    "cond-mat.str-el": {
                        "id": "cond-mat.str-el",
                        "name": "强关联电子",
                        "name_en": "Strongly Correlated Electrons",
                        "recommended": True,
                    },
                    "cond-mat.supr-con": {
                        "id": "cond-mat.supr-con",
                        "name": "超导",
                        "name_en": "Superconductivity",
                        "recommended": True,
                    },
                },
            },
            "gr-qc": {
                "id": "gr-qc",
                "name": "广义相对论与量子宇宙学",
                "name_en": "General Relativity and Quantum Cosmology",
            },
            "hep-ex": {
                "id": "hep-ex",
                "name": "高能物理-实验",
                "name_en": "High Energy Physics - Experiment",
            },
            "hep-lat": {
                "id": "hep-lat",
                "name": "高能物理-格点",
                "name_en": "High Energy Physics - Lattice",
            },
            "hep-ph": {
                "id": "hep-ph",
                "name": "高能物理-唯象学",
                "name_en": "High Energy Physics - Phenomenology",
            },
            "hep-th": {
                "id": "hep-th",
                "name": "高能物理-理论",
                "name_en": "High Energy Physics - Theory",
            },
            "math-ph": {
                "id": "math-ph",
                "name": "数学物理",
                "name_en": "Mathematical Physics",
            },
            "nlin": {
                "id": "nlin",
                "name": "非线性科学",
                "name_en": "Nonlinear Sciences",
                "children": {
                    "nlin.AO": {
                        "id": "nlin.AO",
                        "name": "适应与自组织系统",
                        "name_en": "Adaptation and Self-Organizing Systems",
                    },
                    "nlin.CD": {"id": "nlin.CD", "name": "混沌动力学", "name_en": "Chaotic Dynamics"},
                    "nlin.CG": {
                        "id": "nlin.CG",
                        "name": "元胞自动机与格气",
                        "name_en": "Cellular Automata and Lattice Gases",
                    },
                    "nlin.PS": {"id": "nlin.PS", "name": "模式形成与孤子", "name_en": "Pattern Formation and Solitons"},
                    "nlin.SI": {
                        "id": "nlin.SI",
                        "name": "可积系统",
                        "name_en": "Exactly Solvable and Integrable Systems",
                    },
                },
            },
            "nucl-ex": {
                "id": "nucl-ex",
                "name": "核物理-实验",
                "name_en": "Nuclear Experiment",
            },
            "nucl-th": {
                "id": "nucl-th",
                "name": "核物理-理论",
                "name_en": "Nuclear Theory",
            },
            "physics": {
                "id": "physics",
                "name": "物理学(其他)",
                "name_en": "Physics (Other)",
                "children": {
                    "physics.acc-ph": {"id": "physics.acc-ph", "name": "加速器物理", "name_en": "Accelerator Physics"},
                    "physics.ao-ph": {
                        "id": "physics.ao-ph",
                        "name": "大气与海洋物理",
                        "name_en": "Atmospheric and Oceanic Physics",
                    },
                    "physics.app-ph": {"id": "physics.app-ph", "name": "应用物理", "name_en": "Applied Physics"},
                    "physics.atom-ph": {"id": "physics.atom-ph", "name": "原子物理", "name_en": "Atomic Physics"},
                    "physics.bio-ph": {"id": "physics.bio-ph", "name": "生物物理", "name_en": "Biological Physics"},
                    "physics.chem-ph": {"id": "physics.chem-ph", "name": "化学物理", "name_en": "Chemical Physics"},
                    "physics.class-ph": {"id": "physics.class-ph", "name": "经典物理", "name_en": "Classical Physics"},
                    "physics.comp-ph": {
                        "id": "physics.comp-ph",
                        "name": "计算物理",
                        "name_en": "Computational Physics",
                        "recommended": True,
                    },
                    "physics.data-an": {
                        "id": "physics.data-an",
                        "name": "数据分析、统计与概率",
                        "name_en": "Data Analysis, Statistics and Probability",
                    },
                    "physics.ed-ph": {"id": "physics.ed-ph", "name": "物理教育", "name_en": "Physics Education"},
                    "physics.flu-dyn": {"id": "physics.flu-dyn", "name": "流体动力学", "name_en": "Fluid Dynamics"},
                    "physics.geo-ph": {"id": "physics.geo-ph", "name": "地球物理", "name_en": "Geophysics"},
                    "physics.ins-det": {
                        "id": "physics.ins-det",
                        "name": "仪器与探测器",
                        "name_en": "Instrumentation and Detectors",
                    },
                    "physics.med-ph": {"id": "physics.med-ph", "name": "医学物理", "name_en": "Medical Physics"},
                    "physics.optics": {"id": "physics.optics", "name": "光学", "name_en": "Optics"},
                    "physics.plasm-ph": {"id": "physics.plasm-ph", "name": "等离子体物理", "name_en": "Plasma Physics"},
                    "physics.pop-ph": {"id": "physics.pop-ph", "name": "科普物理", "name_en": "Popular Physics"},
                    "physics.soc-ph": {"id": "physics.soc-ph", "name": "物理与社会", "name_en": "Physics and Society"},
                    "physics.space-ph": {"id": "physics.space-ph", "name": "空间物理", "name_en": "Space Physics"},
                },
            },
            "quant-ph": {
                "id": "quant-ph",
                "name": "量子物理",
                "name_en": "Quantum Physics",
                "recommended": True,
            },
        },
    },
    "math": {
        "id": "math",
        "name": "数学",
        "name_en": "Mathematics",
        "children": {
            "math.AC": {"id": "math.AC", "name": "交换代数", "name_en": "Commutative Algebra"},
            "math.AG": {"id": "math.AG", "name": "代数几何", "name_en": "Algebraic Geometry"},
            "math.AP": {"id": "math.AP", "name": "偏微分方程分析", "name_en": "Analysis of PDEs"},
            "math.AT": {"id": "math.AT", "name": "代数拓扑", "name_en": "Algebraic Topology"},
            "math.CA": {"id": "math.CA", "name": "经典分析与常微分方程", "name_en": "Classical Analysis and ODEs"},
            "math.CO": {"id": "math.CO", "name": "组合数学", "name_en": "Combinatorics"},
            "math.CT": {"id": "math.CT", "name": "范畴论", "name_en": "Category Theory"},
            "math.CV": {"id": "math.CV", "name": "复变函数", "name_en": "Complex Variables"},
            "math.DG": {"id": "math.DG", "name": "微分几何", "name_en": "Differential Geometry"},
            "math.DS": {"id": "math.DS", "name": "动力系统", "name_en": "Dynamical Systems"},
            "math.FA": {"id": "math.FA", "name": "泛函分析", "name_en": "Functional Analysis"},
            "math.GM": {"id": "math.GM", "name": "普通数学", "name_en": "General Mathematics"},
            "math.GN": {"id": "math.GN", "name": "一般拓扑", "name_en": "General Topology"},
            "math.GR": {"id": "math.GR", "name": "群论", "name_en": "Group Theory"},
            "math.GT": {"id": "math.GT", "name": "几何拓扑", "name_en": "Geometric Topology"},
            "math.HO": {"id": "math.HO", "name": "历史与概述", "name_en": "History and Overview"},
            "math.IT": {"id": "math.IT", "name": "信息论", "name_en": "Information Theory"},
            "math.KT": {"id": "math.KT", "name": "K-理论与同调", "name_en": "K-Theory and Homology"},
            "math.LO": {"id": "math.LO", "name": "逻辑", "name_en": "Logic"},
            "math.MG": {"id": "math.MG", "name": "度量几何", "name_en": "Metric Geometry"},
            "math.NA": {"id": "math.NA", "name": "数值分析", "name_en": "Numerical Analysis", "recommended": True},
            "math.NT": {"id": "math.NT", "name": "数论", "name_en": "Number Theory"},
            "math.OA": {"id": "math.OA", "name": "算子代数", "name_en": "Operator Algebras"},
            "math.OC": {"id": "math.OC", "name": "优化与控制", "name_en": "Optimization and Control"},
            "math.PR": {"id": "math.PR", "name": "概率论", "name_en": "Probability"},
            "math.QA": {"id": "math.QA", "name": "量子代数", "name_en": "Quantum Algebra"},
            "math.RA": {"id": "math.RA", "name": "环与代数", "name_en": "Rings and Algebras"},
            "math.RT": {"id": "math.RT", "name": "表示论", "name_en": "Representation Theory"},
            "math.SG": {"id": "math.SG", "name": "辛几何", "name_en": "Symplectic Geometry"},
            "math.SP": {"id": "math.SP", "name": "谱理论", "name_en": "Spectral Theory"},
            "math.ST": {"id": "math.ST", "name": "统计理论", "name_en": "Statistics Theory"},
        },
    },
    "cs": {
        "id": "cs",
        "name": "计算机科学",
        "name_en": "Computer Science",
        "recommended": True,
        "children": {
            "cs.AI": {"id": "cs.AI", "name": "人工智能", "name_en": "Artificial Intelligence", "recommended": True},
            "cs.AR": {"id": "cs.AR", "name": "硬件架构", "name_en": "Hardware Architecture"},
            "cs.CC": {"id": "cs.CC", "name": "计算复杂性", "name_en": "Computational Complexity"},
            "cs.CE": {
                "id": "cs.CE",
                "name": "计算工程、金融与科学",
                "name_en": "Computational Engineering, Finance, and Science",
            },
            "cs.CG": {"id": "cs.CG", "name": "计算几何", "name_en": "Computational Geometry"},
            "cs.CL": {"id": "cs.CL", "name": "计算与语言", "name_en": "Computation and Language"},
            "cs.CR": {"id": "cs.CR", "name": "密码学与安全", "name_en": "Cryptography and Security"},
            "cs.CV": {"id": "cs.CV", "name": "计算机视觉", "name_en": "Computer Vision and Pattern Recognition"},
            "cs.CY": {"id": "cs.CY", "name": "计算机与社会", "name_en": "Computers and Society"},
            "cs.DB": {"id": "cs.DB", "name": "数据库", "name_en": "Databases"},
            "cs.DC": {
                "id": "cs.DC",
                "name": "分布式、并行与集群计算",
                "name_en": "Distributed, Parallel, and Cluster Computing",
            },
            "cs.DL": {"id": "cs.DL", "name": "数字图书馆", "name_en": "Digital Libraries"},
            "cs.DM": {"id": "cs.DM", "name": "离散数学", "name_en": "Discrete Mathematics"},
            "cs.DS": {"id": "cs.DS", "name": "数据结构与算法", "name_en": "Data Structures and Algorithms"},
            "cs.ET": {"id": "cs.ET", "name": "新兴技术", "name_en": "Emerging Technologies"},
            "cs.FL": {"id": "cs.FL", "name": "形式语言与自动机理论", "name_en": "Formal Languages and Automata Theory"},
            "cs.GL": {"id": "cs.GL", "name": "一般文献", "name_en": "General Literature"},
            "cs.GR": {"id": "cs.GR", "name": "图形学", "name_en": "Graphics"},
            "cs.GT": {"id": "cs.GT", "name": "计算机科学与博弈论", "name_en": "Computer Science and Game Theory"},
            "cs.HC": {"id": "cs.HC", "name": "人机交互", "name_en": "Human-Computer Interaction"},
            "cs.IR": {"id": "cs.IR", "name": "信息检索", "name_en": "Information Retrieval"},
            "cs.IT": {"id": "cs.IT", "name": "信息论", "name_en": "Information Theory"},
            "cs.LG": {"id": "cs.LG", "name": "机器学习", "name_en": "Machine Learning", "recommended": True},
            "cs.LO": {"id": "cs.LO", "name": "计算机科学中的逻辑", "name_en": "Logic in Computer Science"},
            "cs.MA": {"id": "cs.MA", "name": "多智能体系统", "name_en": "Multiagent Systems"},
            "cs.MM": {"id": "cs.MM", "name": "多媒体", "name_en": "Multimedia"},
            "cs.MS": {"id": "cs.MS", "name": "数学软件", "name_en": "Mathematical Software"},
            "cs.NA": {"id": "cs.NA", "name": "数值分析", "name_en": "Numerical Analysis"},
            "cs.NE": {"id": "cs.NE", "name": "神经与进化计算", "name_en": "Neural and Evolutionary Computing"},
            "cs.NI": {"id": "cs.NI", "name": "网络与互联网架构", "name_en": "Networking and Internet Architecture"},
            "cs.OH": {"id": "cs.OH", "name": "计算机科学其他", "name_en": "Other Computer Science"},
            "cs.OS": {"id": "cs.OS", "name": "操作系统", "name_en": "Operating Systems"},
            "cs.PF": {"id": "cs.PF", "name": "性能", "name_en": "Performance"},
            "cs.PL": {"id": "cs.PL", "name": "编程语言", "name_en": "Programming Languages"},
            "cs.RO": {"id": "cs.RO", "name": "机器人学", "name_en": "Robotics"},
            "cs.SC": {"id": "cs.SC", "name": "符号计算", "name_en": "Symbolic Computation"},
            "cs.SD": {"id": "cs.SD", "name": "声音", "name_en": "Sound"},
            "cs.SE": {"id": "cs.SE", "name": "软件工程", "name_en": "Software Engineering"},
            "cs.SI": {"id": "cs.SI", "name": "社会与信息网络", "name_en": "Social and Information Networks"},
            "cs.SY": {"id": "cs.SY", "name": "系统与控制", "name_en": "Systems and Control"},
        },
    },
    "q-bio": {
        "id": "q-bio",
        "name": "定量生物学",
        "name_en": "Quantitative Biology",
        "children": {
            "q-bio.BM": {"id": "q-bio.BM", "name": "生物分子", "name_en": "Biomolecules"},
            "q-bio.CB": {"id": "q-bio.CB", "name": "细胞行为", "name_en": "Cell Behavior"},
            "q-bio.GN": {"id": "q-bio.GN", "name": "基因组学", "name_en": "Genomics"},
            "q-bio.MN": {"id": "q-bio.MN", "name": "分子网络", "name_en": "Molecular Networks"},
            "q-bio.NC": {"id": "q-bio.NC", "name": "神经元与认知", "name_en": "Neurons and Cognition"},
            "q-bio.OT": {"id": "q-bio.OT", "name": "定量生物学其他", "name_en": "Other Quantitative Biology"},
            "q-bio.PE": {"id": "q-bio.PE", "name": "种群与进化", "name_en": "Populations and Evolution"},
            "q-bio.QM": {"id": "q-bio.QM", "name": "定量方法", "name_en": "Quantitative Methods"},
            "q-bio.SC": {"id": "q-bio.SC", "name": "亚细胞过程", "name_en": "Subcellular Processes"},
            "q-bio.TO": {"id": "q-bio.TO", "name": "组织与器官", "name_en": "Tissues and Organs"},
        },
    },
    "q-fin": {
        "id": "q-fin",
        "name": "定量金融",
        "name_en": "Quantitative Finance",
        "children": {
            "q-fin.CP": {"id": "q-fin.CP", "name": "计算金融", "name_en": "Computational Finance"},
            "q-fin.EC": {"id": "q-fin.EC", "name": "经济学", "name_en": "Economics"},
            "q-fin.GN": {"id": "q-fin.GN", "name": "一般金融", "name_en": "General Finance"},
            "q-fin.MF": {"id": "q-fin.MF", "name": "数学金融", "name_en": "Mathematical Finance"},
            "q-fin.PM": {"id": "q-fin.PM", "name": "投资组合管理", "name_en": "Portfolio Management"},
            "q-fin.PR": {"id": "q-fin.PR", "name": "证券定价", "name_en": "Pricing of Securities"},
            "q-fin.RM": {"id": "q-fin.RM", "name": "风险管理", "name_en": "Risk Management"},
            "q-fin.ST": {"id": "q-fin.ST", "name": "统计金融", "name_en": "Statistical Finance"},
            "q-fin.TR": {
                "id": "q-fin.TR",
                "name": "交易与市场微观结构",
                "name_en": "Trading and Market Microstructure",
            },
        },
    },
    "stat": {
        "id": "stat",
        "name": "统计学",
        "name_en": "Statistics",
        "children": {
            "stat.AP": {"id": "stat.AP", "name": "应用", "name_en": "Applications"},
            "stat.CO": {"id": "stat.CO", "name": "计算", "name_en": "Computation"},
            "stat.ME": {"id": "stat.ME", "name": "方法论", "name_en": "Methodology"},
            "stat.ML": {"id": "stat.ML", "name": "机器学习", "name_en": "Machine Learning", "recommended": True},
            "stat.OT": {"id": "stat.OT", "name": "统计学其他", "name_en": "Other Statistics"},
            "stat.TH": {"id": "stat.TH", "name": "统计理论", "name_en": "Statistics Theory"},
        },
    },
    "eess": {
        "id": "eess",
        "name": "电子工程与系统科学",
        "name_en": "Electrical Engineering and Systems Science",
        "children": {
            "eess.AS": {"id": "eess.AS", "name": "音频与语音处理", "name_en": "Audio and Speech Processing"},
            "eess.IV": {"id": "eess.IV", "name": "图像与视频处理", "name_en": "Image and Video Processing"},
            "eess.SP": {"id": "eess.SP", "name": "信号处理", "name_en": "Signal Processing"},
            "eess.SY": {"id": "eess.SY", "name": "系统与控制", "name_en": "Systems and Control"},
        },
    },
    "econ": {
        "id": "econ",
        "name": "经济学",
        "name_en": "Economics",
        "children": {
            "econ.EM": {"id": "econ.EM", "name": "计量经济学", "name_en": "Econometrics"},
            "econ.GN": {"id": "econ.GN", "name": "一般经济学", "name_en": "General Economics"},
            "econ.TH": {"id": "econ.TH", "name": "理论经济学", "name_en": "Theoretical Economics"},
        },
    },
}

DEFAULT_FIELDS = ["cond-mat.mtrl-sci", "quant-ph", "cs.LG"]


def get_all_categories() -> dict:
    """获取所有分类的扁平化字典"""
    result = {}

    def traverse(node: dict, parent_id: str = ""):
        if "id" in node:
            cat_id = node["id"]
            result[cat_id] = {
                "id": cat_id,
                "name": node.get("name", cat_id),
                "name_en": node.get("name_en", cat_id),
                "parent": parent_id,
                "recommended": node.get("recommended", False),
                "has_children": "children" in node,
            }
            if "children" in node:
                for child in node["children"].values():
                    traverse(child, cat_id)

    for group in ARXIV_CATEGORIES.values():
        traverse(group)

    return result


def get_category_query(category_id: str) -> str:
    """获取分类对应的 arXiv 查询字符串"""
    if "." in category_id:
        return f"cat:{category_id}"
    else:
        return f"cat:{category_id}.*"


def get_queries_for_fields(field_ids: list[str]) -> list[str]:
    """获取多个领域对应的查询列表"""
    queries = []
    for field_id in field_ids:
        queries.append(get_category_query(field_id))
    return queries


def get_recommended_fields() -> list[str]:
    """获取推荐领域列表"""
    all_cats = get_all_categories()
    return [cat_id for cat_id, info in all_cats.items() if info.get("recommended", False)]


def get_field_display_name(field_id: str, lang: str = "zh") -> str:
    """获取领域的显示名称"""
    all_cats = get_all_categories()
    if field_id in all_cats:
        return all_cats[field_id].get("name" if lang == "zh" else "name_en", field_id)
    return field_id
