import logging
import os
import time
from datetime import UTC, datetime, timedelta
from typing import Any

import arxiv
from tqdm import tqdm

from arxiv_pulse.core import Config, Database
from arxiv_pulse.models import Paper
from arxiv_pulse.utils import output

logger = logging.getLogger(__name__)


class ArXivCrawler:
    def __init__(self):
        self.db = Database()
        self.client = arxiv.Client(page_size=500, delay_seconds=3.0, num_retries=3)
        self.config = Config

        logging.getLogger("arxiv").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)

    def search_arxiv(
        self,
        query: str,
        max_results: int = 100,
        days_back: int | None = None,
        cutoff_date: datetime | None = None,
    ) -> list[arxiv.Result]:
        """Search arXiv for papers matching query

        Args:
            query: arXiv search query
            max_results: Maximum number of results to return
            days_back: Optional number of days to look back (deprecated, use cutoff_date)
            cutoff_date: Optional UTC datetime cutoff; papers older than this will be skipped
                         and iteration will stop early due to descending date order.
        """
        sort_by_map = {
            "submittedDate": arxiv.SortCriterion.SubmittedDate,
            "lastUpdatedDate": arxiv.SortCriterion.LastUpdatedDate,
            "relevance": arxiv.SortCriterion.Relevance,
        }
        sort_by = sort_by_map.get(Config.ARXIV_SORT_BY, arxiv.SortCriterion.SubmittedDate)

        sort_order_map = {
            "descending": arxiv.SortOrder.Descending,
            "ascending": arxiv.SortOrder.Ascending,
        }
        sort_order = sort_order_map.get(Config.ARXIV_SORT_ORDER, arxiv.SortOrder.Descending)

        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        results = []
        for paper in self.client.results(search):
            if cutoff_date is not None and hasattr(paper, "published") and paper.published:
                if paper.published.tzinfo is None:
                    paper_date = paper.published.replace(tzinfo=UTC)
                else:
                    paper_date = paper.published.astimezone(UTC)

                if paper_date < cutoff_date:
                    output.debug(f"遇到旧论文 ({paper_date.date()})，停止爬取")
                    break

            results.append(paper)

            if len(results) >= max_results:
                break

        output.debug(f"Found {len(results)} papers for query: {query}")
        return results

    def filter_new_papers(self, papers: list[arxiv.Result]) -> list[arxiv.Result]:
        """Filter out papers already in database"""
        new_papers = []
        for paper in papers:
            arxiv_id = paper.entry_id.split("/")[-1]
            if not self.db.paper_exists(arxiv_id):
                new_papers.append(paper)
            else:
                output.debug(f"Paper {arxiv_id} already exists in database")

        output.debug(f"Filtered to {len(new_papers)} new papers")
        return new_papers

    def save_papers(self, papers: list[arxiv.Result], search_query: str) -> list[Paper]:
        """Save papers to database"""
        saved_papers = []
        for paper in tqdm(papers, desc="Saving papers"):
            try:
                arxiv_id = paper.entry_id.split("/")[-1]
                if self.db.paper_exists(arxiv_id):
                    continue

                paper_obj = Paper.from_arxiv_entry(paper, search_query)
                self.db.add_paper(paper_obj)
                saved_papers.append(paper_obj)

            except Exception as e:
                output.error(
                    "保存论文失败",
                    details={"paper_id": paper.entry_id, "exception": str(e)},
                )

        output.done(f"保存完成: {len(saved_papers)} 篇新论文")
        return saved_papers

    def initial_crawl(self) -> dict[str, Any]:
        """Perform initial crawl with multiple queries"""
        output.do("开始初始爬取")
        all_saved = []

        for query in self.config.SEARCH_QUERIES:
            output.do(f"搜索: {query}")
            try:
                papers = self.search_arxiv(query, max_results=self.config.ARXIV_MAX_RESULTS)
                new_papers = self.filter_new_papers(papers)
                saved = self.save_papers(new_papers, query)
                all_saved.extend(saved)

                output.done(f"保存: {len(saved)} 篇论文")
                time.sleep(1)

            except Exception as e:
                output.error(f"爬取查询失败: {query}", details={"exception": str(e)})

        output.done(f"初始爬取完成: 共保存 {len(all_saved)} 篇论文")
        return {
            "total_saved": len(all_saved),
            "queries_searched": len(self.config.SEARCH_QUERIES),
            "saved_papers": all_saved,
        }

    def daily_update(self) -> dict[str, Any]:
        """Perform daily update crawl with early stopping optimization"""
        output.do("开始每日更新")
        all_saved = []

        cutoff_date = datetime.now(UTC) - timedelta(days=2)
        output.info(f"查找 {cutoff_date.date()} 之后的新论文")

        for query in self.config.SEARCH_QUERIES:
            output.do(f"搜索: {query}")
            try:
                papers = self.search_arxiv(
                    query,
                    max_results=self.config.ARXIV_MAX_RESULTS,
                    cutoff_date=cutoff_date,
                )

                output.debug(f"找到 {len(papers)} 篇最近论文")

                new_papers = self.filter_new_papers(papers)
                saved = self.save_papers(new_papers, query)
                all_saved.extend(saved)

                output.done(f"保存: {len(saved)} 篇新论文")
                time.sleep(1)

            except Exception as e:
                output.error(f"每日更新失败: {query}", details={"exception": str(e)})

        output.done(f"每日更新完成: 共保存 {len(all_saved)} 篇新论文")
        return {
            "total_saved": len(all_saved),
            "queries_searched": len(self.config.SEARCH_QUERIES),
            "date_range": f"Since {cutoff_date.date()}",
            "saved_papers": all_saved,
        }

    def crawl_by_categories(self, categories: list[str], max_results: int = 64) -> dict[str, Any]:
        """Crawl specific arXiv categories"""
        all_saved = []

        for category in categories:
            query = f"cat:{category}"
            output.do(f"搜索类别: {category}")
            try:
                papers = self.search_arxiv(query, max_results=max_results)
                new_papers = self.filter_new_papers(papers)
                saved = self.save_papers(new_papers, f"cat:{category}")
                all_saved.extend(saved)

                output.done(f"保存: {len(saved)} 篇论文")
                time.sleep(1)

            except Exception as e:
                output.error(f"爬取类别失败: {category}", details={"exception": str(e)})

        return {
            "total_saved": len(all_saved),
            "categories": categories,
            "saved_papers": all_saved,
        }

    def get_latest_paper_date_for_query(self, query: str) -> datetime | None:
        """Get the latest paper date for a specific query in database"""
        with self.db.get_session() as session:
            latest_paper = (
                session.query(Paper).filter(Paper.search_query == query).order_by(Paper.published.desc()).first()
            )
            return latest_paper.published if latest_paper else None

    def get_latest_paper_date_for_any_query(self) -> datetime | None:
        """Get the latest paper date across all queries in database"""
        with self.db.get_session() as session:
            latest_paper = session.query(Paper).order_by(Paper.published.desc()).first()
            return latest_paper.published if latest_paper else None

    def get_sync_description(self, years_back: int, force: bool) -> str:
        """获取同步描述

        Args:
            years_back: 回溯的年数
            force: 是否强制模式

        Returns:
            str: 同步描述
        """
        if force:
            start_date = datetime.now(UTC) - timedelta(days=365 * years_back)
            return f"同步 {years_back} 年 (从 {start_date.strftime('%Y-%m-%d')} 到现在)"

        latest_date = self.get_latest_paper_date_for_any_query()

        if latest_date is None:
            return f"首次同步 {years_back} 年"

        days_since_sync = (datetime.now(UTC) - latest_date.replace(tzinfo=UTC)).days

        if days_since_sync > years_back * 365:
            return f"同步 {years_back} 年 (上次: {latest_date.strftime('%Y-%m-%d')}，距离现在已超过 {years_back} 年)"

        return f"同步最近 {days_since_sync} 天 (上次: {latest_date.strftime('%Y-%m-%d')})"

    def sync_query(
        self, query: str, years_back: int = 3, force: bool = False, arxiv_max_results: int | None = None
    ) -> dict[str, Any]:
        """Sync papers for a specific query, fetching missing papers from recent years

        Args:
            query: arXiv search query
            years_back: Number of years to look back
            force: If True, continue fetching all papers within time range,
                   skip existing papers only (don't stop early)
            arxiv_max_results: Maximum papers to fetch from arXiv API (default: Config.ARXIV_MAX_RESULTS)
        """
        output.do(f"同步查询: {query}" + (" (强制模式)" if force else ""))

        max_results = int(arxiv_max_results) if arxiv_max_results is not None else int(Config.ARXIV_MAX_RESULTS)

        cutoff_date = datetime.now(UTC) - timedelta(days=365 * years_back)

        if force:
            output.debug(f"强制同步: 获取最近 {years_back} 年的所有论文 ({cutoff_date.strftime('%Y-%m-%d')} 到现在)")
            output.debug(f"跳过已有论文，继续获取直到达到时间范围")
        else:
            latest_date = self.get_latest_paper_date_for_query(query)
            if latest_date:
                cutoff_date = latest_date.replace(tzinfo=UTC) - timedelta(days=1)
                output.debug(f"增量同步: 从 {cutoff_date.strftime('%Y-%m-%d')} 到现在 (遇到已有论文则停止)")
            else:
                output.debug(f"首次同步: 获取最近 {years_back} 年的论文 ({cutoff_date.strftime('%Y-%m-%d')} 到现在)")

        output.debug(f"最大返回论文数: {max_results}")

        try:
            papers = self.search_arxiv(
                query,
                max_results=max_results,
                cutoff_date=cutoff_date,
            )

            new_papers = self.filter_new_papers(papers)
            saved = self.save_papers(new_papers, query)

            output.done(f"同步完成: 查询 {len(papers)} 篇，新增 {len(saved)} 篇")

            if force:
                existing_count = len(papers) - len(new_papers)
                if existing_count > 0:
                    output.info(f"跳过 {existing_count} 篇已存在的论文")
                if len(papers) >= max_results:
                    output.info(f"达到最大返回限制 ({max_results})，可能还有更多论文")
            elif len(new_papers) < len(papers) and len(papers) < max_results:
                output.info(f"遇到已有论文，提前停止。已查询 {len(papers)} 篇")

            time.sleep(1)

            return {
                "query": query,
                "start_date": cutoff_date,
                "total_found": len(papers),
                "new_papers": len(saved),
                "saved_papers": saved,
                "force_mode": force,
            }

        except Exception as e:
            output.error(f"同步查询失败: {query}", details={"exception": str(e)})
            return {"query": query, "error": str(e), "new_papers": 0, "force_mode": force}

    def sync_all_queries(
        self, years_back: int = 3, force: bool = False, arxiv_max_results: int | None = None
    ) -> dict[str, Any]:
        """Sync all configured search queries

        Args:
            years_back: Number of years to look back
            force: If True, continue querying even after encountering existing papers,
                  skip existing papers only (no download)
            arxiv_max_results: Maximum papers to fetch from arXiv API (default: Config.ARXIV_MAX_RESULTS)
        """
        sync_description = self.get_sync_description(years_back, force)
        output.do(f"同步所有查询 ({sync_description})" + (" (强制模式)" if force else ""))

        if arxiv_max_results is None:
            arxiv_max_results = Config.ARXIV_MAX_RESULTS

        all_results = []
        total_new = 0

        for query in self.config.SEARCH_QUERIES:
            result = self.sync_query(query, years_back, force, arxiv_max_results)
            all_results.append(result)
            total_new += result.get("new_papers", 0)

        output.done(f"同步完成: 共 {total_new} 篇论文")
        return {
            "total_new_papers": total_new,
            "query_results": all_results,
            "years_back": years_back,
            "force_mode": force,
            "arxiv_max_results": arxiv_max_results,
        }

    def fetch_paper_by_id(self, arxiv_id: str) -> Paper | None:
        """Fetch a single paper from arXiv by ID and save to database

        Args:
            arxiv_id: arXiv ID (e.g., 2602.09790 or 2602.09790v1)

        Returns:
            Paper object if found, None otherwise
        """
        clean_id = arxiv_id.strip()

        if clean_id.startswith("arXiv:"):
            clean_id = clean_id[6:]

        if "arxiv.org" in clean_id:
            import re

            match = re.search(r"(\d{4}\.\d{4,5}(v\d+)?)", clean_id)
            if match:
                clean_id = match.group(1)

        if "v" in clean_id:
            clean_id = clean_id.split("v")[0]

        if self.db.paper_exists(clean_id):
            output.debug(f"论文已在数据库中: {clean_id}")
            with self.db.get_session() as session:
                return session.query(Paper).filter_by(arxiv_id=clean_id).first()

        try:
            search = arxiv.Search(id_list=[clean_id])
            results = list(self.client.results(search))
            output.debug(f"arXiv API 返回 {len(results)} 条结果")

            if results:
                paper = results[0]
                paper_obj = Paper.from_arxiv_entry(paper, "quick_fetch")
                paper_id = self.db.add_paper(paper_obj)
                output.done(f"已获取论文: {clean_id} (ID: {paper_id})")
                return paper_obj
            else:
                output.warn(f"未找到论文: {clean_id}")
                return None

        except Exception as e:
            output.error(f"获取论文失败: {clean_id}", details={"exception": str(e)})
            import traceback

            traceback.print_exc()
            return None

    def search_and_save(self, query: str, max_results: int = 15) -> tuple[list[Paper], int, int]:
        """Search arXiv by query and save new papers to database

        Args:
            query: Search query string
            max_results: Maximum results to fetch from arXiv

        Returns:
            Tuple of (list of Paper objects, total found, new papers count)
        """
        try:
            results = self.search_arxiv(query=query, max_results=max_results)
            if not results:
                return [], 0, 0

            total = len(results)
            new_papers = []
            saved_papers = []

            with self.db.get_session() as session:
                for result in results:
                    arxiv_id = result.entry_id.split("/")[-1]
                    if "v" in arxiv_id:
                        arxiv_id = arxiv_id.split("v")[0]

                    existing = session.query(Paper).filter_by(arxiv_id=arxiv_id).first()
                    if existing:
                        saved_papers.append(existing)
                    else:
                        paper_obj = Paper.from_arxiv_entry(result, f"remote_search:{query}")
                        session.add(paper_obj)
                        new_papers.append(paper_obj)
                        saved_papers.append(paper_obj)

                session.commit()

                for p in saved_papers:
                    session.refresh(p)

            output.debug(f"远程搜索 '{query}': 找到 {total} 篇，新增 {len(new_papers)} 篇")
            return saved_papers, total, len(new_papers)

        except Exception as e:
            output.error(f"远程搜索失败: {query}", details={"exception": str(e)})
            return [], 0, 0

    def get_crawler_stats(self) -> dict[str, Any]:
        """Get crawler statistics"""
        with self.db.get_session() as session:
            total = session.query(Paper).count()
            today = datetime.now().date()
            today_start = datetime.combine(today, datetime.min.time())
            today_count = session.query(Paper).filter(Paper.created_at >= today_start).count()

            by_query = {}
            papers = session.query(Paper).all()
            for paper in papers:
                query = paper.search_query
                by_query[query] = by_query.get(query, 0) + 1

            return {
                "total_papers": total,
                "papers_today": today_count,
                "papers_by_query": by_query,
            }
