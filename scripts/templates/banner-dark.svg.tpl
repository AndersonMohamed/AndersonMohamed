<svg xmlns="http://www.w3.org/2000/svg" width="900" height="300" viewBox="0 0 900 300" role="img" aria-label="{{NAME}} — banner">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e1b4b"/>
    </linearGradient>
    <radialGradient id="glow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#8b5cf6" stop-opacity="0.25"/>
      <stop offset="100%" stop-color="#8b5cf6" stop-opacity="0"/>
    </radialGradient>
    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
      <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#ffffff" stroke-opacity="0.04" stroke-width="1"/>
    </pattern>
    <linearGradient id="nameGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#8b5cf6"/>
      <stop offset="50%" stop-color="#06b6d4"/>
      <stop offset="100%" stop-color="#8b5cf6"/>
      <animate attributeName="x1" values="0%;100%;0%" dur="10s" repeatCount="indefinite"/>
      <animate attributeName="x2" values="100%;0%;100%" dur="10s" repeatCount="indefinite"/>
    </linearGradient>
  </defs>

  <rect width="900" height="300" fill="url(#bg)"/>
  <rect width="900" height="300" fill="url(#glow)"/>
  <rect width="900" height="300" fill="url(#grid)"/>

  <!-- Partículas flutuantes -->
  <circle cx="120" cy="60" r="3" fill="#8b5cf6">
    <animate attributeName="cy" values="60;95;60" dur="6s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0.8;0.3;0.8" dur="5s" repeatCount="indefinite"/>
  </circle>
  <circle cx="300" cy="225" r="2" fill="#06b6d4">
    <animate attributeName="cy" values="225;185;225" dur="7s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0.6;0.2;0.6" dur="6s" repeatCount="indefinite"/>
  </circle>
  <circle cx="520" cy="80" r="2.5" fill="#8b5cf6">
    <animate attributeName="cy" values="80;120;80" dur="5s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0.7;0.25;0.7" dur="4.5s" repeatCount="indefinite"/>
  </circle>
  <circle cx="680" cy="210" r="3" fill="#06b6d4">
    <animate attributeName="cy" values="210;170;210" dur="8s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0.75;0.3;0.75" dur="5.5s" repeatCount="indefinite"/>
  </circle>
  <circle cx="790" cy="70" r="2" fill="#8b5cf6">
    <animate attributeName="cy" values="70;105;70" dur="6.5s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0.5;0.15;0.5" dur="7s" repeatCount="indefinite"/>
  </circle>

  <!-- Chaves decorativas -->
  <text x="90" y="150" text-anchor="middle" font-family="Consolas, monospace" font-size="60" fill="#8b5cf6" fill-opacity="0.35">{</text>
  <text x="810" y="150" text-anchor="middle" font-family="Consolas, monospace" font-size="60" fill="#8b5cf6" fill-opacity="0.35">}</text>

  <!-- Nome -->
  <text x="450" y="140" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="64" font-weight="700" fill="url(#nameGrad)">{{NAME}}</text>

  <!-- Subtítulo -->
  <text x="450" y="185" text-anchor="middle" font-family="Consolas, monospace" font-size="20" fill="#94a3b8">{{SUBTITLE}}</text>

  <!-- Cursor piscando -->
  <rect x="{{CURSOR_X}}" y="172" width="12" height="22" fill="#06b6d4">
    <animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/>
  </rect>

  <!-- Linha terminal -->
  <text x="450" y="240" text-anchor="middle" font-family="Consolas, monospace" font-size="14" fill="#64748b">{{WHOAMI}}</text>
</svg>