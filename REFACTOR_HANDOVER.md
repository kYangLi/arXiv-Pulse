# ArXiv-Pulse Refactor Handover

## Goal

Refactor the ArXiv-Pulse project to improve code organization, modularity, and maintainability:
- Reduce index.html from 7035 lines (monolithic Vue app) to ~2500 lines
- Create modular Vue components with Pinia stores
- Ensure all functionality works correctly with comprehensive tests

## Instructions

- Keep code simple and elegant
- Commit changes with `REFACTOR` prefix
- Update this file after major changes
- Use `storeToRefs()` from Pinia to destructure store properties while maintaining reactivity
- Run `black --check . && ruff check .` before commits
- Test in `tests/` directory using `.venv` with `uv pip` for package installation

## Discoveries

- **Pinia storeToRefs()**: Essential for destructuring store properties while maintaining reactivity. Regular destructuring breaks reactivity.
- **Store property naming**: Some properties exist in multiple stores (e.g., `cartPanelRef` in paperStore, `chatPanelRef` in chatStore) - careful naming prevents conflicts.
- **Computed in stores**: `filteredCollections` is a computed property in collectionStore that can be accessed via storeToRefs.
- **LSP errors**: SQLAlchemy Column type errors in Python files are false positives - code works at runtime.
- **Migration strategy**: Using `storeToRefs()` allows keeping same variable names in setup(), so template bindings don't need changes.
- **Pinia/VueDemi**: Pinia requires VueDemi shim. Must expose all Vue reactivity APIs (effectScope, hasInjectionContext, etc.) globally.
- **PaperCard props**: Pass `t` and `currentLang` as props to avoid Pinia initialization timing issues.
- **configStore.t()**: All `t()` calls in JavaScript code must use `configStore.t()` instead of local `t()`.
- **Optional chaining**: Use `?.` for potentially null refs in templates (e.g., `cacheStats?.translations || 0`).

## Current Progress

### File Size Progress

| File | Original | Current | Reduction |
|------|----------|---------|-----------|
| index.html | 7035 | 3452 | **-51%** |
| papers.py | 1069 | 812 | **-24%** |

### Completed Modules

**Backend service layer**:
- `services/paper_service.py` - Paper data enhancement
- `services/translation_service.py` - Translation logic
- `services/ai_client.py` - AI API client abstraction
- `utils/sse.py` - SSE streaming utilities
- `utils/time.py` - Time formatting utilities
- `web/dependencies.py` - FastAPI dependencies

**Frontend API layer**:
- `js/services/api.js` (125 lines) - unified API calls

**Vue component**:
- `js/components/PaperCard.js` (315 lines) - Paper card with i18n props

**Pinia stores** (1469 lines total):
- `js/stores/configStore.js` (341 lines) - Config, settings, categories, i18n, field selector
- `js/stores/paperStore.js` (359 lines) - Papers, cart, search, export
- `js/stores/collectionStore.js` (302 lines) - Collections, collection papers
- `js/stores/chatStore.js` (321 lines) - Chat sessions, messages
- `js/stores/uiStore.js` (146 lines) - Navigation, sync, cache

### i18n Decision

**Keep i18n separated** - do NOT merge:
- `arxiv_pulse/i18n/` (Python) - Backend API messages, AI prompts
- `js/i18n/` (JavaScript) - Frontend UI text

Reasons:
1. Different runtime environments (server vs browser)
2. Merging would require network requests, increasing latency
3. AI prompts should not be exposed to frontend
4. Current separation is clean and maintainable

---

## Remaining Work: Frontend Component Extraction

### Overview

Extract 5 components from index.html:

| Component | Template Lines | Setup Lines | Total | Store Dependency |
|-----------|---------------|-------------|-------|------------------|
| FieldSelectorDialog | 154 | ~50 | ~200 | configStore |
| PaperBasketPanel | 70 | ~30 | ~100 | paperStore, configStore.t |
| ChatWidget | 200 | ~80 | ~280 | chatStore, configStore.t |
| SettingsDrawer | 80 | ~40 | ~120 | configStore |
| CollectionDialogs | 155 | ~50 | ~200 | collectionStore, configStore.t |
| **Total** | **659** | **~250** | **~900** | |

