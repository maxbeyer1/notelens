import { AnimatePresence } from "framer-motion";

import ProgressScreen from "@/components/onboarding/ProgressScreen";

const App = () => {
  // const [step, setStep] = useState("welcome");

  return (
    <AnimatePresence mode="wait">
      {/* {step === "welcome" && <Welcome onContinue={() => setStep("progress")} />} */}
      <ProgressScreen />
    </AnimatePresence>
  );
};

export default App;
