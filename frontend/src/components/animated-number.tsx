"use client";

import { useEffect, useRef } from "react";
import { animate, useMotionValue, useMotionValueEvent } from "framer-motion";
import { useState } from "react";

interface AnimatedNumberProps {
  value: number; // 0-100
  decimals?: number;
  suffix?: string;
  className?: string;
  durationSec?: number;
}

export function AnimatedNumber({ value, decimals = 0, suffix = "", className, durationSec = 1.1 }: AnimatedNumberProps) {
  const motionVal = useMotionValue(0);
  const [display, setDisplay] = useState("0");
  const firstRun = useRef(true);

  useMotionValueEvent(motionVal, "change", (latest) => setDisplay(latest.toFixed(decimals)));

  useEffect(() => {
    const controls = animate(motionVal, value, {
      duration: firstRun.current ? durationSec : durationSec * 0.7,
      ease: [0.16, 1, 0.3, 1],
    });
    firstRun.current = false;
    return () => controls.stop();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  return (
    <span className={className}>
      {display}
      {suffix}
    </span>
  );
}
