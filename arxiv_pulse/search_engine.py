"""
增强搜索引擎 - 提供高级搜索和过滤功能
"""

from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from sqlalchemy import and_, or_, not_, func, desc, asc
from sqlalchemy.orm import Session

from arxiv_pulse.models import Paper
from arxiv_pulse.output_manager import output


@dataclass
class SearchFilter:
    """搜索过滤器配置"""

    # 文本搜索
    query: Optional[str] = None
    search_fields: List[str] = field(default_factory=lambda: ["title", "abstract"])

    # 分类过滤
    categories: Optional[List[str]] = None
    exclude_categories: Optional[List[str]] = None
    primary_category: Optional[str] = None

    # 作者过滤
    authors: Optional[List[str]] = None
    author_match: str = "contains"  # "contains", "exact", "any"

    # 时间过滤
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    days_back: Optional[int] = None

    # 处理状态过滤
    summarized_only: bool = False
    downloaded_only: bool = False

    # 搜索结果限制
    limit: int = 20
    offset: int = 0

    # 排序
    sort_by: str = "published"  # "published", "relevance_score", "title", "updated"
    sort_order: str = "desc"  # "asc", "desc"

    # 相似性搜索
    similar_to_paper_id: Optional[str] = None
    similarity_threshold: float = 0.5

    # 高级选项
    match_all: bool = False  # True: AND逻辑, False: OR逻辑


