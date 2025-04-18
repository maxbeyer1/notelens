import { motion } from "framer-motion";
import { Link } from "@tanstack/react-router";

import { Button } from "@/components/ui/Button";

const Welcome = () => {
  // Subtle fade up animation
  const fadeUp = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 1.2, ease: [0.23, 1, 0.32, 1] }, // Apple-like easing
  };

  // Container for staggered children
  const container = {
    animate: {
      transition: {
        staggerChildren: 0.4,
        delayChildren: 0.6,
      },
    },
  };

  return (
    <motion.div
      className="h-screen w-screen flex flex-col items-center justify-center bg-white"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 1.6, ease: [0.23, 1, 0.32, 1] }}
    >
      {/* Main Content */}
      <motion.div
        className="flex flex-col items-center space-y-16"
        variants={container}
        initial="initial"
        animate="animate"
      >
        {/* App Name */}
        <motion.div variants={fadeUp}>
          <motion.h1
            className="text-5xl font-medium text-gray-900"
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{
              duration: 1.4,
              ease: [0.23, 1, 0.32, 1],
              scale: { duration: 1.6 },
            }}
          >
            NoteLens
          </motion.h1>
        </motion.div>

        {/* Single, Impactful Message */}
        <motion.p variants={fadeUp} className="text-2xl text-gray-500">
          Your notes. Brilliantly searchable.
        </motion.p>

        {/* Action Button */}
        <motion.div
          variants={fadeUp}
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.98 }}
        >
          <Link to="/onboarding/progress">
            <Button
              // bg-[#0066cc] hover:bg-[#0055aa]
              className="px-8 py-6 text-lg bg-gray-900 hover:bg-gray-900/90 text-white rounded-lg 
                       transition-colors duration-200 mt-8"
            >
              Continue
            </Button>
          </Link>
        </motion.div>
      </motion.div>

      {/* Footer */}
      <motion.p
        className="absolute bottom-6 text-sm text-gray-400"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.8, duration: 1.2 }}
      >
        {/* Securely enhances your Apple Notes */}
        v0.1.0
      </motion.p>
    </motion.div>
  );
};

export default Welcome;
