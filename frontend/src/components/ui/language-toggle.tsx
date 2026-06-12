'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from 'antd';
import { Globe, Languages } from 'lucide-react';

interface LanguageToggleProps {
  locale: 'zh' | 'en';
  onToggle: () => void;
}

/**
 * A premium language switcher component with smooth animations.
 * Provides a "wow" factor with spring-based transitions and interactive hover/tap states.
 */
export function LanguageToggle({ locale, onToggle }: LanguageToggleProps) {
  const [isRippling, setIsRippling] = React.useState(false);

  const handleClick = () => {
    setIsRippling(true);
    onToggle();
    setTimeout(() => setIsRippling(false), 600);
  };

  return (
    <motion.div
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      className="relative flex items-center justify-center"
    >
      <Button
        type="text"
        onClick={handleClick}
        className="relative flex items-center justify-center w-10 h-10 p-0 border-none bg-transparent hover:bg-primary/10 transition-all duration-300 overflow-hidden"
        style={{ 
          borderRadius: '12px',
        }}

      >
        {/* Ripple Effect */}
        <AnimatePresence>
          {isRippling && (
            <motion.span
              initial={{ scale: 0, opacity: 0.5 }}
              animate={{ scale: 4, opacity: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.6, ease: "easeOut" }}
              className="absolute inset-0 bg-primary/20 rounded-full pointer-events-none"
            />
          )}
        </AnimatePresence>

        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            key={locale}
            initial={{ opacity: 0, y: 15, rotateX: -90 }}
            animate={{ opacity: 1, y: 0, rotateX: 0 }}
            exit={{ opacity: 0, y: -15, rotateX: 90 }}
            transition={{ 
              type: "spring",
              stiffness: 400,
              damping: 25
            }}
            className="flex items-center justify-center"
          >
            {locale === 'zh' ? (
              <div className="flex items-center justify-center text-primary group relative">
                <Languages size={20} strokeWidth={2.2} />
                <motion.div 
                  layoutId="lang-badge"
                  className="absolute -top-1.5 -right-1.5 flex items-center justify-center bg-primary text-white text-[8px] font-black w-4 h-4 rounded-full ring-2 ring-surface-bg shadow-sm"
                >
                  中
                </motion.div>
              </div>
            ) : (
              <div className="flex items-center justify-center text-primary group relative">
                <Globe size={20} strokeWidth={2.2} />
                <motion.div 
                  layoutId="lang-badge"
                  className="absolute -top-1.5 -right-1.5 flex items-center justify-center bg-primary text-white text-[8px] font-black w-4 h-4 rounded-full ring-2 ring-surface-bg shadow-sm"
                >
                  EN
                </motion.div>
              </div>
            )}
          </motion.div>
        </AnimatePresence>
      </Button>
    </motion.div>
  );
}

