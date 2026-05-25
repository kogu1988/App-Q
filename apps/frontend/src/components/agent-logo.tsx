"use client";

import { useEffect, useState } from "react";

interface AgentLogoProps {
  className?: string;
  size?: number;
  strokeColor?: string;
  innerStrokeColor?: string;
  dotColor?: string;
  animate?: boolean;
}

export default function AgentLogo({
  className = "",
  size = 48,
  strokeColor = "#003c33",
  innerStrokeColor = "#ff7759",
  dotColor = "#003c33",
  animate = false,
}: AgentLogoProps) {
  const [active, setActive] = useState(false);

  useEffect(() => {
    // Delay slightly to trigger smooth drawing animation after mount
    const timer = setTimeout(() => setActive(true), 100);
    return () => clearTimeout(timer);
  }, []);

  return (
    <svg
      viewBox="-100 -100 200 200"
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      className={`agent-animated ${active ? "active" : ""} ${animate ? "agent-thinking-active" : ""} ${className}`}
      style={{ overflow: "visible" }}
    >
      <defs>
        <style>
          {`
            @keyframes pulse-anim{0%,to{opacity:1;transform:scale(1)}50%{opacity:.5;transform:scale(.85)}}
            
            @keyframes draw-loop-1 {
              0%, 100% { stroke-dashoffset: 178.96920776367188px; }
              50% { stroke-dashoffset: 0; }
            }
            @keyframes draw-loop-2 {
              0%, 100% { stroke-dashoffset: 473.23889803846896px; }
              50% { stroke-dashoffset: 0; }
            }
            @keyframes draw-loop-3 {
              0%, 100% { stroke-dashoffset: 89.96459430051421px; }
              50% { stroke-dashoffset: 0; }
            }
            @keyframes draw-loop-4 {
              0%, 100% { stroke-dashoffset: 27.132741228718345px; }
              50% { stroke-dashoffset: 0; }
            }
            @keyframes think-glow {
              0%, 100% { filter: drop-shadow(0 0 2px rgba(255, 119, 89, 0.2)); opacity: 0.85; }
              50% { filter: drop-shadow(0 0 12px rgba(255, 119, 89, 0.65)); opacity: 1; }
            }

            .agent-thinking-active {
              animation: think-glow 3s infinite ease-in-out;
            }
            .agent-thinking-active .svg-elem-1 {
              animation: draw-loop-1 3s infinite ease-in-out !important;
            }
            .agent-thinking-active .svg-elem-2 {
              animation: draw-loop-2 3s infinite ease-in-out !important;
            }
            .agent-thinking-active .svg-elem-3 {
              animation: draw-loop-3 3s infinite ease-in-out !important;
            }
            .agent-thinking-active .svg-elem-4 {
              animation: draw-loop-4 3s infinite ease-in-out !important;
            }
          `}
        </style>
        <path
          id="agent-leaf"
          d="M0-40c22 25 22 55 0 80-22-25-22-55 0-80"
          className="svg-elem-1"
        />
      </defs>
      <circle
        r="75"
        fill="none"
        stroke={strokeColor}
        strokeWidth="5"
        className="svg-elem-2"
      />
      <g fill="none" strokeLinecap="round" strokeLinejoin="round">
        {/* Outer leaf ring */}
        <g stroke="#1863dc" strokeWidth="5" opacity=".4">
          <use href="#agent-leaf" transform="matrix(.8 0 0 .8 0 -24)" />
          <use href="#agent-leaf" transform="rotate(45 28.97 12)scale(.8)" />
          <use href="#agent-leaf" transform="matrix(0 .8 -.8 0 24 0)" />
          <use href="#agent-leaf" transform="rotate(135 4.97 12)scale(.8)" />
          <use href="#agent-leaf" transform="matrix(-.8 0 0 -.8 0 24)" />
          <use href="#agent-leaf" transform="rotate(225 -4.97 12)scale(.8)" />
          <use href="#agent-leaf" transform="matrix(0 -.8 .8 0 -24 0)" />
          <use href="#agent-leaf" transform="rotate(-45 -28.97 12)scale(.8)" />
        </g>
        {/* Inner leaf ring */}
        <g stroke={innerStrokeColor} strokeWidth="1.5" opacity=".9">
          <use href="#agent-leaf" transform="rotate(22.5 30.164 6)scale(.55)" />
          <use href="#agent-leaf" transform="rotate(67.5 8.98 6)scale(.55)" />
          <use href="#agent-leaf" transform="rotate(112.5 4.01 6)scale(.55)" />
          <use href="#agent-leaf" transform="rotate(157.5 1.193 6)scale(.55)" />
          <use href="#agent-leaf" transform="rotate(202.5 -1.193 6)scale(.55)" />
          <use href="#agent-leaf" transform="rotate(247.5 -4.01 6)scale(.55)" />
          <use href="#agent-leaf" transform="rotate(-67.5 -8.98 6)scale(.55)" />
          <use href="#agent-leaf" transform="rotate(-22.5 -30.164 6)scale(.55)" />
        </g>
        <circle r="14" stroke={strokeColor} strokeWidth="3" className="svg-elem-3" />
        <circle r="4" fill={dotColor} className="svg-elem-4" />
      </g>
    </svg>
  );
}
