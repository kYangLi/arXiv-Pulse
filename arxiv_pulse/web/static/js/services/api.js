const API_BASE = '/api';

const API = {
    config: {
        get: () => fetch(`${API_BASE}/config`),
        update: (data) => fetch(`${API_BASE}/config`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        }),
        status: () => fetch(`${API_BASE}/config/status`),
        categories: () => fetch(`${API_BASE}/config/categories`),
        testAI: (data) => fetch(`${API_BASE}/config/test-ai`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        }),
        init: (data) => fetch(`${API_BASE}/config/init`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        }),
        initSync: () => fetch(`${API_BASE}/config/init/sync`, { method: 'POST' })
    },

    stats: {
        get: () => fetch(`${API_BASE}/stats`),
        fields: () => fetch(`${API_BASE}/stats/fields`),
        refresh: () => fetch(`${API_BASE}/stats/refresh`, { method: 'POST' })
    },

    papers: {
        recentCacheStream: (params) => fetch(`${API_BASE}/papers/recent/cache/stream?${params}`),
        recentUpdate: (params, signal) => fetch(`${API_BASE}/papers/recent/update?${params}`, { method: 'POST', signal }),
        searchStream: (params, signal) => fetch(`${API_BASE}/papers/search/stream?${params}`, { signal }),
        aiFilter: (data) => fetch(`${API_BASE}/papers/ai-filter`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        }),
        quick: (params, signal) => fetch(`${API_BASE}/papers/quick?${params}`, { signal }),
        pdf: (arxivId) => fetch(`${API_BASE}/papers/pdf/${arxivId}`)
    },

    collections: {
        list: () => fetch(`${API_BASE}/collections`),
        get: (id) => fetch(`${API_BASE}/collections/${id}`),
        create: (data) => fetch(`${API_BASE}/collections`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        }),
        update: (id, data) => fetch(`${API_BASE}/collections/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        }),
        delete: (id) => fetch(`${API_BASE}/collections/${id}`, { method: 'DELETE' }),
        merge: (id, targetId) => fetch(`${API_BASE}/collections/${id}/merge`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target_collection_id: targetId })
        }),
        aiSearch: (id, query) => fetch(`${API_BASE}/collections/${id}/ai-search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        }),
        papers: (id, params) => fetch(`${API_BASE}/collections/${id}/papers?${params}`),
        addPaper: (id, paperId) => fetch(`${API_BASE}/collections/${id}/papers`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ paper_id: paperId })
        }),
        removePaper: (id, paperId) => fetch(`${API_BASE}/collections/${id}/papers/${paperId}`, { method: 'DELETE' }),
        addPapersBatch: (id, paperIds) => fetch(`${API_BASE}/collections/${id}/papers/batch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ paper_ids: paperIds })
        })
    },

    tasks: {
        status: () => fetch(`${API_BASE}/tasks/status`),
        sync: (params) => fetch(`${API_BASE}/tasks/sync?${params}`, { method: 'POST' })
    },

    cache: {
        stats: () => fetch(`${API_BASE}/cache/stats`),
        clear: (cacheType) => fetch(`${API_BASE}/cache/clear`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cache_type: cacheType })
        })
    },

    export: {
        papers: (data) => fetch(`${API_BASE}/export/papers`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        }),
        collection: (data) => fetch(`${API_BASE}/export/collection`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
    },

    chat: {
        sessions: {
            list: () => fetch(`${API_BASE}/chat/sessions`),
            create: () => fetch(`${API_BASE}/chat/sessions`, { method: 'POST' }),
            get: (id) => fetch(`${API_BASE}/chat/sessions/${id}`),
            delete: (id) => fetch(`${API_BASE}/chat/sessions/${id}`, { method: 'DELETE' }),
            send: (id, data) => fetch(`${API_BASE}/chat/sessions/${id}/send`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            })
        }
    }
};

function buildParams(params) {
    return Object.entries(params)
        .filter(([, v]) => v !== undefined && v !== null)
        .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
        .join('&');
}
