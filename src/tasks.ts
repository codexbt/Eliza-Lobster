import { Task } from "./types";
import { v4 as uuidv4 } from "uuid";

export const tasks: Task[] = [
  {
    id: uuidv4(),
    title: "Tweet about Eliza Lobster",
    description: "Create viral tweet & tag account.",
    reward: 10,
    rewardToken: "USDC"
  }
];