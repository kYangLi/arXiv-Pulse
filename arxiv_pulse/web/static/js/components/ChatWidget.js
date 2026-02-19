const ChatWidgetTemplate = `
    <transition name="panel">
        <div v-if="show" 
             class="chat-window" 
             :class="{ fullscreen: fullscreen, 'animate-fullscreen': animating }"
             :style="fullscreen ? { zIndex: zIndex } : { position: 'fixed', left: position.x + 'px', top: position.y + 'px', width: size.width + 'px', height: size.height + 'px', zIndex: zIndex }"
             @mousedown="onMouseDown"
             @click="$emit('bring-to-front')">
            <div class="chat-header">
                <span class="chat-title">
                    <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
                        <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
                    </svg>
                    {{ t('chat.title') }}
                </span>
                <div class="chat-header-actions">
                    <el-button text @click.stop="createNewChat" :title="t('chat.newChat')">
                        <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                            <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
                        </svg>
                    </el-button>
                    <el-button text @click.stop="toggleFullscreen" :title="fullscreen ? (currentLang === 'zh' ? '还原' : 'Restore') : (currentLang === 'zh' ? '全屏' : 'Fullscreen')">
                        <svg v-if="fullscreen" viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                            <path d="M5 16h3v3h2v-5H5v2zm3-8H5v2h5V5H8v3zm6 11h2v-3h3v-2h-5v5zm2-11V5h-2v5h5V8h-3z"/>
                        </svg>
                        <svg v-else viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                            <path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/>
                        </svg>
                    </el-button>
                    <div class="collapse-btn" @click.stop="$emit('update:show', false)" :title="currentLang === 'zh' ? '收起' : 'Collapse'">
                        <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                            <path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6z"/>
                        </svg>
                    </div>
                </div>
            </div>
            
            <div class="chat-body">
                <transition name="sidebar-slide">
                    <div v-if="showChatSidebar" class="chat-sidebar">
                        <div class="chat-sidebar-header">
                            <span>{{ t('chat.history') }}</span>
                            <div class="sidebar-header-actions">
                                <el-button 
                                    v-if="chatSessions.length > 0"
                                    text 
                                    size="small" 
                                    @click="clearAllChatSessions"
                                    :title="t('chat.clearAll')"
                                    class="clear-all-btn"
                                >
                                    <el-icon><Delete /></el-icon>
                                </el-button>
                                <el-button text size="small" @click="showChatSidebar = false">
                                    <el-icon><ArrowLeft /></el-icon>
                                </el-button>
                            </div>
                        </div>
                        <div class="chat-session-list">
                            <div 
                                v-for="session in chatSessions" 
                                :key="session.id" 
                                class="chat-session-item"
                                :class="{ active: currentChatSession?.id === session.id }"
                            >
                                <div class="session-info" @click="selectChatSession(session)">
                                    <div class="session-title">{{ session.title }}</div>
                                    <div class="session-time">{{ formatChatTime(session.updated_at) }}</div>
                                </div>
                                <el-button 
                                    class="session-delete" 
                                    text 
                                    size="small" 
                                    @click.stop="deleteChatSession(session)"
                                    :title="t('common.delete')"
                                >
                                    <el-icon><Delete /></el-icon>
                                </el-button>
                            </div>
                            <div v-if="chatSessions.length === 0" class="no-sessions">
                                {{ t('chat.noSession') }}
                            </div>
                        </div>
                    </div>
                </transition>
                <div v-if="showChatSidebar" class="sidebar-overlay" @click="showChatSidebar = false"></div>
                
                <div class="chat-main" @click="showChatSidebar = false">
                    <div class="chat-messages" ref="chatMessagesContainer" @scroll="handleChatScroll">
                        <div v-if="chatMessages.length === 0" class="chat-welcome">
                            <div class="welcome-icon">
                                <span class="welcome-omega">Ω</span>
                            </div>
                            <h3>{{ t('chat.title') }}</h3>
                            <p>{{ t('chat.welcome') }}</p>
                            <div class="quick-prompts">
                                <div 
                                    v-for="(prompt, idx) in quickPrompts" 
                                    :key="idx" 
                                    class="quick-prompt-btn"
                                    @click="sendQuickPrompt(prompt.text)"
                                >
                                    <span class="prompt-icon">{{ prompt.icon }}</span>
                                    <span class="prompt-text">{{ prompt.text }}</span>
                                </div>
                            </div>
                        </div>
                        <div v-for="(msg, idx) in chatMessages" :key="msg.id" class="chat-message" :class="msg.role">
                            <div v-if="msg.role === 'assistant'" class="message-avatar assistant">
                                <span class="omega-symbol">Ω</span>
                            </div>
                            <div class="message-content">
                                <div v-if="msg.paper_ids?.length" class="message-papers">
                                    <el-tag v-for="pid in msg.paper_ids" :key="pid" size="small" type="info">{{ pid }}</el-tag>
                                </div>
                                <template v-if="msg.role === 'assistant' && msg.isStreaming">
                                    <div v-if="chatProgress" class="chat-progress">
                                        <div class="progress-header">
                                            <el-icon class="is-loading"><Loading /></el-icon>
                                            <span class="progress-message">{{ chatProgress.message }}</span>
                                        </div>
                                        <div v-if="chatProgress.progress" class="progress-bar-container">
                                            <div class="progress-bar" :style="{ width: chatProgress.progress + '%' }"></div>
                                        </div>
                                        <div v-if="chatProgress.textLength || chatProgress.pageCount" class="progress-details">
                                            <span v-if="chatProgress.textLength">{{ chatProgress.textLength.toLocaleString() }} 字符</span>
                                            <span v-if="chatProgress.pageCount">{{ chatProgress.pageCount }} 页</span>
                                        </div>
                                    </div>
                                    <div v-else class="message-text streaming">
                                        <span v-html="formatChatMessage(msg.content, true)"></span>
                                        <span class="streaming-cursor"></span>
                                    </div>
                                </template>
                                <template v-else-if="msg.role === 'assistant'">
                                    <div class="message-text" :id="'msg-' + msg.id" v-html="formatChatMessage(msg.content)"></div>
                                    <div v-if="!msg.isStreaming && msg.content" class="message-actions">
                                        <el-button text size="small" @click="copyMessage(msg.content)" :title="t('chat.copy')">
                                            <el-icon><CopyDocument /></el-icon>
                                        </el-button>
                                        <el-button text size="small" @click="regenerateMessage(idx)" :title="t('chat.regenerate')" :loading="msg.isRegenerating">
                                            <el-icon><Refresh /></el-icon>
                                        </el-button>
                                    </div>
                                </template>
                                <div v-else class="message-text" v-html="formatChatMessage(msg.content)"></div>
                            </div>
                            <div v-if="msg.role === 'user'" class="message-avatar user">
                                <svg viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/>
                                </svg>
                            </div>
                        </div>
                    </div>
                    
                    <div v-if="selectedChatPapers.length > 0" class="selected-papers-bar">
                        <span>{{ t('chat.selectedPapers', { count: selectedChatPapers.length }) }}</span>
                        <el-tag 
                            v-for="paper in selectedChatPapers" 
                            :key="paper.arxiv_id" 
                            closable 
                            size="small"
                            @close="removeSelectedChatPaper(paper.arxiv_id)"
                        >
                            {{ paper.title?.slice(0, 20) }}...
                        </el-tag>
                    </div>
                    
                    <div class="chat-input-area">
                        <el-button text @click.stop="showChatSidebar = !showChatSidebar" :title="t('chat.history')" class="history-btn">
                            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                                <path d="M13 3c-4.97 0-9 4.03-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42C8.27 19.99 10.51 21 13 21c4.97 0 9-4.03 9-9s-4.03-9-9-9zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z"/>
                            </svg>
                        </el-button>
                        <el-input
                            v-model="chatInput"
                            type="textarea"
                            :autosize="{ minRows: 1, maxRows: 4 }"
                            :placeholder="t('chat.inputPlaceholder')"
                            @keydown.enter.exact.prevent="sendChatMessage"
                            :disabled="chatTyping"
                            resize="none"
                        />
                        <el-button type="primary" @click="sendChatMessage" :loading="chatTyping" :disabled="!chatInput.trim()" class="send-btn">
                            <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
                                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                            </svg>
                        </el-button>
                    </div>
                </div>
                <div v-if="!fullscreen" class="chat-resize-handle right" @mousedown.stop="onResizeStart('right', $event)"></div>
                <div v-if="!fullscreen" class="chat-resize-handle bottom" @mousedown.stop="onResizeStart('bottom', $event)"></div>
                <div v-if="!fullscreen" class="chat-resize-handle left" @mousedown.stop="onResizeStart('left', $event)"></div>
                <div v-if="!fullscreen" class="chat-resize-handle top" @mousedown.stop="onResizeStart('top', $event)"></div>
                <div v-if="!fullscreen" class="chat-resize-handle corner top-left" @mousedown.stop="onResizeStart('top-left', $event)"></div>
                <div v-if="!fullscreen" class="chat-resize-handle corner top-right" @mousedown.stop="onResizeStart('top-right', $event)"></div>
                <div v-if="!fullscreen" class="chat-resize-handle corner bottom-left" @mousedown.stop="onResizeStart('bottom-left', $event)"></div>
                <div v-if="!fullscreen" class="chat-resize-handle corner bottom-right" @mousedown.stop="onResizeStart('bottom-right', $event)"></div>
            </div>
        </div>
    </transition>
`;

