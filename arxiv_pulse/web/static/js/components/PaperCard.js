const PaperCardTemplate = `
<div class="paper-card" :data-arxiv-id="paper.arxiv_id">
    <div class="paper-header">
        <div class="paper-title" @click="openArxiv(paper.arxiv_id)">{{ paper.title }}</div>
    </div>
    <div v-if="paper.title_translation" class="paper-title-cn">{{ paper.title_translation }}</div>
    <div v-else-if="!paper.ai_available" class="paper-title-cn" style="color: var(--text-muted); font-style: italic;">
        {{ isZh ? '未配置 AI API Key，无法翻译' : 'AI API Key not configured' }}
    </div>
    <div class="paper-meta">
        <span class="paper-meta-item">
            <el-icon><Calendar /></el-icon>
            {{ formatDate(paper.published) }}
        </span>
        <span class="paper-meta-item">
            <el-icon><User /></el-icon>
            {{ paper.authors?.slice(0, 2).map(a => a.name).join(', ') }}{{ paper.authors?.length > 2 ? (isZh ? ' 等' : ' et al.') : '' }}
        </span>
        <span class="paper-relevance">
            <span v-for="i in 5" :key="i" class="star">{{ i <= paper.relevance_score ? '★' : '☆' }}</span>
        </span>
    </div>
    <div class="paper-category" v-if="paper.category_explanation">{{ paper.category_explanation }}</div>
    <div v-if="!expanded" class="paper-abstract-preview">{{ paper.abstract?.slice(0, 200) }}...</div>
    <div class="paper-actions">
        <el-button size="small" text type="primary" @click="openArxiv(paper.arxiv_id)">
            <el-icon><Promotion /></el-icon> {{ t('paper.arxiv') }}
        </el-button>
        <el-button size="small" text type="primary" @click="downloadPDF(paper.arxiv_id)">
            <el-icon><Download /></el-icon> {{ t('paper.pdf') }}
        </el-button>
        <el-button size="small" text type="primary" @click="downloadCard">
            <el-icon><Picture /></el-icon> {{ t('paper.card') }}
        </el-button>
        <el-button v-if="!inCart" size="small" text type="warning" @click="$emit('add-to-cart', paper)">
            <el-icon><Star /></el-icon> {{ t('paper.bookmark') }}
        </el-button>
        <el-button v-else size="small" type="warning" plain @click="$emit('remove-from-cart', paper.arxiv_id)">
            <el-icon><StarFilled /></el-icon> {{ t('paper.bookmarked') }}
        </el-button>
        <el-button size="small" text type="primary" @click="analyzePaper">
            <el-icon><ChatDotRound /></el-icon> {{ t('paper.analyze') }}
        </el-button>
        <el-button size="small" text type="primary" @click="$emit('add-to-collection', paper)">
            <el-icon><Folder /></el-icon> {{ t('paper.addToCollection') }}
        </el-button>
        <el-button size="small" text @click="expanded = !expanded">
            {{ expanded ? t('paper.collapse') : t('paper.expandDetail') }}
        </el-button>
        <el-button v-if="inCollection" size="small" text type="danger" @click="$emit('remove-from-collection', paper.id)">
            <el-icon><Delete /></el-icon> {{ t('paper.removeFromCollection') }}
        </el-button>
    </div>
    <div v-if="expanded" class="paper-detail">
        <div v-if="paper.summary_text" class="ai-summary-section">
            <h4>{{ t('paper.aiSummary') }}</h4>
            <p class="summary-text" v-html="formatSummary(paper.summary_text)"></p>
        </div>
        <div v-else-if="!paper.ai_available" class="ai-summary-section" style="color: var(--text-muted); font-style: italic;">
            <h4>{{ t('paper.aiSummary') }}</h4>
            <p>{{ isZh ? '未配置 AI API Key，无法生成总结。请在设置中配置。' : 'AI API Key not configured. Please configure in Settings.' }}</p>
        </div>
        <div v-else class="ai-summary-section" style="color: var(--text-muted); font-style: italic;">
            <h4>{{ t('paper.aiSummary') }}</h4>
            <p>{{ isZh ? '暂无 AI 总结' : 'No AI summary available' }}</p>
        </div>
        <div v-if="paper.key_findings?.length" class="key-findings">
            <h4>{{ t('paper.keyFindings') }}</h4>
            <ul>
                <li v-for="(finding, i) in paper.key_findings" :key="i">{{ finding }}</li>
            </ul>
        </div>
        <div v-if="paper.keywords?.length" class="paper-keywords">
            <h4>{{ t('paper.keywords') }}</h4>
            <div class="keywords-list">
                <el-tag v-for="kw in paper.keywords" :key="kw" size="small" type="info">{{ kw }}</el-tag>
            </div>
        </div>
        <div v-if="paper.figure_url" class="paper-figure">
            <img :src="paper.figure_url" @click="openImage(paper.figure_url)" />
        </div>
        <div class="abstract-section">
            <h4>{{ t('paper.abstract') }}</h4>
            <p>{{ paper.abstract }}</p>
            <div v-if="paper.abstract_translation" class="translation">
                <h4>{{ t('paper.chineseTranslation') }}</h4>
                <p>{{ paper.abstract_translation }}</p>
            </div>
            <div v-else-if="!paper.ai_available" class="translation" style="color: var(--text-muted); font-style: italic;">
                <h4>{{ t('paper.chineseTranslation') }}</h4>
                <p>{{ isZh ? '未配置 AI API Key，无法翻译。请在设置中配置。' : 'AI API Key not configured. Please configure in Settings.' }}</p>
            </div>
        </div>
    </div>
</div>
`;

