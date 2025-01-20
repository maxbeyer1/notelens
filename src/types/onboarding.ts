export type Stage = {
  id: number;
  title: string;
  description: string;
  status: "waiting" | "in-progress" | "completed";
};
