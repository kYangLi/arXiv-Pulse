const CollectionDialogsTemplate = `
    <div>
        <el-dialog v-model="showCreateCollection" :title="editingCollection ? t('collections.edit') : t('collections.create')" width="480px" @closed="cancelCollectionDialog">
            <el-form label-position="top" @submit.prevent="saveCollection">
                <el-form-item :label="t('collections.name')">
                    <el-input v-model="newCollection.name" :placeholder="t('collections.name')" />
                </el-form-item>
                <el-form-item :label="t('collections.description')">
                    <el-input v-model="newCollection.description" type="textarea" rows="3" :placeholder="t('collections.description')" />
                </el-form-item>
                <el-form-item :label="t('collections.color')">
                    <el-color-picker v-model="newCollection.color" />
                </el-form-item>
            </el-form>
            <template #footer>
                <el-button @click="showCreateCollection = false">{{ t('common.cancel') }}</el-button>
                <el-button type="primary" @click="saveCollection" :loading="savingCollection">{{ t('common.confirm') }}</el-button>
            </template>
        </el-dialog>

        <el-dialog v-model="showAddToCollection" :title="t('collections.addToCollection')" width="400px" @closed="selectedPaper = null">
            <p style="margin-bottom: 12px; color: var(--text-secondary);">
                {{ t('collections.addPapersTo', { count: selectedPaper ? 1 : paperCart.length }) }}
            </p>
            <div v-if="selectedPaper?.collection_ids?.length > 0" style="margin-bottom: 12px; padding: 8px 12px; background: var(--bg-subtle); border-radius: 8px;">
                <span style="color: var(--text-muted); font-size: 12px;">{{ t('collections.alreadyIn') }}: </span>
                <el-tag v-for="cid in selectedPaper.collection_ids" :key="cid" size="small" style="margin: 2px;">
                    {{ collections.find(c => c.id === cid)?.name || '#' + cid }}
                </el-tag>
            </div>
            <el-select v-model="selectedCollectionId" :placeholder="t('collections.selectPlaceholder')" style="width: 100%;">
                <el-option v-for="c in collections" :key="c.id" :label="c.name" :value="c.id" />
            </el-select>
            <template #footer>
                <el-button @click="showAddToCollection = false">{{ t('common.cancel') }}</el-button>
                <el-button type="primary" @click="confirmAddToCollection" :loading="addingToCollection">{{ t('common.add') }}</el-button>
            </template>
        </el-dialog>

        <el-dialog v-model="showCollectionDetail" width="800px">
            <template #header>
                <div style="display: flex; align-items: center; justify-content: space-between; width: 100%;">
                    <div>
                        <span style="font-size: 18px; font-weight: 600;">{{ viewingCollection?.name }}</span>
                        <div v-if="viewingCollection" style="font-size: 12px; color: var(--text-secondary); margin-top: 4px;">
                            {{ collectionTotalCount }} {{ t('collections.papers') }} · {{ t('collections.lastAdded') }}: {{ formatRelativeTime(viewingCollection.updated_at) }}
                        </div>
                    </div>
                </div>
            </template>
            <div v-if="loadingCollectionPapers" style="text-align: center; padding: 40px;">
                <el-icon class="is-loading" style="font-size: 32px;"><Loading /></el-icon>
                <p v-if="aiSearching" style="color: var(--text-secondary); margin-top: 12px;">{{ t('collections.aiSearching') }}</p>
            </div>
            <div v-else>
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid var(--border-light); flex-wrap: wrap; gap: 12px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <el-input 
                            v-model="collectionPaperSearch" 
                            :placeholder="useAiSearch ? t('collections.aiSearchPlaceholder') : t('collections.searchPapers')" 
                            clearable 
                            style="width: 280px;" 
                            @keyup.enter="performSearch" 
                            @clear="performSearch"
                            :disabled="aiSearching"
                        >
                            <template #prefix><el-icon><Search /></el-icon></template>
                        </el-input>
                        <el-checkbox v-model="useAiSearch" :disabled="aiSearching">{{ t('collections.aiSearch') }}</el-checkbox>
                        <el-divider direction="vertical"></el-divider>
                        <el-radio-group v-model="collectionSortBy" size="small" @change="performSearch">
                            <el-radio-button value="published">
                                <el-icon><Calendar /></el-icon>
                                <span style="margin-left: 4px;">{{ t('collections.sortPublished') }}</span>
                            </el-radio-button>
                            <el-radio-button value="added_at">
                                <el-icon><Clock /></el-icon>
                                <span style="margin-left: 4px;">{{ t('collections.sortAdded') }}</span>
                            </el-radio-button>
                        </el-radio-group>
                        <el-button size="small" @click="toggleSortOrder">
                            <el-icon>
                                <component :is="collectionSortOrder === 'desc' ? 'SortDown' : 'SortUp'" />
                            </el-icon>
                        </el-button>
                        <el-divider direction="vertical"></el-divider>
                        <el-button-group size="small">
                            <el-button :type="collectionViewMode === 'card' ? 'primary' : ''" @click="collectionViewMode = 'card'">
                                <el-icon><Grid /></el-icon>
                            </el-button>
                            <el-button :type="collectionViewMode === 'list' ? 'primary' : ''" @click="collectionViewMode = 'list'">
                                <el-icon><List /></el-icon>
                            </el-button>
                        </el-button-group>
                    </div>
                </div>
                <div v-if="collectionPapers.length > 0">
                    <template v-if="collectionViewMode === 'card'">
                        <paper-card 
                            v-for="(paper, idx) in collectionPapers" 
                            :key="paper.id" 
                            :paper="paper"
                            :collections="collections"
                            :in-collection="true"
                            :in-cart="isInCart(paper.arxiv_id)"
                            :t="t"
                            :current-lang="currentLang"
                            :index="paper._originalIndex !== undefined ? paper._originalIndex : (collectionCurrentPage - 1) * 20 + idx"
                            @add-to-collection="addToCollection"
                            @remove-from-collection="removePaperFromCollection"
                            @add-to-cart="addToCart"
                            @remove-from-cart="removeFromCartByArxivId"
                        />
                    </template>
                    <template v-else>
                        <div v-for="(paper, idx) in collectionPapers" :key="paper.id" class="collection-list-item">
                            <span class="paper-index-list">{{ (paper._originalIndex !== undefined ? paper._originalIndex : (collectionCurrentPage - 1) * 20 + idx) + 1 }}</span>
                            <div class="list-item-content">
                                <div class="list-item-header">
                                    <div class="list-item-title" @click="openPaperUrl(paper.arxiv_url)">{{ paper.title }}</div>
                                    <div class="list-item-actions">
                                        <a :href="'https://arxiv.org/abs/' + paper.arxiv_id" target="_blank" class="arxiv-link" @click.stop>{{ paper.arxiv_id }}</a>
                                        <el-button 
                                            v-if="!isInCart(paper.arxiv_id)" 
                                            size="small" 
                                            text 
                                            type="warning"
                                            @click.stop="addToCart(paper)"
                                            :title="currentLang === 'zh' ? '暂存' : 'Mark'"
                                        >
                                            <el-icon><Star /></el-icon>
                                        </el-button>
                                        <el-button 
                                            v-else 
                                            size="small" 
                                            type="warning" 
                                            plain
                                            @click.stop="removeFromCartByArxivId(paper.arxiv_id)"
                                            :title="currentLang === 'zh' ? '取消暂存' : 'Unmark'"
                                        >
                                            <el-icon><StarFilled /></el-icon>
                                        </el-button>
                                    </div>
                                </div>
                                <div class="list-item-meta">
                                    <span>{{ paper.authors?.map(a => a.name).slice(0, 3).join(', ') }}{{ paper.authors?.length > 3 ? '...' : '' }}</span>
                                    <span>·</span>
                                    <span>{{ paper.published?.slice(0, 10) }}</span>
                                </div>
                            </div>
                        </div>
                    </template>
                </div>
                <div v-else class="empty-state">
                    <p v-if="useAiSearch && collectionPaperSearch">{{ t('collections.aiNoResult') }}</p>
                    <p v-else-if="collectionPaperSearch">{{ t('collections.noSearchResult') }}</p>
                    <p v-else>{{ t('collections.noPapersInCollection') }}</p>
                </div>
                <div v-if="collectionTotalPages > 1 && !(useAiSearch && collectionPaperSearch)" style="display: flex; justify-content: center; margin-top: 20px; padding-top: 20px; border-top: 1px solid var(--border-light);">
                    <el-pagination
                        v-model:current-page="collectionCurrentPage"
                        :page-size="20"
                        :total="collectionTotalCount"
                        layout="prev, pager, next"
                        @current-change="loadCollectionPage"
                    />
                </div>
            </div>
        </el-dialog>

        <el-dialog v-model="showDeleteConfirm" :title="t('common.confirmDelete')" width="400px">
            <p>{{ t('collections.deleteConfirm', { name: deletingCollection?.name }) }}</p>
            <template #footer>
                <el-button @click="showDeleteConfirm = false">{{ t('common.cancel') }}</el-button>
                <el-button type="danger" @click="deleteCollection" :loading="deletingCollectionInProgress">{{ t('common.delete') }}</el-button>
            </template>
        </el-dialog>

        <el-dialog v-model="showMergeConfirmDialog" :title="t('collections.mergePapers')" width="400px">
            <p>{{ t('collections.mergeConfirm', { count: mergingFromCollection?.paper_count || 0, name: mergingToCollection?.name }) }}</p>
            <template #footer>
                <el-button @click="showMergeConfirmDialog = false">{{ t('common.cancel') }}</el-button>
                <el-button type="primary" @click="mergePapers" :loading="mergingInProgress">{{ t('common.confirm') }}</el-button>
            </template>
        </el-dialog>
    </div>
`;

