const FieldSelectorDialogTemplate = `
<el-dialog 
    v-model="showFieldSelector" 
    width="800px" 
    :close-on-click-modal="false"
    append-to-body
>
    <div style="margin-bottom: 12px; display: flex; align-items: center; gap: 12px;">
        <div style="font-size: 14px; font-weight: 500; color: var(--text-primary);">
            {{ t('fields.selectFields') }}
        </div>
        <el-tooltip :content="fieldAdvancedMode ? t('fields.switchToVisual') : t('fields.switchToCode')" placement="top">
            <el-button 
                :type="fieldAdvancedMode ? 'primary' : 'default'" 
                size="small" 
                @click="fieldAdvancedMode = !fieldAdvancedMode"
                style="display: flex; align-items: center; gap: 4px;"
            >
                <el-icon style="font-size: 14px;"><Document /></el-icon>
                <span style="font-size: 12px;">{{ fieldAdvancedMode ? t('fields.visualMode') : t('fields.codeMode') }}</span>
            </el-button>
        </el-tooltip>
    </div>
    
    <div class="field-selector">
        <div class="field-selector-left">
            <template v-if="fieldAdvancedMode">
                <div style="flex: 1; display: flex; flex-direction: column; background: #1e1e1e; border-radius: 8px 0 0 8px; overflow: hidden;">
                    <el-input
                        v-model="advancedQueriesText"
                        type="textarea"
                        :placeholder="t('fields.advancedPlaceholder')"
                        style="flex: 1; --el-input-bg-color: #1e1e1e; --el-input-text-color: #d4d4d4; --el-input-border-color: #3c3c3c; --el-input-placeholder-color: #6a6a6a;"
                        input-style="font-family: 'SF Mono', Monaco, 'Courier New', monospace; font-size: 13px; line-height: 1.6; background: #1e1e1e; color: #d4d4d4; height: 100%;"
                    />
                    <div style="padding: 8px 12px; background: #252526; font-size: 11px; color: #8a8a8a; display: flex; justify-content: space-between;">
                        <span>{{ advancedQueriesLines.length }} {{ currentLang === 'zh' ? '条查询' : 'queries' }}</span>
                        <span style="color: #6a6a6a;">arXiv API</span>
                    </div>
                </div>
            </template>
            <template v-else>
                <div class="field-selector-search">
                    <el-input v-model="fieldSearchQuery" :placeholder="t('fields.searchPlaceholder')" clearable>
                        <template #prefix>
                            <el-icon><Search /></el-icon>
                        </template>
                    </el-input>
                </div>
                <div class="field-selector-tree">
                    <template v-for="(group, groupKey) in filteredCategories" :key="groupKey">
                        <div class="field-group">
                            <div class="field-group-header" :class="{ expanded: fieldSelectorExpanded[groupKey] }" @click="toggleFieldSelectorGroup(groupKey)">
                                <el-icon><ArrowRight /></el-icon>
                                <span>{{ currentLang === 'zh' ? group.name : group.name_en }}</span>
                                <span v-if="group.recommended" class="recommended-badge">{{ t('fields.recommended') }}</span>
                            </div>
                            <div v-show="fieldSelectorExpanded[groupKey]" class="field-group-children">
                                <template v-for="(cat, catKey) in group.children" :key="catKey">
                                    <div v-if="cat.children" class="field-group">
                                        <div class="field-group-header" :class="{ expanded: fieldSelectorExpanded[catKey] }" @click.stop="toggleFieldSelectorGroup(catKey)">
                                            <el-icon><ArrowRight /></el-icon>
                                            <span>{{ currentLang === 'zh' ? cat.name : cat.name_en }}</span>
                                        </div>
                                        <div v-show="fieldSelectorExpanded[catKey]" class="field-group-children">
                                            <div v-for="(subcat, subcatKey) in cat.children" :key="subcatKey"
                                                 class="field-item"
                                                 :class="{ selected: tempSelectedFields.includes(subcat.id) }"
                                                 @click="toggleTempField(subcat.id)">
                                                <el-checkbox :model-value="tempSelectedFields.includes(subcat.id)" />
                                                <span v-if="subcat.recommended" class="star">⭐</span>
                                                <span>{{ currentLang === 'zh' ? subcat.name : subcat.name_en }}</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div v-else
                                         class="field-item"
                                         :class="{ selected: tempSelectedFields.includes(cat.id) }"
                                         @click="toggleTempField(cat.id)">
                                        <el-checkbox :model-value="tempSelectedFields.includes(cat.id)" />
                                        <span v-if="cat.recommended" class="star">⭐</span>
                                        <span>{{ currentLang === 'zh' ? cat.name : cat.name_en }}</span>
                                    </div>
                                </template>
                            </div>
                        </div>
                    </template>
                </div>
            </template>
        </div>
        <div class="field-selector-right">
            <div class="field-selector-header">
                <span>{{ currentLang === 'zh' ? '已选择' : 'Selected' }}</span>
                <span class="toggle-btn" v-if="!fieldAdvancedMode && tempSelectedFields.length > 0" @click="clearTempSelection">{{ currentLang === 'zh' ? '清空' : 'Clear' }}</span>
            </div>
            <div class="field-selector-list">
                <template v-if="!fieldAdvancedMode">
                    <div v-if="tempSelectedFields.length === 0" class="field-selector-empty">
                        {{ currentLang === 'zh' ? '点击左侧领域添加' : 'Click fields to add' }}
                    </div>
                    <div v-for="fieldId in tempSelectedFields" :key="fieldId" class="field-selected-item">
                        <div class="name">
                            <span v-if="allCategories[fieldId]?.recommended" class="star">⭐</span>
                            <span>{{ currentLang === 'zh' ? allCategories[fieldId]?.name : allCategories[fieldId]?.name_en }}</span>
                            <span style="color: var(--text-muted); font-size: 11px; margin-left: 4px;">{{ fieldId }}</span>
                        </div>
                        <div class="remove-btn" @click="removeFromTempSelection(fieldId)">
                            <el-icon><Close /></el-icon>
                        </div>
                    </div>
                </template>
                <template v-else>
                    <div v-if="advancedQueriesLines.length === 0" class="field-selector-empty">
                        {{ currentLang === 'zh' ? '在左侧输入查询语句' : 'Enter queries on the left' }}
                    </div>
                    <template v-else>
                        <div v-if="parsedCodeResult.standardFields.length > 0" style="margin-bottom: 8px;">
                            <div style="font-size: 11px; color: var(--text-muted); margin-bottom: 4px;">{{ currentLang === 'zh' ? '标准分类' : 'Standard' }}</div>
                            <div v-for="fieldId in parsedCodeResult.standardFields" :key="fieldId" class="field-selected-item" style="background: #e8f4ff;">
                                <div class="name">
                                    <span v-if="allCategories[fieldId]?.recommended" class="star">⭐</span>
                                    <span style="color: var(--primary);">{{ currentLang === 'zh' ? allCategories[fieldId]?.name : allCategories[fieldId]?.name_en }}</span>
                                </div>
                            </div>
                        </div>
                        <div v-if="parsedCodeResult.customQueries.length > 0">
                            <div style="font-size: 11px; color: #e6a23c; margin-bottom: 4px;">{{ currentLang === 'zh' ? '自定义规则' : 'Custom' }}</div>
                            <div v-for="(query, idx) in parsedCodeResult.customQueries" :key="idx" class="field-selected-item" style="background: #fdf6ec; border-color: #e6a23c;">
                                <div class="name" style="font-family: 'SF Mono', Monaco, monospace; font-size: 11px; color: #e6a23c;">
                                    {{ query }}
                                </div>
                            </div>
                        </div>
                    </template>
                </template>
            </div>
            <div class="field-selector-footer">
                <span class="count">
                    <template v-if="!fieldAdvancedMode">
                        {{ tempSelectedFields.length }} {{ currentLang === 'zh' ? '个领域' : 'fields' }}
                    </template>
                    <template v-else>
                        {{ advancedQueriesLines.length }} {{ currentLang === 'zh' ? '条查询' : 'queries' }}
                        <span v-if="parsedCodeResult.customQueries.length > 0" style="color: #e6a23c;"> ({{ parsedCodeResult.customQueries.length }} {{ currentLang === 'zh' ? '自定义' : 'custom' }})</span>
                    </template>
                </span>
            </div>
        </div>
    </div>
    <template #footer>
        <el-button @click="showFieldSelector = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="confirmFieldSelection">{{ t('common.confirm') }}</el-button>
    </template>
</el-dialog>
`;

const FieldSelectorDialogSetup = () => {
    const configStore = useConfigStore();
    const {
        showFieldSelector,
        fieldAdvancedMode,
        advancedQueriesText,
        tempSelectedFields,
        fieldSearchQuery,
        fieldSelectorExpanded,
        allCategories,
        filteredCategories,
        advancedQueriesLines,
        parsedCodeResult,
        currentLang
    } = storeToRefs(configStore);
    
    const {
        toggleFieldSelectorGroup,
        toggleTempField,
        removeFromTempSelection,
        clearTempSelection,
        confirmFieldSelection,
        t
    } = configStore;
    
    return {
        showFieldSelector,
        fieldAdvancedMode,
        advancedQueriesText,
        tempSelectedFields,
        fieldSearchQuery,
        fieldSelectorExpanded,
        allCategories,
        filteredCategories,
        advancedQueriesLines,
        parsedCodeResult,
        currentLang,
        toggleFieldSelectorGroup,
        toggleTempField,
        removeFromTempSelection,
        clearTempSelection,
        confirmFieldSelection,
        t
    };
};
