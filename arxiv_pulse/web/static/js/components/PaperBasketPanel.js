const PaperBasketPanelTemplate = `
<transition name="panel">
    <div v-if="show" 
         class="cart-panel" 
         ref="panelRef"
         :style="{ position: 'fixed', left: position.x + 'px', top: position.y + 'px', zIndex }"
         @mousedown="$emit('start-drag', $event)"
         @click="$emit('bring-to-front')">
        <div class="cart-header">
            <h3>
                <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
                    <path d="M7 18c-1.1 0-1.99.9-1.99 2S5.9 22 7 22s2-.9 2-2-.9-2-2-2zM1 2v2h2l3.6 7.59-1.35 2.45c-.16.28-.25.61-.25.96 0 1.1.9 2 2 2h12v-2H7.42c-.14 0-.25-.11-.25-.25l.03-.12.9-1.63h7.45c.75 0 1.41-.41 1.75-1.03l3.58-6.49c.08-.14.12-.31.12-.48 0-.55-.45-1-1-1H5.21l-.94-2H1zm16 16c-1.1 0-1.99.9-1.99 2s.89 2 1.99 2 2-.9 2-2-.9-2-2-2z"/>
                </svg>
                {{ t('basket.title') }}
                <span v-if="paperCart.length > 0" style="opacity: 0.7; font-weight: 400;">({{ paperCart.length }})</span>
            </h3>
            <div class="collapse-btn" @click.stop="$emit('update:show', false)" :title="currentLang === 'zh' ? '收起' : 'Collapse'">
                <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
                    <path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6z"/>
                </svg>
            </div>
        </div>
        <div class="cart-body">
            <div v-if="paperCart.length === 0" class="cart-empty">
                <svg viewBox="0 0 24 24" width="48" height="48" fill="currentColor" style="opacity: 0.5;">
                    <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/>
                </svg>
                <p style="margin-top: 12px; color: var(--text-muted);">{{ t('basket.empty') }}</p>
                <p style="font-size: 12px; color: var(--text-muted);">{{ t('basket.emptyHint') }}</p>
            </div>
            <div v-for="(paper, index) in paperCart" :key="paper.arxiv_id" class="cart-item">
                <div class="cart-item-info">
                    <div class="cart-item-title">{{ paper.title }}</div>
                    <div class="cart-item-meta">{{ paper.arxiv_id }} · {{ formatDate(paper.published) }}</div>
                </div>
                <div class="cart-item-actions">
                    <el-button text size="small" @click="removeFromCart(index)" :title="t('common.delete')">
                        <el-icon><Delete /></el-icon>
                    </el-button>
                </div>
            </div>
        </div>
        <div v-if="paperCart.length > 0" class="cart-footer">
            <div class="cart-actions">
                <el-dropdown @command="exportCart" placement="top">
                    <el-button type="primary" plain>
                        <el-icon><Download /></el-icon> {{ t('basket.export') }}
                    </el-button>
                    <template #dropdown>
                        <el-dropdown-menu>
                            <el-dropdown-item command="markdown">Markdown</el-dropdown-item>
                            <el-dropdown-item command="pdf">{{ t('basket.exportPdfSummary') }}</el-dropdown-item>
                            <el-dropdown-item command="pdf_original">{{ t('basket.exportPdfOriginal') }}</el-dropdown-item>
                            <el-dropdown-item command="csv">CSV</el-dropdown-item>
                            <el-dropdown-item command="bibtex">BibTeX</el-dropdown-item>
                        </el-dropdown-menu>
                    </template>
                </el-dropdown>
                <el-button @click="$emit('add-to-collection')" plain>
                    <el-icon><Folder /></el-icon> {{ t('basket.addToCollection') }}
                </el-button>
                <el-button @click="copyCartLinks" type="info" plain>
                    <el-icon><Tickets /></el-icon> {{ t('basket.copyLinks') }}
                </el-button>
                <el-button @click="clearCart" type="danger" plain>
                    <el-icon><Delete /></el-icon> {{ t('basket.clear') }}
                </el-button>
            </div>
        </div>
    </div>
</transition>
`;

const PaperBasketPanelSetup = (props) => {
    const paperStore = usePaperStore();
    const configStore = useConfigStore();
    
    const { paperCart } = storeToRefs(paperStore);
    const { removeFromCart, clearCart, exportCart, copyCartLinks } = paperStore;
    const { t, currentLang } = configStore;
    
    const panelRef = ref(null);
    
    const formatDate = (dateStr) => {
        if (!dateStr) return '';
        return new Date(dateStr).toLocaleDateString('zh-CN');
    };
    
    return {
        paperCart,
        panelRef,
        formatDate,
        removeFromCart,
        clearCart,
        exportCart,
        copyCartLinks,
        t,
        currentLang
    };
};
