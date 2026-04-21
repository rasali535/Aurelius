export type PromptRunResponse = {
  run_id: string;
  draft_response: string;
  final_status: string;
  total_cost_usdc: number;
  validator_count: number;
  results: ValidatorResult[];
};

export type ValidatorResult = {
  validator_id: string;
  check_type: string;
  status: string;
  risk_score: number;
  reason: string;
  response_time_ms: number;
  unit_price: number;
  payment_status?: string;
  tx_hash?: string;
};

export type Transaction = {
  id: string;
  amount_usdc: number;
  status: string;
  tx_hash: string;
  x402_status?: string;
  wallet_address?: string;
  settled_at: string;
};

export type DashboardSummary = {
  total_prompt_runs: number;
  total_validations: number;
  total_payments: number;
  total_spend_usdc: number;
  latest_transactions: Transaction[];
};
