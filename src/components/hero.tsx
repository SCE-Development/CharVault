export function Hero() {
    return (
        <div className="relative min-h-screen flex items-center justify-center overflow-hidden bg-linear-to-br from-blue-50 via-pink-50 to-blue-100">
            {/* Background pattern */}
            <div className="absolute inset-0 opacity-10">
                <div className="absolute top-10 left-10 w-32 h-32 rounded-full bg-pink-400 blur-3xl"></div>
                <div className="absolute bottom-20 right-20 w-40 h-40 rounded-full bg-blue-400 blur-3xl"></div>
                <div className="absolute top-1/2 left-1/3 w-36 h-36 rounded-full bg-pink-300 blur-3xl"></div>
            </div>
        </div>
    )
}