const ChatWidgetSetup = (props, { emit }) => {
    const chatStore = useChatStore();
    const configStore = useConfigStore();
    
    const {
        chatSessions, currentChatSession, chatMessages, chatInput,
        selectedChatPapers, chatTyping, chatProgress, showChatSidebar,
        chatMessagesContainer, quickPrompts
    } = storeToRefs(chatStore);
    
    const {
        createNewChat, selectChatSession, deleteChatSession, clearAllChatSessions,
        sendChatMessage, sendQuickPrompt, removeSelectedChatPaper,
        formatChatMessage, formatChatTime, handleChatScroll,
        copyMessage, regenerateMessage
    } = chatStore;
    
    function t(key, params) {
        return configStore.t(key, params);
    }
    
    function renderLatexInMessages() {
        if (typeof renderMathInElement === 'undefined') return;
        nextTick(() => {
            const msgElements = document.querySelectorAll('.message-text:not(.streaming)');
            msgElements.forEach(el => {
                try {
                    renderMathInElement(el, {
                        delimiters: [
                            { left: '$$', right: '$$', display: true },
                            { left: '$', right: '$', display: false },
                            { left: '\\[', right: '\\]', display: true },
                            { left: '\\(', right: '\\)', display: false }
                        ],
                        throwOnError: false,
                        output: 'html'
                    });
                } catch (e) {}
            });
        });
    }
    
    watch(chatMessages, () => {
        renderLatexInMessages();
    }, { deep: true });
    
    function onMouseDown(e) {
        if (e.target.closest('.collapse-btn') || e.target.closest('.el-button') || e.target.closest('.chat-resize-handle')) return;
        emit('start-drag', e);
    }
    
    function toggleFullscreen() {
        emit('update:fullscreen', !props.fullscreen);
    }
    
    function onResizeStart(direction, e) {
        emit('start-resize', direction, e);
    }
    
    onMounted(() => {
        renderLatexInMessages();
    });
    
    return {
        showChatSidebar, chatSessions, currentChatSession, chatMessages, chatInput,
        selectedChatPapers, chatTyping, chatProgress, chatMessagesContainer, quickPrompts,
        t, createNewChat, selectChatSession, deleteChatSession, clearAllChatSessions,
        sendChatMessage, sendQuickPrompt, removeSelectedChatPaper,
        formatChatMessage, formatChatTime, handleChatScroll,
        copyMessage, regenerateMessage,
        onMouseDown, toggleFullscreen, onResizeStart
    };
};