**Expected final index.html**: ~2500 lines (64% reduction from 7035)

---

## Component Extraction Details

### 1. FieldSelectorDialog

**File**: `js/components/FieldSelectorDialog.js`
**Template location in index.html**: Lines 730-883

**Props**:
```javascript
props: {
    modelValue: Boolean,  // v-model for showFieldSelector
    source: String        // 'init' | 'settings' | 'recent'
}
```

**Emits**:
```javascript
emits: ['update:modelValue', 'confirm']
```

**Template structure**:
```html
<el-dialog v-model="showDialog" width="800px" :close-on-click-modal="false" append-to-body>
    <!-- Mode toggle: Visual / Code -->
    <div class="field-selector">
        <div class="field-selector-left">
            <!-- Visual mode: category tree -->
            <!-- Code mode: textarea for advanced queries -->
        </div>
        <div class="field-selector-right">
            <!-- Selected fields list -->
        </div>
    </div>
    <template #footer>
        <el-button @click="cancel">Cancel</el-button>
        <el-button type="primary" @click="confirm">Confirm</el-button>
    </template>
</el-dialog>
```

**Setup dependencies from configStore**:
```javascript
const configStore = useConfigStore();
const {
    fieldAdvancedMode, advancedQueriesText, tempSelectedFields,
    fieldSearchQuery, fieldSelectorExpanded, allCategories,
    filteredCategories, advancedQueriesLines, parsedCodeResult,
    currentLang
} = storeToRefs(configStore);

const {
    toggleFieldSelectorGroup, toggleTempField,
    removeFromTempSelection, clearTempSelection, t
} = configStore;
```

**Methods to implement**:
- `cancel()` - Close dialog without saving
- `confirm()` - Emit selected fields and close
- Watch `source` prop to initialize `tempSelectedFields`

---

### 2. PaperBasketPanel

**File**: `js/components/PaperBasketPanel.js`
**Template location in index.html**: Lines 915-985

**Props**:
```javascript
props: {
    show: Boolean,
    position: Object,     // { x, y }
    zIndex: Number
}
```

**Emits**:
```javascript
emits: ['update:show', 'bring-to-front', 'start-drag']
```

**Template structure**:
```html
<transition name="panel">
    <div v-if="show" class="cart-panel" :style="{ left: position.x + 'px', top: position.y + 'px', zIndex }">
        <div class="cart-header">
            <h3>Basket ({{ paperCart.length }})</h3>
            <div class="collapse-btn" @click="$emit('update:show', false)">...</div>
        </div>
        <div class="cart-body">
            <div v-if="paperCart.length === 0" class="cart-empty">...</div>
            <div v-for="paper in paperCart" class="cart-item">...</div>
        </div>
        <div v-if="paperCart.length > 0" class="cart-footer">
            <!-- Export, Add to Collection, Copy Links, Clear buttons -->
        </div>
    </div>
</transition>
```

**Setup dependencies**:
```javascript
const paperStore = usePaperStore();
const configStore = useConfigStore();

const { paperCart } = storeToRefs(paperStore);
const { removeFromCart, exportCart, addCartToCollection, copyCartLinks, clearCart } = paperStore;
const { t, currentLang } = configStore;
const formatDate = (dateStr) => new Date(dateStr).toLocaleDateString('zh-CN');
```

---

### 3. ChatWidget

**File**: `js/components/ChatWidget.js`
**Template location in index.html**: Lines 1015-1200+

**Props**:
```javascript
props: {
    show: Boolean,
    position: Object,
    size: Object,         // { width, height }
    zIndex: Number,
    fullscreen: Boolean
}
```

**Emits**:
```javascript
emits: ['update:show', 'update:fullscreen', 'bring-to-front', 'start-drag']
```

