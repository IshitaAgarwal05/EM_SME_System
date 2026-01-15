import React, { useState } from 'react';
import { StyleSheet, Text, View, SafeAreaView, ScrollView, TouchableOpacity, TextInput } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { LayoutDashboard, CheckSquare, Wallet, Bot, User } from 'lucide-react-native';

export default function App() {
    const [activeTab, setActiveTab] = useState('Home');

    const navigation = [
        { name: 'Home', icon: LayoutDashboard },
        { name: 'Tasks', icon: CheckSquare },
        { name: 'Finance', icon: Wallet },
        { name: 'Clara', icon: Bot },
        { name: 'Profile', icon: User },
    ];

    return (
        <SafeAreaView style={styles.container}>
            <StatusBar style="auto" />

            {/* Header */}
            <View style={styles.header}>
                <Text style={styles.headerTitle}>Event OS Mobile</Text>
            </View>

            {/* Main Content */}
            <ScrollView style={styles.content}>
                <View style={styles.card}>
                    <Text style={styles.cardTitle}>Quick Summary</Text>
                    <View style={styles.statsRow}>
                        <View style={styles.stat}>
                            <Text style={styles.statLabel}>Profit</Text>
                            <Text style={styles.statValue}>₹45,200</Text>
                        </View>
                        <View style={styles.stat}>
                            <Text style={styles.statLabel}>Overdue</Text>
                            <Text style={[styles.statValue, { color: '#ef4444' }]}>3 Tasks</Text>
                        </View>
                    </View>
                </View>

                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>Ask Clara (AI)</Text>
                    <View style={styles.inputWrapper}>
                        <TextInput
                            placeholder="Ask about your finances..."
                            style={styles.input}
                        />
                        <TouchableOpacity style={styles.sendButton}>
                            <Text style={styles.sendButtonText}>Ask</Text>
                        </TouchableOpacity>
                    </View>
                </View>
            </ScrollView>

            {/* Top-Level Navigation */}
            <View style={styles.navBar}>
                {navigation.map((item) => (
                    <TouchableOpacity
                        key={item.name}
                        onPress={() => setActiveTab(item.name)}
                        style={styles.navItem}
                    >
                        <item.icon
                            color={activeTab === item.name ? '#2563eb' : '#64748b'}
                            size={24}
                        />
                        <Text style={[
                            styles.navText,
                            { color: activeTab === item.name ? '#2563eb' : '#64748b' }
                        ]}>
                            {item.name}
                        </Text>
                    </TouchableOpacity>
                ))}
            </View>
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#f8fafc',
    },
    header: {
        height: 60,
        backgroundColor: '#fff',
        borderBottomWidth: 1,
        borderBottomColor: '#e2e8f0',
        alignItems: 'center',
        justifyContent: 'center',
    },
    headerTitle: {
        fontSize: 18,
        fontWeight: 'bold',
        color: '#0f172a',
    },
    content: {
        flex: 1,
        padding: 16,
    },
    card: {
        backgroundColor: '#fff',
        padding: 16,
        borderRadius: 12,
        borderWidth: 1,
        borderBottomColor: '#e2e8f0',
        marginBottom: 20,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.05,
        shadowRadius: 2,
        elevation: 2,
    },
    cardTitle: {
        fontSize: 14,
        color: '#64748b',
        marginBottom: 8,
    },
    statsRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
    },
    stat: {
        flex: 1,
    },
    statLabel: {
        fontSize: 12,
        color: '#94a3b8',
    },
    statValue: {
        fontSize: 20,
        fontWeight: 'bold',
        color: '#1e293b',
    },
    section: {
        marginBottom: 20,
    },
    sectionTitle: {
        fontSize: 16,
        fontWeight: 'bold',
        color: '#334155',
        marginBottom: 12,
    },
    inputWrapper: {
        flexDirection: 'row',
        gap: 8,
    },
    input: {
        flex: 1,
        backgroundColor: '#fff',
        borderWidth: 1,
        borderColor: '#e2e8f0',
        borderRadius: 8,
        paddingHorizontal: 12,
        height: 44,
    },
    sendButton: {
        backgroundColor: '#2563eb',
        paddingHorizontal: 16,
        borderRadius: 8,
        alignItems: 'center',
        justifyContent: 'center',
    },
    sendButtonText: {
        color: '#fff',
        fontWeight: 'bold',
    },
    navBar: {
        flexDirection: 'row',
        height: 70,
        backgroundColor: '#fff',
        borderTopWidth: 1,
        borderTopColor: '#e2e8f0',
        paddingBottom: 10,
    },
    navItem: {
        flex: 1,
        alignItems: 'center',
        justifyContent: 'center',
    },
    navText: {
        fontSize: 10,
        marginTop: 4,
    },
});
