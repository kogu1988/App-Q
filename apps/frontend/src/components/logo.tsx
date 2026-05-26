"use client";

import { useEffect, useState } from "react";

interface LogoProps {
  className?: string;
  size?: number;
  strokeColor?: string;
}

export default function Logo({ className = "", size = 32, strokeColor = "currentColor" }: LogoProps) {
  const [active, setActive] = useState(false);

  useEffect(() => {
    // Delay slightly to trigger smooth animation after mount
    const timer = setTimeout(() => setActive(true), 100);
    return () => clearTimeout(timer);
  }, []);

  return (
    <svg
      viewBox="0 0 1000 1000"
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      className={`logo-animated overflow-visible ${active ? "active" : ""} ${className}`}
    >
      <defs>
        <path
          id="logo-path-a"
          className="svg-elem-1"
          d="M500 50c100 0 300 50 400 100s100 250 0 300-300 100-400 100-300-50-400-100-100-250 0-300S400 50 500 50Z"
          fill="none"
          stroke={strokeColor}
          strokeWidth="4"
        />
      </defs>
      <g transform="translate(500 500)">
        <use href="#logo-path-a" transform="translate(-500 -300)" />
        <use href="#logo-path-a" transform="rotate(10 1964.508 -2707.513)" />
        <use href="#logo-path-a" transform="rotate(20 1100.692 -1267.82)" />
        <use href="#logo-path-a" transform="rotate(30 809.808 -783.013)" />
        <use href="#logo-path-a" transform="rotate(40 662.122 -536.87)" />
        <use href="#logo-path-a" transform="rotate(50 571.676 -386.127)" />
        <use href="#logo-path-a" transform="rotate(60 509.808 -283.013)" />
        <use href="#logo-path-a" transform="rotate(70 464.222 -207.037)" />
        <use href="#logo-path-a" transform="rotate(80 428.763 -147.938)" />
        <use href="#logo-path-a" transform="rotate(90 400 -100)" />
        <use href="#logo-path-a" transform="rotate(100 375.865 -59.775)" />
        <use href="#logo-path-a" transform="rotate(110 355.031 -25.052)" />
        <use href="#logo-path-a" transform="rotate(120 336.603 5.662)" />
        <use href="#logo-path-a" transform="rotate(130 319.946 33.423)" />
        <use href="#logo-path-a" transform="rotate(140 304.596 59.007)" />
        <use href="#logo-path-a" transform="rotate(150 290.192 83.013)" />
        <use href="#logo-path-a" transform="rotate(160 276.449 105.918)" />
        <use href="#logo-path-a" transform="rotate(170 263.123 128.128)" />
        <circle className="svg-elem-2" r="120" fill="none" stroke={strokeColor} strokeWidth="4" />
        <circle className="svg-elem-3" r="80" fill="none" stroke={strokeColor} strokeWidth="4" />
      </g>
    </svg>
  );
}
