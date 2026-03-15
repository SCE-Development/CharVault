"use client";

import { useState, useRef, useEffect } from "react";
import { TimeGrid } from '@/src/components/TimeGrid'

type EventColor = "blue" | "pink" | "purple";
type EventRole = "interviewer" | "interviewee" | "event";
type ViewMode = "month" | "week" | "day";
type ThemeKey = "blush" | "ocean" | "lavender";

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

interface ColorTokens {
    chip: string;
    dot: string;
    badge: string;
    block: string;
}

interface Theme {
    sidebar: string;
    main: string;
    accent: string;
    button: string;
    name: string;
}

const SAMPLE_EVENTS: CalendarEvent[] = [];

const colors: Record<EventColor, ColorTokens> = {
    blue: { chip: "bg-blue-100 border border-blue-200 text-blue-800", dot: "bg-blue-400", badge: "bg-blue-50 text-blue-600 border border-blue-200", block: "bg-blue-100 border-l-4 border-blue-400 text-blue-800" },
    pink: { chip: "bg-rose-100 border border-rose-200 text-rose-800", dot: "bg-rose-400", badge: "bg-rose-50 text-rose-600 border border-rose-200", block: "bg-rose-100 border-l-4 border-rose-400 text-rose-800" },
    purple: { chip: "bg-purple-100 border border-purple-200 text-purple-800", dot: "bg-purple-400", badge: "bg-purple-50 text-purple-600 border border-purple-200", block: "bg-purple-100 border-l-4 border-purple-400 text-purple-800" },
};

const weekDays_Abbreiv = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"] as const;

const themes: Record<ThemeKey, Theme> = {
    blush: { sidebar: "from-rose-100 via-pink-50 to-pink-100", main: "from-sky-50 via-blue-50 to-indigo-50", accent: "from-rose-400 to-pink-500", button: "from-rose-400 to-pink-500", name: "Blush" },
    ocean: { sidebar: "from-cyan-100 via-teal-50 to-sky-100", main: "from-blue-50 via-sky-50 to-cyan-50", accent: "from-cyan-400 to-teal-500", button: "from-cyan-400 to-teal-500", name: "Ocean" },
    lavender: { sidebar: "from-purple-100 via-violet-50 to-fuchsia-100", main: "from-indigo-50 via-purple-50 to-violet-50", accent: "from-purple-400 to-violet-500", button: "from-purple-400 to-violet-500", name: "Lavender" },
};

