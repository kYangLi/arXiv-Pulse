import arxiv
import asyncio
import aiohttp
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from tqdm import tqdm
import time
import logging

from arxiv_pulse.models import Database, Paper
from arxiv_pulse.config import Config
from arxiv_pulse.output_manager import output

# 使用根日志记录器的配置（保留用于向后兼容）
logger = logging.getLogger(__name__)


class ArXivCrawler:
    def __init__(self):
        self.db = Database()
        # 配置arXiv客户端，遵守调用频率限制
        self.client = arxiv.Client(page_size=100, delay_seconds=3.0, num_retries=3)
        self.config = Config

        # 抑制第三方库的详细日志
        logging.getLogger("arxiv").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)

    def search_arxiv(
        self,
        query: str,
        max_results: int = 100,
        days_back: Optional[int] = None,
        cutoff_date: Optional[datetime] = None,
    ) -> List[arxiv.Result]:
        """Search arXiv for papers matching query

        Args:
            query: arXiv search query
            max_results: Maximum number of results to return
            days_back: Optional number of days to look back (deprecated, use cutoff_date)
            cutoff_date: Optional UTC datetime cutoff; papers older than this will be skipped
                         and iteration will stop early due to descending date order.
        """
        # Map sort_by string to arxiv enum
        sort_by_map = {
            "submittedDate": arxiv.SortCriterion.SubmittedDate,
            "lastUpdatedDate": arxiv.SortCriterion.LastUpdatedDate,
            "relevance": arxiv.SortCriterion.Relevance,
        }
        sort_by = sort_by_map.get(Config.ARXIV_SORT_BY, arxiv.SortCriterion.SubmittedDate)

        # Map sort_order string to arxiv enum
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
            # If cutoff date is provided, check paper date
            if cutoff_date is not None and hasattr(paper, "published") and paper.published:
                # Convert paper.published to UTC aware datetime
                if paper.published.tzinfo is None:
                    # Assume naive datetime is UTC
                    paper_date = paper.published.replace(tzinfo=timezone.utc)
                else:
                    paper_date = paper.published.astimezone(timezone.utc)

                if paper_date < cutoff_date:
                    output.debug(f"遇到旧论文 ({paper_date.date()})，停止爬取")
                    break

            results.append(paper)

            # Safety: don't exceed max_results even if cutoff_date not reached
            if len(results) >= max_results:
                break

        output.debug(f"Found {len(results)} papers for query: {query}")
        return results

    def filter_new_papers(self, papers: List[arxiv.Result]) -> List[arxiv.Result]:
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

    def save_papers(self, papers: List[arxiv.Result], search_query: str) -> List[Paper]:
        """Save papers to database"""
        saved_papers = []
        for paper in tqdm(papers, desc="Saving papers"):
            try:
                # Check again to avoid race conditions
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

    def initial_crawl(self) -> Dict[str, Any]:
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
                time.sleep(1)  # Be nice to arXiv API

            except Exception as e:
                output.error(f"爬取查询失败: {query}", details={"exception": str(e)})

        output.done(f"初始爬取完成: 共保存 {len(all_saved)} 篇论文")
        return {
            "total_saved": len(all_saved),
            "queries_searched": len(self.config.SEARCH_QUERIES),
            "saved_papers": all_saved,
        }

    def daily_update(self) -> Dict[str, Any]:
        """Perform daily update crawl with early stopping optimization"""
        output.do("开始每日更新")
        all_saved = []

        # 使用2天的时间窗口，因为arXiv通常在UTC 00:00-02:00更新
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=2)
        output.info(f"查找 {cutoff_date.date()} 之后的新论文")

        for query in self.config.SEARCH_QUERIES:
            output.do(f"搜索: {query}")
            try:
                # 使用cutoff_date参数实现早期终止
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

    def crawl_by_categories(self, categories: List[str], max_results: int = 64) -> Dict[str, Any]:
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

    def get_latest_paper_date_for_query(self, query: str) -> Optional[datetime]:
        """Get the latest paper date for a specific query in database"""
        with self.db.get_session() as session:
            latest_paper = (
                session.query(Paper).filter(Paper.search_query == query).order_by(Paper.published.desc()).first()
            )
            return latest_paper.published if latest_paper else None  # type: ignore

    def get_latest_paper_date_for_any_query(self) -> Optional[datetime]:
        """Get the latest paper date across all queries in database"""
        with self.db.get_session() as session:
            latest_paper = session.query(Paper).order_by(Paper.published.desc()).first()
            return latest_paper.published if latest_paper else None  # type: ignore

    def sync_query(
        self, query: str, years_back: int = 3, force: bool = False, arxiv_max_results: Optional[int] = None
    ) -> Dict[str, Any]:
        """Sync papers for a specific query, fetching missing papers from recent years

        Args:
            query: arXiv search query
            years_back: Number of years to look back
            force: If True, continue querying even after encountering existing papers,
                  skip existing papers only (no download)
            arxiv_max_results: Maximum papers to fetch from arXiv API (default: Config.ARXIV_MAX_RESULTS)
            arxiv_max_results: Maximum papers to fetch from arXiv API (default: Config.ARXIV_MAX_RESULTS)
        """
        output.do(f"同步查询: {query}" + (" (强制模式)" if force else ""))

        # Set max_results
        if arxiv_max_results is None:
            arxiv_max_results = Config.ARXIV_MAX_RESULTS

        if force:
            # Force mode: always start from years_back years ago, continue querying
            start_date = datetime.now(timezone.utc) - timedelta(days=365 * years_back)
            output.debug(f"强制同步: 获取最近 {years_back} 年的所有论文 ({start_date.strftime('%Y-%m-%d')} 到现在)")
            output.debug(f"最大返回论文数: {arxiv_max_results}")
        else:
            # Normal mode: get latest paper date in database for this query
            latest_date = self.get_latest_paper_date_for_query(query)

            if latest_date:
                # If we have papers, fetch from latest date onward
                start_date = latest_date.replace(tzinfo=timezone.utc)
                # 减去一天以确保获取所有可能的新论文，避免因时间精度问题错过论文
                start_date = start_date - timedelta(days=1)
                output.debug(f"获取论文从 {start_date.strftime('%Y-%m-%d')} 到现在")
                output.debug(f"最大返回论文数: {arxiv_max_results}")
            else:
                # If no papers, fetch from years_back years ago
                start_date = datetime.now(timezone.utc) - timedelta(days=365 * years_back)
                output.debug(f"获取最近 {years_back} 年的论文 ({start_date.strftime('%Y-%m-%d')} 到现在)")
                output.debug(f"最大返回论文数: {arxiv_max_results}")

        # Search arXiv with cutoff_date for early stopping
        try:
            papers = self.search_arxiv(
                query,
                max_results=arxiv_max_results,
                cutoff_date=start_date,
            )

            # Always filter out existing papers (even in force mode)
            new_papers = self.filter_new_papers(papers)
            saved = self.save_papers(new_papers, query)

            output.done(f"同步完成: {len(saved)} 篇新论文")

            if force:
                # Force mode: check if we hit the limit
                if len(papers) >= arxiv_max_results:
                    output.info(f"达到最大返回论文数限制 ({arxiv_max_results})，可能还有更多论文未获取")
                else:
                    output.info(f"查询完成，共找到 {len(papers)} 篇论文")
            else:
                # Normal mode: check if we stopped early due to existing papers
                if len(papers) < arxiv_max_results and len(new_papers) < len(papers):
                    output.info(
                        f"遇到已存在的论文，提前停止同步。共查询 {len(papers)} 篇，其中 {len(papers) - len(new_papers)} 篇已存在"
                    )

            time.sleep(1)  # Rate limiting

            return {
                "query": query,
                "start_date": start_date,
                "total_found": len(papers),
                "new_papers": len(saved),
                "saved_papers": saved,
                "force_mode": force,
            }

        except Exception as e:
            output.error(f"同步查询失败: {query}", details={"exception": str(e)})
            return {"query": query, "error": str(e), "new_papers": 0, "force_mode": force}

    def sync_all_queries(
        self, years_back: int = 3, force: bool = False, arxiv_max_results: Optional[int] = None
    ) -> Dict[str, Any]:
        """Sync all configured search queries

        Args:
            years_back: Number of years to look back
            force: If True, continue querying even after encountering existing papers,
                  skip existing papers only (no download)
            arxiv_max_results: Maximum papers to fetch from arXiv API (default: Config.ARXIV_MAX_RESULTS)
        """
        output.do(f"同步所有查询 (回溯 {years_back} 年)" + (" (强制模式)" if force else ""))

        # Set max_results
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

    def sync_important_papers(self) -> Dict[str, Any]:
        """Ensure important papers are in database"""
        important_file = Config.IMPORTANT_PAPERS_FILE
        if not os.path.exists(important_file):
            output.warn(f"重要论文文件未找到: {important_file}")
            return {"total_processed": 0, "added": 0, "errors": []}

        added = 0
        errors = []

        with open(important_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Extract arXiv ID (format: 1234.56789v1 or 1234.56789)
                arxiv_id = line.split()[0] if " " in line else line

                # Remove version suffix if present
                if "v" in arxiv_id:
                    arxiv_id = arxiv_id.split("v")[0]

                # Check if paper already exists
                if self.db.paper_exists(arxiv_id):
                    output.debug(f"重要论文已在数据库中: {arxiv_id}")
                    continue

                # Try to fetch paper from arXiv
                try:
                    search = arxiv.Search(id_list=[arxiv_id])
                    results = list(self.client.results(search))

                    if results:
                        paper = results[0]
                        paper_obj = Paper.from_arxiv_entry(paper, "important")
                        self.db.add_paper(paper_obj)
                        added += 1
                        output.done(f"添加重要论文: {arxiv_id}")
                    else:
                        errors.append(f"Paper not found on arXiv: {arxiv_id}")

                except Exception as e:
                    errors.append(f"Error fetching paper {arxiv_id}: {e}")

                time.sleep(0.5)  # Rate limiting

        return {
            "total_processed": added + len(errors),
            "added": added,
            "errors": errors,
        }

    def get_crawler_stats(self) -> Dict[str, Any]:
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


def main():
    """Test the crawler"""
    crawler = ArXivCrawler()

    print("Testing arXiv crawler...")
    print(f"Search queries: {Config.SEARCH_QUERIES}")

    # Test with a small crawl
    test_query = Config.SEARCH_QUERIES[0]
    print(f"\nTesting search for: {test_query}")

    papers = crawler.search_arxiv(test_query, max_results=5)
    print(f"Found {len(papers)} papers")

    if papers:
        paper = papers[0]
        print(f"\nSample paper:")
        print(f"Title: {paper.title[:100]}...")
        print(f"Authors: {[author.name for author in paper.authors[:3]]}")
        print(f"Published: {paper.published}")
        print(f"Categories: {paper.categories if hasattr(paper, 'categories') else paper.primary_category}")

    # Get stats
    stats = crawler.get_crawler_stats()
    print(f"\nDatabase stats:")
    print(f"Total papers: {stats['total_papers']}")
    print(f"Papers today: {stats['papers_today']}")


if __name__ == "__main__":
    main()
