// src/components/CosmicBackground.tsx
import React from 'react';

const CosmicBackground: React.FC = () => {
  return (
    <div className="fixed inset-0 z-0">
      <div className="absolute inset-0 bg-gradient-to-b from-space-blue via-deep-space to-cosmic-black"></div>
      <div className="absolute inset-0 opacity-30">
        {/* Add any additional cosmic effects here */}
      </div>
    </div>
  );
};

export default CosmicBackground;