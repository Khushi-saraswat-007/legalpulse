"""Tunable constants for nlp_core. Keep every magic number / keyword list here so it is
easy to defend in the viva and easy to tune."""

# ---------------------------------------------------------------- ingestion
# A PDF page with fewer extracted characters than this is treated as "probably scanned".
MIN_CHARS_PER_PAGE = 40
# If more than this fraction of pages look empty, we raise ScannedPDFError (OCR needed).
SCANNED_PAGE_FRACTION = 0.5

# ---------------------------------------------------------------- segmentation
MAX_HEADING_WORDS = 8          # a numbered line with <= this many words and no final "." is a heading
MAX_NUMBER_DIGITS = 3          # "2025. The ..." must not be read as clause number 2025

# ---------------------------------------------------------------- parties
# Role words commonly used for contract parties. Matching is case-sensitive and whole-word,
# so "Buyer" matches but "buyer" does not (legal drafting capitalises defined roles).
PARTY_ROLES = [
    "Buyer", "Seller", "Supplier", "Vendor", "Customer", "Client", "Licensor", "Licensee",
    "Landlord", "Tenant", "Lessor", "Lessee", "Employer", "Employee", "Contractor",
    "Consultant", "Service Provider", "Disclosing Party", "Receiving Party", "Borrower",
    "Lender", "Company", "Owner", "Developer", "Publisher", "Distributor", "Franchisor",
    "Franchisee", "Principal", "Agent", "Provider",
]
COLLECTIVE_PARTY_PHRASES = ["either party", "neither party", "each party", "both parties", "the parties", "any party"]

# ---------------------------------------------------------------- obligation types
# Ordered: the FIRST rule whose pattern matches wins. Heading is tried before body text.
# (type, heading_regex, text_regex)
OBLIGATION_RULES = [
    ("definition",        r"definition|interpretation", r"\bmeans\b|\bshall mean\b|\bhas the meaning\b"),
    ("governing_law",     r"governing law|applicable law|jurisdiction", r"governed by the laws?|subject to the (exclusive )?jurisdiction"),
    ("dispute_resolution", r"dispute|arbitration", r"\barbitrat|\bmediation\b|dispute resolution"),
    ("force_majeure",     r"force majeure", r"force majeure"),
    ("confidentiality",   r"confidential|non-?disclosure", r"\bconfidential\b|\bnon-?disclosure\b"),
    ("indemnity",         r"indemni", r"\bindemnif|\bindemnity\b"),
    ("liability",         r"liabilit", r"limitation of liability|\bliable for\b|aggregate liability"),
    ("penalty",           r"penalt|liquidated damages|late fee", r"\bpenalt|liquidated damages|late fee|interest on (late|overdue)"),
    ("termination",       r"terminat", r"\bterminat"),
    ("renewal",           r"renewal|extension", r"\brenew|\bauto-?renew"),
    ("term",              r"^term$|duration|\bterm of\b", r"(agreement|lease|contract) (runs|continues|remains in force) for|\bshall commence on\b"),
    ("deposit",           r"deposit", r"security deposit"),
    ("payment",           r"payment|fee|invoice|rent|price|charges", r"\bshall pay\b|\bpayable\b|\binvoices?\b|\bpay\b.*\b(within|before)\b"),
    ("warranty",          r"warrant", r"\bwarrant"),
    ("ip",                r"intellectual property|\bip\b|copyright", r"intellectual property|copyright|patent|trademark"),
    ("data_protection",   r"data protection|privacy|data", r"personal data|data protection|\bdelete .*data\b"),
    ("insurance",         r"insurance", r"\binsur(e|ance)\b"),
    ("subcontracting",    r"subcontract|assign", r"\bsubcontract|\bassign\b|\bassignment\b"),
    ("support",           r"support|maintenance|service level", r"\bprovide support\b|\bmaintenance\b|service level"),
    ("delivery",          r"deliver", r"\bdeliver"),
    ("audit",             r"audit|records", r"\baudit\b|\bkeep (accurate )?records\b"),
    ("restriction",       r"restriction|prohibit", r"\bshall not\b|\bmay not\b|\bmust not\b|\bprohibited\b|\bnot permitted\b"),
    ("grant",             r"grant|licen[cs]e", r"\bgrants?\b.*\blicen[cs]e\b|\blicen[cs]e to use\b"),
    ("notice",            r"notice", r"\bnotices? (shall|must|may) be\b|\bwritten notice\b"),
]
DEFAULT_OBLIGATION_TYPE = "general"

# ---------------------------------------------------------------- contradiction detection
NLI_MODEL_NAME = "cross-encoder/nli-deberta-v3-small"   # CPU friendly; swap to "roberta-large-mnli" for more accuracy
NLI_BATCH_SIZE = 16
NLI_MAX_LENGTH = 256

CONTRADICTION_THRESHOLD = 0.80   # mean P(contradiction) over both directions
ENTAILMENT_THRESHOLD = 0.80      # mean P(entailment) over both directions
EMIT_LABELS = ("contradiction",)  # which labels are written to contract["contradictions"]

# Candidate pair filtering (avoid O(n^2) NLI calls on long contracts)
MAX_CANDIDATE_PAIRS = 400
MIN_TEXT_SIMILARITY = 0.12       # TF-IDF cosine; pairs with no other link need at least this
SKIP_TYPES_FOR_PAIRS = {"definition", "governing_law"}
# Words that carry no topic. Used ONLY for the candidate-admission similarity, so two clauses
# are not paired just because both say "within 30 days of ... shall ...". (P1, 26 Oct)
GENERIC_TOKENS = frozenset(
    "a an the of in on at to for by with from and or nor but as is are be been being was were "
    "this that these those it its any all each every such other not no may must shall will would "
    "should can could upon under over into than then there their his her which who whom whose "
    "within after before during day days week weeks month months year years hour hours "
    "party parties licensee licensor".split())

# Explicit exception / override markers. If clause B uses one of these AND cites clause A,
# B is an intentional carve-out of A, so the pair is NOT reported as an accidental contradiction.
EXCEPTION_MARKERS = [
    r"notwithstanding", r"except as (provided|set out|stated|specified)", r"subject to",
    r"save as (provided|set out)", r"without prejudice to", r"other than as provided",
]
