# NovaRide enterprise business case

Status: configurable decision model. Values are planning assumptions until validated by research, contracts, provider quotations and pilot data.

## Value and revenue model

NovaRide targets mobility segments where reliability, auditability and institutional control have measurable value: airport/venue transport, employee and shift mobility, healthcare, education, government and managed fleets.

Candidate revenue streams are rider service fees, driver commission, fleet subscriptions, corporate/institutional contracts, approved government programmes, integration/partner fees and optional ancillary services. Advertising and premium safety charges are disabled assumptions and require explicit product, legal and ethical approval.

## Cost model

The model must include driver payouts; incentives; refunds and chargebacks; payment and identity fees; maps, messaging and notifications; cloud, storage and observability; security and compliance; insurance; support and safety staffing; engineering and operations staff; devices and physical testing; app-store costs; partner onboarding; and region-specific licensing, tax and operating costs.

## Unit-economics definitions

| Metric | Formula |
|---|---|
| Gross booking value | completed trips × average fare |
| Platform gross revenue | GBV × take rate + service and subscription revenue |
| Variable cost per trip | driver payout + payment + identity + maps/messages + incentive + support + insurance + fraud + refund + infrastructure |
| Contribution per trip | revenue per trip − variable cost per trip |
| Contribution margin | contribution per trip ÷ revenue per trip |
| Rider LTV | contribution per retained rider period × expected retained periods |
| Driver LTV | contribution from served trips during expected active periods |
| Break-even trips | allocated fixed monthly cost ÷ positive contribution per trip |

## Configurable assumptions

The machine-readable assumptions are in `docs/novaride/strategy/novaride_unit_economics.yaml`. Currency, region, scenario and effective date are mandatory. Unknown inputs remain `null`; validators and decision reports must not convert missing values to zero.

## Decision gates

- Controlled pilot: operating loss is capped and funded; payment/safety/support exposure is bounded.
- Public pilot: observed service quality and contribution drivers are within approved ranges.
- GA: provider contracts, insurance, taxes, support capacity, fraud/refund reserves and regional costs are approved.
- Expansion: cohort retention, driver supply, reliability and regional contribution justify incremental exposure.

## Risks

Material risks include adverse driver economics, incentive dependence, low retention, payment/fraud loss, underestimated support and insurance costs, provider concentration, regulatory change, weak supply at peak times, and cross-region cost variance. Scenario analysis must show downside and severe-but-plausible cases before commercial approval.
