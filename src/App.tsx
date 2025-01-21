import React, { useState } from "react";
import { AnimatePresence } from "framer-motion";

import Welcome from "@/components/onboarding/Welcome";
import ProgressScreen from "@/components/onboarding/ProgressScreen";

const App = () => {
  const [step, setStep] = useState("welcome");

  return (
    <AnimatePresence mode="wait">
      {/* {step === "welcome" && <Welcome onContinue={() => setStep("progress")} />} */}
      {step === "progress" && <ProgressScreen />}
    </AnimatePresence>
  );
};

export default App;
