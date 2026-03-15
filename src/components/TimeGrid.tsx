"use client";

import { FC, UIEvent } from "react";

type EventColor = "blue" | "pink" | "purple";
type EventRole = "interviewer" | "interviewee" | "event";

interface TimeGridColumn {
    dateObj: Date;
    label: string;
    isToday: boolean;
}

interface ColorTokens {
    chip: string;
    dot: string;
    badge: string;
    block: string;
}

interface CalendarEvent {
    id: number;
    title: string;
    time: string;
    duration: number;
    person: string;
    role: EventRole;
    day: number;
    color: EventColor;
}


interface TimeGridProps {
    columns: TimeGridColumn[];
    dk: boolean;
    accent: string;
    getEventsForDate: (d: Date) => CalendarEvent[];
    onEventClick: (day: number) => void;
    scrollRef: React.RefObject<HTMLDivElement | null>;
}

const COLOR_MAP: Record<EventColor, ColorTokens> = {
    blue: { chip: "bg-blue-100 border border-blue-200 text-blue-800", dot: "bg-blue-400", badge: "bg-blue-50 text-blue-600 border border-blue-200", block: "bg-blue-100 border-l-4 border-blue-400 text-blue-800" },
    pink: { chip: "bg-rose-100 border border-rose-200 text-rose-800", dot: "bg-rose-400", badge: "bg-rose-50 text-rose-600 border border-rose-200", block: "bg-rose-100 border-l-4 border-rose-400 text-rose-800" },
    purple: { chip: "bg-purple-100 border border-purple-200 text-purple-800", dot: "bg-purple-400", badge: "bg-purple-50 text-purple-600 border border-purple-200", block: "bg-purple-100 border-l-4 border-purple-400 text-purple-800" },
};
const HOURS: number[] = Array.from({ length: 24 }, (_, i) => i);

function fmtHour(h: number): string {
    if (h === 0) return "12 AM";
    if (h < 12) return `${h} AM`;
    if (h === 12) return "12 PM";
    return `${h - 12} PM`;
}

function timeToMins(t: string): number {
    const [h, m] = t.split(":").map(Number);
    return h * 60 + m;
}

function fmtTime(t: string): string {
    const [h, m] = t.split(":").map(Number);
    const ampm = h >= 12 ? "PM" : "AM";
    const hr = h % 12 || 12;
    return `${hr}:${String(m).padStart(2, "0")} ${ampm}`;
}
export const TimeGrid: FC<TimeGridProps> = ({ columns, dk, accent, getEventsForDate, onEventClick, scrollRef }) => {
    const handleScroll = (e: UIEvent<HTMLDivElement>) => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = e.currentTarget.scrollTop;
        }
    };

    return (
        <div className="flex flex-1 overflow-hidden">
            {/* Hour labels */}
            <div
                className="shrink-0 w-14 overflow-y-auto"
                ref={scrollRef}
                style={{ scrollbarWidth: "none" }}
            >
                <div style={{ height: 24 * 64 }}>
                    {HOURS.map((h) => (
                        <div key={h} style={{ height: 64 }} className="relative">
                            <span className={`absolute -top-2.5 right-2 text-xs font-medium ${dk ? "text-gray-500" : "text-gray-400"}`}>
                                {fmtHour(h)}
                            </span>
                        </div>
                    ))}
                </div>
            </div>

            {/* Day columns */}
            <div
                className="flex flex-1 overflow-y-auto overflow-x-hidden"
                style={{ scrollbarWidth: "thin" }}
                onScroll={handleScroll}
            >
                <div className="flex flex-1" style={{ minHeight: 24 * 64, height: 24 * 64 }}>
                    {columns.map(({ dateObj, isToday }, ci) => {
                        const colEvents = getEventsForDate(dateObj);
                        return (
                            <div key={ci} className={`flex-1 relative border-r ${dk ? "border-gray-800" : "border-white/50"}`}>
                                {/* Hour lines */}
                                {HOURS.map((h) => (
                                    <div
                                        key={h}
                                        style={{ height: 64, top: h * 64 }}
                                        className={`absolute w-full border-t ${dk ? "border-gray-800" : "border-white/60"}`}
                                    />
                                ))}
                                {/* Half-hour lines */}
                                {HOURS.map((h) => (
                                    <div
                                        key={`half-${h}`}
                                        style={{ height: 32, top: h * 64 + 32 }}
                                        className={`absolute w-full border-t border-dashed ${dk ? "border-gray-800/60" : "border-white/40"}`}
                                    />
                                ))}
                                {/* Events */}
                                {colEvents.map((ev) => {
                                    const startMin = timeToMins(ev.time);
                                    const top = (startMin / 60) * 64;
                                    const height = Math.max((ev.duration / 60) * 64, 24);
                                    return (
                                        <div
                                            key={ev.id}
                                            onClick={() => onEventClick(ev.day)}
                                            style={{ top, height, left: 2, right: 2, position: "absolute" }}
                                            className={`rounded-lg px-2 py-1 cursor-pointer chip overflow-hidden z-10 ${COLOR_MAP[ev.color].block}`}
                                        >
                                            <p className="text-xs font-semibold truncate leading-tight">{ev.title}</p>
                                            <p className="text-xs opacity-70 truncate">{fmtTime(ev.time)} · {ev.person}</p>
                                        </div>
                                    );
                                })}
                                {/* Current-time indicator */}
                                {isToday && (() => {
                                    const now = new Date();
                                    const mins = now.getHours() * 60 + now.getMinutes();
                                    return (
                                        <div
                                            style={{ top: (mins / 60) * 64, position: "absolute", left: 0, right: 0, zIndex: 20 }}
                                            className="flex items-center"
                                        >
                                            <div className={`w-2.5 h-2.5 rounded-full bg-linear-to-br ${accent} -ml-1.5 shadow`} />
                                            <div className={`flex-1 h-px bg-linear-to-r ${accent}`} />
                                        </div>
                                    );
                                })()}
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
};