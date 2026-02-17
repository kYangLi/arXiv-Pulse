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
        toggleHomeSelection, addToCart, removeFromCart, clearCart, isInCart,
        fetchStats, fetchFieldStats, fetchRecentCache, updateRecentPapers,
        searchPapers, startHomeSearch, exportPapers
    };
});