**Template structure**:
```html
<transition name="panel">
    <div v-if="show" class="chat-window" :class="{ fullscreen }">
        <div class="chat-header">
            <span class="chat-title">AI Chat</span>
            <div class="chat-header-actions">
                <!-- New chat, Fullscreen toggle, Close buttons -->
            </div>
        </div>
        <div class="chat-body">
            <div v-if="showChatSidebar" class="chat-sidebar">...</div>
            <div class="chat-main">
                <div class="chat-messages">
                    <div v-if="chatMessages.length === 0" class="chat-welcome">...</div>
                    <div v-for="msg in chatMessages" class="chat-message">...</div>
                </div>
                <div v-if="selectedChatPapers.length > 0" class="selected-papers-bar">...</div>
                <div class="chat-input-area">
                    <el-input v-model="chatInput" @keyup.enter="sendMessage">...</el-input>
                </div>
            </div>
        </div>
    </div>
</transition>
```

**Setup dependencies**:
```javascript
const chatStore = useChatStore();
const configStore = useConfigStore();

const {
    chatSessions, currentChatSession, chatMessages, chatInput,
    showChatSidebar, selectedChatPapers, chatProgress
} = storeToRefs(chatStore);

const {
    createNewChat, selectChatSession, deleteChatSession, clearAllChatSessions,
    sendChatMessage, togglePaperSelection, removeSelectedChatPaper
} = chatStore;

const { t, currentLang } = configStore;
```

**Helper methods**:
```javascript
const formatChatMessage = (content, isStreaming = false) => { /* markdown formatting */ };
const formatChatTime = (timeStr) => { /* relative time */ };
const quickPrompts = [ /* predefined prompts */ ];
```

---

### 4. SettingsDrawer

**File**: `js/components/SettingsDrawer.js`
**Template location in index.html**: Lines 492-571

**Props**:
```javascript
props: {
    modelValue: Boolean  // v-model for showSettings
}
```

**Emits**:
```javascript
emits: ['update:modelValue']
```

**Template structure**:
```html
<el-drawer :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" size="480px">
    <div style="padding: 24px;">
        <!-- Language selector -->
        <div class="language-selector">...</div>
        
        <!-- AI Config section -->
        <div class="settings-section">
            <h3>AI Config</h3>
            <el-form>
                <el-form-item label="API Base URL">...</el-form-item>
                <el-form-item label="API Key">...</el-form-item>
                <el-form-item label="Model Name">...</el-form-item>
                <el-form-item label="AI Language">...</el-form-item>
                <el-button @click="testAIConnection">Test Connection</el-button>
            </el-form>
        </div>
        
        <!-- Research Fields section -->
        <div class="settings-section">
            <h3>Research Fields</h3>
            <div @click="openFieldSelector">Selected: {{ count }} fields</div>
        </div>
        
        <!-- Sync Settings section -->
        <div class="settings-section">
            <h3>Sync Settings</h3>
            <el-form>
                <el-form-item label="Years Back">...</el-form-item>
                <el-form-item label="Max Results Per Field">...</el-form-item>
                <el-form-item label="Max Results Global">...</el-form-item>
                <el-form-item label="Recent Papers Limit">...</el-form-item>
                <el-form-item label="Search Limit">...</el-form-item>
            </el-form>
        </div>
    </div>
</el-drawer>
```

**Setup dependencies**:
```javascript
const configStore = useConfigStore();

const {
    settingsConfig, testingAI, savingSettings, currentLang
} = storeToRefs(configStore);

const {
    t, saveApiKey, testAIConnection, openFieldSelector
} = configStore;

// Computed options
const aiLanguageOptions = computed(() => [
    { value: 'zh', label: '中文' },
    { value: 'en', label: 'English' },
    { value: 'ja', label: '日本語' },
    { value: 'ko', label: '한국어' },
    { value: 'fr', label: 'Français' },
    { value: 'ru', label: 'Русский' },
    { value: 'de', label: 'Deutsch' },
    { value: 'es', label: 'Español' }
]);

const initYearOptions = computed(() => 
    [1, 2, 3, 5, 7, 10].map(y => ({ value: y, label: `${y} ${currentLang.value === 'zh' ? '年' : 'years'}` }))
);

const onLanguageChange = (lang) => {
    settingsConfig.value.ui_language = lang;
    // Save to backend
};
```

---

### 5. CollectionDialogs

