'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { sendChatMessage } from '@/lib/api';
import type { ChatMessage } from '@/lib/types';
import { ArrowLeft, Send, Sparkles, Bot, User, LayoutDashboard, CheckCircle2 } from 'lucide-react';

export default function ChatPage() {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState('');
    const [sessionId, setSessionId] = useState<string>('');
    const [loading, setLoading] = useState(false);
    const [autoSaved, setAutoSaved] = useState<number | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim()) return;

        const userMessage: ChatMessage = {
            role: 'user',
            content: input,
            timestamp: new Date().toISOString(),
        };

        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setLoading(true);

        try {
            const response = await sendChatMessage(input, sessionId || undefined);

            if (!sessionId) {
                setSessionId(response.session_id);
            }

            const aiMessage: ChatMessage = {
                role: 'assistant',
                content: response.message,
                timestamp: response.timestamp,
            };

            setMessages(prev => [...prev, aiMessage]);

            if (response.auto_saved && response.idea_id) {
                setAutoSaved(response.idea_id);
                setTimeout(() => setAutoSaved(null), 5000);
            }
        } catch (error) {
            console.error('Error sending message:', error);
            const errorMessage: ChatMessage = {
                role: 'assistant',
                content: 'Sorry, I encountered an error. Please try again.',
                timestamp: new Date().toISOString(),
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setLoading(false);
            setTimeout(() => inputRef.current?.focus(), 100);
        }
    };

    return (
        <div className="h-screen flex flex-col overflow-hidden">
            {/* Navigation - Fixed height */}
            <nav className="nav-glass shrink-0 px-6 py-4 z-50">
                <div className="max-w-5xl mx-auto flex items-center justify-between">
                    <Link href="/" className="flex items-center gap-2">
                        <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">
                            <ArrowLeft className="w-4 h-4 mr-2" />
                            Back
                        </Button>
                    </Link>
                    <div className="flex items-center gap-2">
                        <Sparkles className="w-5 h-5 text-indigo-400" />
                        <span className="font-semibold gradient-text">IdeaForge Chat</span>
                    </div>
                    <Link href="/dashboard">
                        <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">
                            <LayoutDashboard className="w-4 h-4 mr-2" />
                            Dashboard
                        </Button>
                    </Link>
                </div>
            </nav>

            {/* Auto-save Toast */}
            {autoSaved && (
                <div className="fixed top-20 left-1/2 -translate-x-1/2 z-50 animate-slide-up">
                    <div className="glass-card rounded-full px-6 py-3 flex items-center gap-3 pulse-glow border-emerald-500/30">
                        <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                        <span className="text-emerald-400 font-medium">Idea #{autoSaved} saved automatically!</span>
                    </div>
                </div>
            )}

            {/* Chat Messages - Scrollable area that fills remaining space */}
            <div className="flex-1 overflow-y-auto px-4">
                <div className="max-w-4xl mx-auto py-6">
                    {/* Messages */}
                    <div className="space-y-6">
                        {messages.length === 0 ? (
                            <div className="text-center py-20 animate-fade-in">
                                <div className="empty-state-glow inline-block p-12 rounded-full mb-8">
                                    <div className="w-24 h-24 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center mx-auto">
                                        <Sparkles className="w-12 h-12 text-white" />
                                    </div>
                                </div>
                                <h2 className="text-3xl font-bold mb-4">
                                    <span className="gradient-text">Start Brainstorming</span>
                                </h2>
                                <p className="text-muted-foreground text-lg max-w-md mx-auto mb-8">
                                    Describe your idea and I'll help you refine it.
                                    When it's ready, I'll save it automatically.
                                </p>
                                <div className="flex flex-wrap justify-center gap-3">
                                    {['💡 App idea', '🚀 Startup concept', '🔧 Process improvement', '📊 New feature'].map((suggestion) => (
                                        <button
                                            key={suggestion}
                                            onClick={() => setInput(suggestion.split(' ').slice(1).join(' '))}
                                            className="glass-card px-4 py-2 rounded-full text-sm text-muted-foreground hover:text-foreground transition-all hover:border-indigo-500/30"
                                        >
                                            {suggestion}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        ) : (
                            messages.map((msg, idx) => (
                                <div
                                    key={idx}
                                    className={`flex items-start gap-4 animate-fade-in ${msg.role === 'user' ? 'flex-row-reverse' : ''
                                        }`}
                                >
                                    {/* Avatar */}
                                    <div className={`flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center ${msg.role === 'user'
                                        ? 'bg-gradient-to-br from-indigo-500 to-purple-600'
                                        : 'glass-card'
                                        }`}>
                                        {msg.role === 'user' ? (
                                            <User className="w-5 h-5 text-white" />
                                        ) : (
                                            <Bot className="w-5 h-5 text-indigo-400" />
                                        )}
                                    </div>

                                    {/* Message Bubble */}
                                    <div className={`max-w-[75%] ${msg.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-ai'
                                        } px-5 py-4`}>
                                        <p className="whitespace-pre-wrap text-[15px] leading-relaxed">
                                            {msg.content}
                                        </p>
                                    </div>
                                </div>
                            ))
                        )}

                        {/* Typing Indicator */}
                        {loading && (
                            <div className="flex items-start gap-4 animate-fade-in">
                                <div className="flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center glass-card">
                                    <Bot className="w-5 h-5 text-indigo-400" />
                                </div>
                                <div className="chat-bubble-ai px-5 py-4">
                                    <div className="typing-indicator">
                                        <div className="typing-dot" />
                                        <div className="typing-dot" />
                                        <div className="typing-dot" />
                                    </div>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>
                </div>
            </div>

            {/* Input Area - Fixed height at bottom */}
            <div className="shrink-0 p-4 nav-glass">
                <div className="max-w-4xl mx-auto">
                    <div className="glass-card rounded-2xl p-2 flex gap-2">
                        <Textarea
                            ref={inputRef}
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' && !e.shiftKey) {
                                    e.preventDefault();
                                    handleSend();
                                }
                            }}
                            placeholder="Describe your idea or ask a question..."
                            className="input-premium min-h-[56px] max-h-[200px] resize-none rounded-xl border-0 bg-transparent focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0"
                            disabled={loading}
                            autoFocus
                        />
                        <Button
                            onClick={handleSend}
                            disabled={loading || !input.trim()}
                            size="lg"
                            className="btn-premium rounded-xl px-6 self-end"
                        >
                            <Send className="w-5 h-5" />
                        </Button>
                    </div>
                    <p className="text-center text-xs text-muted-foreground mt-2">
                        Press Enter to send • Shift + Enter for new line
                    </p>
                </div>
            </div>
        </div>
    );
}
