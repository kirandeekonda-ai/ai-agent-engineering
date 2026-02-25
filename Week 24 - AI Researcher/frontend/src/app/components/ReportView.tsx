"use client";

import ReactMarkdown from "react-markdown";

interface ReportViewProps {
    content: string;
}

export default function ReportView({ content }: ReportViewProps) {
    return (
        <div className="glass p-8 mt-8 animate-in fade-in zoom-in duration-1000">
            <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-full bg-purple-500/20 flex items-center justify-center border border-purple-500/30">
                    <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                </div>
                <h2 className="text-2xl font-bold text-white">Research Report</h2>
            </div>

            <div className="
                prose prose-invert max-w-none
                prose-headings:text-white prose-headings:font-bold
                prose-h1:text-2xl prose-h2:text-xl prose-h3:text-lg
                prose-p:text-slate-300 prose-p:leading-relaxed prose-p:text-base
                prose-strong:text-white prose-strong:font-semibold
                prose-em:text-slate-300
                prose-ul:text-slate-300 prose-ol:text-slate-300
                prose-li:my-1
                prose-a:text-purple-400 hover:prose-a:text-purple-300
                prose-blockquote:border-purple-500 prose-blockquote:text-slate-400
                prose-code:text-purple-300 prose-code:bg-white/5 prose-code:px-1 prose-code:rounded
                prose-hr:border-white/10
            ">
                <ReactMarkdown>{content}</ReactMarkdown>
            </div>
        </div>
    );
}
