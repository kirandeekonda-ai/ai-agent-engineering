import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { MessageSquare, LayoutDashboard, Sparkles, Brain, Zap, Shield } from 'lucide-react';

export default function Home() {
  return (
    <main className="min-h-screen overflow-hidden">
      {/* Navigation */}
      <nav className="nav-glass fixed top-0 left-0 right-0 z-50 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold gradient-text">IdeaForge</span>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/chat">
              <Button variant="ghost" className="text-muted-foreground hover:text-foreground">
                Chat
              </Button>
            </Link>
            <Link href="/dashboard">
              <Button variant="ghost" className="text-muted-foreground hover:text-foreground">
                Dashboard
              </Button>
            </Link>
            <Link href="/chat">
              <Button className="btn-premium rounded-full px-6">
                Get Started
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 px-6">
        {/* Background Elements */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-500/20 rounded-full blur-3xl animate-pulse" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse delay-1000" />
        </div>

        <div className="max-w-6xl mx-auto text-center relative z-10">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass-card mb-8 animate-fade-in">
            <Sparkles className="w-4 h-4 text-indigo-400" />
            <span className="text-sm text-muted-foreground">Powered by Advanced AI</span>
          </div>

          {/* Main Heading */}
          <h1 className="text-6xl md:text-7xl lg:text-8xl font-bold mb-6 tracking-tight animate-fade-in">
            <span className="gradient-text">Transform Ideas</span>
            <br />
            <span className="text-foreground">Into Reality</span>
          </h1>

          {/* Subtitle */}
          <p className="text-xl md:text-2xl text-muted-foreground max-w-2xl mx-auto mb-12 leading-relaxed animate-fade-in">
            Your AI-powered idea assistant that helps you brainstorm, refine,
            and organize your ideas with intelligent automation.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-fade-in">
            <Link href="/chat">
              <Button size="lg" className="btn-premium rounded-full px-8 py-6 text-lg font-semibold">
                <MessageSquare className="w-5 h-5 mr-2" />
                Start Brainstorming
              </Button>
            </Link>
            <Link href="/dashboard">
              <Button size="lg" variant="outline" className="glass-card rounded-full px-8 py-6 text-lg font-semibold border-white/10 hover:bg-white/5">
                <LayoutDashboard className="w-5 h-5 mr-2" />
                View Dashboard
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 px-6 relative">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4">
              <span className="gradient-text-accent">Supercharge</span> Your Creativity
            </h2>
            <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
              Everything you need to capture, develop, and track your ideas
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {/* Feature 1 */}
            <div className="glass-card rounded-2xl p-8 group">
              <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-indigo-500/20 to-indigo-600/20 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                <Brain className="w-7 h-7 text-indigo-400" />
              </div>
              <h3 className="text-xl font-semibold mb-3">AI-Powered Analysis</h3>
              <p className="text-muted-foreground leading-relaxed">
                Intelligent extraction of key details from your conversations.
                Get instant insights on feasibility, impact, and complexity.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="glass-card rounded-2xl p-8 group">
              <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-purple-500/20 to-purple-600/20 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                <Zap className="w-7 h-7 text-purple-400" />
              </div>
              <h3 className="text-xl font-semibold mb-3">Auto-Save Magic</h3>
              <p className="text-muted-foreground leading-relaxed">
                Ideas are automatically captured when ready. No manual work
                needed — our AI knows when your idea is complete.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="glass-card rounded-2xl p-8 group">
              <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-emerald-500/20 to-emerald-600/20 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                <Shield className="w-7 h-7 text-emerald-400" />
              </div>
              <h3 className="text-xl font-semibold mb-3">Smart Organization</h3>
              <p className="text-muted-foreground leading-relaxed">
                Automatic categorization by domain, complexity, and status.
                Filter, search, and track progress effortlessly.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-6">
        <div className="max-w-4xl mx-auto">
          <div className="glass-card rounded-3xl p-12 text-center relative overflow-hidden">
            {/* Glow Effect */}
            <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/10 via-purple-500/10 to-pink-500/10" />

            <div className="relative z-10">
              <h2 className="text-4xl font-bold mb-4">
                Ready to <span className="gradient-text">Build Something Amazing?</span>
              </h2>
              <p className="text-muted-foreground text-lg mb-8 max-w-xl mx-auto">
                Start capturing your ideas today. No sign-up required.
              </p>
              <Link href="/chat">
                <Button size="lg" className="btn-premium rounded-full px-10 py-6 text-lg font-semibold">
                  <Sparkles className="w-5 h-5 mr-2" />
                  Start Free Now
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-6 border-t border-white/5">
        <div className="max-w-6xl mx-auto flex items-center justify-between text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-indigo-400" />
            <span>IdeaForge</span>
          </div>
          <p>Built with AI • Week 23 Project</p>
        </div>
      </footer>
    </main>
  );
}