**File**: `js/components/CollectionDialogs.js`
**Template location in index.html**: Lines 574-728

**Props**:
```javascript
props: {
    // Create/Edit Collection
    showCreate: Boolean,
    editingCollection: Object,  // null for create, object for edit
    
    // Add to Collection
    showAddTo: Boolean,
    selectedPaper: Object,
    collections: Array,
    
    // Collection Detail
    showDetail: Boolean,
    viewingCollection: Object,
    
    // Delete Confirm
    showDelete: Boolean,
    deletingCollection: Object,
    
    // Merge Confirm
    showMerge: Boolean,
    mergingPapers: Array,
    mergingToCollection: Object
}
```

**Emits**:
```javascript
emits: [
    'update:showCreate', 'save-collection',
    'update:showAddTo', 'add-to-collection',
    'update:showDetail',
    'update:showDelete', 'confirm-delete',
    'update:showMerge', 'confirm-merge'
]
```

**Template structure** (5 dialogs in one file):
```html
<!-- Create/Edit Collection Dialog -->
<el-dialog v-model="showCreate" :title="editingCollection ? 'Edit' : 'Create'">
    <el-form>
        <el-form-item label="Name">...</el-form-item>
        <el-form-item label="Description">...</el-form-item>
        <el-form-item label="Color">...</el-form-item>
    </el-form>
    <template #footer>...</template>
</el-dialog>

<!-- Add to Collection Dialog -->
<el-dialog v-model="showAddTo" title="Add to Collection">
    <el-select v-model="selectedCollectionId">...</el-select>
    <template #footer>...</template>
</el-dialog>

<!-- Collection Detail Dialog -->
<el-dialog v-model="showDetail" width="800px">
    <div class="collection-detail">
        <!-- Collection info, papers list, etc. -->
    </div>
</el-dialog>

<!-- Delete Confirm Dialog -->
<el-dialog v-model="showDelete" title="Confirm Delete">
    <p>Are you sure you want to delete "{collection.name}"?</p>
    <template #footer>...</template>
</el-dialog>

<!-- Merge Confirm Dialog -->
<el-dialog v-model="showMerge" title="Merge Papers">
    <p>Move {count} papers to "{collection.name}"?</p>
    <template #footer>...</template>
</el-dialog>
```

**Setup dependencies**:
```javascript
const collectionStore = useCollectionStore();
const configStore = useConfigStore();

const { savingCollection, selectedCollectionId, newCollection } = storeToRefs(collectionStore);
const { t, currentLang } = configStore;

const saveCollection = async () => { /* create or update */ };
const confirmAddToCollection = () => { /* add paper to collection */ };
const confirmDelete = () => { /* delete collection */ };
const confirmMerge = () => { /* merge papers */ };
```

---

## Implementation Order

1. **Clean up** - Delete empty `arxiv_pulse/web/services/` directory

2. **FieldSelectorDialog** - Most self-contained, good starting point
   - Create `js/components/FieldSelectorDialog.js`
   - Update index.html to use component
   - Add test in `tests/test_field_selector_component.py`

3. **PaperBasketPanel** - Simple, clear dependencies
   - Create `js/components/PaperBasketPanel.js`
   - Update index.html
   - Add test in `tests/test_basket_component.py`

4. **SettingsDrawer** - Medium complexity
   - Create `js/components/SettingsDrawer.js`
   - Update index.html
   - Add test in `tests/test_settings_component.py`

5. **CollectionDialogs** - Multiple dialogs, more complex
   - Create `js/components/CollectionDialogs.js`
   - Update index.html
   - Add test in `tests/test_collection_dialogs_component.py`

6. **ChatWidget** - Most complex, do last
   - Create `js/components/ChatWidget.js`
   - Update index.html
   - Add test in `tests/test_chat_component.py`

---

## Testing Requirements

Each component needs tests in `tests/` directory:

### Test Environment Setup
```bash
# From project root
cd tests
../.venv/bin/python test_xxx.py

# If need to install packages
uv pip install playwright
```

