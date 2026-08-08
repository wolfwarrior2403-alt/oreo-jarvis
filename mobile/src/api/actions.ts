import client from './client';
import type {ActionExecutionResult, ProposedAction} from './types';

export async function listPendingActions(): Promise<ProposedAction[]> {
  const resp = await client.get<ProposedAction[]>('/actions/pending');
  return resp.data;
}

/** The confirmation gate: nothing the agent proposes runs until this is
 * called with approve=true. Approving with false just marks it rejected. */
export async function decideAction(actionId: string, approve: boolean): Promise<ActionExecutionResult> {
  const resp = await client.post<ActionExecutionResult>('/execute/action', {
    action_id: actionId,
    approve,
  });
  return resp.data;
}
