import express from "express";
import { tasks } from "./tasks";
import { sendSol } from "./solanaPayout";

const router = express.Router();

router.post("/ask", (req, res) => {
  const randomTask = tasks[Math.floor(Math.random() * tasks.length)];
  res.json(randomTask);
});

router.post("/complete", async (req, res) => {
  const { wallet, reward } = req.body;
  try {
    const tx = await sendSol(wallet, reward);
    res.json({ status: "paid", tx });
  } catch {
    res.status(500).json({ error: "Payout failed" });
  }
});

export default router;