import type { ReactNode, CSSProperties } from 'react'
import { useInView } from '../../hooks/useInView'

interface FadeInProps {
  children: ReactNode
  /** Extra delay in ms — use for staggered card rows */
  delay?: number
  /** Direction the element slides in from */
  from?: 'bottom' | 'left' | 'right'
  /** Additional classes forwarded to the wrapper div */
  className?: string
}

const TRANSLATE: Record<NonNullable<FadeInProps['from']>, string> = {
  bottom: 'translate-y-6',
  left: '-translate-x-6',
  right: 'translate-x-6',
}

export default function FadeIn({ children, delay = 0, from = 'bottom', className = '' }: FadeInProps) {
  const { ref, inView } = useInView()

  const style: CSSProperties = delay > 0 ? { transitionDelay: `${delay}ms` } : {}

  return (
    <div
      ref={ref}
      style={style}
      className={`transition-all duration-700 ease-out ${
        inView
          ? 'opacity-100 translate-x-0 translate-y-0'
          : `opacity-0 ${TRANSLATE[from]}`
      } ${className}`}
    >
      {children}
    </div>
  )
}
