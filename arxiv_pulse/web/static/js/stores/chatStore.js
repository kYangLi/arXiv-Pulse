const useChatStore = defineStore('chat', () => {
    const chatExpanded = ref(false);
    const chatSessions = ref([]);
    const currentChatSession = ref(null);
    const chatMessages = ref([]);
    const chatInput = ref('');
    const selectedChatPapers = ref([]);
    const chatTyping = ref(false);
    const chatProgress = ref(null);
    const showChatSidebar = ref(false);
    const chatUnreadCount = ref(0);
    const chatMessagesContainer = ref(null);
    const userScrolledUp = ref(false);
    const chatPosition = ref({ x: window.innerWidth - 500, y: 80 });
    const chatPanelRef = ref(null);
    const chatZIndex = ref(999);
    const chatFullscreen = ref(false);
    const chatSize = ref({ width: 480, height: 640 });
    const chatAnimating = ref(false);
    
    const quickPrompts = computed(() => {
        const configStore = useConfigStore();
        return configStore.currentLang === 'zh' ? [
            { icon: '📝', text: '帮我总结这篇论文的核心内容' },
            { icon: '🔍', text: '解释论文中的方法论' },
            { icon: '💡', text: '这个领域有哪些最新进展' },
            { icon: '⚖️', text: '比较这些论文的异同' },
        ] : [
            { icon: '📝', text: 'Summarize the core content of this paper' },
            { icon: '🔍', text: 'Explain the methodology in this paper' },
            { icon: '💡', text: 'What are the latest advances in this field' },
            { icon: '⚖️', text: 'Compare the similarities and differences' },
        ];
    });
    
    function scrollToBottom() {
        if (chatMessagesContainer.value) {
            chatMessagesContainer.value.scrollTop = chatMessagesContainer.value.scrollHeight;
        }
    }
    
    function handleChatScroll() {
        if (chatMessagesContainer.value) {
            const { scrollTop, scrollHeight, clientHeight } = chatMessagesContainer.value;
            const isNearBottom = scrollHeight - scrollTop - clientHeight < 100;
            userScrolledUp.value = !isNearBottom;
        }
    }
    
    async function fetchChatSessions() {
        try {
            const res = await API.chat.sessions.list();
            chatSessions.value = await res.json();
        } catch (e) {
            console.error('Failed to fetch chat sessions:', e);
        }
    }
    
    async function createNewChat() {
        try {
            const res = await API.chat.sessions.create();
            const session = await res.json();
            chatSessions.value.unshift(session);
            currentChatSession.value = session;
            chatMessages.value = [];
            showChatSidebar.value = false;
        } catch (e) {
            ElementPlus.ElMessage.error('创建对话失败');
        }
    }
    
    async function selectChatSession(session) {
        currentChatSession.value = session;
        showChatSidebar.value = false;
        chatMessages.value = [];
        try {
            const res = await API.chat.sessions.get(session.id);
            const data = await res.json();
            chatMessages.value = data.messages || [];
        } catch (e) {
            console.error('Failed to fetch messages:', e);
        }
    }
    
    async function deleteChatSession(session) {
        const configStore = useConfigStore();
        try {
            await ElementPlus.ElMessageBox.confirm(
                `确定要删除对话 "${session.title}" 吗？`,
                '删除对话',
                { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
            );
            
            const res = await API.chat.sessions.delete(session.id);
            if (res.ok) {
                const idx = chatSessions.value.findIndex(s => s.id === session.id);
                if (idx >= 0) chatSessions.value.splice(idx, 1);
                
                if (currentChatSession.value?.id === session.id) {
                    currentChatSession.value = null;
                    chatMessages.value = [];
                }
                ElementPlus.ElMessage.success('已删除');
            }
        } catch (e) {
            if (e !== 'cancel') {
                ElementPlus.ElMessage.error('删除失败');
            }
        }
    }
    
    async function clearAllChatSessions() {
        const configStore = useConfigStore();
        try {
            const confirmMsg = configStore.currentLang === 'zh' 
                ? '确定要清空所有对话记录吗？此操作不可恢复。' 
                : 'Clear all chat history? This cannot be undone.';
            const titleMsg = configStore.currentLang === 'zh' ? '清空所有记录' : 'Clear All';
            await ElementPlus.ElMessageBox.confirm(confirmMsg, titleMsg, { 
                confirmButtonText: configStore.currentLang === 'zh' ? '清空' : 'Clear', 
                cancelButtonText: configStore.currentLang === 'zh' ? '取消' : 'Cancel', 
                type: 'warning' 
            });
            
            for (const session of chatSessions.value) {
                await API.chat.sessions.delete(session.id);
            }
            chatSessions.value = [];
            currentChatSession.value = null;
            chatMessages.value = [];
            showChatSidebar.value = false;
            ElementPlus.ElMessage.success(configStore.currentLang === 'zh' ? '已清空所有记录' : 'All sessions cleared');
        } catch (e) {
            if (e !== 'cancel') {
                ElementPlus.ElMessage.error(configStore.currentLang === 'zh' ? '清空失败' : 'Failed to clear');
            }
        }
    }
    
    async function sendQuickPrompt(promptText) {
        if (chatTyping.value) return;
        chatInput.value = promptText;
        await sendChatMessage();
    }
    
    async function sendChatMessage() {
        const configStore = useConfigStore();
        if (!chatInput.value.trim() || chatTyping.value) return;
        
        if (!currentChatSession.value) {
            await createNewChat();
            if (!currentChatSession.value) return;
        }
        
        const userMessage = {
            id: Date.now(),
            role: 'user',
            content: chatInput.value,
            paper_ids: selectedChatPapers.value.map(p => p.arxiv_id),
            created_at: new Date().toISOString()
        };
        chatMessages.value.push(userMessage);
        
        const messageContent = chatInput.value;
        const paperIds = selectedChatPapers.value.map(p => p.arxiv_id);
        chatInput.value = '';
        selectedChatPapers.value = [];
        chatTyping.value = true;
        chatProgress.value = null;
        userScrolledUp.value = false;
        
        await nextTick();
        scrollToBottom();
        
        const assistantMessage = {
            id: Date.now() + 1,
            role: 'assistant',
            content: '',
            isStreaming: true,
            created_at: new Date().toISOString()
        };
        chatMessages.value.push(assistantMessage);
        const assistantIdx = chatMessages.value.length - 1;
        
        try {
            const response = await API.chat.sessions.send(currentChatSession.value.id, {
                content: messageContent,
                paper_ids: paperIds,
                language: configStore.currentLang
            });
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            if (data.type === 'progress') {
                                chatProgress.value = {
                                    stage: data.stage,
                                    message: data.message,
                                    arxivId: data.arxiv_id,
                                    paperIndex: data.paper_index,
                                    totalPapers: data.total_papers,
                                    progress: data.progress,
                                    textLength: data.text_length,
                                    pageCount: data.page_count,
                                };
                                await nextTick();
                                scrollToBottom();
                            } else if (data.type === 'chunk') {
                                chatProgress.value = null;
                                chatMessages.value[assistantIdx].content += data.content;
                                await nextTick();
                                if (!userScrolledUp.value) {
                                    scrollToBottom();
                                }
                            } else if (data.type === 'error') {
                                chatProgress.value = null;
                                chatMessages.value[assistantIdx].content = `**错误**: ${data.message}`;
                            } else if (data.type === 'done') {
                                chatProgress.value = null;
                                chatMessages.value[assistantIdx].isStreaming = false;
                            }
                        } catch (e) {}
                    }
                }
            }
            
            fetchChatSessions();
        } catch (e) {
            ElementPlus.ElMessage.error('发送消息失败');
            if (chatMessages.value[assistantIdx]) {
                chatMessages.value[assistantIdx].content = '发送消息失败，请重试。';
            }
        } finally {
            chatTyping.value = false;
            chatProgress.value = null;
            userScrolledUp.value = false;
            if (chatMessages.value[assistantIdx]) {
                chatMessages.value[assistantIdx].isStreaming = false;
            }
        }
    }
    
    function removeSelectedChatPaper(arxivId) {
        const idx = selectedChatPapers.value.findIndex(p => p.arxiv_id === arxivId);
        if (idx >= 0) {
            selectedChatPapers.value.splice(idx, 1);
        }
    }
    
    function formatChatMessage(content, isStreaming = false) {
        if (!content) return '';
        
        let processedContent = content;
        
        if (isStreaming) {
            const codeBlockCount = (content.match(/```/g) || []).length;
            if (codeBlockCount % 2 !== 0) {
                processedContent += '\n```';
            }
        }
        
        if (typeof marked !== 'undefined') {
            try {
                return marked.parse(processedContent, {
                    breaks: true,
                    gfm: true,
                });
            } catch (e) {
                return content
                    .replace(/</g, '&lt;')
                    .replace(/>/g, '&gt;')
                    .replace(/\n/g, '<br>');
            }
        }
        return content
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code style="background:#f5f5f5;padding:2px 6px;border-radius:4px;">$1</code>');
    }
    
    function formatChatTime(timeStr) {
        const configStore = useConfigStore();
        if (!timeStr) return '';
        const dateStr = timeStr.endsWith('Z') ? timeStr : timeStr + 'Z';
        const date = new Date(dateStr);
        const now = new Date();
        const diff = now - date;
        if (diff < 60000) return configStore.currentLang === 'zh' ? '刚刚' : 'Just now';
        if (diff < 3600000) return configStore.currentLang === 'zh' ? `${Math.floor(diff / 60000)} 分钟前` : `${Math.floor(diff / 60000)} min ago`;
        if (diff < 86400000) return configStore.currentLang === 'zh' ? `${Math.floor(diff / 3600000)} 小时前` : `${Math.floor(diff / 3600000)} hours ago`;
        return date.toLocaleDateString();
    }
    
    return {
        chatExpanded, chatSessions, currentChatSession, chatMessages, chatInput,
        selectedChatPapers, chatTyping, chatProgress, showChatSidebar,
        chatUnreadCount, chatMessagesContainer, userScrolledUp, chatPosition,
        chatPanelRef, chatZIndex, chatFullscreen, chatSize, chatAnimating,
        quickPrompts,
        scrollToBottom, handleChatScroll, fetchChatSessions, createNewChat,
        selectChatSession, deleteChatSession, clearAllChatSessions,
        sendQuickPrompt, sendChatMessage, removeSelectedChatPaper,
        formatChatMessage, formatChatTime
    };
});
