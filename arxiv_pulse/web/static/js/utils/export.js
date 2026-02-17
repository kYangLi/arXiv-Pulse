const API_BASE = '/api';

async function downloadExport(url, options, filename) {
    try {
        const res = await fetch(url, options);
        if (!res.ok) throw new Error('Export failed');
        const blob = await res.blob();
        const blobUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = blobUrl;
        a.download = filename;
        a.click();
        window.URL.revokeObjectURL(blobUrl);
        return { success: true, count: options.body ? JSON.parse(options.body).paper_ids?.length : null };
    } catch (e) {
        return { success: false, error: e };
    }
}

function getFileExtension(format) {
    if (format === 'markdown') return 'md';
    if (format === 'bibtex') return 'bib';
    return format;
}

async function exportPapers(paperIds, format, filename = 'papers') {
    if (!paperIds || paperIds.length === 0) return { success: false, error: 'No papers selected' };
    const result = await downloadExport(
        `${API_BASE}/export/papers`,
        {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ paper_ids: paperIds, format, include_summary: true })
        },
        `${filename}.${getFileExtension(format)}`
    );
    return result;
}

async function exportCollection(collectionId, collectionName, format) {
    const result = await downloadExport(
        `${API_BASE}/export/collection`,
        {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ collection_id: collectionId, format, include_summary: true })
        },
        `collection_${collectionName.replace(/\s+/g, '_')}.${getFileExtension(format)}`
    );
    return result;
}

function showMessage(result, successMsg, errorMsg) {
    if (result.success) {
        const msg = result.count ? successMsg.replace('{count}', result.count) : successMsg;
        ElementPlus.ElMessage.success(msg);
    } else {
        ElementPlus.ElMessage.error(errorMsg);
    }
}