const PaperCardSetup = (props) => {
    const expanded = ref(false);
    
    // Use props for i18n (passed from parent)
    const t = props.t || ((key) => key);
    const currentLang = ref(props.currentLang || 'zh');
    const isZh = computed(() => currentLang.value === 'zh');
    
    const formatDate = (dateStr) => {
        if (!dateStr) return '';
        return new Date(dateStr).toLocaleDateString('zh-CN');
    };
    
    const formatSummary = (text) => {
        if (!text) return '';
        return text.replace(/\n/g, '<br>');
    };
    
    const openArxiv = (arxivId) => {
        window.open(`https://arxiv.org/abs/${arxivId}`, '_blank');
    };
    
    const downloadPDF = (arxivId) => {
        window.open(`https://arxiv.org/pdf/${arxivId}.pdf`, '_blank');
    };
    
    const openImage = (url) => {
        window.open(url, '_blank');
    };
    
    const downloadCard = async () => {
        const scale = 2;
        const width = 700 * scale;
        const padding = 32 * scale;
        
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        const wrapText = (text, maxWidth, fontSize, fontFamily = 'sans-serif', fontWeight = 'normal') => {
            if (!text) return [];
            ctx.font = `${fontWeight} ${fontSize * scale}px ${fontFamily}`;
            const chars = text.split('');
            const result = [];
            let current = '';
            for (const char of chars) {
                const test = current + char;
                if (ctx.measureText(test).width > maxWidth && current) {
                    result.push(current);
                    current = char;
                } else {
                    current = test;
                }
            }
            if (current) result.push(current);
            return result;
        };
        
        let y = padding;
        const elements = [];
        
        const titleLines = wrapText(props.paper.title, width - padding * 2, 20, 'Georgia, "Noto Serif SC", serif', 'bold');
        titleLines.forEach(line => {
            elements.push({ type: 'text', text: line, font: `bold ${20 * scale}px Georgia, "Noto Serif SC", serif`, color: '#1e3a5f', y: y });
            y += 32 * scale;
        });
        
        if (props.paper.title_translation) {
            const transLines = wrapText(props.paper.title_translation, width - padding * 2, 16);
            transLines.forEach(line => {
                elements.push({ type: 'text', text: line, font: `italic ${16 * scale}px sans-serif`, color: '#5a6c7d', y: y });
                y += 26 * scale;
            });
            y += 8 * scale;
        }
        
        const pubDate = props.paper.published ? new Date(props.paper.published).toLocaleDateString('zh-CN') : 'N/A';
        const authors = props.paper.authors?.slice(0, 4).map(a => a.name).join(', ') || '';
        elements.push({ type: 'text', text: `${pubDate}  |  ${authors}${props.paper.authors?.length > 4 ? ' 等' : ''}`, font: `${13 * scale}px sans-serif`, color: '#909399', y: y });
        y += 36 * scale;
        
        elements.push({ type: 'divider', y: y });
        y += 20 * scale;
        
        if (props.paper.summary_text) {
            elements.push({ type: 'section-title', text: 'AI 总结', y: y });
            y += 28 * scale;
            const paragraphs = props.paper.summary_text.split('\n\n');
            paragraphs.forEach(para => {
                if (para.trim()) {
                    const summaryLines = wrapText(para.trim(), width - padding * 2, 14);
                    summaryLines.forEach(line => {
                        elements.push({ type: 'text', text: line, font: `${14 * scale}px sans-serif`, color: '#333', y: y });
                        y += 22 * scale;
                    });
                    y += 8 * scale;
                }
            });
            y += 4 * scale;
        }
        
        if (props.paper.keywords?.length) {
            elements.push({ type: 'section-title', text: '关键词', y: y });
            y += 28 * scale;
            const keywordsText = props.paper.keywords.join('  •  ');
            const keywordLines = wrapText(keywordsText, width - padding * 2, 13);
            keywordLines.forEach(line => {
                elements.push({ type: 'text', text: line, font: `${13 * scale}px sans-serif`, color: '#c9a227', y: y });
                y += 20 * scale;
            });
            y += 12 * scale;
        }
        
        if (props.paper.key_findings?.length) {
            elements.push({ type: 'section-title', text: '关键发现', y: y });
            y += 28 * scale;
            props.paper.key_findings.forEach(finding => {
                const findingLines = wrapText(`• ${finding}`, width - padding * 2 - 20 * scale, 14);
                findingLines.forEach(line => {
                    elements.push({ type: 'text', text: line, font: `${14 * scale}px sans-serif`, color: '#5a6c7d', y: y });
                    y += 22 * scale;
                });
            });
            y += 12 * scale;
        }
        
        if (props.paper.figure_url) {
            try {
                const img = new Image();
                img.crossOrigin = 'anonymous';
                await new Promise((resolve, reject) => {
                    img.onload = resolve;
                    img.onerror = reject;
                    img.src = props.paper.figure_url;
                });
                const maxImgWidth = width - padding * 2;
                const imgScale = Math.min(1, maxImgWidth / img.width);
                const imgDrawWidth = img.width * imgScale;
                const imgDrawHeight = img.height * imgScale;
                elements.push({ type: 'image', img, y, width: imgDrawWidth, height: imgDrawHeight });
                y += imgDrawHeight + 20 * scale;
            } catch (e) {}
        }
        
        elements.push({ type: 'section-title', text: '摘要 (Abstract)', y: y });
        y += 28 * scale;
        
        const abstractLines = wrapText(props.paper.abstract || '', width - padding * 2, 14);
        abstractLines.forEach(line => {
            elements.push({ type: 'text', text: line, font: `${14 * scale}px sans-serif`, color: '#444', y: y });
            y += 22 * scale;
        });
        y += 12 * scale;
        
        if (props.paper.abstract_translation) {
            elements.push({ type: 'section-title', text: t('paper.chineseTranslation'), y: y });
            y += 28 * scale;
            const transAbstractLines = wrapText(props.paper.abstract_translation, width - padding * 2, 14);
            transAbstractLines.forEach(line => {
                elements.push({ type: 'text', text: line, font: `${14 * scale}px sans-serif`, color: '#555', y: y });
                y += 22 * scale;
            });
            y += 12 * scale;
        }
        
        y += 16 * scale;
        elements.push({ type: 'divider', y: y });
        y += 20 * scale;
        
        elements.push({ type: 'text', text: `arXiv: ${props.paper.arxiv_id}`, font: `${12 * scale}px sans-serif`, color: '#909399', y: y });
        y += 24 * scale;
        elements.push({ type: 'text', text: 'arXiv Pulse', font: `bold ${13 * scale}px Georgia, serif`, color: '#c9a227', y: y });
        
        const height = y + padding;
        canvas.width = width;
        canvas.height = height;
        
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, width, height);
        
        ctx.fillStyle = '#1e3a5f';
        ctx.fillRect(0, 0, 6 * scale, height);
        
        ctx.fillStyle = '#c9a227';
        ctx.fillRect(0, height - 4 * scale, width, 4 * scale);
        
        for (const el of elements) {
            if (el.type === 'text') {
                ctx.font = el.font;
                ctx.fillStyle = el.color;
                ctx.fillText(el.text, padding, el.y);
            } else if (el.type === 'section-title') {
                ctx.font = `bold ${15 * scale}px sans-serif`;
                ctx.fillStyle = '#1e3a5f';
                ctx.fillText(el.text, padding, el.y);
                ctx.fillStyle = '#c9a227';
                ctx.fillRect(padding, el.y + 6 * scale, 40 * scale, 2 * scale);
            } else if (el.type === 'divider') {
                ctx.strokeStyle = '#e8e6e1';
                ctx.lineWidth = 1 * scale;
                ctx.beginPath();
                ctx.moveTo(padding, el.y);
                ctx.lineTo(width - padding, el.y);
                ctx.stroke();
            } else if (el.type === 'image') {
                ctx.drawImage(el.img, padding, el.y, el.width, el.height);
            }
        }
        
        const link = document.createElement('a');
        link.download = `paper_${props.paper.arxiv_id}.png`;
        link.href = canvas.toDataURL('image/png', 1.0);
        link.click();
        
        ElementPlus.ElMessage.success('已导出卡片图片');
    };
    
    const analyzePaper = () => {
        window.dispatchEvent(new CustomEvent('analyze-paper', { detail: props.paper }));
    };
    
    return { expanded, formatDate, formatSummary, openArxiv, downloadPDF, openImage, downloadCard, analyzePaper, t, currentLang, isZh };
};
