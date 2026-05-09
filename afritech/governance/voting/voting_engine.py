from governance.voting.voting_models import VotingSession, Vote, VoteDecision
from governance.voting.voting_repository import VotingRepository
from governance.adr.adr_workflow_engine import ADRWorkflowEngine, ADRStatus


class VotingEngineError(Exception):
    pass


class GovernanceVotingEngine:

    def __init__(self, base_path):
        self.repo = VotingRepository(base_path)
        self.workflow = ADRWorkflowEngine(base_path)

    # -----------------------------------------------------------------
    # START VOTING
    # -----------------------------------------------------------------

    def start_voting(self, adr_id):

        session = VotingSession(adr_id)

        self.repo.save(session)
        return session

    # -----------------------------------------------------------------
    # CAST VOTE
    # -----------------------------------------------------------------

    def vote(self, adr_id, voter_id, decision, weight=1):

        if decision not in [VoteDecision.APPROVE, VoteDecision.REJECT]:
            raise VotingEngineError("Invalid vote decision")

        session = self.repo.load(adr_id)

        vote = Vote(voter_id, decision, weight)
        session.add_vote(vote)

        result = session.compute_result()

        # ---------------------------------------------
        # DECISION TRIGGER
        # ---------------------------------------------
        if result == "APPROVED":
            session.closed = True
            self.workflow.approve(adr_id, voter_id)

        elif result == "REJECTED":
            session.closed = True
            self.workflow.reject(adr_id, voter_id)

        self.repo.save(session)

        return session.to_dict()

    # -----------------------------------------------------------------
    # GET STATUS
    # -----------------------------------------------------------------

    def get_status(self, adr_id):
        session = self.repo.load(adr_id)
        return session.to_dict()
    
    # -----------------------------------------------------------------
    # UTILITIES
    # -----------------------------------------------------------------         
    def list_voting_sessions(self):
        return self.repo.store.glob("*.json")   
    
    def _generate_id(self):     
            import hashlib
            from datetime import datetime
    
            # Use current timestamp as seed for ID generation       
            timestamp = datetime.utcnow().isoformat()
            return hashlib.sha256(timestamp.encode()).hexdigest()[:10]  
    