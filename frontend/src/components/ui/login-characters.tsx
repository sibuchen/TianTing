"use client";

import { useState, useEffect, useRef } from "react";
import { Sparkles } from "lucide-react";

interface PupilProps {
  size?: number;
  maxDistance?: number;
  pupilColor?: string;
  forceLookX?: number;
  forceLookY?: number;
  mouseX: number;
  mouseY: number;
}

const Pupil = ({ 
  size = 12, 
  maxDistance = 5,
  pupilColor = "black",
  forceLookX,
  forceLookY,
  mouseX,
  mouseY
}: PupilProps) => {
  const pupilRef = useRef<HTMLDivElement>(null);

  const calculatePupilPosition = () => {
    if (!pupilRef.current) return { x: 0, y: 0 };

    if (forceLookX !== undefined && forceLookY !== undefined) {
      return { x: forceLookX, y: forceLookY };
    }

    const pupil = pupilRef.current.getBoundingClientRect();
    const pupilCenterX = pupil.left + pupil.width / 2;
    const pupilCenterY = pupil.top + pupil.height / 2;

    const deltaX = mouseX - pupilCenterX;
    const deltaY = mouseY - pupilCenterY;
    const distance = Math.min(Math.sqrt(deltaX ** 2 + deltaY ** 2), maxDistance);

    const angle = Math.atan2(deltaY, deltaX);
    const x = Math.cos(angle) * distance;
    const y = Math.sin(angle) * distance;

    return { x, y };
  };

  const pupilPosition = calculatePupilPosition();

  return (
    <div
      ref={pupilRef}
      className="rounded-full"
      style={{
        width: `${size}px`,
        height: `${size}px`,
        backgroundColor: pupilColor,
        transform: `translate(${pupilPosition.x}px, ${pupilPosition.y}px)`,
        transition: 'transform 0.1s ease-out',
      }}
    />
  );
};

interface EyeBallProps {
  size?: number;
  pupilSize?: number;
  maxDistance?: number;
  eyeColor?: string;
  pupilColor?: string;
  isBlinking?: boolean;
  forceLookX?: number;
  forceLookY?: number;
  mouseX: number;
  mouseY: number;
}

const EyeBall = ({ 
  size = 48, 
  pupilSize = 16, 
  maxDistance = 10,
  eyeColor = "white",
  pupilColor = "black",
  isBlinking = false,
  forceLookX,
  forceLookY,
  mouseX,
  mouseY
}: EyeBallProps) => {
  const eyeRef = useRef<HTMLDivElement>(null);

  const calculatePupilPosition = () => {
    if (!eyeRef.current) return { x: 0, y: 0 };

    if (forceLookX !== undefined && forceLookY !== undefined) {
      return { x: forceLookX, y: forceLookY };
    }

    const eye = eyeRef.current.getBoundingClientRect();
    const eyeCenterX = eye.left + eye.width / 2;
    const eyeCenterY = eye.top + eye.height / 2;

    const deltaX = mouseX - eyeCenterX;
    const deltaY = mouseY - eyeCenterY;
    const distance = Math.min(Math.sqrt(deltaX ** 2 + deltaY ** 2), maxDistance);

    const angle = Math.atan2(deltaY, deltaX);
    const x = Math.cos(angle) * distance;
    const y = Math.sin(angle) * distance;

    return { x, y };
  };

  const pupilPosition = calculatePupilPosition();

  return (
    <div
      ref={eyeRef}
      className="rounded-full flex items-center justify-center transition-all duration-150"
      style={{
        width: `${size}px`,
        height: isBlinking ? '2px' : `${size}px`,
        backgroundColor: eyeColor,
        overflow: 'hidden',
      }}
    >
      {!isBlinking && (
        <div
          className="rounded-full"
          style={{
            width: `${pupilSize}px`,
            height: `${pupilSize}px`,
            backgroundColor: pupilColor,
            transform: `translate(${pupilPosition.x}px, ${pupilPosition.y}px)`,
            transition: 'transform 0.1s ease-out',
          }}
        />
      )}
    </div>
  );
};