class SearchEngine:
    """增强的论文搜索引擎"""

    def __init__(self, db_session: Session):
        self.session = db_session

    def build_text_filter(self, query: str, search_fields: List[str], match_all: bool = False):
        """构建文本搜索过滤器，简单模糊匹配（支持单词拆分）"""
        if not query or not search_fields:
            return None

        # 将查询转换为小写进行不区分大小写的匹配
        query_lower = query.lower()

        # 拆分为单词（按非字母数字字符，保留中文）
        import re

        # 使用正则表达式分割，保留中文字符（支持Unicode）
        words = re.split(r"[^\w]+", query_lower, flags=re.UNICODE)
        # 过滤掉空字符串和过短的单词（长度>1）
        words = [w for w in words if w and len(w) > 1]

        # 如果没有有效的单词，使用整个查询作为单个单词
        if not words:
            words = [query_lower]

        # 如果只有一个单词，使用简单的字段间OR逻辑
        if len(words) == 1:
            word = words[0]
            field_filters = []
            for field in search_fields:
                if field == "title":
                    field_filters.append(Paper.title.ilike(f"%{word}%"))
                elif field == "abstract":
                    field_filters.append(Paper.abstract.ilike(f"%{word}%"))
                elif field == "categories":
                    field_filters.append(Paper.categories.ilike(f"%{word}%"))
                elif field == "search_query":
                    field_filters.append(Paper.search_query.ilike(f"%{word}%"))
                elif field == "authors":
                    field_filters.append(Paper.authors.ilike(f"%{word}%"))

            if field_filters:
                return or_(*field_filters)
            return None

        # 多个单词：首先尝试短语匹配（整个查询字符串）
        phrase_filters = []
        for field in search_fields:
            if field == "title":
                phrase_filters.append(Paper.title.ilike(f"%{query_lower}%"))
            elif field == "abstract":
                phrase_filters.append(Paper.abstract.ilike(f"%{query_lower}%"))
            elif field == "categories":
                phrase_filters.append(Paper.categories.ilike(f"%{query_lower}%"))
            elif field == "search_query":
                phrase_filters.append(Paper.search_query.ilike(f"%{query_lower}%"))
            elif field == "authors":
                phrase_filters.append(Paper.authors.ilike(f"%{query_lower}%"))

        # 尝试顺序匹配（单词按顺序出现，中间可间隔）
        sequence_filters = []
        if len(words) > 1:
            # 构建模式：%word1%word2%word3%
            sequence_pattern = "%" + "%".join(words) + "%"
            for field in search_fields:
                if field == "title":
                    sequence_filters.append(Paper.title.ilike(sequence_pattern))
                elif field == "abstract":
                    sequence_filters.append(Paper.abstract.ilike(sequence_pattern))
                elif field == "categories":
                    sequence_filters.append(Paper.categories.ilike(sequence_pattern))
                elif field == "search_query":
                    sequence_filters.append(Paper.search_query.ilike(sequence_pattern))
                elif field == "authors":
                    sequence_filters.append(Paper.authors.ilike(sequence_pattern))

        # 然后添加单词AND匹配（所有单词必须在同一个字段中出现）
        word_and_filters = []
        for field in search_fields:
            if field == "title":
                # 标题必须包含所有单词
                title_filters = [Paper.title.ilike(f"%{word}%") for word in words]
                if title_filters:
                    word_and_filters.append(and_(*title_filters))
            elif field == "abstract":
                # 摘要必须包含所有单词
                abstract_filters = [Paper.abstract.ilike(f"%{word}%") for word in words]
                if abstract_filters:
                    word_and_filters.append(and_(*abstract_filters))
            elif field == "categories":
                # 分类必须包含所有单词（通常分类搜索是单个词）
                category_filters = [Paper.categories.ilike(f"%{word}%") for word in words]
                if category_filters:
                    word_and_filters.append(and_(*category_filters))
            elif field == "search_query":
                search_query_filters = [Paper.search_query.ilike(f"%{word}%") for word in words]
                if search_query_filters:
                    word_and_filters.append(and_(*search_query_filters))
            elif field == "authors":
                author_filters = [Paper.authors.ilike(f"%{word}%") for word in words]
                if author_filters:
                    word_and_filters.append(and_(*author_filters))

        # 组合所有过滤器：短语匹配 OR 顺序匹配 OR 单词AND匹配
        all_filters = []
        if phrase_filters:
            all_filters.append(or_(*phrase_filters))
        if sequence_filters:
            all_filters.append(or_(*sequence_filters))
        if word_and_filters:
            all_filters.append(or_(*word_and_filters))

        if not all_filters:
            return None

        # 使用OR逻辑连接所有匹配类型
        return or_(*all_filters)

    def build_category_filter(
        self,
        categories: Optional[List[str]] = None,
        exclude_categories: Optional[List[str]] = None,
        primary_category: Optional[str] = None,
    ):
        """构建分类过滤器"""
        filters = []

        if categories:
            category_filters = []
            for cat in categories:
                category_filters.append(Paper.categories.contains(cat))
            if category_filters:
                filters.append(or_(*category_filters))

        if exclude_categories:
            exclude_filters = []
            for cat in exclude_categories:
                exclude_filters.append(not_(Paper.categories.contains(cat)))
            if exclude_filters:
                filters.append(and_(*exclude_filters))

        if primary_category:
            filters.append(Paper.primary_category == primary_category)

        return and_(*filters) if filters else None

    def build_author_filter(self, authors: Optional[List[str]] = None, match_type: str = "contains"):
        """构建作者过滤器"""
        if not authors:
            return None

        filters = []
        for author in authors:
            if match_type == "exact":
                # 精确匹配（作者名在JSON数组中）
                # 由于SQLite限制，使用contains近似
                filters.append(Paper.authors.contains(f'"name": "{author}"'))
            else:  # contains
                filters.append(Paper.authors.contains(author))

        if not filters:
            return None

        if match_type == "any":
            return or_(*filters)
        else:
            return and_(*filters)

    def build_date_filter(
        self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None, days_back: Optional[int] = None
    ):
        """构建时间过滤器"""
        filters = []

        if days_back:
            cutoff_date = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days_back)
            filters.append(Paper.published >= cutoff_date)

        if date_from:
            filters.append(Paper.published >= date_from)

        if date_to:
            filters.append(Paper.published <= date_to)

        return and_(*filters) if filters else None

    def build_status_filter(self, summarized_only: bool = False, downloaded_only: bool = False):
        """构建处理状态过滤器"""
        filters = []

        if summarized_only:
            filters.append(Paper.summarized == True)

        if downloaded_only:
            filters.append(Paper.downloaded == True)

        return and_(*filters) if filters else None

    def get_sort_column(self, sort_by: str, sort_order: str = "desc"):
        """获取排序列"""
        if sort_by == "published":
            column = Paper.published
        elif sort_by == "relevance_score":
            column = Paper.relevance_score
        elif sort_by == "title":
            column = Paper.title
        elif sort_by == "updated":
            column = Paper.updated
        elif sort_by == "created_at":
            column = Paper.created_at
        else:
            column = Paper.published

        return desc(column) if sort_order == "desc" else asc(column)

    def search_papers(self, filter_config: SearchFilter) -> List[Paper]:
        """执行搜索并返回论文列表"""
        try:
            query = self.session.query(Paper)

            # 应用所有过滤器
            filters = []

            # 文本搜索
            if filter_config.query:
                text_filter = self.build_text_filter(
                    filter_config.query, filter_config.search_fields, filter_config.match_all
                )
                if text_filter is not None:
                    filters.append(text_filter)

            # 分类过滤
            cat_filter = self.build_category_filter(
                filter_config.categories, filter_config.exclude_categories, filter_config.primary_category
            )
            if cat_filter is not None:
                filters.append(cat_filter)

            # 作者过滤
            author_filter = self.build_author_filter(filter_config.authors, filter_config.author_match)
            if author_filter is not None:
                filters.append(author_filter)

            # 时间过滤
            date_filter = self.build_date_filter(
                filter_config.date_from, filter_config.date_to, filter_config.days_back
            )
            if date_filter is not None:
                filters.append(date_filter)

            # 状态过滤
            status_filter = self.build_status_filter(filter_config.summarized_only, filter_config.downloaded_only)
            if status_filter is not None:
                filters.append(status_filter)

            # 应用所有过滤器
            if filters:
                query = query.filter(and_(*filters))

            # 排序
            sort_column = self.get_sort_column(filter_config.sort_by, filter_config.sort_order)
            query = query.order_by(sort_column)

            # 分页
            query = query.offset(filter_config.offset).limit(filter_config.limit)

            papers = query.all()
            output.debug(f"搜索找到 {len(papers)} 篇论文")
            return papers

        except Exception as e:
            output.error(f"搜索失败: {str(e)}")
            import traceback

            output.debug(f"搜索失败详情: {traceback.format_exc()}")
            return []

    def search_similar_papers(
        self, paper_id: str, limit: int = 10, threshold: float = 0.5
    ) -> List[tuple[Paper, float]]:
        """查找相似论文（基于标题和摘要的文本相似性）"""
        try:
            # 获取目标论文
            target_paper = self.session.query(Paper).filter(Paper.arxiv_id == paper_id).first()
            if not target_paper:
                output.warn(f"未找到论文: {paper_id}")
                return []

            # 简化的相似性搜索：基于共同关键词或分类
            # 在实际应用中，可以使用更复杂的文本相似性算法
            all_papers = self.session.query(Paper).filter(Paper.arxiv_id != paper_id).all()

            # 计算简单相似度：分类重叠
            similar_papers_with_scores = []
            target_cats = set(target_paper.categories.split()) if target_paper.categories else set()

            for paper in all_papers:
                if not paper.categories:
                    continue

                paper_cats = set(paper.categories.split())
                common_cats = target_cats.intersection(paper_cats)

                if common_cats:
                    # 简单相似度分数：共同分类数 / 总分类数
                    similarity = len(common_cats) / max(len(target_cats), len(paper_cats))
                    if similarity >= threshold:
                        similar_papers_with_scores.append((paper, similarity))

            # 按相似度排序
            similar_papers_with_scores.sort(key=lambda x: x[1], reverse=True)

            return similar_papers_with_scores[:limit]

        except Exception as e:
            output.error("相似论文搜索失败", details={"exception": str(e)})
            return []

    def get_search_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取搜索历史（从数据库中的search_query字段提取）"""
        try:
            # 查询所有使用过的搜索查询
            search_queries = (
                self.session.query(Paper.search_query, func.count(Paper.id).label("count"))
                .filter(Paper.search_query.isnot(None))
                .group_by(Paper.search_query)
                .order_by(desc("count"))
                .limit(limit)
                .all()
            )

            history = []
            for query, count in search_queries:
                # 获取最近一篇使用该查询的论文
                recent_paper = (
                    self.session.query(Paper)
                    .filter(Paper.search_query == query)
                    .order_by(desc(Paper.published))
                    .first()
                )

                history.append(
                    {
                        "query": query,
                        "count": count,
                        "last_used": recent_paper.published if recent_paper else None,
                        "last_paper_id": recent_paper.arxiv_id if recent_paper else None,
                    }
                )

            return history

        except Exception as e:
            output.error("获取搜索历史失败", details={"exception": str(e)})
            return []

    def save_search_query(self, query: str, description: Optional[str] = None):
        """保存搜索查询到历史（简单实现）"""
        # 这里可以扩展为保存到单独的搜索历史表
        # 目前依赖于Paper表中的search_query字段
        pass
