import { useState, useEffect } from "react";
import { DashboardLayout } from "../components/layout/DashboardLayout";
import api from "../lib/api";
import { format, startOfMonth, endOfMonth, startOfWeek, endOfWeek, eachDayOfInterval, isSameMonth, isSameDay, addMonths, subMonths } from "date-fns";
import { Calendar as CalendarIcon, MapPin, Clock, Plus, Edit2, Trash2, ChevronLeft, ChevronRight } from "lucide-react";
import CreateMeetingModal from "../components/CreateMeetingModal";

type Meeting = {
    id: string;
    title: string;
    start_time: string;
    end_time: string;
    location?: string;
    status: string;
    description?: string;
};

export default function MeetingsPage() {
    const [meetings, setMeetings] = useState<Meeting[]>([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingMeeting, setEditingMeeting] = useState<Meeting | null>(null);
    const [currentDate, setCurrentDate] = useState(new Date());

    useEffect(() => {
        fetchMeetings();
    }, []);

    const fetchMeetings = async () => {
        try {
            const res = await api.get("/meetings");
            setMeetings(res.data.items || []);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const nextMonth = () => setCurrentDate(addMonths(currentDate, 1));
    const previousMonth = () => setCurrentDate(subMonths(currentDate, 1));

    const renderHeader = () => {
        return (
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight">Calendar</h2>
                    <p className="text-muted-foreground">{format(currentDate, "MMMM yyyy")}</p>
                </div>
                <div className="flex items-center gap-4">
                    <div className="flex items-center rounded-md border bg-white p-1">
                        <button onClick={previousMonth} className="p-2 hover:bg-slate-50 rounded-md transition-colors">
                            <ChevronLeft className="h-4 w-4" />
                        </button>
                        <button onClick={() => setCurrentDate(new Date())} className="px-3 py-1 text-sm font-medium hover:bg-slate-50 rounded-md">
                            Today
                        </button>
                        <button onClick={nextMonth} className="p-2 hover:bg-slate-50 rounded-md transition-colors">
                            <ChevronRight className="h-4 w-4" />
                        </button>
                    </div>
                    <button
                        onClick={() => { setEditingMeeting(null); setIsModalOpen(true); }}
                        className="inline-flex items-center justify-center rounded-md text-sm font-medium bg-slate-900 text-slate-50 hover:bg-slate-900/90 h-10 px-4 py-2"
                    >
                        <Plus className="mr-2 h-4 w-4" />
                        Schedule Meeting
                    </button>
                </div>
            </div>
        );
    };

    const renderDays = () => {
        const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
        return (
            <div className="grid grid-cols-7 mb-2 border-b border-slate-100">
                {days.map((day) => (
                    <div key={day} className="py-3 text-center text-xs font-semibold text-slate-400">
                        {day}
                    </div>
                ))}
            </div>
        );
    };

    const renderCells = () => {
        const monthStart = startOfMonth(currentDate);
        const monthEnd = endOfMonth(monthStart);
        const startDate = startOfWeek(monthStart);
        const endDate = endOfWeek(monthEnd);

        const calendarDays = eachDayOfInterval({ start: startDate, end: endDate });

        return (
            <div className="grid grid-cols-7 auto-rows-fr h-[calc(100vh-320px)] border-l border-t border-slate-100 min-h-[600px]">
                {calendarDays.map((day, i) => {
                    const dayMeetings = meetings.filter(m => isSameDay(new Date(m.start_time), day));
                    const isOtherMonth = !isSameMonth(day, monthStart);
                    const isToday = isSameDay(day, new Date());

                    return (
                        <div
                            key={i}
                            className={`min-h-[120px] p-2 border-r border-b border-slate-100 transition-colors hover:bg-slate-50/50 
                                ${isOtherMonth ? 'bg-slate-50/30 text-slate-300' : 'bg-white text-slate-700'}`}
                        >
                            <div className="flex justify-end mb-1">
                                <span className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-medium 
                                    ${isToday ? 'bg-blue-600 text-white shadow-sm ring-2 ring-blue-100' : ''}`}>
                                    {format(day, "d")}
                                </span>
                            </div>
                            <div className="space-y-1">
                                {dayMeetings.map(m => (
                                    <button
                                        key={m.id}
                                        onClick={() => { setEditingMeeting(m); setIsModalOpen(true); }}
                                        className={`w-full text-left px-2 py-1 rounded text-[10px] font-medium truncate border-l-2 shadow-sm
                                            ${m.status === 'scheduled' ? 'bg-blue-50 border-blue-400 text-blue-700 hover:bg-blue-100' :
                                                m.status === 'cancelled' ? 'bg-red-50 border-red-400 text-red-700 hover:bg-red-100' :
                                                    'bg-slate-50 border-slate-400 text-slate-700 hover:bg-slate-100'}`}
                                    >
                                        <div className="flex items-center gap-1">
                                            <span className="font-bold">{format(new Date(m.start_time), "HH:mm")}</span>
                                            <span className="truncate">{m.title}</span>
                                        </div>
                                    </button>
                                ))}
                            </div>
                        </div>
                    );
                })}
            </div>
        );
    };

    return (
        <DashboardLayout>
            <div className="flex flex-col h-full">
                {renderHeader()}

                <CreateMeetingModal
                    isOpen={isModalOpen}
                    onClose={() => setIsModalOpen(false)}
                    onSuccess={fetchMeetings}
                    meeting={editingMeeting}
                />

                <div className="flex-1 bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
                    {renderDays()}
                    <div className="overflow-y-auto">
                        {renderCells()}
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}
