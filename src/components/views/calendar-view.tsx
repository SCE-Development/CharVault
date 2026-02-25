import {
    Card,
    CardAction,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/src/components/ui/card"
import { cn } from "@/lib/utils";
export default function CalendarView() {
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const daysArray = Array.from({ length: daysInMonth }, (_, i) => i + 1);


    const monthName = now.toLocaleString('default', { month: 'long' });
    return (
        <Card>
            <CardHeader>
                Your Events
                <CardDescription>
                    {monthName} {year}
                </CardDescription>
            </CardHeader>
            <CardContent>
                <div className="grid grid-cols-7 gap-2 sm:grid-cols-10 md:grid-cols-12">
                    {daysArray.map((day) => (
                        <div
                            key={day}
                            className={cn(
                                "flex h-10 w-full items-center justify-center rounded-md border text-sm font-medium",
                                "bg-secondary text-secondary-foreground",
                                day === now.getDate() && "bg-primary text-primary-foreground border-primary"
                            )}
                        >
                            {day}
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    )
}