const CollectionDialogsSetup = (props, { emit }) => {
    const collectionStore = useCollectionStore();
    const configStore = useConfigStore();
    const uiStore = useUiStore();
    
    const { t, currentLang } = configStore;
    
    const {
        viewingCollection, collectionPapers,
        collectionCurrentPage, collectionTotalCount, collectionTotalPages,
        collectionPaperSearch, loadingCollectionPapers, useAiSearch, aiSearching,
        collectionViewMode, collectionSearchQuery, collectionSortBy, collectionSortOrder,
        showCreateCollection, savingCollection, editingCollection, newCollection,
        showDeleteConfirm, deletingCollection, deletingCollectionInProgress,
        showMergeConfirmDialog, mergingFromCollection, mergingToCollection, mergingInProgress,
        selectedCollectionId, showCollectionDetail, showAddToCollection, selectedPaper, addingToCollection
    } = storeToRefs(collectionStore);
    
    function formatRelativeTime(dateStr) {
        return uiStore.formatRelativeTime(dateStr, configStore);
    }
    
    function isInCart(arxivId) {
        return props.paperCart.some(p => p.arxiv_id === arxivId);
    }
    
    function addToCart(paper) {
        emit('add-to-cart', paper);
    }
    
    function removeFromCartByArxivId(arxivId) {
        emit('remove-from-cart', arxivId);
    }
    
    async function saveCollection() {
        await collectionStore.saveNewCollection(configStore);
    }
    
    function cancelCollectionDialog() {
        collectionStore.cancelCollectionDialog();
    }
    
    async function confirmAddToCollection() {
        const paperStore = usePaperStore();
        await collectionStore.confirmAddToCollection(configStore, props.paperCart, paperStore);
    }
    
    function addToCollection(paper) {
        collectionStore.addToCollection(paper);
    }
    
    async function removePaperFromCollection(paperId) {
        await collectionStore.removePaperFromCollection(paperId, configStore);
    }
    
    async function performSearch() {
        await collectionStore.performSearch(configStore);
    }
    
    function toggleSortOrder() {
        collectionStore.toggleSortOrder(configStore);
    }
    
    function openPaperUrl(url) {
        collectionStore.openPaperUrl(url);
    }
    
    async function loadCollectionPage() {
        await collectionStore.loadCollectionPage(configStore);
    }
    
    async function deleteCollection() {
        await collectionStore.deleteCollection(configStore);
    }
    
    async function mergePapers() {
        await collectionStore.mergePapers(configStore);
    }
    
    return {
        showCreateCollection, editingCollection, newCollection, savingCollection,
        showAddToCollection, selectedPaper, selectedCollectionId, addingToCollection,
        showCollectionDetail, viewingCollection, collectionTotalCount, collectionPapers,
        loadingCollectionPapers, aiSearching, useAiSearch, collectionPaperSearch,
        collectionSortBy, collectionSortOrder, collectionViewMode, collectionCurrentPage, collectionTotalPages,
        showDeleteConfirm, deletingCollection, deletingCollectionInProgress,
        showMergeConfirmDialog, mergingFromCollection, mergingToCollection, mergingInProgress,
        collectionDetailZIndex: props.collectionDetailZIndex,
        formatRelativeTime, t, currentLang,
        isInCart, addToCart, removeFromCartByArxivId,
        saveCollection, cancelCollectionDialog, confirmAddToCollection,
        addToCollection, removePaperFromCollection, performSearch, toggleSortOrder,
        openPaperUrl, loadCollectionPage, deleteCollection, mergePapers
    };
};
