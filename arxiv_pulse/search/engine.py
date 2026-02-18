"""
增强搜索引擎 - 提供高级搜索和过滤功能
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import and_, asc, desc, func, not_, or_
from sqlalchemy.orm import Session

from arxiv_pulse.models import Paper
from arxiv_pulse.utils import output


@dataclass
class SearchFilter:
    """搜索过滤器配置"""

    query: str | None = None
    search_fields: list[str] = field(default_factory=lambda: ["title", "abstract"])

    categories: list[str] | None = None
    exclude_categories: list[str] | None = None
    primary_category: str | None = None

    authors: list[str] | None = None
    author_match: str = "contains"

    date_from: datetime | None = None
    date_to: datetime | None = None
    days_back: int | None = None

    summarized_only: bool = False
    downloaded_only: bool = False

    limit: int = 20
    offset: int = 0

    sort_by: str = "published"
    sort_order: str = "desc"

    similar_to_paper_id: str | None = None
    similarity_threshold: float = 0.5

    match_all: bool = False
    strict_match: bool = False


class SearchEngine:
    """增强的论文搜索引擎"""

    def __init__(self, db_session: Session):
        self.session = db_session

    def build_text_filter(
        self, query: str, search_fields: list[str], match_all: bool = False, strict_match: bool = False
    ):
        """构建文本搜索过滤器，支持严格匹配（单词边界）和模糊匹配"""
        if not query or not search_fields:
            return None

        query_lower = query.lower()

        import re

        words = re.split(r"[^\w]+", query_lower, flags=re.UNICODE)
        words = [w for w in words if w and len(w) > 1]

        if not words:
            words = [query_lower]

        original_words = re.split(r"[^\w]+", query, flags=re.UNICODE)
        original_words = [w for w in original_words if w and len(w) > 1]
        if not original_words:
            original_words = [query]

        if len(words) == 1:
            word = words[0]

            field_filters = []
            for field in search_fields:
                if field == "title":
                    if strict_match:
                        field_filters.append(
                            or_(
                                Paper.title.ilike(f"{word} %"),
                                Paper.title.ilike(f"% {word}"),
                                Paper.title.ilike(f"% {word} %"),
                                Paper.title.ilike(word),
                            )
                        )
                    else:
                        field_filters.append(Paper.title.ilike(f"%{word}%"))
                elif field == "abstract":
                    if strict_match:
                        field_filters.append(
                            or_(
                                Paper.abstract.ilike(f"{word} %"),
                                Paper.abstract.ilike(f"% {word}"),
                                Paper.abstract.ilike(f"% {word} %"),
                                Paper.abstract.ilike(word),
                            )
                        )
                    else:
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

        sequence_filters = []
        if len(words) > 1:
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

        word_and_filters = []
        for field in search_fields:
            if field == "title":
                title_filters = [Paper.title.ilike(f"%{word}%") for word in words]
                if title_filters:
                    word_and_filters.append(and_(*title_filters))
            elif field == "abstract":
                abstract_filters = [Paper.abstract.ilike(f"%{word}%") for word in words]
                if abstract_filters:
                    word_and_filters.append(and_(*abstract_filters))
            elif field == "categories":
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

        all_filters = []

        if match_all:
            if word_and_filters:
                all_filters.append(or_(*word_and_filters))
        else:
            if phrase_filters:
                all_filters.append(or_(*phrase_filters))
            if sequence_filters:
                all_filters.append(or_(*sequence_filters))
            if word_and_filters:
                all_filters.append(or_(*word_and_filters))

        if not all_filters:
            return None

        return or_(*all_filters)

    def build_category_filter(
        self,
        categories: list[str] | None = None,
        exclude_categories: list[str] | None = None,
        primary_category: str | None = None,
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

    def build_author_filter(self, authors: list[str] | None = None, match_type: str = "contains"):
        """构建作者过滤器"""
        if not authors:
            return None

        filters = []
        for author in authors:
            if match_type == "exact":
                filters.append(Paper.authors.contains(f'"name": "{author}"'))
            else:
                filters.append(Paper.authors.contains(author))

        if not filters:
            return None

        if match_type == "any":
            return or_(*filters)
        return and_(*filters)

    def build_date_filter(
        self, date_from: datetime | None = None, date_to: datetime | None = None, days_back: int | None = None
    ):
        """构建时间过滤器"""
        filters = []

        if days_back:
            cutoff_date = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=days_back)
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

    def _search_papers_basic(self, filter_config: SearchFilter) -> list[Paper]:
        """基础搜索逻辑（原有实现）"""
        try:
            query = self.session.query(Paper)

            filters = []

            if filter_config.query:
                text_filter = self.build_text_filter(
                    filter_config.query,
                    filter_config.search_fields,
                    filter_config.match_all,
                    filter_config.strict_match,
                )
                if text_filter is not None:
                    filters.append(text_filter)

            cat_filter = self.build_category_filter(
                filter_config.categories, filter_config.exclude_categories, filter_config.primary_category
            )
            if cat_filter is not None:
                filters.append(cat_filter)

            author_filter = self.build_author_filter(filter_config.authors, filter_config.author_match)
            if author_filter is not None:
                filters.append(author_filter)

            date_filter = self.build_date_filter(
                filter_config.date_from, filter_config.date_to, filter_config.days_back
            )
            if date_filter is not None:
                filters.append(date_filter)

            status_filter = self.build_status_filter(filter_config.summarized_only, filter_config.downloaded_only)
            if status_filter is not None:
                filters.append(status_filter)

            if filters:
                query = query.filter(and_(*filters))

            sort_column = self.get_sort_column(filter_config.sort_by, filter_config.sort_order)
            query = query.order_by(sort_column)

            query = query.offset(filter_config.offset).limit(filter_config.limit)

            papers = query.all()
            output.debug(f"搜索找到 {len(papers)} 篇论文")
            return papers

        except Exception as e:
            output.error(f"搜索失败: {e!s}")
            import traceback

            output.debug(f"搜索失败详情: {traceback.format_exc()}")
            return []

    def search_papers(self, filter_config: SearchFilter) -> list[Paper]:
        """执行搜索并返回论文列表，支持严格匹配分级排序"""
        try:
            if not filter_config.strict_match:
                return self._search_papers_basic(filter_config)

            if not filter_config.query:
                return self._search_papers_basic(filter_config)

            import re
            from copy import copy

            fuzzy_config = copy(filter_config)
            fuzzy_config.strict_match = False
            fuzzy_config.limit = 1000000
            fuzzy_config.offset = 0

            fuzzy_papers = self._search_papers_basic(fuzzy_config)

            if not fuzzy_papers:
                return []

            strict_papers = []
            non_strict_papers = []

            assert filter_config.query is not None
            query_text = filter_config.query.lower()
            words = re.split(r"[^\w]+", query_text, flags=re.UNICODE)
            words = [w for w in words if w and len(w) > 1]
            if not words:
                words = [query_text]

            for paper in fuzzy_papers:
                is_strict = False

                text_to_check = ""
                if "title" in filter_config.search_fields:
                    text_to_check += (paper.title or "").lower() + " "
                if "abstract" in filter_config.search_fields:
                    text_to_check += (paper.abstract or "").lower() + " "
                if "categories" in filter_config.search_fields:
                    text_to_check += (paper.categories or "").lower() + " "
                if "search_query" in filter_config.search_fields:
                    text_to_check += (paper.search_query or "").lower() + " "
                if "authors" in filter_config.search_fields:
                    text_to_check += (paper.authors or "").lower() + " "

                all_words_strict = True
                for word in words:
                    pattern = r"\b" + re.escape(word) + r"\b"
                    if not re.search(pattern, text_to_check):
                        all_words_strict = False
                        break

                if all_words_strict:
                    strict_papers.append(paper)
                else:
                    non_strict_papers.append(paper)

            all_papers = strict_papers + non_strict_papers

            start_idx = filter_config.offset
            end_idx = filter_config.offset + filter_config.limit
            paginated_papers = all_papers[start_idx:end_idx]

            output.debug(
                f"分级搜索找到 {len(strict_papers)} 篇严格匹配, {len(non_strict_papers)} 篇非严格匹配, 返回 {len(paginated_papers)} 篇"
            )
            return paginated_papers

        except Exception as e:
            output.error(f"分级搜索失败: {e!s}")
            import traceback

            output.debug(f"分级搜索失败详情: {traceback.format_exc()}")
            return []

    def search_similar_papers(
        self, paper_id: str, limit: int = 10, threshold: float = 0.5
    ) -> list[tuple[Paper, float]]:
        """查找相似论文（基于标题和摘要的文本相似性）"""
        try:
            target_paper = self.session.query(Paper).filter(Paper.arxiv_id == paper_id).first()
            if not target_paper:
                output.warn(f"未找到论文: {paper_id}")
                return []

            all_papers = self.session.query(Paper).filter(Paper.arxiv_id != paper_id).all()

            similar_papers_with_scores = []
            target_cats = set(target_paper.categories.split()) if target_paper.categories is not None else set()

            for paper in all_papers:
                if paper.categories is None:
                    continue

                paper_cats = set(paper.categories.split())
                common_cats = target_cats.intersection(paper_cats)

                if common_cats:
                    similarity = len(common_cats) / max(len(target_cats), len(paper_cats))
                    if similarity >= threshold:
                        similar_papers_with_scores.append((paper, similarity))

            similar_papers_with_scores.sort(key=lambda x: x[1], reverse=True)

            return similar_papers_with_scores[:limit]

        except Exception as e:
            output.error("相似论文搜索失败", details={"exception": str(e)})
            return []

    def get_search_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """获取搜索历史（从数据库中的search_query字段提取）"""
        try:
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

    def save_search_query(self, query: str, description: str | None = None):
        """保存搜索查询到历史（简单实现）"""
