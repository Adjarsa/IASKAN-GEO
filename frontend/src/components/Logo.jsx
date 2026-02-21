import React from "react";

const Logo = ({ size = "default", showText = true }) => {
  const sizes = {
    small: { icon: 32, text: "text-lg" },
    default: { icon: 40, text: "text-xl" },
    large: { icon: 48, text: "text-2xl" }
  };

  const { icon, text } = sizes[size] || sizes.default;

  return (
    <div className="flex items-center gap-3">
      <div 
        className="relative flex items-center justify-center rounded-xl bg-gradient-to-br from-violet-600 to-cyan-500 shadow-lg"
        style={{ width: icon, height: icon }}
      >
        {/* Stylized "i" letter */}
        <svg 
          viewBox="0 0 24 24" 
          fill="none" 
          className="w-6 h-6"
          style={{ width: icon * 0.6, height: icon * 0.6 }}
        >
          {/* Dot */}
          <circle cx="12" cy="6" r="2.5" fill="white" />
          {/* Body with AI spark */}
          <path 
            d="M12 10.5V18.5" 
            stroke="white" 
            strokeWidth="3" 
            strokeLinecap="round"
          />
          {/* Spark lines */}
          <path 
            d="M16 12L18 10M16 16L19 17M8 12L6 10M8 16L5 17" 
            stroke="white" 
            strokeWidth="1.5" 
            strokeLinecap="round"
            opacity="0.7"
          />
        </svg>
        
        {/* Glow effect */}
        <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-violet-400 to-cyan-400 opacity-0 group-hover:opacity-30 transition-opacity blur-xl" />
      </div>
      
      {showText && (
        <span className={`font-bold ${text} bg-gradient-to-r from-violet-600 to-cyan-600 bg-clip-text text-transparent`}>
          IAskan
        </span>
      )}
    </div>
  );
};

export default Logo;
