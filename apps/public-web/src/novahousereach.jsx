import React, { useMemo, useState } from "react";

const LIFECYCLE_STAGES = [
  { title: "Discover", summary: "AI search, market comparison, saved favourites, and virtual inspections." },
  { title: "Inspect", summary: "Open homes, building reports, digital evidence, and defect capture." },
  { title: "Finance", summary: "Mortgage pre-approval, escrow, deposits, settlement, and receipts." },
  { title: "Acquire", summary: "Offers, contracts, digital signing, and settlement tracking." },
  { title: "Occupy", summary: "Move-in checklists, utilities, leases, and resident communications." },
  { title: "Operate", summary: "Rent, compliance, maintenance, contractors, and portfolio control." },
  { title: "Optimise", summary: "Analytics, yield tracking, digital twins, and predictive maintenance." },
];

const ROLE_APPS = [
  {
    title: "Homeowner App",
    summary: "Property portfolio, mortgage overview, insurance, utilities, maintenance, and renovation planning.",
  },
  {
    title: "Buyer App",
    summary: "Search, favourites, inspection booking, AI recommendations, offers, contracts, and settlement.",
  },
  {
    title: "Tenant App",
    summary: "Applications, identity verification, digital leases, rent payments, maintenance, and bond tracking.",
  },
  {
    title: "Landlord App",
    summary: "Listings, screening, lease lifecycle, rent collection, vacancy tracking, and reporting.",
  },
  {
    title: "Agent App",
    summary: "CRM, listings, marketing, inspection management, digital contracts, and commission tracking.",
  },
  {
    title: "Property Manager App",
    summary: "Portfolio operations, communications, renewals, arrears, compliance, and document storage.",
  },
  {
    title: "Contractor App",
    summary: "Job assignment, quotes, scheduling, invoicing, photos, and digital completion evidence.",
  },
  {
    title: "Inspector App",
    summary: "Building, rental, safety, and compliance inspections with structured defect reporting.",
  },
  {
    title: "Developer App",
    summary: "Land acquisition, project delivery, sales, buyer communications, and warranty handover.",
  },
  {
    title: "Admin & Operations",
    summary: "Moderation, fraud detection, support, audit trails, analytics, and platform configuration.",
  },
];

const MARKET_SEGMENTS = [
  { title: "Residential", summary: "Houses, apartments, townhouses, villas, units, and apartments for every lifecycle stage." },
  { title: "Commercial", summary: "Offices, retail, hospitality, medical, industrial, logistics, and warehousing." },
  { title: "Rentals", summary: "Long-term, short-stay, student, shared, and furnished rental surfaces." },
  { title: "Development", summary: "Land, build-to-rent, off-the-plan sales, handover, and defect management." },
  { title: "Institutional", summary: "Government housing, universities, hospitals, REITs, and large portfolios." },
  { title: "Investment", summary: "Yields, capital growth, occupancy, vacancy risk, and cash-flow analytics." },
];

const TRUST_AND_PLATFORM = [
  {
    title: "NovaID",
    summary: "Verified buyers, sellers, tenants, landlords, agents, contractors, and inspectors.",
  },
  {
    title: "NovaPay",
    summary: "Deposits, rent, bond, escrow, settlement, contractor, and invoice payments.",
  },
  {
    title: "NovaTrust",
    summary: "Verified ownership, fraud controls, audit trails, property history, and trust scoring.",
  },
  {
    title: "NovaAI",
    summary: "Natural-language property search, matching, valuation assistance, and workflow automation.",
  },
  {
    title: "NovaData",
    summary: "Market trends, portfolio intelligence, maintenance analytics, and reporting.",
  },
  {
    title: "NovaConnect",
    summary: "Open APIs, webhooks, registry integration, accounting, banking, and insurance connections.",
  },
];

