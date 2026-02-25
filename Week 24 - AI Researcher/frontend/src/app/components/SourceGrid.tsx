"use client";

interface Source {
    url: string;
    title: string;
    snippet: string;
    verified?: boolean;   // true = deep-scraped + judge approved
    score?: number | null; // relevance score 0-10 from judge
}

interface SourceGridProps {
    sources: Source[];
}

export default function SourceGrid({ sources }: SourceGridProps) {
    if (!sources || sources.length === 0) return null;

    return (
        <div className="mt-8 space-y-4">
            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-widest pl-1">
                Verified Sources
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {sources.map((source, i) => {
                    let hostname = "";
                    try { hostname = new URL(source.url).hostname; } catch { }

                    return (
                        <a
                            key={i}
                            href={source.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="glass p-4 glass-hover block transition-all group relative overflow-hidden"
                        >
                            {/* Verified badge — deep-scraped + judge approved */}
                            {source.verified && (
                                <div className="absolute top-2 right-2 flex items-center gap-1 bg-emerald-500/20 border border-emerald-500/30 rounded-full px-2 py-0.5">
                                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                                    <span className="text-[10px] font-semibold text-emerald-400 uppercase tracking-wider">
                                        Deep Read
                                    </span>
                                    {source.score != null && (
                                        <span className="text-[10px] text-emerald-500 ml-0.5">
                                            {source.score}/10
                                        </span>
                                    )}
                                </div>
                            )}

                            <div className="flex items-center gap-2 mb-2 pr-20">
                                <div className="w-6 h-6 rounded bg-slate-800 flex items-center justify-center overflow-hidden shrink-0">
                                    {hostname && (
                                        <img
                                            src={`https://www.google.com/s2/favicons?domain=${hostname}&sz=32`}
                                            alt="icon"
                                            className="w-4 h-4"
                                        />
                                    )}
                                </div>
                                <span className="text-sm font-medium text-slate-200 truncate group-hover:text-purple-400 transition-colors">
                                    {source.title}
                                </span>
                            </div>

                            <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                                {source.snippet}
                            </p>

                            <p className="text-[10px] text-slate-600 mt-2 truncate">
                                {source.url}
                            </p>
                        </a>
                    );
                })}
            </div>
        </div>
    );
}
