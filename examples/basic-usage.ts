/**
 * Basic Usage Examples for Eliza Lobster API
 * 
 * This file demonstrates common patterns for interacting with
 * the Eliza Lobster bounty system.
 */

const API_BASE = 'http://localhost:3000/api';

// Example 1: Fetch all available tasks
async function getAllTasks() {
  const response = await fetch(`${API_BASE}/tasks`);
  const data = await response.json();
  
  if (data.success) {
    console.log('Available tasks:', data.data);
    data.data.forEach((task: any) => {
      console.log(`- ${task.title} (${task.category}) - ${task.reward} ${task.rewardToken}`);
    });
  }
}

// Example 2: Get tasks by category
async function getTasksByCategory(category: string) {
  const response = await fetch(`${API_BASE}/tasks/category/${category}`);
  const data = await response.json();
  
  if (data.success) {
    console.log(`Tasks in ${category}:`, data.data);
  } else {
    console.error('Error:', data.error);
  }
}

// Example 3: Request a bounty
async function requestBounty(taskId: string, walletAddress: string) {
  const response = await fetch(`${API_BASE}/bounties/request`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      taskId,
      wallet: walletAddress
    })
  });

  const data = await response.json();
  
  if (data.success) {
    console.log('Bounty requested:', data.data);
    return data.data;
  } else {
    console.error('Failed to request bounty:', data.error);
    throw new Error(data.error);
  }
}

// Example 4: Complete a bounty
async function completeBounty(
  bountyId: string,
  walletAddress: string,
  rewardToken: 'SOL' | 'USDC'
) {
  const response = await fetch(`${API_BASE}/bounties/complete`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      bountyId,
      wallet: walletAddress,
      rewardToken
    })
  });

  const data = await response.json();
  
  if (data.success) {
    console.log('Bounty completed! Payout sent.');
    console.log('Transaction hash:', data.data.transactionHash);
    return data.data;
  } else {
    console.error('Failed to complete bounty:', data.error);
    throw new Error(data.error);
  }
}

// Example 5: Check user's bounties
async function getUserBounties(userId: string) {
  const response = await fetch(`${API_BASE}/bounties/${userId}`);
  const data = await response.json();
  
  if (data.success) {
    console.log(`Bounties for user ${userId}:`);
    data.data.forEach((bounty: any) => {
      console.log(`- Task ${bounty.taskId}: ${bounty.status} (${bounty.reward} ${bounty.rewardToken})`);
    });
  }
}

// Example 6: Complete workflow
async function completeWorkflow() {
  try {
    console.log('=== Eliza Lobster Workflow Example ===\n');

    // Step 1: Get available tasks
    console.log('Step 1: Fetching available tasks...');
    await getAllTasks();
    console.log();

    // Step 2: Request a specific bounty
    const taskId = '1';
    const wallet = '11111111111111111111111111111112';
    
    console.log('Step 2: Requesting bounty for task', taskId);
    const bounty = await requestBounty(taskId, wallet);
    console.log('Bounty created:', bounty.id);
    console.log();

    // Step 3: Complete the bounty
    console.log('Step 3: Completing bounty...');
    const result = await completeBounty(bounty.id, wallet, 'SOL');
    console.log('Payout result:', result);
    console.log();

    // Step 4: Check bounty history
    console.log('Step 4: Checking bounty history...');
    await getUserBounties(wallet);

  } catch (error) {
    console.error('Workflow error:', error);
  }
}

export {
  getAllTasks,
  getTasksByCategory,
  requestBounty,
  completeBounty,
  getUserBounties,
  completeWorkflow
};
