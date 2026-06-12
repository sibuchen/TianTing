'use client';

import React, { useRef, useEffect, useState } from 'react';
import './SlidingSwitch.css';

export interface SlidingSwitchOption<T extends string> {
  label: string;
  value: T;
  icon?: string;
}

interface SlidingSwitchProps<T extends string> {
  value: T;
  onChange: (value: T) => void;
  options: SlidingSwitchOption<T>[];
  className?: string;
}

export function SlidingSwitch<T extends string>({ 
  value, 
  onChange, 
  options,
  className = "" 
}: SlidingSwitchProps<T>) {
  const containerRef = useRef<HTMLDivElement>(null);
  const itemsRef = useRef<(HTMLDivElement | null)[]>([]);
  const [sliderStyle, setSliderStyle] = useState<React.CSSProperties>({});

  const updateSlider = React.useCallback(() => {
    const activeIndex = options.findIndex(opt => opt.value === value);
    const activeItem = itemsRef.current[activeIndex];
    
    if (activeItem && containerRef.current) {
      const { offsetLeft, offsetWidth } = activeItem;
      setSliderStyle({
        '--slider-left': `${offsetLeft}px`,
        '--slider-width': `${offsetWidth}px`,
      } as React.CSSProperties);
    }
  }, [value, options]);

  useEffect(() => {
    // Initial update
    updateSlider();

    // Update on resize
    const resizeObserver = new ResizeObserver(() => {
      updateSlider();
    });

    if (containerRef.current) {
      resizeObserver.observe(containerRef.current);
    }

    return () => resizeObserver.disconnect();
  }, [updateSlider]);

  return (
    <div 
      ref={containerRef}
      className={`sliding-switch ${className}`}
      style={sliderStyle}
    >
      {options.map((option, index) => (
        <div
          key={option.value}
          ref={el => { itemsRef.current[index] = el; }}
          className={`switch-option ${value === option.value ? 'active' : ''}`}
          onClick={() => onChange(option.value)}
        >
          {option.icon && (
            <span className="material-symbols-outlined text-[18px] mr-2">
              {option.icon}
            </span>
          )}
          {option.label}
        </div>
      ))}
    </div>
  );
}
