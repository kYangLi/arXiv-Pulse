const usePaperStore = defineStore('paper', () => {
    const recentPapers = ref([]);
    const loadingRecent = ref(true);
    const loadingProgress = ref(0);
    const loadingTotal = ref(0);
    const loadingController = ref(null);
    const updatingRecent = ref(false);
    const recentLogs = ref([]);
    const recentDays = ref('7');
    const recentNeedSync = ref(true);
    const recentSelectedIds = ref([]);
    
    const homeQuery = ref('');
    const homeSearching = ref(false);
    const homeLogs = ref([]);
    const homeResults = ref([]);
    const homeSelectedIds = ref([]);
    
    const searchQuery = ref('');
    const searching = ref(false);
    const searchLogs = ref([]);
    const searchResults = ref([]);
    const searchSelectedIds = ref([]);
    
    const paperCart = ref([]);
    const showCart = ref(false);
    const cartExportLoading = ref(false);
    const cartPosition = ref({ x: window.innerWidth - 424, y: window.innerHeight - 520 });
    const cartPanelRef = ref(null);
    const cartZIndex = ref(1000);
    
    const stats = ref(null);
    const fieldStats = ref([]);
    
    function toggleRecentSelection(paperId) {
        const idx = recentSelectedIds.value.indexOf(paperId);
        if (idx >= 0) {
            recentSelectedIds.value.splice(idx, 1);
        } else {
            recentSelectedIds.value.push(paperId);
        }
    }
    
    function toggleAllRecent() {
        if (recentSelectedIds.value.length !== recentPapers.value.length) {
            recentSelectedIds.value = recentPapers.value.map(p => p.id);
        } else {
            recentSelectedIds.value = [];
        }
    }
    
    function toggleSearchSelection(paperId) {
        const idx = searchSelectedIds.value.indexOf(paperId);
        if (idx >= 0) {
            searchSelectedIds.value.splice(idx, 1);
        } else {
            searchSelectedIds.value.push(paperId);
        }
    }
    
    function toggleAllSearch() {
        if (searchSelectedIds.value.length !== searchResults.value.length) {
            searchSelectedIds.value = searchResults.value.map(p => p.id);
        } else {
            searchSelectedIds.value = [];
        }
    }
    
    function toggleHomeSelection(paperId) {
        const idx = homeSelectedIds.value.indexOf(paperId);
        if (idx >= 0) {
            homeSelectedIds.value.splice(idx, 1);
        } else {
            homeSelectedIds.value.push(paperId);
        }
    }
    
    function addToCart(paper) {
        if (!paperCart.value.find(p => p.arxiv_id === paper.arxiv_id)) {
            paperCart.value.push(paper);
        }
    }
    
    function removeFromCart(arxivId) {
        const idx = paperCart.value.findIndex(p => p.arxiv_id === arxivId);
        if (idx >= 0) {
            paperCart.value.splice(idx, 1);
        }
    }
    
    function clearCart() {
        paperCart.value = [];
    }
    
    function isInCart(arxivId) {
        return paperCart.value.some(p => p.arxiv_id === arxivId);
    }
    
    function exportCart(format) {
        if (paperCart.value.length === 0) return;
        
        const papersWithId = paperCart.value.filter(p => p.id);
        const filename = `papers_export_${Date.now()}`;
        
        if (format === 'pdf') {
            if (papersWithId.length === 0) {
                ElementPlus.ElMessage.warning('PDF 导出需要论文已保存到数据库，请先同步论文');
                return;
            }
            API.export.papers({ 
                paper_ids: papersWithId.map(p => p.id), 
                format: 'pdf',
                include_summary: true 
            }).then(res => {
                if (res.ok) {
                    return res.blob();
                }
                throw new Error('Export failed');
            }).then(blob => {
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${filename}.pdf`;
                a.click();
                URL.revokeObjectURL(url);
            }).catch(() => {
                ElementPlus.ElMessage.error('导出失败');
            });
            return;
        }
        
        if (format === 'pdf_original') {
            ElementPlus.ElMessage.info(`开始下载 ${paperCart.value.length} 个 PDF 原文...`);
            let successCount = 0;
            const downloadNext = async (index) => {
                if (index >= paperCart.value.length) {
                    if (successCount > 0) {
                        ElementPlus.ElMessage.success(`已下载 ${successCount} 个 PDF 原文`);
                    } else {
                        ElementPlus.ElMessage.error('下载失败');
                    }
                    return;
                }
                const paper = paperCart.value[index];
                try {
                    const res = await API.papers.pdf(paper.arxiv_id);
                    if (res.ok) {
                        const blob = await res.blob();
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        const safeId = paper.arxiv_id.replace(/[\/\\]/g, '_');
                        a.download = `${safeId}.pdf`;
                        a.click();
                        URL.revokeObjectURL(url);
                        successCount++;
                        await new Promise(r => setTimeout(r, 300));
                    }
                } catch (e) {
                    console.error(`Failed to download ${paper.arxiv_id}:`, e);
                }
                downloadNext(index + 1);
            };
            downloadNext(0);
            return;
        }
        
        const downloadFile = (content, filename, mimeType) => {
            const blob = new Blob([content], { type: mimeType });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.click();
            URL.revokeObjectURL(url);
        };
        
        let content = '';
        
        if (format === 'markdown') {
            content = paperCart.value.map(p => {
                return `## ${p.title}\n\n**arXiv:** ${p.arxiv_id}\n**作者:** ${p.authors?.map(a => a.name).join(', ') || 'N/A'}\n**日期:** ${p.published || 'N/A'}\n\n**摘要:**\n${p.abstract || ''}\n\n${p.summary_text ? '**AI 总结:**\n' + p.summary_text : ''}\n\n---\n`;
            }).join('\n');
            downloadFile(content, `${filename}.md`, 'text/markdown');
        } else if (format === 'csv') {
            const header = 'arxiv_id,title,authors,published,abstract\n';
            const rows = paperCart.value.map(p => {
                const title = (p.title || '').replace(/"/g, '""');
                const authors = (p.authors?.map(a => a.name).join('; ') || '').replace(/"/g, '""');
                const abstract = (p.abstract || '').replace(/"/g, '""').replace(/\n/g, ' ');
                return `"${p.arxiv_id}","${title}","${authors}","${p.published || ''}","${abstract}"`;
            }).join('\n');
            downloadFile(header + rows, `${filename}.csv`, 'text/csv');
        } else if (format === 'bibtex') {
            content = paperCart.value.map(p => {
                const year = p.published ? new Date(p.published).getFullYear() : new Date().getFullYear();
                const firstAuthor = p.authors?.[0]?.name?.split(' ').pop() || 'Unknown';
                const key = `${firstAuthor}${year}${p.arxiv_id.replace('.', '')}`;
                return `@article{${key},\n  title={${p.title || 'Untitled'}},\n  author={${p.authors?.map(a => a.name).join(' and ') || 'Unknown'}},\n  journal={arXiv preprint arXiv:${p.arxiv_id}},\n  year={${year}},\n  eprint={${p.arxiv_id}}\n}`;
            }).join('\n\n');
            downloadFile(content, `${filename}.bib`, 'application/x-bibtex');
        }
    }
    
    function copyCartLinks() {
        if (paperCart.value.length === 0) return;
        const links = paperCart.value.map(p => `https://arxiv.org/abs/${p.arxiv_id}`).join('\n');
        
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(links).then(() => {
                ElementPlus.ElMessage.success(`已复制 ${paperCart.value.length} 个链接`);
            }).catch(() => {
                const textarea = document.createElement('textarea');
                textarea.value = links;
                textarea.style.position = 'fixed';
                textarea.style.left = '-9999px';
                document.body.appendChild(textarea);
                textarea.select();
                document.execCommand('copy');
                document.body.removeChild(textarea);
                ElementPlus.ElMessage.success(`已复制 ${paperCart.value.length} 个链接`);
            });
        } else {
            const textarea = document.createElement('textarea');
            textarea.value = links;
            textarea.style.position = 'fixed';
            textarea.style.left = '-9999px';
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
            ElementPlus.ElMessage.success(`已复制 ${paperCart.value.length} 个链接`);
        }
    }
    
    async function fetchStats() {
        try {
            const res = await API.stats.get();
            stats.value = await res.json();
        } catch (e) {
            console.error('Failed to fetch stats:', e);
        }
    }
    
    async function fetchFieldStats() {
        try {
            const res = await API.stats.fields();
            const data = await res.json();
            fieldStats.value = data.fields || [];
        } catch (e) {
            console.error('Failed to fetch field stats:', e);
        }
    }
    
    async function fetchRecentCache() {
        loadingRecent.value = true;
        loadingProgress.value = 0;
        loadingTotal.value = 0;
        recentPapers.value = [];
        
        const controller = new AbortController();
        loadingController.value = controller;
        
        try {
            const response = await API.papers.recentCacheStream('');
            response.body.cancel = () => controller.abort();
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            if (data.type === 'log') {
                                recentLogs.value.push({ type: 'info', message: data.message });
                            } else if (data.type === 'paper') {
                                recentPapers.value.push(data.paper);
                                loadingProgress.value++;
                            } else if (data.type === 'total') {
                                loadingTotal.value = data.total;
                            } else if (data.type === 'done') {
                                recentNeedSync.value = data.need_sync || false;
                                if (recentPapers.value.length === 0) {
                                    recentLogs.value.push({ type: 'info', message: '暂无数据，请先同步论文' });
                                }
                            } else if (data.type === 'error') {
                                recentLogs.value.push({ type: 'error', message: data.message });
                            }
                        } catch (e) {}
                    }
                }
            }
        } catch (e) {
            if (e.name !== 'AbortError') {
                console.error('Failed to fetch recent papers:', e);
                recentLogs.value.push({ type: 'error', message: `加载失败: ${e.message}` });
            }
        } finally {
            loadingRecent.value = false;
        }
    }
    
    async function updateRecentPapers(configStore) {
        updatingRecent.value = true;
        recentLogs.value = [];
        
        try {
            const params = new URLSearchParams({
                days: recentDays.value,
                limit: configStore.settingsConfig.recent_papers_limit || 64
            });
            
            const response = await API.papers.recentUpdate(params.toString());
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            if (data.type === 'log') {
                                recentLogs.value.push({ type: 'info', message: data.message });
                            } else if (data.type === 'paper') {
                                recentPapers.value.unshift(data.paper);
                            } else if (data.type === 'done') {
                                recentNeedSync.value = false;
                            } else if (data.type === 'error') {
                                recentLogs.value.push({ type: 'error', message: data.message });
                            }
                        } catch (e) {}
                    }
                }
            }
        } catch (e) {
            recentLogs.value.push({ type: 'error', message: `更新失败: ${e.message}` });
        } finally {
            updatingRecent.value = false;
        }
    }
    
    async function searchPapers(configStore) {
        if (!searchQuery.value.trim()) return;
        
        searching.value = true;
        searchLogs.value = [];
        searchResults.value = [];
        searchSelectedIds.value = [];
        
        try {
            const params = new URLSearchParams({
                q: searchQuery.value,
                limit: configStore.settingsConfig.search_limit || 20
            });
            
            const response = await API.papers.searchStream(params.toString());
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            if (data.type === 'log') {
                                searchLogs.value.push({ type: 'info', message: data.message });
                            } else if (data.type === 'result') {
                                searchResults.value.push(data.paper);
                            } else if (data.type === 'done') {
                                if (data.total === 0) {
                                    searchLogs.value.push({ type: 'info', message: '未找到匹配的论文' });
                                }
                            } else if (data.type === 'error') {
                                searchLogs.value.push({ type: 'error', message: data.message });
                            }
                        } catch (e) {}
                    }
                }
            }
        } catch (e) {
            searchLogs.value.push({ type: 'error', message: `搜索失败: ${e.message}` });
        } finally {
            searching.value = false;
        }
    }
    
    async function startHomeSearch(configStore) {
        if (!homeQuery.value.trim()) return;
        
        homeSearching.value = true;
        homeLogs.value = [];
        homeResults.value = [];
        homeSelectedIds.value = [];
        
        try {
            const params = new URLSearchParams({ q: homeQuery.value });
            const response = await API.papers.quick(params.toString());
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            if (data.type === 'log') {
                                homeLogs.value.push({ type: 'info', message: data.message });
                            } else if (data.type === 'result') {
                                homeResults.value.push(data.paper);
                            } else if (data.type === 'done') {
                                if (data.total === 0) {
                                    homeLogs.value.push({ type: 'info', message: '未找到匹配的论文' });
                                }
                            } else if (data.type === 'error') {
                                homeLogs.value.push({ type: 'error', message: data.message });
                            }
                        } catch (e) {}
                    }
                }
            }
        } catch (e) {
            homeLogs.value.push({ type: 'error', message: `搜索失败: ${e.message}` });
        } finally {
            homeSearching.value = false;
        }
    }
    
    async function exportPapers(paperIds, format, configStore) {
        try {
            const res = await API.export.papers({
                paper_ids: paperIds,
                format: format,
                include_summary: true
            });
            if (!res.ok) throw new Error('Export failed');
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            const ext = format === 'markdown' ? 'md' : format === 'bibtex' ? 'bib' : format;
            a.download = `papers.${ext}`;
            a.click();
            window.URL.revokeObjectURL(url);
            ElementPlus.ElMessage.success(`已导出 ${paperIds.length} 篇论文`);
        } catch (e) {
            ElementPlus.ElMessage.error('导出失败');
        }
    }
    
    return {
        recentPapers, loadingRecent, loadingProgress, loadingTotal, loadingController,
        updatingRecent, recentLogs, recentDays, recentNeedSync, recentSelectedIds,
        homeQuery, homeSearching, homeLogs, homeResults, homeSelectedIds,
        searchQuery, searching, searchLogs, searchResults, searchSelectedIds,
        paperCart, showCart, cartExportLoading, cartPosition, cartPanelRef, cartZIndex,
        stats, fieldStats,
        toggleRecentSelection, toggleAllRecent, toggleSearchSelection, toggleAllSearch,
        toggleHomeSelection, addToCart, removeFromCart, clearCart, isInCart, exportCart, copyCartLinks,
        fetchStats, fetchFieldStats, fetchRecentCache, updateRecentPapers,
        searchPapers, startHomeSearch, exportPapers
    };
});
