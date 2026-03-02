export interface Task {
  id: string;
  title: string;
  description: string;
  reward: number;
  rewardToken: "SOL" | "USDC";
}