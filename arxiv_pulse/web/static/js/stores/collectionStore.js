const useCollectionStore = defineStore('collection', () => {
    const collections = ref([]);
    const viewingCollection = ref(null);
    const collectionPapers = ref([]);
    const collectionCurrentPage = ref(1);
    const collectionTotalCount = ref(0);
    const collectionTotalPages = ref(0);
    const collectionPaperSearch = ref('');
    const loadingCollectionPapers = ref(false);
    const useAiSearch = ref(false);
    const aiSearching = ref(false);
    const collectionViewMode = ref('card');
    const collectionSearchQuery = ref('');
    const collectionSortBy = ref('published');
    const collectionSortOrder = ref('desc');
    
    const showCreateCollection = ref(false);
    const savingCollection = ref(false);
    const editingCollection = ref(null);
    const newCollection = ref({ name: '', description: '', color: '#1e3a5f' });
    
    const showDeleteConfirm = ref(false);
    const deletingCollection = ref(null);
    const deletingCollectionInProgress = ref(false);
    
    const showMergeConfirmDialog = ref(false);
    const mergingFromCollection = ref(null);
    const mergingToCollection = ref(null);
    const mergingInProgress = ref(false);
    
    const selectedCollectionId = ref(null);
    const showCollectionDetail = ref(false);
    const showAddToCollection = ref(false);
    const selectedPaper = ref(null);
    const addingToCollection = ref(false);
    
    const filteredCollections = computed(() => {
        if (!collectionSearchQuery.value) return collections.value;
        const query = collectionSearchQuery.value.toLowerCase();
        return collections.value.filter(c => 
            c.name.toLowerCase().includes(query) || 
            (c.description && c.description.toLowerCase().includes(query))
        );
    });
    
    async function fetchCollections() {
        try {
            const res = await API.collections.list();
            collections.value = await res.json();
        } catch (e) {
            console.error('Failed to fetch collections:', e);
        }
    }
    
    async function openCollectionDetail(collection, configStore) {
        viewingCollection.value = collection;
        collectionCurrentPage.value = 1;
        collectionPaperSearch.value = '';
        useAiSearch.value = false;
        collectionSortBy.value = 'published';
        collectionSortOrder.value = 'desc';
        loadingCollectionPapers.value = true;
        showCollectionDetail.value = true;
        await loadCollectionPage(configStore);
    }
    
    async function performSearch(configStore) {
        if (!viewingCollection.value) return;
        collectionCurrentPage.value = 1;
        
        if (useAiSearch.value && collectionPaperSearch.value.trim()) {
            aiSearching.value = true;
            loadingCollectionPapers.value = true;
            try {
                const res = await API.collections.aiSearch(viewingCollection.value.id, collectionPaperSearch.value.trim());
                const data = await res.json();
                if (data.papers && data.papers.length > 0) {
                    collectionPapers.value = data.papers;
                    collectionTotalCount.value = data.papers.length;
                    collectionTotalPages.value = 1;
                    ElementPlus.ElMessage.success(configStore.t('collections.aiResult', { count: data.papers.length }));
                } else {
                    collectionPapers.value = [];
                    collectionTotalCount.value = 0;
                    collectionTotalPages.value = 0;
                    ElementPlus.ElMessage.info(configStore.t('collections.aiNoResult'));
                }
            } catch (e) {
                console.error('AI search failed:', e);
                ElementPlus.ElMessage.error(configStore.currentLang === 'zh' ? 'AI 检索失败' : 'AI search failed');
            } finally {
                aiSearching.value = false;
                loadingCollectionPapers.value = false;
            }
        } else {
            await loadCollectionPage(configStore);
        }
    }
    
    function toggleSortOrder(configStore) {
        collectionSortOrder.value = collectionSortOrder.value === 'desc' ? 'asc' : 'desc';
        performSearch(configStore);
    }
    
    function openPaperUrl(url) {
        if (url) window.open(url, '_blank');
    }
    
    async function loadCollectionPage(configStore) {
        if (!viewingCollection.value) return;
        loadingCollectionPapers.value = true;
        try {
            const params = new URLSearchParams({
                page: collectionCurrentPage.value,
                page_size: 20
            });
            if (collectionPaperSearch.value && !useAiSearch.value) {
                params.append('search', collectionPaperSearch.value);
            }
            if (collectionSortBy.value) {
                params.append('sort_by', collectionSortBy.value);
            }
            if (collectionSortOrder.value) {
                params.append('sort_order', collectionSortOrder.value);
            }
            const res = await API.collections.papers(viewingCollection.value.id, params.toString());
            const data = await res.json();
            collectionPapers.value = data.papers || [];
            collectionTotalCount.value = data.total_count || 0;
            collectionTotalPages.value = data.total_pages || 0;
        } catch (e) {
            console.error('Failed to load collection papers:', e);
        } finally {
            loadingCollectionPapers.value = false;
        }
    }
    
    async function saveNewCollection(configStore) {
        savingCollection.value = true;
        try {
            if (editingCollection.value) {
                const res = await API.collections.update(editingCollection.value.id, newCollection.value);
                if (res.ok) {
                    ElementPlus.ElMessage.success(configStore.currentLang === 'zh' ? '更新成功' : 'Updated');
                    showCreateCollection.value = false;
                    editingCollection.value = null;
                    newCollection.value = { name: '', description: '', color: '#1e3a5f' };
                    fetchCollections();
                } else {
                    ElementPlus.ElMessage.error(configStore.currentLang === 'zh' ? '更新失败' : 'Failed to update');
                }
            } else {
                const res = await API.collections.create(newCollection.value);
                if (res.ok) {
                    ElementPlus.ElMessage.success(configStore.currentLang === 'zh' ? '创建成功' : 'Created');
                    showCreateCollection.value = false;
                    newCollection.value = { name: '', description: '', color: '#1e3a5f' };
                    fetchCollections();
                } else {
                    ElementPlus.ElMessage.error(configStore.currentLang === 'zh' ? '创建失败' : 'Failed to create');
                }
            }
        } catch (e) {
            ElementPlus.ElMessage.error(configStore.currentLang === 'zh' ? '操作失败' : 'Operation failed');
        } finally {
            savingCollection.value = false;
        }
    }
    
    async function deleteCollection(configStore) {
        deletingCollectionInProgress.value = true;
        try {
            const res = await API.collections.delete(deletingCollection.value.id);
            if (res.ok) {
                ElementPlus.ElMessage.success('删除成功');
                showDeleteConfirm.value = false;
                fetchCollections();
            } else {
                ElementPlus.ElMessage.error('删除失败');
            }
        } catch (e) {
            ElementPlus.ElMessage.error('删除失败');
        } finally {
            deletingCollectionInProgress.value = false;
        }
    }
    
    function showMergeConfirm(fromCollection, toCollection) {
        mergingFromCollection.value = fromCollection;
        mergingToCollection.value = toCollection;
        showMergeConfirmDialog.value = true;
    }
    
    async function mergePapers(configStore) {
        if (!mergingFromCollection.value || !mergingToCollection.value) return;
        mergingInProgress.value = true;
        try {
            const res = await API.collections.merge(mergingFromCollection.value.id, mergingToCollection.value.id);
            if (res.ok) {
                ElementPlus.ElMessage.success(configStore.currentLang === 'zh' ? '合并成功' : 'Merged successfully');
                showMergeConfirmDialog.value = false;
                fetchCollections();
            } else {
                ElementPlus.ElMessage.error(configStore.currentLang === 'zh' ? '合并失败' : 'Merge failed');
            }
        } catch (e) {
            ElementPlus.ElMessage.error(configStore.currentLang === 'zh' ? '合并失败' : 'Merge failed');
        } finally {
            mergingInProgress.value = false;
        }
    }
    
    async function removePaperFromCollection(paperId, configStore) {
        try {
            const res = await API.collections.removePaper(viewingCollection.value.id, paperId);
            if (res.ok) {
                ElementPlus.ElMessage.success('已移除');
                loadCollectionPage(configStore);
                fetchCollections();
            }
        } catch (e) {
            ElementPlus.ElMessage.error('移除失败');
        }
    }
    
    function editCollection(collection) {
        editingCollection.value = { ...collection };
        newCollection.value = { 
            name: collection.name, 
            description: collection.description || '', 
            color: collection.color || '#1e3a5f' 
        };
        showCreateCollection.value = true;
    }
    
    async function duplicateCollection(collection, configStore) {
        savingCollection.value = true;
        try {
            const res = await API.collections.create({
                name: `${collection.name} (copy)`,
                description: collection.description,
                color: collection.color
            });
            if (res.ok) {
                ElementPlus.ElMessage.success(configStore.currentLang === 'zh' ? '复制成功' : 'Duplicated');
                fetchCollections();
            }
        } catch (e) {
            ElementPlus.ElMessage.error(configStore.currentLang === 'zh' ? '复制失败' : 'Failed to duplicate');
        } finally {
            savingCollection.value = false;
        }
    }
    
    function confirmDeleteCollection(collection) {
        deletingCollection.value = collection;
        showDeleteConfirm.value = true;
    }
    
    function addToCollection(paper) {
        selectedPaper.value = paper;
        selectedCollectionId.value = null;
        showAddToCollection.value = true;
    }
    
    async function confirmAddToCollection(configStore, paperCart) {
        if (!selectedCollectionId.value) {
            ElementPlus.ElMessage.warning(configStore.currentLang === 'zh' ? '请选择论文集' : 'Please select a collection');
            return;
        }
        addingToCollection.value = true;
        try {
            const papersToAdd = selectedPaper.value ? [selectedPaper.value] : paperCart;
            if (papersToAdd.length === 0) {
                ElementPlus.ElMessage.warning(configStore.currentLang === 'zh' ? '没有选中的论文' : 'No papers selected');
                return;
            }
            
            const paperIds = papersToAdd.map(p => p.id);
            const res = await API.collections.addPapersBatch(selectedCollectionId.value, paperIds);
            
            if (res.ok) {
                const data = await res.json();
                const messages = [];
                if (data.added_count > 0) {
                    messages.push(configStore.currentLang === 'zh' ? `成功添加 ${data.added_count} 篇论文` : `Added ${data.added_count} papers`);
                }
                if (data.skipped_count > 0) {
                    messages.push(configStore.currentLang === 'zh' ? `${data.skipped_count} 篇已在论文集中` : `${data.skipped_count} already in collection`);
                }
                if (messages.length > 0) {
                    ElementPlus.ElMessage.success(messages.join('，'));
                }
                showAddToCollection.value = false;
                fetchCollections();
            }
        } catch (e) {
            ElementPlus.ElMessage.error(configStore.currentLang === 'zh' ? '添加失败' : 'Failed to add');
        } finally {
            addingToCollection.value = false;
            selectedPaper.value = null;
        }
    }
    
    function cancelCollectionDialog() {
        showCreateCollection.value = false;
        editingCollection.value = null;
        newCollection.value = { name: '', description: '', color: '#1e3a5f' };
    }
    
    async function addPapersToCollection(paperIds, configStore) {
        if (!selectedCollectionId.value) return;
        try {
            const res = await API.collections.addPapersBatch(selectedCollectionId.value, paperIds);
            if (res.ok) {
                ElementPlus.ElMessage.success(configStore.currentLang === 'zh' ? '添加成功' : 'Added successfully');
                fetchCollections();
            }
        } catch (e) {
            ElementPlus.ElMessage.error(configStore.currentLang === 'zh' ? '添加失败' : 'Failed to add');
        }
    }
    
    async function exportCollection(format, configStore) {
        if (!viewingCollection.value) return;
        try {
            const res = await API.export.collection({
                collection_id: viewingCollection.value.id,
                format: format,
                include_summary: true
            });
            if (!res.ok) throw new Error('Export failed');
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            const ext = format === 'markdown' ? 'md' : format === 'bibtex' ? 'bib' : format;
            a.download = `collection_${viewingCollection.value.name.replace(/\s+/g, '_')}.${ext}`;
            a.click();
            window.URL.revokeObjectURL(url);
            ElementPlus.ElMessage.success('导出成功');
        } catch (e) {
            ElementPlus.ElMessage.error('导出失败');
        }
    }
    
    async function exportCollectionWithId(collectionId, format, configStore) {
        const collection = collections.value.find(c => c.id === collectionId);
        if (!collection) return;
        try {
            const res = await API.export.collection({
                collection_id: collectionId,
                format: format,
                include_summary: true
            });
            if (!res.ok) throw new Error('Export failed');
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            const ext = format === 'markdown' ? 'md' : format === 'bibtex' ? 'bib' : format;
            a.download = `collection_${collection.name.replace(/\s+/g, '_')}.${ext}`;
            a.click();
            window.URL.revokeObjectURL(url);
            ElementPlus.ElMessage.success('导出成功');
        } catch (e) {
            ElementPlus.ElMessage.error('导出失败');
        }
    }
    
    return {
        collections, viewingCollection, collectionPapers,
        collectionCurrentPage, collectionTotalCount, collectionTotalPages,
        collectionPaperSearch, loadingCollectionPapers, useAiSearch, aiSearching,
        collectionViewMode, collectionSearchQuery, collectionSortBy, collectionSortOrder,
        showCreateCollection, savingCollection, editingCollection, newCollection,
        showDeleteConfirm, deletingCollection, deletingCollectionInProgress,
        showMergeConfirmDialog, mergingFromCollection, mergingToCollection, mergingInProgress,
        selectedCollectionId, showCollectionDetail, showAddToCollection, selectedPaper, addingToCollection,
        filteredCollections,
        fetchCollections, openCollectionDetail, loadCollectionPage, performSearch, toggleSortOrder, openPaperUrl,
        saveNewCollection, deleteCollection, showMergeConfirm, mergePapers,
        removePaperFromCollection, editCollection, duplicateCollection,
        confirmDeleteCollection, addToCollection, confirmAddToCollection, cancelCollectionDialog,
        addPapersToCollection,
        exportCollection, exportCollectionWithId
    };
});
