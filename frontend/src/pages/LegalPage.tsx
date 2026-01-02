import React, { useState } from 'react';
import { DashboardLayout } from '../components/layout/DashboardLayout';
import { Shield, FileText, Scale, AlertTriangle, CheckCircle } from 'lucide-react';

const LegalPage: React.FC = () => {
    const [activeTab, setActiveTab] = useState('privacy');

    const tabs = [
        { id: 'privacy', label: 'Privacy Notice', icon: Shield },
        { id: 'terms', label: 'Terms & Conditions', icon: FileText },
        { id: 'disclaimer', label: 'Disclaimer', icon: AlertTriangle },
        { id: 'rules', label: 'Rules & Regulations', icon: Scale },
    ];

    const content = {
        privacy: (
            <div className="space-y-4">
                <h3 className="text-xl font-bold text-gray-900">Privacy Notice (GDPR & DPDPA Compliant)</h3>
                <p className="text-gray-600">This Privacy Notice explains how we collect, use, and protect your information as per the <b>General Data Protection Regulation (GDPR)</b> and the <b>Digital Personal Data Protection Act (DPDPA)</b> of India.</p>
                <div className="space-y-2">
                    <h4 className="font-semibold">1. Data We Collect</h4>
                    <ul className="list-disc ml-5 text-sm text-gray-600">
                        <li><b>Personal Identifiers:</b> Full name, email address, phone number.</li>
                        <li><b>Financial Data:</b> Bank statements (Excel/CSV), transaction history.</li>
                        <li><b>Professional Data:</b> Contractor details, service history.</li>
                    </ul>
                </div>
                <div className="space-y-2">
                    <h4 className="font-semibold">2. Purpose of Collection</h4>
                    <p className="text-sm text-gray-600">Data is processed solely for providing financial analytics, task management, and contractor tracking. We rely on "Legitimate Interest" and "Contractual Necessity" for processing.</p>
                </div>
                <div className="space-y-2">
                    <h4 className="font-semibold">3. Your Rights</h4>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="p-3 bg-blue-50 rounded-lg border border-blue-100 italic text-xs">
                            <b>GDPR Rights:</b> Right to access, rectify, erase ("Right to be forgotten"), and object to processing.
                        </div>
                        <div className="p-3 bg-green-50 rounded-lg border border-green-100 italic text-xs">
                            <b>DPDPA Rights:</b> Right to correction, completion, erasure, and grievance redressal through a Data Protection Officer.
                        </div>
                    </div>
                </div>
            </div>
        ),
        terms: (
            <div className="space-y-4">
                <h3 className="text-xl font-bold text-gray-900">Terms & Conditions</h3>
                <p className="text-sm text-gray-600">By using the Event Management & SME System, you agree to the following terms:</p>
                <div className="space-y-2">
                    <h4 className="font-semibold">1. Acceptance of Terms</h4>
                    <p className="text-xs text-gray-600">Services are provided on an "AS IS" basis. Unauthorized use of this system for fraudulent financial reporting is strictly prohibited.</p>
                </div>
                <div className="space-y-2">
                    <h4 className="font-semibold">2. Data Sovereignty</h4>
                    <p className="text-xs text-gray-600">Your organization's data is isolated. However, you are responsible for the accuracy of the bank statements you upload.</p>
                </div>
                <div className="space-y-2">
                    <h4 className="font-semibold">3. Subscription & Billing</h4>
                    <p className="text-xs text-gray-600">Usage is governed by the organization tier selected. Late payments may result in suspension of AI analytical capabilities.</p>
                </div>
            </div>
        ),
        disclaimer: (
            <div className="space-y-4">
                <h3 className="text-xl font-bold text-gray-900">Disclaimer</h3>
                <div className="flex items-start gap-4 p-4 bg-orange-50 border border-orange-200 rounded-lg">
                    <AlertTriangle className="h-6 w-6 text-orange-600 flex-shrink-0" />
                    <div className="text-sm text-orange-800">
                        <p className="font-bold">Not Financial Advice</p>
                        <p>The analytics, summaries, and AI-generated insights provided by this system are for <b>informational purposes only</b>. They do not constitute professional accounting, tax, or legal advice.</p>
                    </div>
                </div>
                <div className="space-y-2">
                    <h4 className="font-semibold">1. AI Accuracy</h4>
                    <p className="text-sm text-gray-600">AI (Clara) uses large language models. While we ground responses in your real data, hallucinations or inaccuracies in financial reasoning may occur. Always verify important numbers manually.</p>
                </div>
                <div className="space-y-2">
                    <h4 className="font-semibold">2. Bank Statement Parsing</h4>
                    <p className="text-sm text-gray-600">While highly accurate, our parsers rely on heuristic patterns. Variations in bank formats may lead to misclassified transactions.</p>
                </div>
            </div>
        ),
        rules: (
            <div className="space-y-4">
                <h3 className="text-xl font-bold text-gray-900">Rules & Regulations</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 border rounded-lg bg-white shadow-sm">
                        <h4 className="font-bold flex items-center gap-2 mb-2 text-red-600">
                            Prohibited Actions
                        </h4>
                        <ul className="space-y-1 text-xs text-gray-500 list-disc ml-4">
                            <li>Uploading malware-infected documents.</li>
                            <li>Attempting to bypass multi-tenant isolation.</li>
                            <li>Using the AI to generate illegal financial strategies.</li>
                        </ul>
                    </div>
                    <div className="p-4 border rounded-lg bg-white shadow-sm">
                        <h4 className="font-bold flex items-center gap-2 mb-2 text-blue-600">
                            Operational Guidelines
                        </h4>
                        <ul className="space-y-1 text-xs text-gray-500 list-disc ml-4">
                            <li>Keep JWT tokens secure.</li>
                            <li>Deactivate contractor access immediately upon contract termination.</li>
                            <li>Regularly audit data reconciliation.</li>
                        </ul>
                    </div>
                </div>
            </div>
        )
    };

    return (
        <DashboardLayout>
            <div className="space-y-6 max-w-5xl mx-auto">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight">Compliance & Legal</h2>
                    <p className="text-muted-foreground">Governance documents and data protection policies for your organization.</p>
                </div>

                <div className="flex flex-col md:flex-row gap-6 bg-white rounded-xl shadow-sm border overflow-hidden min-h-[500px]">
                    {/* Sidebar Tabs */}
                    <div className="w-full md:w-64 bg-gray-50 border-r py-4 px-2 space-y-1">
                        {tabs.map((tab) => {
                            const Icon = tab.icon;
                            return (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id)}
                                    className={`w-full flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg transition-colors ${activeTab === tab.id
                                            ? 'bg-blue-600 text-white shadow-md'
                                            : 'text-gray-600 hover:bg-gray-100'
                                        }`}
                                >
                                    <Icon className="h-4 w-4" />
                                    {tab.label}
                                </button>
                            );
                        })}
                    </div>

                    {/* Content Section */}
                    <div className="flex-1 p-8 overflow-y-auto">
                        {content[activeTab as keyof typeof content]}
                    </div>
                </div>

                <div className="py-4 border-t flex items-center justify-between text-xs text-gray-400">
                    <div className="flex items-center gap-2">
                        <CheckCircle className="h-3 w-3 text-green-500" />
                        Last Reviewed: January 2026
                    </div>
                    <div>Version 1.0.4 (GDPR / DPDPA v1)</div>
                </div>
            </div>
        </DashboardLayout>
    );
};

export default LegalPage;