interface LoginCharactersProps {
  isTyping: boolean;
  passwordLength: number;
  showPassword: boolean;
  brandName?: string;
}

export function LoginCharacters({ isTyping, passwordLength, showPassword, brandName = "TianTing" }: LoginCharactersProps) {
  const [mouseX, setMouseX] = useState<number>(0);
  const [mouseY, setMouseY] = useState<number>(0);
  const [isPurpleBlinking, setIsPurpleBlinking] = useState(false);
  const [isBlackBlinking, setIsBlackBlinking] = useState(false);
  const [isLookingAtEachOther, setIsLookingAtEachOther] = useState(false);
  const [isPurplePeeking, setIsPurplePeeking] = useState(false);
  
  const purpleRef = useRef<HTMLDivElement>(null);
  const blackRef = useRef<HTMLDivElement>(null);
  const yellowRef = useRef<HTMLDivElement>(null);
  const orangeRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMouseX(e.clientX);
      setMouseY(e.clientY);
    };

    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  // Blinking effects
  useEffect(() => {
    const scheduleBlink = (setBlink: (val: boolean) => void) => {
      const timeout = setTimeout(() => {
        setBlink(true);
        setTimeout(() => {
          setBlink(false);
          scheduleBlink(setBlink);
        }, 150);
      }, Math.random() * 4000 + 3000);
      return timeout;
    };

    const purpleTimeout = scheduleBlink(setIsPurpleBlinking);
    const blackTimeout = scheduleBlink(setIsBlackBlinking);
    return () => {
      clearTimeout(purpleTimeout);
      clearTimeout(blackTimeout);
    };
  }, []);

  // Looking at each other logic
  useEffect(() => {
    if (isTyping) {
      setIsLookingAtEachOther(true);
      const timer = setTimeout(() => setIsLookingAtEachOther(false), 800);
      return () => clearTimeout(timer);
    }
  }, [isTyping]);

  // Peeking logic
  useEffect(() => {
    if (passwordLength > 0 && !showPassword) {
      const schedulePeek = () => {
        const timeout = setTimeout(() => {
          setIsPurplePeeking(true);
          setTimeout(() => setIsPurplePeeking(false), 800);
          schedulePeek();
        }, Math.random() * 3000 + 2000);
        return timeout;
      };
      const timeout = schedulePeek();
      return () => clearTimeout(timeout);
    } else {
      setIsPurplePeeking(false);
    }
  }, [passwordLength, showPassword]);

  const calculatePosition = (ref: React.RefObject<HTMLDivElement | null>) => {
    if (!ref.current) return { faceX: 0, faceY: 0, bodySkew: 0 };
    const rect = ref.current.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 3;
    const deltaX = mouseX - centerX;
    const deltaY = mouseY - centerY;
    const faceX = Math.max(-15, Math.min(15, deltaX / 20));
    const faceY = Math.max(-10, Math.min(10, deltaY / 30));
    const bodySkew = Math.max(-6, Math.min(6, -deltaX / 120));
    return { faceX, faceY, bodySkew };
  };

  const purplePos = calculatePosition(purpleRef);
  const blackPos = calculatePosition(blackRef);
  const yellowPos = calculatePosition(yellowRef);
  const orangePos = calculatePosition(orangeRef);

  return (
    <div className="relative flex flex-col items-center justify-center h-full w-full overflow-hidden min-h-[500px]">
      <div className="relative z-20 flex items-end justify-center h-full w-full">
        <div className="relative" style={{ width: '550px', height: '400px' }}>
          {/* Purple character */}
          <div 
            ref={purpleRef}
            className="absolute bottom-0 transition-all duration-700 ease-in-out"
            style={{
              left: '70px',
              width: '180px',
              height: (isTyping || (passwordLength > 0 && !showPassword)) ? '440px' : '400px',
              backgroundColor: '#6C3FF5',
              borderRadius: '10px 10px 0 0',
              zIndex: 1,
              transform: (passwordLength > 0 && showPassword)
                ? `skewX(0deg)`
                : (isTyping || (passwordLength > 0 && !showPassword))
                  ? `skewX(${(purplePos.bodySkew || 0) - 12}deg) translateX(40px)` 
                  : `skewX(${purplePos.bodySkew || 0}deg)`,
              transformOrigin: 'bottom center',
            }}
          >
            <div 
              className="absolute flex gap-8 transition-all duration-700 ease-in-out"
              style={{
                left: (passwordLength > 0 && !showPassword) ? `${20}px` : isLookingAtEachOther ? `${55}px` : `${45 + purplePos.faceX}px`,
                top: (passwordLength > 0 && !showPassword) ? `${35}px` : isLookingAtEachOther ? `${65}px` : `${40 + purplePos.faceY}px`,
              }}
            >
              <EyeBall 
                size={18} pupilSize={7} maxDistance={5} eyeColor="white" pupilColor="#2D2D2D" 
                isBlinking={isPurpleBlinking} mouseX={mouseX} mouseY={mouseY}
                forceLookX={(passwordLength > 0 && !showPassword) ? (isPurplePeeking ? 4 : -4) : isLookingAtEachOther ? 3 : undefined}
                forceLookY={(passwordLength > 0 && !showPassword) ? (isPurplePeeking ? 5 : -4) : isLookingAtEachOther ? 4 : undefined}
              />
              <EyeBall 
                size={18} pupilSize={7} maxDistance={5} eyeColor="white" pupilColor="#2D2D2D" 
                isBlinking={isPurpleBlinking} mouseX={mouseX} mouseY={mouseY}
                forceLookX={(passwordLength > 0 && !showPassword) ? (isPurplePeeking ? 4 : -4) : isLookingAtEachOther ? 3 : undefined}
                forceLookY={(passwordLength > 0 && !showPassword) ? (isPurplePeeking ? 5 : -4) : isLookingAtEachOther ? 4 : undefined}
              />
            </div>
          </div>

          {/* Black character */}
          <div 
            ref={blackRef}
            className="absolute bottom-0 transition-all duration-700 ease-in-out"
            style={{
              left: '240px',
              width: '120px',
              height: '310px',
              backgroundColor: '#2D2D2D',
              borderRadius: '8px 8px 0 0',
              zIndex: 2,
              transform: (passwordLength > 0 && !showPassword)
                ? `skewX(0deg)`
                : isLookingAtEachOther
                  ? `skewX(${(blackPos.bodySkew || 0) * 1.5 + 10}deg) translateX(20px)`
                  : (isTyping || (passwordLength > 0 && showPassword))
                    ? `skewX(${(blackPos.bodySkew || 0) * 1.5}deg)` 
                    : `skewX(${blackPos.bodySkew || 0}deg)`,
              transformOrigin: 'bottom center',
            }}
          >
            <div 
              className="absolute flex gap-6 transition-all duration-700 ease-in-out"
              style={{
                left: (passwordLength > 0 && !showPassword) ? `${10}px` : isLookingAtEachOther ? `${32}px` : `${26 + blackPos.faceX}px`,
                top: (passwordLength > 0 && !showPassword) ? `${28}px` : isLookingAtEachOther ? `${12}px` : `${32 + blackPos.faceY}px`,
              }}
            >
              <EyeBall 
                size={16} pupilSize={6} maxDistance={4} eyeColor="white" pupilColor="#2D2D2D" 
                isBlinking={isBlackBlinking} mouseX={mouseX} mouseY={mouseY}
                forceLookX={(passwordLength > 0 && !showPassword) ? -4 : isLookingAtEachOther ? 0 : undefined}
                forceLookY={(passwordLength > 0 && !showPassword) ? -4 : isLookingAtEachOther ? -4 : undefined}
              />
              <EyeBall 
                size={16} pupilSize={6} maxDistance={4} eyeColor="white" pupilColor="#2D2D2D" 
                isBlinking={isBlackBlinking} mouseX={mouseX} mouseY={mouseY}
                forceLookX={(passwordLength > 0 && !showPassword) ? -4 : isLookingAtEachOther ? 0 : undefined}
                forceLookY={(passwordLength > 0 && !showPassword) ? -4 : isLookingAtEachOther ? -4 : undefined}
              />
            </div>
          </div>

          {/* Orange character */}
          <div 
            ref={orangeRef}
            className="absolute bottom-0 transition-all duration-700 ease-in-out"
            style={{
              left: '0px',
              width: '240px',
              height: '200px',
              zIndex: 3,
              backgroundColor: '#FF9B6B',
              borderRadius: '120px 120px 0 0',
              transform: (passwordLength > 0 && !showPassword) ? `skewX(0deg)` : `skewX(${orangePos.bodySkew || 0}deg)`,
              transformOrigin: 'bottom center',
            }}
          >
            <div 
              className="absolute flex gap-8 transition-all duration-200 ease-out"
              style={{
                left: (passwordLength > 0 && !showPassword) ? `${50}px` : `${82 + (orangePos.faceX || 0)}px`,
                top: (passwordLength > 0 && !showPassword) ? `${85}px` : `${90 + (orangePos.faceY || 0)}px`,
              }}
            >
              <Pupil size={12} maxDistance={5} pupilColor="#2D2D2D" mouseX={mouseX} mouseY={mouseY} forceLookX={(passwordLength > 0 && !showPassword) ? -5 : undefined} forceLookY={(passwordLength > 0 && !showPassword) ? -4 : undefined} />
              <Pupil size={12} maxDistance={5} pupilColor="#2D2D2D" mouseX={mouseX} mouseY={mouseY} forceLookX={(passwordLength > 0 && !showPassword) ? -5 : undefined} forceLookY={(passwordLength > 0 && !showPassword) ? -4 : undefined} />
            </div>
          </div>

          {/* Yellow character */}
          <div 
            ref={yellowRef}
            className="absolute bottom-0 transition-all duration-700 ease-in-out"
            style={{
              left: '310px',
              width: '140px',
              height: '230px',
              backgroundColor: '#E8D754',
              borderRadius: '70px 70px 0 0',
              zIndex: 4,
              transform: (passwordLength > 0 && !showPassword) ? `skewX(0deg)` : `skewX(${yellowPos.bodySkew || 0}deg)`,
              transformOrigin: 'bottom center',
            }}
          >
            <div 
              className="absolute flex gap-6 transition-all duration-200 ease-out"
              style={{
                left: (passwordLength > 0 && !showPassword) ? `${20}px` : `${52 + (yellowPos.faceX || 0)}px`,
                top: (passwordLength > 0 && !showPassword) ? `${35}px` : `${40 + (yellowPos.faceY || 0)}px`,
              }}
            >
              <Pupil size={12} maxDistance={5} pupilColor="#2D2D2D" mouseX={mouseX} mouseY={mouseY} forceLookX={(passwordLength > 0 && !showPassword) ? -5 : undefined} forceLookY={(passwordLength > 0 && !showPassword) ? -4 : undefined} />
              <Pupil size={12} maxDistance={5} pupilColor="#2D2D2D" mouseX={mouseX} mouseY={mouseY} forceLookX={(passwordLength > 0 && !showPassword) ? -5 : undefined} forceLookY={(passwordLength > 0 && !showPassword) ? -4 : undefined} />
            </div>
            <div 
              className="absolute w-20 h-[4px] bg-[#2D2D2D] rounded-full transition-all duration-200 ease-out"
              style={{
                left: (passwordLength > 0 && !showPassword) ? `${10}px` : `${40 + (yellowPos.faceX || 0)}px`,
                top: (passwordLength > 0 && !showPassword) ? `${88}px` : `${88 + (yellowPos.faceY || 0)}px`,
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
