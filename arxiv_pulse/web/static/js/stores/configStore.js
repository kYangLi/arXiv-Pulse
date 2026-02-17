const useConfigStore = defineStore('config', () => {
    const showSetup = ref(false);
    const setupStep = ref(1);
    const testingAI = ref(false);
    
    const defaultFields = [
        'cond-mat.mtrl-sci', 'cond-mat.str-el', 'cond-mat.supr-con',
        'physics.comp-ph', 'physics.chem-ph', 'quant-ph'
    ];
    
    const setupConfig = ref({
        ai_api_key: '',
        ai_model: 'DeepSeek-V3.2',
        ai_base_url: 'https://llmapi.paratera.com',
        translate_language: 'zh',
        selected_fields: [...defaultFields],
        search_queries: [],
        years_back: 5,
        arxiv_max_results_per_field: 10000,
        arxiv_max_results: 100000,
        recent_papers_limit: 64,
        search_limit: 20
    });
    
    const showSettings = ref(false);
    const savingSettings = ref(false);
    const settingsConfig = ref({
        ai_api_key: '',
        ai_model: 'DeepSeek-V3.2',
        ai_base_url: 'https://llmapi.paratera.com',
        selected_fields: [],
        search_queries: [],
        years_back: 5,
        arxiv_max_results: 100000,
        arxiv_max_results_per_field: 10000,
        recent_papers_limit: 64,
        search_limit: 20,
        ui_language: 'zh',
        translate_language: 'zh'
    });
    
    const arxivCategories = ref({});
    const allCategories = ref({});
    const currentLang = ref('zh');
    
    const showFieldSelector = ref(false);
    const fieldSelectorSource = ref('settings');
    const tempSelectedFields = ref([]);
    const fieldSearchQuery = ref('');
    const fieldSelectorExpanded = ref({});
    const recentCategories = ref([]);
    const fieldAdvancedMode = ref(false);
    const advancedQueriesText = ref('');
    
    const filteredCategories = computed(() => {
        if (!fieldSearchQuery.value) return arxivCategories.value;
        const query = fieldSearchQuery.value.toLowerCase();
        const result = {};
        for (const [key, group] of Object.entries(arxivCategories.value)) {
            const filteredGroup = { ...group };
            if (group.children) {
                const filteredChildren = {};
                for (const [catKey, cat] of Object.entries(group.children)) {
                    if (cat.name.toLowerCase().includes(query) || 
                        cat.name_en?.toLowerCase().includes(query)) {
                        filteredChildren[catKey] = cat;
                    } else if (cat.children) {
                        const filteredSubChildren = {};
                        for (const [subKey, sub] of Object.entries(cat.children)) {
                            if (sub.name.toLowerCase().includes(query) || 
                                sub.name_en?.toLowerCase().includes(query) ||
                                sub.id?.toLowerCase().includes(query)) {
                                filteredSubChildren[subKey] = sub;
                            }
                        }
                        if (Object.keys(filteredSubChildren).length > 0) {
                            filteredChildren[catKey] = { ...cat, children: filteredSubChildren };
                        }
                    }
                }
                if (Object.keys(filteredChildren).length > 0) {
                    filteredGroup.children = filteredChildren;
                    result[key] = filteredGroup;
                }
            } else if (group.name?.toLowerCase().includes(query) || 
                       group.name_en?.toLowerCase().includes(query)) {
                result[key] = filteredGroup;
            }
        }
        return result;
    });
    
    const advancedQueriesLines = computed(() => {
        return advancedQueriesText.value
            .split('\n')
            .map(line => line.trim())
            .filter(line => line.length > 0);
    });
    
    const parsedCodeResult = computed(() => {
        const standardFields = [];
        const customQueries = [];
        for (const line of advancedQueriesLines.value) {
            const catMatch = line.match(/^cat:(.+)$/);
            if (catMatch) {
                standardFields.push(catMatch[1].trim());
            } else {
                customQueries.push(line);
            }
        }
        return { standardFields, customQueries };
    });
    
    function setLanguage(lang) {
        currentLang.value = lang;
        document.documentElement.lang = lang === 'zh' ? 'zh-CN' : 'en';
    }
    
    function t(key, params = {}) {
        const keys = key.split('.');
        let value = currentLang.value === 'zh' ? i18n_zh : i18n_en;
        for (const k of keys) {
            if (value && typeof value === 'object') value = value[k];
            else return key;
        }
        if (typeof value !== 'string') return key;
        return value.replace(/\{(\w+)\}/g, (_, k) => params[k] ?? `{${k}}`);
    }
    
    async function checkInitStatus() {
        try {
            const res = await API.config.status();
            const data = await res.json();
            showSetup.value = !data.is_initialized;
            await fetchCategories();
        } catch (e) {
            console.error('Failed to check init status:', e);
        }
    }
    
    async function fetchCategories() {
        try {
            const res = await API.config.categories();
            const data = await res.json();
            arxivCategories.value = data.categories || {};
            allCategories.value = data.all_categories || {};
            
            const defaultExpanded = ['physics', 'cond-mat', 'cs'];
            defaultExpanded.forEach(key => {
                expandedGroups.value[key] = true;
            });
        } catch (e) {
            console.error('Failed to fetch categories:', e);
        }
    }
    
    async function testSetupAI() {
        testingAI.value = true;
        try {
            const res = await API.config.testAI(setupConfig.value);
            const data = await res.json();
            if (res.ok) {
                ElementPlus.ElMessage.success(data.message || t('settings.connectionSuccess'));
            } else {
                ElementPlus.ElMessage.error(data.detail || t('settings.connectionFailed'));
            }
        } catch (e) {
            ElementPlus.ElMessage.error(t('settings.connectionFailed'));
        } finally {
            testingAI.value = false;
        }
    }
    
    async function fetchConfig() {
        try {
            const res = await API.config.get();
            const data = await res.json();
            settingsConfig.value = {
                ai_api_key: data.ai_api_key || '',
                ai_model: data.ai_model || 'DeepSeek-V3.2',
                ai_base_url: data.ai_base_url || 'https://llmapi.paratera.com',
                selected_fields: data.selected_fields || [],
                search_queries: data.search_queries || [],
                years_back: data.years_back || 5,
                arxiv_max_results: data.arxiv_max_results || 100000,
                arxiv_max_results_per_field: data.arxiv_max_results_per_field || 10000,
                recent_papers_limit: data.recent_papers_limit || 64,
                search_limit: data.search_limit || 20,
                ui_language: data.ui_language || 'zh',
                translate_language: data.translate_language || 'zh'
            };
            setLanguage(settingsConfig.value.ui_language || 'zh');
        } catch (e) {
            console.error('Failed to fetch config:', e);
        }
    }
    
    async function saveApiKey() {
        savingSettings.value = true;
        try {
            const res = await API.config.update({ ai_api_key: settingsConfig.value.ai_api_key });
            if (res.ok) {
                ElementPlus.ElMessage.success(currentLang.value === 'zh' ? 'API Key 已更新' : 'API Key updated');
            } else {
                ElementPlus.ElMessage.error(currentLang.value === 'zh' ? '更新失败' : 'Update failed');
            }
        } catch (e) {
            ElementPlus.ElMessage.error(currentLang.value === 'zh' ? '更新失败' : 'Update failed');
        } finally {
            savingSettings.value = false;
        }
    }
    
    async function testAIConnection() {
        testingAI.value = true;
        try {
            const payload = {
                ai_base_url: settingsConfig.value.ai_base_url,
                ai_model: settingsConfig.value.ai_model
            };
            if (settingsConfig.value.ai_api_key && settingsConfig.value.ai_api_key !== '***') {
                payload.ai_api_key = settingsConfig.value.ai_api_key;
            }
            const res = await API.config.testAI(payload);
            const data = await res.json();
            if (res.ok) {
                ElementPlus.ElMessage.success(data.message || t('settings.connectionSuccess'));
            } else {
                ElementPlus.ElMessage.error(data.detail || t('settings.connectionFailed'));
            }
        } catch (e) {
            ElementPlus.ElMessage.error(t('settings.connectionFailed'));
        } finally {
            testingAI.value = false;
        }
    }
    
    async function saveSettings() {
        savingSettings.value = true;
        try {
            const res = await API.config.update(settingsConfig.value);
            if (res.ok) {
                ElementPlus.ElMessage.success(currentLang.value === 'zh' ? '设置已保存' : 'Settings saved');
                if (settingsConfig.value.ui_language) {
                    setLanguage(settingsConfig.value.ui_language);
                }
            } else {
                ElementPlus.ElMessage.error(currentLang.value === 'zh' ? '保存失败' : 'Save failed');
            }
        } catch (e) {
            ElementPlus.ElMessage.error(currentLang.value === 'zh' ? '保存失败' : 'Save failed');
        } finally {
            savingSettings.value = false;
        }
    }
    
    function openFieldSelector(source) {
        fieldSelectorSource.value = source;
        fieldAdvancedMode.value = false;
        
        if (source === 'settings') {
            tempSelectedFields.value = [...(settingsConfig.value.selected_fields || [])];
            if (settingsConfig.value.search_queries?.length > 0) {
                advancedQueriesText.value = settingsConfig.value.search_queries.join('\n');
            } else {
                advancedQueriesText.value = tempSelectedFields.value.map(f => `cat:${f}`).join('\n');
            }
        } else if (source === 'init') {
            tempSelectedFields.value = [...(setupConfig.value.selected_fields || [])];
            if (setupConfig.value.search_queries?.length > 0) {
                advancedQueriesText.value = setupConfig.value.search_queries.join('\n');
            } else {
                advancedQueriesText.value = tempSelectedFields.value.map(f => `cat:${f}`).join('\n');
            }
        }
        
        fieldSearchQuery.value = '';
        
        const recommendedGroups = ['physics', 'cond-mat', 'cs', 'quant-ph'];
        fieldSelectorExpanded.value = {};
        recommendedGroups.forEach(key => {
            fieldSelectorExpanded.value[key] = true;
        });
        
        showFieldSelector.value = true;
    }
    
    function toggleFieldSelectorGroup(key) {
        fieldSelectorExpanded.value[key] = !fieldSelectorExpanded.value[key];
    }
    
    function toggleTempField(fieldId) {
        const idx = tempSelectedFields.value.indexOf(fieldId);
        if (idx >= 0) {
            tempSelectedFields.value.splice(idx, 1);
        } else {
            tempSelectedFields.value.push(fieldId);
        }
    }
    
    function removeFromTempSelection(fieldId) {
        const idx = tempSelectedFields.value.indexOf(fieldId);
        if (idx >= 0) {
            tempSelectedFields.value.splice(idx, 1);
        }
    }
    
    function clearTempSelection() {
        tempSelectedFields.value = [];
        advancedQueriesText.value = '';
    }
    
    return {
        showSetup, setupStep, testingAI, setupConfig,
        showSettings, savingSettings, settingsConfig,
        arxivCategories, allCategories, currentLang,
        showFieldSelector, fieldSelectorSource, tempSelectedFields,
        fieldSearchQuery, fieldSelectorExpanded, recentCategories,
        fieldAdvancedMode, advancedQueriesText,
        filteredCategories, advancedQueriesLines, parsedCodeResult,
        setLanguage, t,
        checkInitStatus, fetchCategories, testSetupAI, fetchConfig,
        saveApiKey, testAIConnection, saveSettings,
        openFieldSelector, toggleFieldSelectorGroup, toggleTempField,
        removeFromTempSelection, clearTempSelection
    };
});