const DIGITAL_TWIN = [
  "Ownership history",
  "Floor plans and 3D models",
  "Inspection evidence",
  "Renovation and maintenance history",
  "Utilities and energy usage",
  "Compliance and insurance records",
  "Market and pricing history",
  "Document vault",
];

const AI_PROMPTS = [
  {
    prompt: "Find a 4-bedroom home under AUD 850,000 within 15 minutes of Melbourne CBD.",
    result: "Matches verified family homes and townhouses with solar, parking, and strong transport access.",
  },
  {
    prompt: "Show pet-friendly rentals with solar panels.",
    result: "Prioritises rental listings with pet policy support, solar assets, and compliant building evidence.",
  },
  {
    prompt: "Find investment properties with yields above 6 percent.",
    result: "Highlights high-yield opportunities with rent, vacancy, and portfolio risk notes.",
  },
];

const OPEN_PLATFORM = [
  "GET /v1/novahousereach/properties",
  "POST /v1/novahousereach/search",
  "POST /v1/novahousereach/applications",
  "POST /v1/novahousereach/maintenance-requests",
  "POST /v1/novahousereach/inspections",
  "POST /v1/novahousereach/settlements",
];

const SAMPLE_LISTINGS = [
  {
    id: "richmond-family-home",
    title: "Richmond Family Home",
    suburb: "Richmond",
    region: "Melbourne",
    type: "House",
    purpose: "Buy",
    price: 845000,
    beds: 4,
    baths: 2,
    parking: 2,
    landSize: 412,
    petFriendly: true,
    solar: true,
    pool: false,
    newConstruction: false,
    accessibility: true,
    yield: 3.9,
    evidence: "Verified ownership and inspection evidence available.",
    tags: ["15 minutes to CBD", "Mortgage ready", "Move-in ready"],
  },
  {
    id: "brunswick-apartment",
    title: "Brunswick Smart Apartment",
    suburb: "Brunswick",
    region: "Melbourne",
    type: "Apartment",
    purpose: "Rent",
    price: 720,
    beds: 2,
    baths: 1,
    parking: 1,
    landSize: null,
    petFriendly: false,
    solar: true,
    pool: true,
    newConstruction: true,
    accessibility: true,
    yield: 5.2,
    evidence: "Lease-ready with digital inspection trail.",
    tags: ["Short commute", "Energy efficient", "Lift access"],
  },
  {
    id: "werribee-townhouse",
    title: "Werribee Townhouse",
    suburb: "Werribee",
    region: "Melbourne",
    type: "Townhouse",
    purpose: "Buy",
    price: 645000,
    beds: 3,
    baths: 2,
    parking: 1,
    landSize: 198,
    petFriendly: true,
    solar: false,
    pool: false,
    newConstruction: true,
    accessibility: false,
    yield: 4.8,
    evidence: "New-build warranty and defect capture included.",
    tags: ["First home", "New construction", "Family zoning"],
  },
  {
    id: "geelong-unit",
    title: "Geelong Coastal Unit",
    suburb: "Geelong",
    region: "Victoria",
    type: "Unit",
    purpose: "Invest",
    price: 575000,
    beds: 2,
    baths: 1,
    parking: 1,
    landSize: null,
    petFriendly: true,
    solar: true,
    pool: false,
    newConstruction: false,
    accessibility: true,
    yield: 6.4,
    evidence: "Yield and occupancy history attached.",
    tags: ["Investor grade", "High yield", "Coastal demand"],
  },
  {
    id: "ballarat-acreage",
    title: "Ballarat Acreage Parcel",
    suburb: "Ballarat",
    region: "Regional Victoria",
    type: "Land",
    purpose: "Build",
    price: 385000,
    beds: 0,
    baths: 0,
    parking: 0,
    landSize: 1120,
    petFriendly: true,
    solar: true,
    pool: false,
    newConstruction: false,
    accessibility: false,
    yield: null,
    evidence: "Planning and title checks available.",
    tags: ["Build-ready", "Serviced land", "Long-term upside"],
  },
  {
    id: "dandenong-warehouse",
    title: "Dandenong Warehouse",
    suburb: "Dandenong",
    region: "Melbourne",
    type: "Commercial",
    purpose: "Lease",
    price: 2650,
    beds: 0,
    baths: 2,
    parking: 6,
    landSize: 1450,
    petFriendly: false,
    solar: true,
    pool: false,
    newConstruction: false,
    accessibility: true,
    yield: 7.1,
    evidence: "Compliance and loading access verified.",
    tags: ["Industrial", "Logistics ready", "High ceiling"],
  },
];

