import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { Activity, Map, Users, Target, MessageSquare, AlertTriangle, Network, Pickaxe, Cpu, Binary, Database, Brain } from 'lucide-react';
import clsx from 'clsx';
import { LiveFeedTicker } from '../components/LiveFeedTicker';
import { useLanguage } from '../i18n/LanguageContext';

export const DashboardLayout: React.FC = () => {
    const location = useLocation();
    const { t, lang, setLang } = useLanguage();

    const navItems = [
        { label: t('dashboard'), path: '/', icon: <Activity size={18} /> },
        { label: t('ontology'), path: '/ontology', icon: <Network size={18} /> },
        { label: t('map'), path: '/map', icon: <Map size={18} /> },
        { label: t('infrastructure'), path: '/projects', icon: <Pickaxe size={18} /> },
        { label: t('lens'), path: '/constituency', icon: <Target size={18} /> },
        { label: t('schemes'), path: '/beneficiaries', icon: <Database size={18} /> },
        { label: t('workers'), path: '/workers', icon: <Users size={18} /> },
        { label: t('comms'), path: '/comms', icon: <MessageSquare size={18} /> },
        { label: t('alerts'), path: '/alerts', icon: <AlertTriangle size={18} /> },
        { label: t('strategic_brain'), path: '/strategic', icon: <Brain size={18} /> },
    ];

    return (
        <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#09090b] text-[#f8fafc] font-sans">
            <LiveFeedTicker />
            <div className="flex flex-1 overflow-hidden relative">

            {/* Minimal High-Tech Sidebar */}
            <aside className="w-16 hover:w-64 group flex-shrink-0 border-r border-[#27272a] bg-[#141416] flex flex-col justify-between transition-all duration-300 ease-in-out z-[500] shadow-[10px_0_30px_rgba(0,0,0,0.5)]">
                <div className="flex flex-col h-full">
                    {/* Logo Section */}
                    <div className="h-20 flex items-center px-4 border-b border-border/30 overflow-hidden shrink-0">
                        <div className="w-8 h-8 rounded-lg bg-primary-dark/80 flex-shrink-0 flex items-center justify-center shadow-glow">
                            <Cpu className="text-white" size={18} />
                        </div>
                        <h1 className="ml-4 text-sm font-black tracking-[0.2em] text-text-main uppercase whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                            JanGraph <span className="text-primary-light">OS</span>
                        </h1>
                    </div>

                    <nav className="p-3 space-y-2 mt-4 flex-1 overflow-x-hidden">
                        {navItems.map((item) => {
                            const isActive = location.pathname === item.path;
                            return (
                                <Link
                                    key={item.path}
                                    to={item.path}
                                    className={clsx(
                                        "flex items-center space-x-4 px-2.5 py-3 rounded-xl text-sm font-bold transition-all overflow-hidden",
                                        isActive
                                            ? "bg-primary-dark/20 text-primary-light shadow-inner border border-primary/20"
                                            : "text-text-muted hover:bg-border/30 hover:text-text-main"
                                    )}
                                >
                                    <div className="flex-shrink-0 scale-110">
                                        {item.icon}
                                    </div>
                                    <span className="opacity-0 group-hover:opacity-100 transition-opacity duration-300 whitespace-nowrap font-mono tracking-tight uppercase text-[11px]">
                                        {item.label}
                                    </span>
                                </Link>
                            );
                        })}
                    </nav>

                    {/* Environment Info */}
                    <div className="p-4 border-t border-border/30 shrink-0 overflow-hidden">
                        <div className="flex items-center text-[10px] font-black tracking-tighter text-text-muted/40 uppercase whitespace-nowrap">
                            <Binary size={12} className="mr-3 flex-shrink-0" />
                            <span className="opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">Sovereign Node v2.1.4</span>
                        </div>
                    </div>
                </div>
            </aside>

            {/* Main Command Workspace */}
            <main className="flex-1 flex flex-col relative overflow-hidden bg-background">
                {/* Minimal Global Header */}
                <header className="h-14 border-b border-white/[0.03] bg-panel/40 backdrop-blur-3xl flex items-center justify-between px-8 z-10 sticky top-0">
                    <div className="flex items-center space-x-4">
                        <div className="text-[10px] font-black text-text-muted uppercase tracking-[0.3em] flex items-center border border-border/40 px-3 py-1 rounded bg-background/50 shadow-inner">
                            <span className="w-1.5 h-1.5 rounded-full bg-success mr-2 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.8)]"></span>
                            {t('active_node')}: {location.pathname.replace('/', '') || 'ROOT'}
                        </div>
                    </div>

                    <div className="flex items-center space-x-6">
                        {/* Language Toggle */}
                        <div className="flex items-center bg-background border border-border/60 rounded-lg p-0.5 shadow-inner">
                            {(['en', 'hi', 'ta'] as const).map(l => (
                                <button
                                    key={l}
                                    onClick={() => setLang(l)}
                                    className={clsx(
                                        "px-2 py-1 text-[9px] font-bold tracking-widest uppercase transition-all rounded",
                                        lang === l ? "bg-primary/20 text-primary-light" : "text-text-muted hover:text-text-main hover:bg-panel"
                                    )}
                                >
                                    {l}
                                </button>
                            ))}
                        </div>

                        {/* Environment status details */}
                        <div className="hidden md:flex flex-col items-end">
                            <div className="text-[9px] font-black text-text-muted uppercase tracking-tighter opacity-50">{t('op_strategist')}</div>
                            <div className="text-[10px] font-bold text-primary-light uppercase font-mono tracking-widest">{t('auth_level')}</div>
                        </div>
                        <div className="h-8 w-px bg-border/40"></div>
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary/30 to-background border border-border/60 flex items-center justify-center text-[10px] font-bold text-primary-light shadow-inner">
                            ST
                        </div>
                    </div>
                </header>

                {/* Workspace Canvas Area */}
                <div className="flex-1 overflow-auto bg-background selection:bg-primary-dark/30">
                    <div className="max-w-[1600px] mx-auto min-h-full p-4 md:p-8 animate-in fade-in duration-700">
                        <Outlet />
                    </div>
                </div>

                {/* Visual Glitch/Texture Overlay */}
                <div className="absolute inset-0 pointer-events-none opacity-[0.02] bg-[url('https://grainy-gradients.vercel.app/noise.svg')] blend-overlay"></div>
            </main>
            </div>
        </div>
    );
};
