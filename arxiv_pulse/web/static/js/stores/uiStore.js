const useUiStore = defineStore('ui', () => {
    const currentPage = ref('home');
    const expandedGroups = ref({});
    const cacheStats = ref(null);
    const cacheClearing = ref(null);
    
    const syncing = ref(false);
    const syncLogs = ref([]);
    const syncYearsBack = ref(5);
    const syncForce = ref(false);
    const syncStatus = ref(null);
    
    function navigateTo(page) {
        currentPage.value = page;
    }
    
    function formatRelativeTime(dateStr, configStore) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        const now = new Date();
        const diff = now - date;
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        const isZh = configStore.currentLang === 'zh';
        
        if (days === 0) return isZh ? '今天' : 'today';
        if (days === 1) return isZh ? '昨天' : 'yesterday';
        if (days < 7) return isZh ? `${days} 天前` : `${days} days ago`;
        if (days < 30) return isZh ? `${Math.floor(days / 7)} 周前` : `${Math.floor(days / 7)} weeks ago`;
        if (days < 365) return isZh ? `${Math.floor(days / 30)} 月前` : `${Math.floor(days / 30)} months ago`;
        return isZh ? `${Math.floor(days / 365)} 年前` : `${Math.floor(days / 365)} years ago`;
    }
    
    function formatDate(dateStr) {
        if (!dateStr) return '';
        return new Date(dateStr).toLocaleDateString('zh-CN');
    }
    
    async function fetchSyncStatus() {
        try {
            const res = await API.tasks.status();
            syncStatus.value = await res.json();
        } catch (e) {
            console.error('Failed to fetch sync status:', e);
        }
    }
    
    async function startSync(configStore) {
        syncing.value = true;
        syncLogs.value = [];
        try {
            const params = new URLSearchParams({
                years_back: syncYearsBack.value,
                force: syncForce.value
            });
            
            const response = await API.tasks.sync(params.toString());
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
                                syncLogs.value.push({ type: data.level || 'info', message: data.message });
                            } else if (data.type === 'done') {
                                syncLogs.value.push({ type: 'success', message: configStore.currentLang === 'zh' ? '同步完成' : 'Sync completed' });
                            } else if (data.type === 'error') {
                                syncLogs.value.push({ type: 'error', message: data.message });
                            }
                        } catch (e) {}
                    }
                }
            }
        } catch (e) {
            syncLogs.value.push({ type: 'error', message: `同步出错: ${e.message}` });
        } finally {
            syncing.value = false;
        }
    }
    
    async function fetchCacheStats() {
        try {
            const res = await API.cache.stats();
            cacheStats.value = await res.json();
        } catch (e) {
            console.error('Failed to fetch cache stats:', e);
        }
    }
    
    async function clearCache(type, configStore) {
        const typeNames = {
            translations: configStore.currentLang === 'zh' ? '翻译缓存' : 'translation cache',
            summaries: configStore.currentLang === 'zh' ? 'AI 总结' : 'AI summaries',
            figures: configStore.currentLang === 'zh' ? '图片缓存' : 'figure cache',
            contents: configStore.currentLang === 'zh' ? '内容缓存' : 'content cache',
            all: configStore.currentLang === 'zh' ? '所有缓存' : 'all cache'
        };
        
        const confirmMsg = type === 'all' 
            ? configStore.t('cache.confirmAll')
            : configStore.t('cache.confirmClear').replace('{type}', typeNames[type]);
        
        try {
            await ElementPlus.ElMessageBox.confirm(confirmMsg, configStore.t('common.confirm'), {
                confirmButtonText: configStore.t('common.confirm'),
                cancelButtonText: configStore.t('common.cancel'),
                type: 'warning'
            });
        } catch {
            return;
        }
        
        cacheClearing.value = type;
        try {
            const res = await API.cache.clear(type);
            const data = await res.json();
            if (res.ok) {
                ElementPlus.ElMessage.success(configStore.currentLang === 'zh' ? '已清理' : 'Cleared');
                fetchCacheStats();
            } else {
                ElementPlus.ElMessage.error(data.detail || 'Failed');
            }
        } catch (e) {
            ElementPlus.ElMessage.error('Failed');
        } finally {
            cacheClearing.value = null;
        }
    }
    
    return {
        currentPage, expandedGroups, cacheStats, cacheClearing,
        syncing, syncLogs, syncYearsBack, syncForce, syncStatus,
        navigateTo, formatRelativeTime, formatDate,
        fetchSyncStatus, startSync, fetchCacheStats, clearCache
    };
});
