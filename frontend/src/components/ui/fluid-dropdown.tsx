"use client"

import * as React from "react"
import { motion, AnimatePresence, MotionConfig } from "framer-motion"
import { ChevronDown } from "lucide-react"

// Utility function for className merging
function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(" ")
}

// Custom hook for click outside detection
function useClickAway(ref: React.RefObject<HTMLElement | null>, handler: (event: MouseEvent | TouchEvent) => void) {
  React.useEffect(() => {
    const listener = (event: MouseEvent | TouchEvent) => {
      if (!ref.current || ref.current.contains(event.target as Node)) {
        return
      }
      handler(event)
    }

    document.addEventListener("mousedown", listener)
    document.addEventListener("touchstart", listener)

    return () => {
      document.removeEventListener("mousedown", listener)
      document.removeEventListener("touchstart", listener)
    }
  }, [ref, handler])
}

// Button component
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "outline"
  children: React.ReactNode
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2",
          "disabled:pointer-events-none disabled:opacity-50",
          className
        )}
        {...props}
      >
        {children}
      </button>
    )
  }
)
Button.displayName = "Button"

// Types
export interface DropdownOption {
  id: string
  label: string
  icon?: React.ElementType
  color?: string
}

// Icon wrapper with animation
const IconWrapper = ({
  icon: Icon,
  isHovered,
  color,
}: { icon: React.ElementType; isHovered: boolean; color?: string }) => (
  <motion.div 
    className="w-4 h-4 mr-2 relative flex items-center justify-center" 
    initial={false} 
    animate={isHovered ? { scale: 1.2 } : { scale: 1 }}
  >
    <Icon className="w-4 h-4" />
    {isHovered && color && (
      <motion.div
        className="absolute inset-0"
        style={{ color }}
        initial={{ pathLength: 0, opacity: 0 }}
        animate={{ pathLength: 1, opacity: 1 }}
        transition={{ duration: 0.5, ease: "easeInOut" }}
      >
        <Icon className="w-4 h-4" strokeWidth={2} />
      </motion.div>
    )}
  </motion.div>
)

// Animation variants
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      when: "beforeChildren" as const,
      staggerChildren: 0.1,
    },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: -10 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.3,
      ease: [0.25, 0.1, 0.25, 1] as const,
    },
  },
}

interface FluidDropdownProps {
  options: DropdownOption[]
  value?: string
  onChange?: (value: string) => void
  onOptionClick?: (option: DropdownOption) => void
  className?: string
  direction?: "up" | "down"
  triggerLabel?: string
  children?: React.ReactNode
}

/**
 * A fluid dropdown component with smooth animations and hover effects.
 * Optimized for a premium feel.
 */