### Test Template
```python
"""Test Component Name with Playwright"""
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:8000"

def test_component():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        errors = []
        page.on('console', lambda msg: errors.append(msg.text) if msg.type == 'error' else None)
        page.on('pageerror', lambda err: errors.append(str(err)))
        
        page.goto(BASE_URL)
        page.wait_for_load_state('networkidle')
        
        # Test component functionality
        # ...
        
        assert len([e for e in errors if 'error' in e.lower()]) == 0, f"Errors: {errors}"
        browser.close()
```

### Test Cases Per Component

**FieldSelectorDialog**:
- Dialog opens/closes correctly
- Visual mode: category tree expands/collapses
- Visual mode: selecting/deselecting fields works
- Code mode: textarea accepts input
- Code mode: parsed queries show in right panel
- Confirm button emits correct data

**PaperBasketPanel**:
- Panel shows/hides correctly
- Empty state displays when cart is empty
- Papers display correctly in cart
- Remove button works
- Export dropdown functions
- Add to collection button works
- Drag functionality works

**SettingsDrawer**:
- Drawer opens/closes correctly
- Language switcher changes UI language
- AI config form fields are editable
- Test connection button works
- Field selector opens from settings
- Sync settings are editable

**CollectionDialogs**:
- Create dialog: creates new collection
- Edit dialog: updates existing collection
- Add to collection: adds paper to selected collection
- Delete confirm: deletes collection
- Merge confirm: merges papers

**ChatWidget**:
- Window shows/hides correctly
- Sidebar shows chat history
- New chat button creates session
- Messages send and receive
- Quick prompts work
- Fullscreen toggle works
- Drag functionality works

---

## Final File Structure

```
arxiv_pulse/
├── i18n/                          # Backend i18n (Python)
│   ├── __init__.py
│   ├── zh.py
│   └── en.py
├── services/
│   ├── ai_client.py
│   ├── paper_service.py
│   └── translation_service.py
├── utils/
│   ├── __init__.py
│   ├── sse.py
│   └── time.py
├── web/
│   ├── dependencies.py
│   ├── api/
│   │   ├── papers.py
│   │   ├── collections.py
│   │   ├── chat.py
│   │   ├── config.py
│   │   ├── tasks.py
│   │   ├── stats.py
│   │   ├── cache.py
│   │   └── export.py
│   └── static/
│       ├── css/main.css
│       ├── libs/
│       │   ├── vue/vue.global.prod.js
│       │   └── pinia/pinia.iife.js
│       └── js/
│           ├── components/
│           │   ├── PaperCard.js           ✓
│           │   ├── FieldSelectorDialog.js
│           │   ├── PaperBasketPanel.js
│           │   ├── SettingsDrawer.js
│           │   ├── CollectionDialogs.js
│           │   └── ChatWidget.js
│           ├── stores/
│           │   ├── configStore.js         ✓
│           │   ├── paperStore.js          ✓
│           │   ├── collectionStore.js     ✓
│           │   ├── chatStore.js           ✓
│           │   └── uiStore.js             ✓
│           ├── services/
│           │   └── api.js                 ✓
│           ├── i18n/                      # Frontend i18n (JavaScript)
│           │   ├── zh.js
│           │   └── en.js
│           └── utils/
│               └── export.js              ✓
└── index.html                            # Main Vue app (~2500 lines after refactor)

tests/
├── test_navigation.py                    ✓
├── test_field_selector.py                ✓
├── test_ui.py                            ✓
├── test_field_selector_component.py      # NEW
├── test_basket_component.py              # NEW
├── test_settings_component.py            # NEW
├── test_collection_dialogs_component.py  # NEW
└── test_chat_component.py                # NEW
```

---

## Commands Reference

```bash
# Lint check
black --check . && ruff check .

# Start server
cd tests && ../.venv/bin/pulse serve ..

# Run single test
cd tests && ../.venv/bin/python test_xxx.py

# Install package in venv
uv pip install playwright
```

---

## Commit Message Format

```
REFACTOR: Extract ComponentName from index.html

- Create js/components/ComponentName.js
- Template: X lines, Setup: Y lines
- Dependencies: storeA, storeB
- Add tests in tests/test_component_name.py
- index.html: 3452 -> XXXX lines
```