function Badge({ children, tone = "info" }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

function formatMoney(value) {
  return new Intl.NumberFormat("en-AU", {
    style: "currency",
    currency: "AUD",
    maximumFractionDigits: value < 1000 ? 0 : 0,
  }).format(value);
}

function join(items) {
  return items.filter(Boolean).join(" · ");
}

function matchesSearch(listing, filters) {
  const text = `${listing.title} ${listing.suburb} ${listing.region} ${listing.type} ${listing.purpose} ${listing.tags.join(" ")}`.toLowerCase();
  if (filters.query && !text.includes(filters.query.toLowerCase())) return false;
  if (filters.type !== "All" && listing.type !== filters.type) return false;
  if (filters.purpose !== "All" && listing.purpose !== filters.purpose) return false;
  if (filters.region !== "All" && listing.region !== filters.region) return false;
  if (filters.priceCap !== "Any") {
    const cap = Number(filters.priceCap);
    if (Number.isFinite(cap) && listing.price > cap) return false;
  }
  if (filters.petFriendly && !listing.petFriendly) return false;
  if (filters.solar && !listing.solar) return false;
  if (filters.pool && !listing.pool) return false;
  if (filters.newConstruction && !listing.newConstruction) return false;
  return true;
}

function ListingCard({ listing, navigate }) {
  const priceLabel = listing.purpose === "Rent" ? `${formatMoney(listing.price)}/week` : formatMoney(listing.price);
  return (
    <article className="product-card housing-card">
      <div className="card-top">
        <div>
          <Badge tone="trust">{listing.purpose}</Badge>
          <h3>{listing.title}</h3>
          <p>{listing.suburb} · {listing.region}</p>
        </div>
        <Badge tone={listing.yield && listing.yield >= 6 ? "trust" : "info"}>{listing.type}</Badge>
      </div>
      <p className="housing-price">{priceLabel}</p>
      <dl>
        <div><dt>Beds</dt><dd>{listing.beds || "Studio"}</dd></div>
        <div><dt>Baths</dt><dd>{listing.baths}</dd></div>
        <div><dt>Parking</dt><dd>{listing.parking}</dd></div>
        <div><dt>Land</dt><dd>{listing.landSize ? `${listing.landSize} m²` : "N/A"}</dd></div>
        <div><dt>Yield</dt><dd>{listing.yield ? `${listing.yield}%` : "Not stated"}</dd></div>
        <div><dt>Evidence</dt><dd>Verified</dd></div>
      </dl>
      <p>{listing.evidence}</p>
      <div className="chip-row">
        {listing.tags.map((tag) => <span key={tag} className="chip">{tag}</span>)}
      </div>
      <div className="actions housing-actions">
        <button className="button primary" type="button" onClick={() => navigate("/contact")}>Book inspection</button>
        <button className="button secondary" type="button" onClick={() => navigate("/trust")}>View trust trail</button>
      </div>
    </article>
  );
}

function FilterChip({ label, active, onClick }) {
  return (
    <button className={active ? "chip chip-active" : "chip"} type="button" onClick={onClick}>
      {label}
    </button>
  );
}

export function NovaHouseReachDetail({ navigate }) {
  const [query, setQuery] = useState("");
  const [type, setType] = useState("All");
  const [purpose, setPurpose] = useState("All");
  const [region, setRegion] = useState("All");
  const [priceCap, setPriceCap] = useState("Any");
  const [petFriendly, setPetFriendly] = useState(false);
  const [solar, setSolar] = useState(false);
  const [pool, setPool] = useState(false);
  const [newConstruction, setNewConstruction] = useState(false);

  const types = useMemo(() => ["All", ...new Set(SAMPLE_LISTINGS.map((listing) => listing.type))], []);
  const purposes = useMemo(() => ["All", ...new Set(SAMPLE_LISTINGS.map((listing) => listing.purpose))], []);
  const regions = useMemo(() => ["All", ...new Set(SAMPLE_LISTINGS.map((listing) => listing.region))], []);
  const filteredListings = useMemo(
    () =>
      SAMPLE_LISTINGS.filter((listing) =>
        matchesSearch(listing, { query, type, purpose, region, priceCap, petFriendly, solar, pool, newConstruction }),
      ),
    [query, type, purpose, region, priceCap, petFriendly, solar, pool, newConstruction],
  );

  return (
    <section className="detail housing-detail">
      <div className="housing-hero">
        <div className="housing-hero-copy">
          <Badge tone="trust">NovaTech property operating system</Badge>
          <h1>NovaHouseReach</h1>
          <p>
            Find, buy, sell, rent, build, finance, and manage property with trust across a single governed platform.
          </p>
          <div className="actions">
            <button className="button primary" type="button" onClick={() => navigate("/contact")}>Start a property project</button>
            <button className="button secondary" type="button" onClick={() => navigate("/developers")}>Open platform APIs</button>
          </div>
          <div className="trust-strip">
            <span>Private preview</span>
            <span>Australia and Africa ready</span>
            <span>Property lifecycle coverage</span>
            <span>NovaID · NovaPay · NovaTrust</span>
          </div>
        </div>
        <div className="housing-hero-panel">
          <h2>Operating model</h2>
          <div className="metric-grid">
            <article>
              <strong>10</strong>
              <span>role-specific apps</span>
            </article>
            <article>
              <strong>7</strong>
              <span>lifecycle stages</span>
            </article>
            <article>
              <strong>6</strong>
              <span>platform integrations</span>
            </article>
            <article>
              <strong>1</strong>
              <span>trusted property graph</span>
            </article>
          </div>
          <div className="mini-stack">
            {DIGITAL_TWIN.slice(0, 4).map((item) => (
              <div key={item} className="mini-stack-item">{item}</div>
            ))}
          </div>
        </div>
      </div>

      <section className="band">
        <div className="section-heading">
          <Badge>Lifecycle</Badge>
          <h2>Complete property lifecycle coverage</h2>
          <p>NovaHouseReach is designed to carry the same property from discovery through operations and eventual resale or renewal.</p>
        </div>
        <div className="grid lifecycle-grid">
          {LIFECYCLE_STAGES.map((stage) => (
            <article className="capability" key={stage.title}>
              <h3>{stage.title}</h3>
              <p>{stage.summary}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section">
        <div className="section-heading">
          <Badge tone="info">Applications</Badge>
          <h2>User-specific apps for every property role</h2>
          <p>Each role gets a focused application, but all of them sit on the same identity, trust, finance, and evidence layer.</p>
        </div>
        <div className="grid app-grid">
          {ROLE_APPS.map((app) => (
            <article className="product-card" key={app.title}>
              <h3>{app.title}</h3>
              <p>{app.summary}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="band">
        <div className="section-heading">
          <Badge tone="info">Marketplace</Badge>
          <h2>Property categories covered by the platform</h2>
        </div>
        <div className="grid segment-grid">
          {MARKET_SEGMENTS.map((segment) => (
            <article className="capability" key={segment.title}>
              <h3>{segment.title}</h3>
              <p>{segment.summary}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section">
        <div className="section-heading">
          <Badge tone="trust">Search</Badge>
          <h2>Property search with practical filters</h2>
          <p>The implementation keeps the core marketplace filters people actually use: location, price, rooms, parking, solar, pet policy, and new construction.</p>
        </div>
        <div className="housing-search">
          <div className="facet-row">
            <label>
              Search
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search suburb, listing, or feature" />
            </label>
            <label>
              Type
              <select value={type} onChange={(event) => setType(event.target.value)}>
                {types.map((option) => <option key={option} value={option}>{option}</option>)}
              </select>
            </label>
            <label>
              Purpose
              <select value={purpose} onChange={(event) => setPurpose(event.target.value)}>
                {purposes.map((option) => <option key={option} value={option}>{option}</option>)}
              </select>
            </label>
            <label>
              Region
              <select value={region} onChange={(event) => setRegion(event.target.value)}>
                {regions.map((option) => <option key={option} value={option}>{option}</option>)}
              </select>
            </label>
            <label>
              Price cap
              <select value={priceCap} onChange={(event) => setPriceCap(event.target.value)}>
                <option value="Any">Any</option>
                <option value="400000">Under AUD 400k</option>
                <option value="600000">Under AUD 600k</option>
                <option value="800000">Under AUD 800k</option>
                <option value="1000000">Under AUD 1m</option>
              </select>
            </label>
          </div>
          <div className="chip-row">
            <FilterChip label={petFriendly ? "Pet friendly: yes" : "Pet friendly"} active={petFriendly} onClick={() => setPetFriendly(!petFriendly)} />
            <FilterChip label={solar ? "Solar: yes" : "Solar"} active={solar} onClick={() => setSolar(!solar)} />
            <FilterChip label={pool ? "Pool: yes" : "Pool"} active={pool} onClick={() => setPool(!pool)} />
            <FilterChip
              label={newConstruction ? "New construction: yes" : "New construction"}
              active={newConstruction}
              onClick={() => setNewConstruction(!newConstruction)}
            />
          </div>
        </div>
        <div className="grid listing-grid">
          {filteredListings.map((listing) => <ListingCard key={listing.id} listing={listing} navigate={navigate} />)}
        </div>
      </section>

      <section className="band">
        <div className="section-heading">
          <Badge tone="info">AI search</Badge>
          <h2>Natural language property matching</h2>
          <p>NovaAI translates plain-language prompts into filters, evidence, and recommended next actions.</p>
        </div>
        <div className="grid ai-grid">
          {AI_PROMPTS.map((item) => (
            <article className="result" key={item.prompt}>
              <h3>{item.prompt}</h3>
              <p>{item.result}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section">
        <div className="section-heading">
          <Badge tone="trust">Trust and finance</Badge>
          <h2>Identity, payments, and evidence are built in</h2>
        </div>
        <div className="grid integration-grid">
          {TRUST_AND_PLATFORM.map((integration) => (
            <article className="capability" key={integration.title}>
              <h3>{integration.title}</h3>
              <p>{integration.summary}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="band">
        <div className="section-heading">
          <Badge tone="info">Digital twin</Badge>
          <h2>A living property record for every asset</h2>
        </div>
        <div className="detail-grid">
          <article>
            <h3>Core twin fields</h3>
            <ul>
              {DIGITAL_TWIN.map((item) => <li key={item}>{item}</li>)}
            </ul>
          </article>
          <article>
            <h3>Open platform surfaces</h3>
            <ul>
              {OPEN_PLATFORM.map((item) => <li key={item}><code>{item}</code></li>)}
            </ul>
          </article>
        </div>
        <div className="detail-grid">
          <article>
            <h3>Smart building stack</h3>
            <p>IoT sensors, smart locks, cameras, HVAC, lighting, solar, battery, water monitoring, EV chargers, and security systems.</p>
          </article>
          <article>
            <h3>Enterprise operators</h3>
            <p>REITs, universities, hospitals, housing authorities, agencies, developers, and large portfolio owners.</p>
          </article>
        </div>
      </section>
    </section>
  );
}
