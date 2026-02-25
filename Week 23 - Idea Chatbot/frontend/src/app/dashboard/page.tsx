'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { getIdeas } from '@/lib/api';
import type { Idea } from '@/lib/types';
import { ArrowLeft, Sparkles, MessageSquare, Clock, DollarSign, Layers, Target, Calendar, X, Globe, TrendingUp, AlertTriangle } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, AreaChart, Area, CartesianGrid } from 'recharts';

const DOMAIN_COLORS: Record<string, string> = {
    software: '#6366f1',
    engineering: '#f59e0b',
    hr: '#10b981',
    finance: '#8b5cf6',
    general: '#6b7280',
};

export default function DashboardPage() {
    const [ideas, setIdeas] = useState<Idea[]>([]);
    const [selectedIdea, setSelectedIdea] = useState<Idea | null>(null);
    const [filter, setFilter] = useState<string>('all');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadIdeas();
    }, []);

    const loadIdeas = async () => {
        setLoading(true);
        const response = await getIdeas();
        setIdeas(response.ideas);
        setLoading(false);
    };

    const filteredIdeas = filter === 'all'
        ? ideas
        : ideas.filter(idea => idea.status === filter);

    // Chart data
    const domainData = Object.entries(
        ideas.reduce((acc, idea) => {
            acc[idea.domain] = (acc[idea.domain] || 0) + 1;
            return acc;
        }, {} as Record<string, number>)
    ).map(([name, count]) => ({
        name: name.charAt(0).toUpperCase() + name.slice(1),
        value: count,
        color: DOMAIN_COLORS[name] || '#6b7280',
    }));

    const statusData = [
        { name: 'Pending', count: ideas.filter(i => i.status === 'pending').length, color: '#eab308' },
        { name: 'Review', count: ideas.filter(i => i.status === 'review').length, color: '#3b82f6' },
        { name: 'Approved', count: ideas.filter(i => i.status === 'approved').length, color: '#22c55e' },
        { name: 'Rejected', count: ideas.filter(i => i.status === 'rejected').length, color: '#ef4444' },
    ];

    const complexityData = [
        { name: 'Low', count: ideas.filter(i => i.complexity === 'low').length, color: '#22c55e' },
        { name: 'Medium', count: ideas.filter(i => i.complexity === 'medium').length, color: '#f59e0b' },
        { name: 'High', count: ideas.filter(i => i.complexity === 'high').length, color: '#ef4444' },
    ];

    const stats = [
        { label: 'Total Ideas', value: ideas.length, icon: Layers, color: 'from-indigo-500 to-purple-600' },
        { label: 'Pending', value: ideas.filter(i => i.status === 'pending').length, icon: Clock, color: 'from-yellow-500 to-orange-500' },
        { label: 'Approved', value: ideas.filter(i => i.status === 'approved').length, icon: Target, color: 'from-emerald-500 to-green-600' },
        { label: 'This Week', value: ideas.filter(i => new Date(i.created_at) > new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)).length, icon: Calendar, color: 'from-blue-500 to-cyan-500' },
    ];

    return (
        <div className="min-h-screen pb-20">
            {/* Navigation */}
            <nav className="nav-glass fixed top-0 left-0 right-0 z-50 px-6 py-4">
                <div className="max-w-7xl mx-auto flex items-center justify-between">
                    <Link href="/" className="flex items-center gap-2">
                        <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">
                            <ArrowLeft className="w-4 h-4 mr-2" />
                            Back
                        </Button>
                    </Link>
                    <div className="flex items-center gap-2">
                        <Sparkles className="w-5 h-5 text-indigo-400" />
                        <span className="font-semibold gradient-text">IdeaForge Dashboard</span>
                    </div>
                    <Link href="/chat">
                        <Button className="btn-premium rounded-full">
                            <MessageSquare className="w-4 h-4 mr-2" />
                            New Idea
                        </Button>
                    </Link>
                </div>
            </nav>

            <div className="pt-24 px-6 max-w-7xl mx-auto space-y-8">
                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 animate-fade-in">
                    {stats.map((stat, idx) => (
                        <div key={idx} className="stat-card rounded-2xl p-6">
                            <div className="flex items-center justify-between mb-4">
                                <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${stat.color} flex items-center justify-center opacity-80`}>
                                    <stat.icon className="w-6 h-6 text-white" />
                                </div>
                            </div>
                            <p className="text-muted-foreground text-sm mb-1">{stat.label}</p>
                            <p className="text-4xl font-bold">{stat.value}</p>
                        </div>
                    ))}
                </div>

                {/* Main Content */}
                <Tabs defaultValue="ideas" className="w-full animate-fade-in">
                    <TabsList className="glass-card p-1 rounded-xl mb-6">
                        <TabsTrigger value="ideas" className="rounded-lg data-[state=active]:bg-white/10">
                            Ideas
                        </TabsTrigger>
                        <TabsTrigger value="analytics" className="rounded-lg data-[state=active]:bg-white/10">
                            Analytics
                        </TabsTrigger>
                    </TabsList>

                    <TabsContent value="ideas" className="space-y-6">
                        {/* Filters */}
                        <div className="flex gap-2 flex-wrap">
                            {['all', 'pending', 'review', 'approved', 'rejected'].map(f => (
                                <button
                                    key={f}
                                    onClick={() => setFilter(f)}
                                    className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${filter === f
                                        ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg shadow-indigo-500/25'
                                        : 'glass-card hover:bg-white/5'
                                        }`}
                                >
                                    {f.charAt(0).toUpperCase() + f.slice(1)}
                                </button>
                            ))}
                        </div>

                        {/* Ideas Grid */}
                        {loading ? (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                {[1, 2, 3].map(i => (
                                    <div key={i} className="glass-card rounded-2xl p-6 animate-pulse">
                                        <div className="h-6 bg-white/10 rounded w-3/4 mb-4" />
                                        <div className="h-4 bg-white/10 rounded w-full mb-2" />
                                        <div className="h-4 bg-white/10 rounded w-2/3" />
                                    </div>
                                ))}
                            </div>
                        ) : filteredIdeas.length === 0 ? (
                            <div className="text-center py-20">
                                <div className="empty-state-glow inline-block p-8 rounded-full mb-6">
                                    <Layers className="w-16 h-16 text-muted-foreground" />
                                </div>
                                <h3 className="text-xl font-semibold mb-2">No ideas yet</h3>
                                <p className="text-muted-foreground mb-6">Start a conversation to create your first idea</p>
                                <Link href="/chat">
                                    <Button className="btn-premium rounded-full">
                                        <MessageSquare className="w-4 h-4 mr-2" />
                                        Start Chatting
                                    </Button>
                                </Link>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                {filteredIdeas.map((idea, idx) => (
                                    <div
                                        key={idea.id}
                                        onClick={() => setSelectedIdea(idea)}
                                        className="glass-card rounded-2xl p-6 cursor-pointer group animate-fade-in"
                                        style={{ animationDelay: `${idx * 50}ms` }}
                                    >
                                        <div className="flex items-start justify-between mb-4">
                                            <h3 className="text-lg font-semibold group-hover:text-indigo-400 transition-colors line-clamp-1">
                                                {idea.title}
                                            </h3>
                                            <span className={`px-3 py-1 rounded-full text-xs font-medium status-${idea.status}`}>
                                                {idea.status}
                                            </span>
                                        </div>
                                        <p className="text-muted-foreground text-sm line-clamp-2 mb-4">
                                            {idea.description}
                                        </p>
                                        <div className="flex gap-2">
                                            <span className="px-2 py-1 rounded-lg text-xs glass-card" style={{ color: DOMAIN_COLORS[idea.domain] }}>
                                                {idea.domain}
                                            </span>
                                            <span className="px-2 py-1 rounded-lg text-xs glass-card text-muted-foreground">
                                                {idea.complexity}
                                            </span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </TabsContent>

                    <TabsContent value="analytics" className="space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {/* Domain Distribution */}
                            <div className="chart-container p-6 rounded-2xl">
                                <h3 className="text-lg font-semibold mb-4">Ideas by Domain</h3>
                                <ResponsiveContainer width="100%" height={250}>
                                    <PieChart>
                                        <Pie
                                            data={domainData}
                                            cx="50%"
                                            cy="50%"
                                            innerRadius={60}
                                            outerRadius={90}
                                            paddingAngle={4}
                                            dataKey="value"
                                        >
                                            {domainData.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={entry.color} />
                                            ))}
                                        </Pie>
                                        <Tooltip
                                            contentStyle={{
                                                background: 'rgba(17, 17, 17, 0.9)',
                                                border: '1px solid rgba(255,255,255,0.1)',
                                                borderRadius: '8px'
                                            }}
                                        />
                                    </PieChart>
                                </ResponsiveContainer>
                                <div className="flex flex-wrap gap-3 justify-center mt-4">
                                    {domainData.map((entry) => (
                                        <div key={entry.name} className="flex items-center gap-2">
                                            <div className="w-3 h-3 rounded-full" style={{ background: entry.color }} />
                                            <span className="text-sm text-muted-foreground">{entry.name}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Status Distribution */}
                            <div className="chart-container p-6 rounded-2xl">
                                <h3 className="text-lg font-semibold mb-4">Ideas by Status</h3>
                                <ResponsiveContainer width="100%" height={250}>
                                    <BarChart data={statusData} layout="vertical">
                                        <XAxis type="number" stroke="#666" />
                                        <YAxis dataKey="name" type="category" stroke="#666" width={80} />
                                        <Tooltip
                                            contentStyle={{
                                                background: 'rgba(17, 17, 17, 0.9)',
                                                border: '1px solid rgba(255,255,255,0.1)',
                                                borderRadius: '8px'
                                            }}
                                        />
                                        <Bar dataKey="count" radius={[0, 8, 8, 0]}>
                                            {statusData.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={entry.color} />
                                            ))}
                                        </Bar>
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>

                            {/* Complexity Distribution */}
                            <div className="chart-container p-6 rounded-2xl md:col-span-2">
                                <h3 className="text-lg font-semibold mb-4">Complexity Breakdown</h3>
                                <ResponsiveContainer width="100%" height={200}>
                                    <AreaChart data={complexityData}>
                                        <defs>
                                            <linearGradient id="colorComplexity" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                                                <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                                            </linearGradient>
                                        </defs>
                                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                                        <XAxis dataKey="name" stroke="#666" />
                                        <YAxis stroke="#666" />
                                        <Tooltip
                                            contentStyle={{
                                                background: 'rgba(17, 17, 17, 0.9)',
                                                border: '1px solid rgba(255,255,255,0.1)',
                                                borderRadius: '8px'
                                            }}
                                        />
                                        <Area type="monotone" dataKey="count" stroke="#6366f1" fillOpacity={1} fill="url(#colorComplexity)" />
                                    </AreaChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    </TabsContent>
                </Tabs>
            </div>

            {/* Idea Detail Modal */}
            <Dialog open={!!selectedIdea} onOpenChange={() => setSelectedIdea(null)}>
                <DialogContent className="glass-card border-white/10 max-w-2xl max-h-[85vh] overflow-y-auto">
                    {selectedIdea && (
                        <>
                            <DialogHeader>
                                <div className="flex items-start justify-between">
                                    <div>
                                        <DialogTitle className="text-2xl font-bold mb-2">{selectedIdea.title}</DialogTitle>
                                        <div className="flex gap-2">
                                            <span className={`px-3 py-1 rounded-full text-xs font-medium status-${selectedIdea.status}`}>
                                                {selectedIdea.status}
                                            </span>
                                            <span className="px-3 py-1 rounded-full text-xs font-medium glass-card" style={{ color: DOMAIN_COLORS[selectedIdea.domain] }}>
                                                {selectedIdea.domain}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </DialogHeader>

                            <div className="space-y-6 mt-6">
                                <div>
                                    <h4 className="text-sm font-medium text-muted-foreground mb-2 flex items-center gap-2">
                                        <Target className="w-4 h-4" /> Description
                                    </h4>
                                    <p className="text-foreground leading-relaxed">{selectedIdea.description}</p>
                                </div>

                                <div>
                                    <h4 className="text-sm font-medium text-muted-foreground mb-2 flex items-center gap-2">
                                        <Sparkles className="w-4 h-4" /> Problem Solved
                                    </h4>
                                    <p className="text-foreground leading-relaxed">{selectedIdea.problem_solved}</p>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div className="glass-card rounded-xl p-4">
                                        <h4 className="text-sm font-medium text-muted-foreground mb-1 flex items-center gap-2">
                                            <Clock className="w-4 h-4" /> Time Estimate
                                        </h4>
                                        <p className="text-foreground font-medium">{selectedIdea.time_estimate || 'Not specified'}</p>
                                    </div>
                                    <div className="glass-card rounded-xl p-4">
                                        <h4 className="text-sm font-medium text-muted-foreground mb-1 flex items-center gap-2">
                                            <DollarSign className="w-4 h-4" /> Cost Estimate
                                        </h4>
                                        <p className="text-foreground font-medium">{selectedIdea.cost_estimate || 'Not specified'}</p>
                                    </div>
                                </div>

                                <div>
                                    <h4 className="text-sm font-medium text-muted-foreground mb-2">Impact</h4>
                                    <p className="text-foreground leading-relaxed">{selectedIdea.impact}</p>
                                </div>

                                <div className="flex items-center gap-4 pt-4 border-t border-white/10">
                                    <span className="text-sm text-muted-foreground">Complexity:</span>
                                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${selectedIdea.complexity === 'low' ? 'bg-emerald-500/20 text-emerald-400' :
                                        selectedIdea.complexity === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                                            'bg-red-500/20 text-red-400'
                                        }`}>
                                        {selectedIdea.complexity}
                                    </span>
                                </div>

                                {/* Market Context Section */}
                                {(selectedIdea.market_alternatives || selectedIdea.market_summary) && (
                                    <div className="pt-4 border-t border-white/10 space-y-4">
                                        <h4 className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                                            <Globe className="w-4 h-4" /> Market Context
                                        </h4>

                                        {selectedIdea.market_summary && (
                                            <p className="text-foreground text-sm leading-relaxed bg-indigo-500/10 rounded-xl p-4 border border-indigo-500/20">
                                                {selectedIdea.market_summary}
                                            </p>
                                        )}

                                        {selectedIdea.market_recommendation && (
                                            <div className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm ${selectedIdea.market_recommendation === 'proceed' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                                                    selectedIdea.market_recommendation === 'consider_existing' ? 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20' :
                                                        'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                                                }`}>
                                                {selectedIdea.market_recommendation === 'proceed' && <TrendingUp className="w-4 h-4" />}
                                                {selectedIdea.market_recommendation === 'consider_existing' && <AlertTriangle className="w-4 h-4" />}
                                                <span className="capitalize font-medium">
                                                    {String(selectedIdea.market_recommendation).replace(/_/g, ' ')}
                                                </span>
                                            </div>
                                        )}

                                        {selectedIdea.market_maturity && (
                                            <div className="flex items-center gap-2">
                                                <span className="text-xs text-muted-foreground">Market Maturity:</span>
                                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${selectedIdea.market_maturity === 'stable' ? 'bg-emerald-500/20 text-emerald-400' :
                                                        selectedIdea.market_maturity === 'evolving' ? 'bg-blue-500/20 text-blue-400' :
                                                            selectedIdea.market_maturity === 'fast' ? 'bg-orange-500/20 text-orange-400' :
                                                                'bg-purple-500/20 text-purple-400'
                                                    }`}>
                                                    {selectedIdea.market_maturity}
                                                </span>
                                            </div>
                                        )}

                                        {selectedIdea.market_alternatives && (
                                            <div>
                                                <h5 className="text-xs font-medium text-muted-foreground mb-2">Market Alternatives</h5>
                                                <div className="space-y-2">
                                                    {(typeof selectedIdea.market_alternatives === 'string'
                                                        ? JSON.parse(selectedIdea.market_alternatives)
                                                        : selectedIdea.market_alternatives
                                                    ).slice(0, 5).map((alt: { name: string; pricing?: string; differentiator?: string }, idx: number) => (
                                                        <div key={idx} className="glass-card rounded-lg p-3 text-sm">
                                                            <div className="flex items-center justify-between mb-1">
                                                                <span className="font-medium text-foreground">{alt.name}</span>
                                                                {alt.pricing && (
                                                                    <span className="text-xs text-muted-foreground">{alt.pricing}</span>
                                                                )}
                                                            </div>
                                                            {alt.differentiator && (
                                                                <p className="text-xs text-muted-foreground">{alt.differentiator}</p>
                                                            )}
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        </>
                    )}
                </DialogContent>
            </Dialog>
        </div>
    );
}
