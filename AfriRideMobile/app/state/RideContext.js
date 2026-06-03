import React, { createContext, useContext, useState } from "react";

export const RideContext = createContext(null);

export function RideProvider({ children }) {
  const [currentRide, setCurrentRide] = useState(null);
  const [rideHistory, setRideHistory] = useState([]);

  return (
    <RideContext.Provider
      value={{
        currentRide,
        setCurrentRide,
        rideHistory,
        setRideHistory,
        activeRide: currentRide,
        setActiveRide: setCurrentRide,
      }}
    >
      {children}
    </RideContext.Provider>
  );
}

export function useRide() {
  return useContext(RideContext);
}
