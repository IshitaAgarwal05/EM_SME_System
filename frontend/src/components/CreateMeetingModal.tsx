import { useState, useEffect } from "react";
import api from "../lib/api";
import { X } from "lucide-react";

type Props = {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
    meeting?: any; // If provided, we are in edit mode
};

export default function CreateMeetingModal({ isOpen, onClose, onSuccess, meeting }: Props) {
    const [title, setTitle] = useState("");
    const [description, setDescription] = useState("");
    const [startTime, setStartTime] = useState("");
    const [endTime, setEndTime] = useState("");
    const [location, setLocation] = useState("");
    const [meetingLink, setMeetingLink] = useState("");
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (meeting) {
            setTitle(meeting.title || "");
            setDescription(meeting.description || "");
            setStartTime(meeting.start_time ? new Date(meeting.start_time).toISOString().slice(0, 16) : "");
            setEndTime(meeting.end_time ? new Date(meeting.end_time).toISOString().slice(0, 16) : "");
            setLocation(meeting.location || "");
            setMeetingLink(meeting.meeting_link || "");
        } else {
            setTitle("");
            setDescription("");
            setStartTime("");
            setEndTime("");
            setLocation("");
            setMeetingLink("");
        }
    }, [meeting, isOpen]);

    if (!isOpen) return null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            const data = {
                title,
                description,
                start_time: new Date(startTime).toISOString(),
                end_time: new Date(endTime).toISOString(),
                location,
                meeting_link: meetingLink,
                participants: [] // Simplified for MVP
            };

            if (meeting) {
                await api.patch(`/meetings/${meeting.id}`, data);
            } else {
                await api.post("/meetings", data);
            }
            onSuccess();
            onClose();
        } catch (err) {
            console.error(err);
            alert("Failed to save meeting");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-bold">{meeting ? "Edit Meeting" : "Schedule Meeting"}</h3>
                    <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded-full">
                        <X className="h-5 w-5" />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Title</label>
                        <input
                            type="text"
                            required
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                            placeholder="Kick-off Meeting"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Description</label>
                        <textarea
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                            rows={3}
                        />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700">Start Time</label>
                            <input
                                type="datetime-local"
                                required
                                value={startTime}
                                onChange={(e) => setStartTime(e.target.value)}
                                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700">End Time</label>
                            <input
                                type="datetime-local"
                                required
                                value={endTime}
                                onChange={(e) => setEndTime(e.target.value)}
                                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                            />
                        </div>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Location / Meeting Link</label>
                        <input
                            type="text"
                            value={location}
                            onChange={(e) => setLocation(e.target.value)}
                            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                            placeholder="Zoom Link or Meeting Room"
                        />
                    </div>

                    <div className="flex justify-end gap-3 pt-2">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-md"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className="px-4 py-2 text-sm font-medium text-white bg-slate-900 hover:bg-slate-800 rounded-md disabled:opacity-50"
                        >
                            {loading ? "Saving..." : meeting ? "Update Meeting" : "Schedule"}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