function fmtTime(t: string): string {
    const [h, m] = t.split(":").map(Number);
    const ampm = h >= 12 ? "PM" : "AM";
    const hr = h % 12 || 12;
    return `${hr}:${String(m).padStart(2, "0")} ${ampm}`;
}
export default function CalendarView() {

    const [view, setView] = useState<ViewMode>("month");
    const [dk, setDk] = useState<boolean>(false);
    const [currentDate, setCurrentDate] = useState<Date>(new Date(2026, 5, 1));
    const [selectedDay, setSelectedDay] = useState<number | null>(null);
    const [events, setEvents] = useState<CalendarEvent[]>(SAMPLE_EVENTS);
    const [theme, setTheme] = useState<ThemeKey>("blush");

    const scrollRef = useRef<HTMLDivElement | null>(null);

    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const monthName = currentDate.toLocaleString("default", { month: "long" });
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const today = new Date();
    const isCurrentMonth = today.getMonth() === month && today.getFullYear() === year;

    const themes_list = themes[theme];

    const weekStart = new Date(currentDate);
    weekStart.setDate(currentDate.getDate() - currentDate.getDay());

    const weekDays = Array.from({ length: 7 }, (_, i) => {
        const d = new Date(weekStart);
        d.setDate(weekStart.getDate() + i);
        return d;
    });

    useEffect(() => {
        if ((view === "week" || view === "day") && scrollRef.current) {
            scrollRef.current.scrollTop = 8 * 64;
        }
    }, [view]);

    const prevPeriod = () => {
        if (view === "month") setCurrentDate(new Date(year, month - 1, 1));
        else if (view === "week") { const d = new Date(currentDate); d.setDate(d.getDate() - 7); setCurrentDate(d); }
        else { const d = new Date(currentDate); d.setDate(d.getDate() - 1); setCurrentDate(d); }
    };
    const nextPeriod = () => {
        if (view === "month") setCurrentDate(new Date(year, month + 1, 1));
        else if (view === "week") { const d = new Date(currentDate); d.setDate(d.getDate() + 7); setCurrentDate(d); }
        else { const d = new Date(currentDate); d.setDate(d.getDate() + 1); setCurrentDate(d); }
    };

    const goToToday = (): void => {
        const now = new Date();
        setCurrentDate(new Date(now.getFullYear(), now.getMonth(), now.getDate()));
    };

    const getEventsForDay = (day: number): CalendarEvent[] =>
        events.filter((e) => e.day === day);

    const getEventsForDate = (dateObj: Date) => {
        return events.filter((e) => {
            const eDate = new Date(year, month, e.day);
            return eDate.toDateString() === dateObj.toDateString();
        });
    };

    const cells = [];
    for (let i = 0; i < firstDay; i++) cells.push(null);
    for (let d = 1; d <= daysInMonth; d++) cells.push(d);

    let periodLabel = `${monthName} ${year}`;
    if (view === "week") {
        const endOfWeek = new Date(weekStart); endOfWeek.setDate(weekStart.getDate() + 6);
        const sm = weekStart.toLocaleString("default", { month: "short" });
        const em = endOfWeek.toLocaleString("default", { month: "short" });
        periodLabel = sm === em
            ? `${sm} ${weekStart.getDate()}–${endOfWeek.getDate()}, ${weekStart.getFullYear()}`
            : `${sm} ${weekStart.getDate()} – ${em} ${endOfWeek.getDate()}, ${weekStart.getFullYear()}`;
    } else if (view === "day") {
        periodLabel = currentDate.toLocaleDateString("default", { weekday: "long", month: "long", day: "numeric", year: "numeric" });
    }

    return (
        <div className={`font-sans flex flex-col p-5 gap-3 min-w-0 min-h-0 flex-1 overflow-hidden ${dk ? "bg-gray-250" : "bg-linear-to-br from-slate-100 to-slate-200"}`}
            style={{ fontFamily: "'DM Sans', 'Nunito', sans-serif" }}>
            <div className="flex items-center gap-2 shrink-0">
                <div className={`w-7 h-7 rounded-lg bg-linear-to-br ${themes_list.accent} shadow`} />
                <span className={`text-base font-bold ${dk ? "text-white" : "text-gray-800"}`} style={{ fontFamily: "'Playfair Display', serif" }}>
                    Calendar
                </span>
            </div>

            <div className={`flex-1 rounded-2xl overflow-hidden shadow-xl flex flex-col min-h-0 ${dk ? "bg-gray-900 border border-gray-800" : `bg-linear-to-br ${themes_list.main} border border-white/70`}`}>

                <div className={`flex items-center justify-between px-5 py-3 border-b shrink-0 ${dk ? "border-gray-800" : "border-white/60"}`}>
                    <div className="flex items-center gap-1">
                        {(["month", "week", "day"] as ViewMode[]).map((v) => (
                            <button
                                key={v}
                                onClick={() => setView(v)}
                                className={`px-4 py-1.5 rounded-lg text-sm font-semibold capitalize transition-all ${view === v ? `bg-linear-to-r ${themes_list.button} text-white shadow-md` : dk ? "text-gray-400 hover:bg-gray-800" : "text-gray-500 hover:bg-white/60"}`}
                            >
                                {v}
                            </button>
                        ))}
                    </div>
                    <div className="flex items-center gap-3">
                        <span className={`text-sm font-bold ${dk ? "text-white" : "text-gray-700"}`} style={{ fontFamily: "'Playfair Display', serif" }}>
                            {periodLabel}
                        </span>
                        <div className="flex gap-1">
                            <button onClick={prevPeriod} className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold transition ${dk ? "bg-gray-800 text-gray-300 hover:bg-gray-700" : "bg-white/80 text-gray-600 hover:bg-white shadow-sm"}`}>‹</button>
                            <button onClick={goToToday} className={`px-3 h-8 rounded-lg text-xs font-semibold transition ${dk ? "bg-gray-800 text-gray-300 hover:bg-gray-700" : "bg-white/80 text-gray-600 hover:bg-white shadow-sm"}`}>Today</button>
                            <button onClick={nextPeriod} className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold transition ${dk ? "bg-gray-800 text-gray-300 hover:bg-gray-700" : "bg-white/80 text-gray-600 hover:bg-white shadow-sm"}`}>›</button>
                        </div>
                    </div>
                </div>
                {view === "month" && (
                    <>
                        <div className={`grid grid-cols-7 border-b shrink-0 ${dk ? "border-gray-800" : "border-white/50 bg-white/30"}`}>
                            {weekDays_Abbreiv.map((d) => (
                                <div key={d} className={`py-2 text-center text-xs font-bold uppercase tracking-wider ${dk ? "text-gray-500" : "text-gray-400"}`}>{d}</div>
                            ))}
                        </div>
                        <div className="grid grid-cols-7 overflow-y-auto" style={{ gridAutoRows: "80px" }}>
                            {cells.map((day, idx) => {
                                const dayEvents: CalendarEvent[] = day !== null
                                    ? events.filter(e => e.day === day)
                                    : [];
                                const isToday = isCurrentMonth && day === today.getDate();

                                return (
                                    <div
                                        key={idx}
                                        onClick={() => day !== null && setSelectedDay(day)}
                                        className={`border-b border-r p-1.5 overflow-hidden transition-colors ${day !== null ? "cursor-pointer" : ""
                                            } ${dk ? "border-gray-800 hover:bg-gray-800" : "border-white/50 hover:bg-white/40"} ${day === null ? "opacity-20" : ""
                                            }`}
                                    >
                                        {day !== null && (
                                            <>
                                                <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold mb-1 ${isToday ? `bg-linear-to-br ${themes_list.accent} text-white shadow` : dk ? "text-gray-400" : "text-gray-500"}`}>
                                                    {day}
                                                </div>

                                                <div className="flex flex-col gap-0.5">
                                                    {dayEvents.slice(0, 2).map((ev: CalendarEvent) => (
                                                        <div
                                                            key={ev.id}
                                                            className={`chip rounded-md px-1.5 py-0.5 text-xs font-medium flex items-center gap-1 ${colors[ev.color].chip}`}
                                                        >
                                                            <div className={`w-1.5 h-1.5 rounded-full shrink-0 ${colors[ev.color].dot}`} />
                                                            <span className="truncate">{ev.title}</span>
                                                        </div>
                                                    ))}
                                                    {dayEvents.length > 2 && (
                                                        <span className={`text-xs px-1 ${dk ? "text-gray-500" : "text-gray-400"}`}>
                                                            +{dayEvents.length - 2} more
                                                        </span>
                                                    )}
                                                </div>
                                            </>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    </>
                )}

                {view === "week" && (
                    <div className="flex flex-col flex-1 min-h-0">
                        <div className={`flex border-b shrink-0 ${dk ? "border-gray-800" : "border-white/50"}`}>
                            <div className="w-14 shrink-0" />
                            {weekDays.map((d, i) => {
                                const isToday = d.toDateString() === today.toDateString();
                                return (
                                    <div
                                        key={i}
                                        onClick={() => { setCurrentDate(new Date(d)); setView("day"); }}
                                        className={`flex-1 py-2 text-center cursor-pointer transition ${dk ? "hover:bg-gray-800" : "hover:bg-white/40"}`}
                                    >
                                        <p className={`text-xs font-bold uppercase tracking-wider ${dk ? "text-gray-500" : "text-gray-400"}`}>
                                            {weekDays_Abbreiv[d.getDay()]}
                                        </p>
                                        <div className={`w-7 h-7 rounded-full flex items-center justify-center text-sm font-semibold mx-auto mt-0.5 ${isToday ? `bg-linear-to-br ${themes_list.accent} text-white shadow` : dk ? "text-gray-300" : "text-gray-700"}`}>
                                            {d.getDate()}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                        <TimeGrid
                            columns={weekDays.map((d) => ({
                                dateObj: d,
                                label: `${weekDays_Abbreiv[d.getDay()]} ${d.getDate()}`,
                                isToday: d.toDateString() === today.toDateString(),
                            }))}
                            dk={dk}
                            accent={themes_list.accent}
                            getEventsForDate={getEventsForDate}
                            onEventClick={setSelectedDay}
                            scrollRef={scrollRef}
                        />
                    </div>
                )}

                {view === "day" && (
                    <div className="flex flex-col flex-1 min-h-0">
                        <div className={`flex border-b shrink-0 ${dk ? "border-gray-800" : "border-white/50"}`}>
                            <div className="w-14 shrink-0" />
                            <div className="flex-1 py-2 text-center">
                                <p className={`text-xs font-bold uppercase tracking-wider ${dk ? "text-gray-500" : "text-gray-400"}`}>
                                    {weekDays_Abbreiv[currentDate.getDay()]}
                                </p>
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold mx-auto mt-0.5 ${currentDate.toDateString() === today.toDateString() ? `bg-linear-to-br ${themes_list.accent} text-white shadow` : dk ? "text-gray-300" : "text-gray-700"}`}>
                                    {currentDate.getDate()}
                                </div>
                            </div>
                        </div>
                        <TimeGrid
                            columns={[{
                                dateObj: currentDate,
                                label: currentDate.toDateString(),
                                isToday: currentDate.toDateString() === today.toDateString(),
                            }]}
                            dk={dk}
                            accent={themes_list.accent}
                            getEventsForDate={getEventsForDate}
                            onEventClick={setSelectedDay}
                            scrollRef={scrollRef}
                        />
                    </div>
                )}

                {selectedDay !== null && (
                    <div className="fixed inset-0 flex items-center justify-center z-50 modal-bg bg-black/30" onClick={() => setSelectedDay(null)}>
                        <div
                            className={`rounded-2xl shadow-2xl p-6 w-80 max-h-96 overflow-y-auto ${dk ? "bg-gray-900 border border-gray-700" : "bg-white"}`}
                            onClick={(e) => e.stopPropagation()}
                        >
                            <div className="flex items-center justify-between mb-4">
                                <h3 className={`text-lg font-bold ${dk ? "text-white" : "text-gray-800"}`} style={{ fontFamily: "'Playfair Display', serif" }}>
                                    {monthName} {selectedDay}
                                </h3>
                                <button onClick={() => setSelectedDay(null)} className="text-gray-400 hover:text-gray-600 text-xl leading-none">×</button>
                            </div>
                            {getEventsForDay(selectedDay).length === 0 ? (
                                <p className="text-sm text-gray-400">No events this day.</p>
                            ) : (
                                getEventsForDay(selectedDay).map((ev) => (
                                    <div key={ev.id} className={`rounded-xl p-3 mb-2 ${colors[ev.color].chip}`}>
                                        <p className="font-semibold text-sm">{ev.title}</p>
                                        <p className="text-xs opacity-75">{fmtTime(ev.time)} · {ev.duration} min</p>
                                        <p className="text-xs opacity-75 mt-0.5">with {ev.person}</p>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                )}

            </div>
        </div>

    )
}