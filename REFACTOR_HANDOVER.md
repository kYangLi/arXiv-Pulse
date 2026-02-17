# ArXiv-Pulse Refactor Handover

## Goal

Refactor the ArXiv-Pulse project to improve code organization, modularity, and maintainability:
- Reduce index.html from 7035 lines (monolithic Vue app)
- Reduce papers.py from 1069 lines
- Create modular service layer, utilities, and Vue stores
- Implement Pinia state management for better component decoupling

## Instructions

- Keep code simple and elegant
- Commit changes with `REFACTOR` prefix
- Update this file after major changes
- Use `storeToRefs()` from Pinia to destructure store properties while maintaining reactivity
- Run `black --check . && ruff check .` before commits

## Discoveries

- **Pinia storeToRefs()**: Essential for destructuring store properties while maintaining reactivity. Regular destructuring breaks reactivity.
- **Store property naming**: Some properties exist in multiple stores (e.g., `cartPanelRef` in paperStore, `chatPanelRef` in chatStore) - careful naming prevents conflicts.
- **Computed in stores**: `filteredCollections` is a computed property in collectionStore that can be accessed via storeToRefs.
- **LSP errors**: SQLAlchemy Column type errors in Python files are false positives - code works at runtime.
- **Migration strategy**: Using `storeToRefs()` allows keeping same variable names in setup(), so template bindings don't need changes.

## Accomplished

### Completed (Sessions 1-6):

**Backend service layer**:
- `services/paper_service.py` - Paper data enhancement
- `services/translation_service.py` - Translation logic
- `services/ai_client.py` - AI API client abstraction
- `utils/sse.py` - SSE streaming utilities
- `utils/time.py` - Time formatting utilities
- `web/dependencies.py` - FastAPI dependencies

**Frontend API layer**:
- `js/services/api.js` (121 lines) - unified API calls

**Vue component**:
- `js/components/PaperCard.js` (312 lines)

**Pinia stores** (fully integrated):
- `js/stores/configStore.js` (336 lines) - Config, settings, categories, i18n, field selector
- `js/stores/paperStore.js` (359 lines) - Papers, cart, search, export
- `js/stores/collectionStore.js` (302 lines) - Collections, collection papers
- `js/stores/chatStore.js` (321 lines) - Chat sessions, messages
- `js/stores/uiStore.js` (146 lines) - Navigation, sync, cache

**Store integration completed**:
- All store properties migrated via `storeToRefs()`
- All store methods integrated (checkInitStatus, fetchConfig, saveSettings, etc.)
- Removed duplicate ref() declarations
- Removed duplicate computed properties
- Removed duplicate function definitions
- index.html reduced to 3372 lines (-52% from 7035)

### Key refactorings this session:

1. **configStore full migration**:
   - `showSetup`, `setupStep`, `setupConfig`, `testingAI`
   - `showSettings`, `savingSettings`, `settingsConfig`
   - `arxivCategories`, `allCategories`, `currentLang`
   - `showFieldSelector`, `fieldSelectorSource`, `tempSelectedFields`, etc.
   - `filteredCategories`, `advancedQueriesLines`, `parsedCodeResult`
   - Functions: `t()`, `setLanguage()`, `getFieldTranslation()`, `checkInitStatus()`, `fetchCategories()`, `testSetupAI()`, `fetchConfig()`, `saveSettings()`, `saveApiKey()`, `testAIConnection()`, `openFieldSelector()`, etc.

2. **Removed global scope duplicates**:
   - Removed `currentLang`, `t()`, `setLanguage()`, `getFieldTranslation()` outside setup()
   - Removed `arxivCategories`, `allCategories`, `defaultFields` outside setup()

3. **Removed duplicate local refs**:
   - Removed duplicate `syncStatus`, `syncing`, `syncYearsBack`, `syncForce` (already in uiStore)

## File Size Progress

| File | Original | Current | Reduction |
|------|----------|---------|-----------|
| index.html | 7035 | 3372 | **-52%** |
| papers.py | 1069 | 812 | **-24%** |

## Current Project Structure

```
arxiv_pulse/
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
│   └── static/
│       ├── css/main.css
│       └── js/
│           ├── components/PaperCard.js
│           ├── i18n/zh.js, en.js
│           ├── services/api.js
│           ├── stores/
│           │   ├── configStore.js
│           │   ├── paperStore.js
│           │   ├── collectionStore.js
│           │   ├── chatStore.js
│           │   └── uiStore.js
│           └── utils/export.js
```

## Next Steps

1. **Test the application** - Run `pulse serve .` and verify all functionality
2. **Extract more Vue components** - Now that stores are integrated, extract:
   - ChatWidget component
   - FieldSelector component
   - SettingsDrawer component
3. **Consider Vite build system** - For Vue SFC support and better DX
4. **Optimize re-renders** - Review computed properties for unnecessary updates

## Testing Commands

```bash
black --check . && ruff check .
pulse serve .
```
