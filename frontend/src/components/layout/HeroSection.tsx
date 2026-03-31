import DarkModeToggle from './DarkModeToggle'

export default function HeroSection({
  isDark,
  toggleDark,
}: {
  isDark: boolean
  toggleDark: () => void
}) {
  return (
    <header className="relative min-h-0 flex flex-col hero-gradient text-white overflow-hidden">
      <div className="absolute -top-24 -right-24 w-96 h-96 bg-amber-300 rounded-full blur-3xl opacity-20 pointer-events-none animate-float-blur" />
      <div className="absolute -bottom-12 -left-12 w-56 h-56 bg-orange-700 rounded-full blur-3xl opacity-20 pointer-events-none animate-float-blur-reverse" />

      <div className="relative flex-1 flex flex-col max-w-6xl mx-auto px-4 w-full pt-2 md:pt-3 pb-4 md:pb-5">
        {/* Dark-Mode-Toggle */}
        <div className="flex justify-end mb-1 md:mb-2">
          <DarkModeToggle isDark={isDark} toggle={toggleDark} />
        </div>

        {/* Titel */}
        <div className="flex-1 flex flex-col items-center justify-center text-center py-1 md:py-2">
          <a href="https://supernova1963.github.io/eedc-homeassistant/features/" target="_blank" rel="noopener noreferrer"
            className="animate-fade-slide-up">
            <img src="/eedc-icon.svg" alt="eedc" className="w-12 h-12 md:w-16 md:h-16 mb-2 md:mb-3 select-none hover:opacity-80 transition-opacity" />
          </a>
          <h1 className="text-2xl md:text-4xl lg:text-5xl font-bold mb-1 md:mb-2 tracking-tight animate-fade-slide-up animate-delay-150">
            eedc - Community
          </h1>
          <p className="text-xs md:text-lg lg:text-xl text-orange-100 max-w-lg mx-auto leading-relaxed animate-fade-slide-up animate-delay-300">
            Echte Daten echter PV-Anlagen.
            <span className="hidden sm:inline"><br /></span>
            <span className="sm:hidden"> </span>
            Anonym. Transparent. Vergleichbar.
          </p>
        </div>
      </div>
    </header>
  )
}
