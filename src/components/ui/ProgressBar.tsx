import { motion } from "framer-motion";

interface ProgressBarProps {
  progress: number;
}

const ProgressBar = ({ progress }: ProgressBarProps) => (
  <div className="relative h-1 bg-gray-100 rounded-full overflow-hidden">
    <motion.div
      className="absolute left-0 top-0 h-full bg-gray-900"
      initial={{ width: 0 }}
      animate={{ width: `${progress}%` }}
      transition={{ duration: 0.8, ease: "easeInOut" }}
    />
  </div>
);

export default ProgressBar;
