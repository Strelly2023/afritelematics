"""DAO and token economy advisory for NovaRide."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from afritech.afripay.events import canonical_hash


def _decimal(value: Any, default: Decimal = Decimal("0")) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return default


def _format(value: Decimal) -> str:
    return format(_decimal(value).quantize(Decimal("0.01")), ".2f")


def _percent(value: Decimal) -> str:
    return format(_decimal(value).quantize(Decimal("0.01")), ".2f")


def _stable_int(value: str, minimum: int, maximum: int) -> int:
    span = maximum - minimum
    if span <= 0:
        return minimum
    digest = canonical_hash(value)
    return minimum + (int(digest[:8], 16) % (span + 1))


@dataclass(frozen=True)
class DAOProposal:
    proposal_id: str
    title: str
    category: str
    status: str
    votes_for: int
    votes_against: int
    treasury_request: str
    rationale: str

    def canonical(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "title": self.title,
            "category": self.category,
            "status": self.status,
            "votes_for": self.votes_for,
            "votes_against": self.votes_against,
            "treasury_request": self.treasury_request,
            "rationale": self.rationale,
        }


class DAOEconomyAI:
    """Advisory DAO / token economy model.

    The model produces proposals, token incentives, and treasury allocation
    guidance. It does not mint tokens or execute governance decisions.
    """

    authority_boundary = "advisory_only_and_policy_gated"

    def evaluate(self, snapshot: Mapping[str, Any]) -> dict[str, Any]:
        liquidity_positions = tuple(snapshot.get("liquidity_positions") or ())
        prefunding_accounts = tuple(snapshot.get("prefunding_accounts") or ())
        settlement_exposures = tuple(snapshot.get("settlement_exposures") or ())
        accounts = tuple(snapshot.get("accounts") or ())
        journals = tuple(snapshot.get("journals") or ())
        outbox = tuple(snapshot.get("outbox") or ())
        snapshots = tuple(snapshot.get("snapshots") or ())

        treasury_balance = sum(
            _decimal(position.get("available_balance")) for position in liquidity_positions
        )
        treasury_reserve = sum(
            _decimal(account.get("current_balance")) for account in prefunding_accounts
        )
        token_supply = Decimal("10000000")
        rewards_distributed = max(Decimal("1200000"), treasury_balance * Decimal("0.10"))
        circulating_supply = max(token_supply * Decimal("0.60"), rewards_distributed * Decimal("4"))
        staked_supply = token_supply * Decimal("0.18")
        community_pool = token_supply * Decimal("0.12")
        treasury_allocation = min(token_supply * Decimal("0.22"), treasury_balance * Decimal("8"))
        driver_incentive_pool = treasury_allocation * Decimal("0.40")
        rider_reward_pool = treasury_allocation * Decimal("0.20")
        partner_incentive_pool = treasury_allocation * Decimal("0.18")
        governance_reserve = treasury_allocation * Decimal("0.22")
        participation_rate = self._participation_rate(outbox, snapshots, journals)
        active_proposals = self._build_proposals(
            treasury_balance=treasury_balance,
            settlement_exposures=settlement_exposures,
            prefunding_accounts=prefunding_accounts,
        )
        token_actions = self._token_actions(
            treasury_balance=treasury_balance,
            rewards_distributed=rewards_distributed,
            staking_ratio=staked_supply / token_supply if token_supply > 0 else Decimal("0"),
        )
        governance_score = self._governance_score(participation_rate, len(active_proposals))
        allocation_plan = self._allocation_plan(
            treasury_balance=treasury_balance,
            governance_reserve=governance_reserve,
            driver_incentive_pool=driver_incentive_pool,
            rider_reward_pool=rider_reward_pool,
            partner_incentive_pool=partner_incentive_pool,
        )
        onchain_plan = self._onchain_plan(active_proposals, allocation_plan)

        return {
            "classification": "NOVARIDE_DAO_TOKEN_ECONOMY_REPORT",
            "authority_boundary": self.authority_boundary,
            "token_economy": {
                "symbol": "NVT",
                "name": "NovaToken",
                "utility": ["governance", "rewards", "incentives", "ecosystem staking"],
                "total_supply": _format(token_supply),
                "circulating_supply": _format(circulating_supply),
                "staked_supply": _format(staked_supply),
                "community_pool": _format(community_pool),
                "rewards_distributed": _format(rewards_distributed),
                "treasury_allocation": _format(treasury_allocation),
                "driver_incentive_pool": _format(driver_incentive_pool),
                "rider_reward_pool": _format(rider_reward_pool),
                "partner_incentive_pool": _format(partner_incentive_pool),
                "governance_reserve": _format(governance_reserve),
                "reward_actions": token_actions,
            },
            "governance": {
                "active_proposals": len(active_proposals),
                "total_votes": sum(proposal.votes_for + proposal.votes_against for proposal in active_proposals),
                "participation_rate": _percent(participation_rate),
                "governance_score": _percent(governance_score),
                "voting_model": "token_weighted_proposal_governance",
                "proposal_queue": [proposal.canonical() for proposal in active_proposals],
            },
            "treasury": {
                "treasury_balance": _format(treasury_balance),
                "treasury_reserve": _format(treasury_reserve),
                "allocatable_budget": _format(treasury_allocation),
                "allocation_plan": allocation_plan,
            },
            "onchain": onchain_plan,
            "metrics": {
                "token_supply": _format(token_supply),
                "circulating_supply": _format(circulating_supply),
                "active_proposals": len(active_proposals),
                "governance_score": _percent(governance_score),
                "participation_rate": _percent(participation_rate),
                "treasury_balance": _format(treasury_balance),
            },
            "recommendations": self._recommendations(active_proposals, token_actions, allocation_plan),
        }

    def _participation_rate(
        self,
        outbox: tuple[Mapping[str, Any], ...],
        snapshots: tuple[Mapping[str, Any], ...],
        journals: tuple[Mapping[str, Any], ...],
    ) -> Decimal:
        signal = len(outbox) + len(snapshots) + len(journals)
        baseline = Decimal("50")
        return min(Decimal("1"), (Decimal(signal) / baseline) + Decimal("0.15"))

    def _governance_score(self, participation_rate: Decimal, proposal_count: int) -> Decimal:
        base = participation_rate * Decimal("0.70")
        proposal_bonus = Decimal(min(proposal_count, 8)) / Decimal("20")
        return min(Decimal("1"), base + proposal_bonus + Decimal("0.20"))

    def _build_proposals(
        self,
        *,
        treasury_balance: Decimal,
        settlement_exposures: tuple[Mapping[str, Any], ...],
        prefunding_accounts: tuple[Mapping[str, Any], ...],
    ) -> tuple[DAOProposal, ...]:
        proposals: list[DAOProposal] = []
        proposal_specs = (
            ("Expand Nairobi", "expansion", "growth"),
            ("Increase driver incentives", "incentives", "economy"),
            ("Expand stable reserve", "treasury", "risk"),
            ("Launch partner staking", "stake", "ecosystem"),
            ("Reward rider loyalty", "rewards", "retention"),
        )
        for index, (title, category, rationale_key) in enumerate(proposal_specs, start=1):
            seed = f"{title}:{treasury_balance}:{len(settlement_exposures)}:{len(prefunding_accounts)}"
            votes_for = _stable_int(seed + ":for", 1200, 9200)
            votes_against = _stable_int(seed + ":against", 100, 2400)
            if treasury_balance <= Decimal("50000") and category in {"expansion", "stake"}:
                status = "queued"
            elif category == "treasury":
                status = "active"
            else:
                status = "draft"
            proposals.append(
                DAOProposal(
                    proposal_id=f"dao.{canonical_hash(seed)[:12]}",
                    title=title,
                    category=category,
                    status=status,
                    votes_for=votes_for,
                    votes_against=votes_against,
                    treasury_request=_format(
                        Decimal("200000")
                        if category == "expansion"
                        else Decimal("120000")
                        if category == "incentives"
                        else Decimal("80000")
                        if category == "treasury"
                        else Decimal("40000")
                    ),
                    rationale=self._proposal_rationale(rationale_key, treasury_balance),
                )
            )
        return tuple(proposals)

    def _proposal_rationale(self, category: str, treasury_balance: Decimal) -> str:
        if category == "growth":
            return "Market growth can compound while treasury reserves remain healthy."
        if category == "economy":
            return "Driver incentives should align with utilization and ride completion."
        if category == "risk":
            return "Reserve allocation should increase when foreign exposure or volatility rises."
        if category == "ecosystem":
            return "Partner staking can deepen governance participation."
        return "Loyalty rewards can improve retention without eroding treasury controls."

    def _token_actions(
        self,
        *,
        treasury_balance: Decimal,
        rewards_distributed: Decimal,
        staking_ratio: Decimal,
    ) -> tuple[str, ...]:
        actions: list[str] = []
        if treasury_balance > Decimal("1000000"):
            actions.append("increase_rewards_pool")
        if staking_ratio < Decimal("0.15"):
            actions.append("expand_staking_incentives")
        if rewards_distributed > Decimal("1500000"):
            actions.append("tighten_reward_emission")
        if not actions:
            actions.append("hold_reward_policy")
        return tuple(actions)

    def _allocation_plan(
        self,
        *,
        treasury_balance: Decimal,
        governance_reserve: Decimal,
        driver_incentive_pool: Decimal,
        rider_reward_pool: Decimal,
        partner_incentive_pool: Decimal,
    ) -> list[dict[str, Any]]:
        return [
            {
                "bucket": "governance_reserve",
                "amount": _format(governance_reserve),
                "purpose": "DAO operations and emergency policy headroom",
            },
            {
                "bucket": "driver_incentives",
                "amount": _format(driver_incentive_pool),
                "purpose": "Driver reward pool and participation uplift",
            },
            {
                "bucket": "rider_rewards",
                "amount": _format(rider_reward_pool),
                "purpose": "Ride cashback and retention rewards",
            },
            {
                "bucket": "partner_incentives",
                "amount": _format(partner_incentive_pool),
                "purpose": "Partner, fleet, and ecosystem growth incentives",
            },
            {
                "bucket": "treasury_buffer",
                "amount": _format(max(treasury_balance - (governance_reserve + driver_incentive_pool + rider_reward_pool + partner_incentive_pool), Decimal("0"))),
                "purpose": "Held back for liquidity protection",
            },
        ]

    def _onchain_plan(
        self,
        proposals: tuple[DAOProposal, ...],
        allocation_plan: list[dict[str, Any]],
    ) -> dict[str, Any]:
        proposal_batch_plan = [
            {
                "anchor_id": f"dao.{proposal.proposal_id}",
                "proof_hash": canonical_hash(proposal.canonical()),
                "context": "DAO_PROPOSAL",
            }
            for proposal in proposals
        ]
        treasury_batch_plan = [
            {
                "anchor_id": f"dao.allocation.{item['bucket']}",
                "proof_hash": canonical_hash(item),
                "context": "DAO_TREASURY_ALLOCATION",
            }
            for item in allocation_plan
        ]
        return {
            "authority_boundary": self.authority_boundary,
            "proposal_batch_plan": proposal_batch_plan,
            "treasury_batch_plan": treasury_batch_plan,
            "batch_size": len(proposal_batch_plan) + len(treasury_batch_plan),
            "verification_mode": "advisory_only",
        }

    def _recommendations(
        self,
        proposals: tuple[DAOProposal, ...],
        token_actions: tuple[str, ...],
        allocation_plan: list[dict[str, Any]],
    ) -> tuple[dict[str, Any], ...]:
        recommendations: list[dict[str, Any]] = []
        for proposal in proposals[:3]:
            recommendations.append(
                {
                    "recommendation_id": f"proposal.{proposal.proposal_id}",
                    "title": proposal.title,
                    "action": "submit_proposal",
                    "priority": "high" if proposal.status == "active" else "medium",
                    "rationale": proposal.rationale,
                }
            )
        for index, action in enumerate(token_actions, start=1):
            recommendations.append(
                {
                    "recommendation_id": f"token.{index}",
                    "title": action.replace("_", " ").title(),
                    "action": action,
                    "priority": "medium",
                    "rationale": "Token emission should stay aligned with treasury and participation signals.",
                }
            )
        recommendations.append(
            {
                "recommendation_id": "dao.treasury.allocation",
                "title": "Apply treasury allocation plan",
                "action": "allocate_treasury_to_buckets",
                "priority": "high",
                "rationale": "DAO treasury buckets should be reviewed before any execution.",
                "allocation_buckets": [item["bucket"] for item in allocation_plan],
            }
        )
        return tuple(recommendations)


def default_dao_economy_ai() -> DAOEconomyAI:
    return DAOEconomyAI()