export function FluidDropdown({ 
  options, 
  value, 
  onChange, 
  onOptionClick,
  className, 
  direction = "down",
  triggerLabel,
  children
}: FluidDropdownProps) {
  const [isOpen, setIsOpen] = React.useState(false)
  const [hoveredOptionId, setHoveredOptionId] = React.useState<string | null>(null)
  const dropdownRef = React.useRef<HTMLDivElement>(null)

  const selectedOption = options.find(o => o.id === value) || options[0]
  const isUp = direction === "up"
  const displayOptions = options

  useClickAway(dropdownRef, () => setIsOpen(false))

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      setIsOpen(false)
    }
  }

  const handleOptionClick = (option: DropdownOption) => {
    if (onChange) onChange(option.id)
    if (onOptionClick) onOptionClick(option)
    setIsOpen(false)
  }

  return (
    <MotionConfig reducedMotion="user">
      <div
        className={cn("relative", className)}
        ref={dropdownRef}
      >
        {children ? (
          <div 
            onClick={() => setIsOpen(!isOpen)} 
            className="cursor-pointer"
            aria-expanded={isOpen}
            aria-haspopup="true"
          >
            {children}
          </div>
        ) : (
          <Button
            onClick={() => setIsOpen(!isOpen)}
            className={cn(
              "w-full justify-between bg-surface-bg border border-outline-variant text-on-surface rounded-lg",
              "hover:border-primary/50",
              "focus:ring-2 focus:ring-primary/20 focus:border-primary",
              "transition-all duration-200 ease-in-out",
              "h-10 px-3",
              isOpen && "border-primary",
            )}
            aria-expanded={isOpen}
            aria-haspopup="true"
          >
            <span className="flex items-center">
              {!triggerLabel && selectedOption.icon && (
                <IconWrapper 
                  icon={selectedOption.icon} 
                  isHovered={false} 
                  color={selectedOption.color} 
                />
              )}
              {triggerLabel || selectedOption.label}
            </span>
            <motion.div
              animate={{ rotate: isOpen ? (isUp ? -180 : 180) : 0 }}
              transition={{ duration: 0.2 }}
              className="flex items-center justify-center w-5 h-5"
            >
              <ChevronDown className="w-4 h-4 text-on-surface-variant" />
            </motion.div>
          </Button>
        )}

        <AnimatePresence>
          {isOpen && (
            <motion.div
              initial={{ opacity: 0, y: isUp ? 4 : -4, scale: 0.95 }}
              animate={{
                opacity: 1,
                y: 0,
                scale: 1,
                transition: {
                  type: "spring",
                  stiffness: 500,
                  damping: 30,
                  mass: 1,
                },
              }}
              exit={{
                opacity: 0,
                y: isUp ? 4 : -4,
                scale: 0.95,
                transition: {
                  duration: 0.15,
                },
              }}
              className={cn(
                "absolute z-50",
                isUp ? "bottom-full mb-2" : "top-full mt-2",
                direction === "down" && "right-0 min-w-[160px]" || "left-0 right-0"
              )}
              onKeyDown={handleKeyDown}
            >
              <motion.div
                className="w-full rounded-xl border border-outline-variant bg-card-bg p-1 shadow-lg overflow-hidden"
                style={{ transformOrigin: isUp ? "bottom" : "top" }}
              >
                <motion.div 
                  className="py-1 relative" 
                  variants={containerVariants} 
                  initial="hidden" 
                  animate="visible"
                >
                  <motion.div
                    layoutId="hover-highlight"
                    className="absolute inset-x-1 bg-surface-bg rounded-lg"
                    animate={{
                      y: displayOptions.findIndex((o) => (hoveredOptionId || (value ? selectedOption.id : null)) === o.id) * 40,
                      height: hoveredOptionId || (value ? selectedOption.id : null) ? 40 : 0,
                      opacity: hoveredOptionId || (value ? selectedOption.id : null) ? 1 : 0,
                    }}
                    transition={{
                      type: "spring",
                      bounce: 0.15,
                      duration: 0.5,
                    }}
                  />
                  {displayOptions.map((option) => (
                    <motion.button
                      key={option.id}
                      onClick={() => handleOptionClick(option)}
                      onHoverStart={() => setHoveredOptionId(option.id)}
                      onHoverEnd={() => setHoveredOptionId(null)}
                      className={cn(
                        "relative flex w-full items-center px-3 py-2.5 text-sm rounded-lg",
                        "transition-colors duration-150",
                        "focus:outline-none",
                        (value && selectedOption.id === option.id) || hoveredOptionId === option.id
                          ? "text-primary font-medium"
                          : "text-on-surface-variant",
                      )}
                      whileTap={{ scale: 0.98 }}
                      variants={itemVariants}
                    >
                      {option.icon && (
                        <IconWrapper
                          icon={option.icon}
                          isHovered={hoveredOptionId === option.id}
                          color={option.color}
                        />
                      )}
                      <span className="relative z-10 text-left truncate">{option.label}</span>
                    </motion.button>
                  ))}
                </motion.div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </MotionConfig>
  )
}
