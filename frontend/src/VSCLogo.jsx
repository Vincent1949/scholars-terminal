// VSC Animated Logo Component for Scholar's Terminal
// 64x64 animated SVG with rotating rings and pulsing core

export default function VSCLogo({ size = 64 }) {
  return (
    <svg 
      className="vsc-logo" 
      width={size} 
      height={size} 
      viewBox="0 0 600 600" 
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Background */}
      <rect width="600" height="600" fill="#0a0e17"/>
      
      {/* Rotating orbital structure */}
      <g className="vsc-rings">
        {/* Orbital rings */}
        <circle cx="300" cy="300" r="200" stroke="#2d5ef8" strokeWidth="2" fill="none"/>
        <circle cx="300" cy="300" r="162.5" stroke="#2d5ef8" strokeWidth="1.5" fill="none"/>
        <circle cx="300" cy="300" r="125" stroke="#1a3aa8" strokeWidth="1" fill="none"/>
        
        {/* Cross connections */}
        <line x1="300" y1="137.5" x2="300" y2="462.5" stroke="#2d5ef8" strokeWidth="1.5"/>
        <line x1="137.5" y1="300" x2="462.5" y2="300" stroke="#2d5ef8" strokeWidth="1.5"/>
        <line x1="185" y1="185" x2="415" y2="415" stroke="#2d5ef8" strokeWidth="1.5"/>
        <line x1="415" y1="185" x2="185" y2="415" stroke="#2d5ef8" strokeWidth="1.5"/>
        
        {/* Orbital nodes */}
        <circle cx="300" cy="137.5" r="8" fill="#4dd4ff" stroke="#f2f6ff" strokeWidth="2"/>
        <circle cx="415" cy="185" r="8" fill="#4dd4ff" stroke="#f2f6ff" strokeWidth="2"/>
        <circle cx="462.5" cy="300" r="8" fill="#4dd4ff" stroke="#f2f6ff" strokeWidth="2"/>
        <circle cx="415" cy="415" r="8" fill="#4dd4ff" stroke="#f2f6ff" strokeWidth="2"/>
        <circle cx="300" cy="462.5" r="8" fill="#4dd4ff" stroke="#f2f6ff" strokeWidth="2"/>
        <circle cx="185" cy="415" r="8" fill="#4dd4ff" stroke="#f2f6ff" strokeWidth="2"/>
        <circle cx="137.5" cy="300" r="8" fill="#4dd4ff" stroke="#f2f6ff" strokeWidth="2"/>
        <circle cx="185" cy="185" r="8" fill="#4dd4ff" stroke="#f2f6ff" strokeWidth="2"/>
      </g>
      
      {/* Pulsing core */}
      <g className="vsc-core">
        <circle cx="300" cy="300" r="60" fill="#2d5ef8" opacity="0.3"/>
        <circle cx="300" cy="300" r="45" fill="#2d5ef8" stroke="#f2f6ff" strokeWidth="3"/>
        <circle cx="300" cy="300" r="12" fill="#f2f6ff" stroke="#4dd4ff" strokeWidth="2"/>
        <circle cx="300" cy="300" r="4" fill="#4dd4ff"/>
      </g>
    </svg>
  );
}
