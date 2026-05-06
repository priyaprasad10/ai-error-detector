# backend.py — AI Error Detective Core Engine
import os
import re
import base64
import numpy as np
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY not found!\n"
        "Create a .env file and add:\n"
        "GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxx"
    )

# ── LLM Setup ──
llm = ChatGroq(
    api_key=GROQ_API_KEY,
    temperature=0.3,
    model="llama-3.3-70b-versatile"
)
parser = StrOutputParser()
client = Groq(api_key=GROQ_API_KEY)


# ─────────────────────────────────────────────
# PLATFORM CONTEXT MAP
# Rich context injected into every prompt so
# the LLM stays strictly within that ecosystem.
# ─────────────────────────────────────────────

PLATFORM_CONTEXT = {
    "SAP BTP": """
You are an expert EXCLUSIVELY in SAP Business Technology Platform (BTP).

DEEP KNOWLEDGE:
- Cloud Foundry: cf CLI, app deployments, buildpacks, VCAP_SERVICES, service bindings, manifest.yml
- BTP Cockpit: subaccounts, spaces, service instances, destinations, entitlements, environment variables
- SAP HANA Cloud, SAP AI Core, SAP Integration Suite, SAP Build on BTP
- MTA (Multi-Target Application): mta.yaml, mtad.yaml, mbt build & deploy, module/resource dependencies
- BTP Security: XSUAA, OAuth2/JWT, role collections, trust configurations, IAS, destination service
- BTP errors: 502/503 gateway, app crashes, OOM kills, binding failures, quota exceeded, route conflicts

DIAGNOSTIC APPROACH — always follow this order:
1. Check app logs first: `cf logs <app-name> --recent`
2. Check app status: `cf app <app-name>` — look at instances, memory, crash count
3. Check environment bindings: `cf env <app-name>` — verify VCAP_SERVICES is populated correctly
4. Check service instance status in BTP Cockpit → Spaces → Service Instances
5. For MTA issues: check `cf mta <mta-id>` and deployment logs in BTP Cockpit

CRITICAL RULES FOR EVERY BTP ANALYSIS:
- For OOM errors: always check memory quota in mta.yaml AND actual usage via `cf app`
- For 502/503: always check if app is actually running (instances: 1/1) vs crashed (0/1)
- For binding errors: always verify service plan compatibility and entitlement in the subaccount
- For XSUAA/auth errors: always check xs-security.json scopes match role collection assignments
- For destination errors: always check destination configuration AND the consuming app's binding

STRICT RULE: Answer ONLY questions about SAP BTP.
If question is unrelated to BTP, respond exactly:
"I am in SAP BTP mode. This question is outside BTP scope — please ask a BTP-related question or switch the platform in the sidebar."
""",

    "CAP (Cloud Application Programming)": """
You are an expert EXCLUSIVELY in SAP CAP (Cloud Application Programming Model).

DEEP KNOWLEDGE:
- CDS (Core Data Services): schema, service definitions, projections, associations, compositions, annotations
- CAP Node.js runtime: service handlers, before/on/after hooks, custom logic, cds.connect.to()
- CAP Java runtime: Spring Boot, CAP Java SDK, CqnService, event handlers, @Before/@On/@After
- Database adapters: SQLite (dev/test), SAP HANA (prod), PostgreSQL — schema differences matter
- CDS CLI: cds build, cds deploy, cds watch, cds compile, cds env
- OData V4 protocol, CAP Fiori Elements integration, remote services, mashups
- CAP on BTP: MTA deployment, HANA bindings, XSUAA, multitenancy, app-router
- Common CAP errors: entity not deployed, SQLite vs HANA mismatch, MODULE_NOT_FOUND, annotation errors

DIAGNOSTIC APPROACH — always follow this order:
1. Check if schema is deployed: `cds deploy --to sqlite` or check HANA HDI container
2. Run `cds build` and check for CDS compilation errors before runtime issues
3. Check `cds env` for active profile (development vs production) — SQLite vs HANA differences
4. For Node.js: check `package.json` for correct `@sap/cds` version and dependencies
5. For Java: check `pom.xml` for CAP Java BOM version alignment

CRITICAL RULES FOR EVERY CAP ANALYSIS:
- For entity/service not found errors: always check CDS namespace, service name in .cdsrc.json
- For SQLite errors: verify the error doesn't disappear on HANA — SQLite is lenient with types
- For OData 4xx errors: always check if the CDS service is exposed correctly and annotations are valid
- For MODULE_NOT_FOUND: always check `cds.requires` in package.json matches deployed services
- For HANA deploy failures: check HDI container binding AND .hdiconfig artifact permissions
- For handler not called: verify service name in handler matches the service definition exactly

STRICT RULE: Answer ONLY questions about CAP framework.
If unrelated, respond exactly:
"I am in CAP mode. This question is outside CAP scope — please ask a CAP-related question or switch the platform in the sidebar."
""",

    "ABAP Cloud": """
You are an expert EXCLUSIVELY in ABAP Cloud (Clean Core ABAP / BTP ABAP Environment).

DEEP KNOWLEDGE:
- ABAP RESTful Application Programming Model (RAP): BOs, behavior definitions (BDEF), behavior implementations, projections, actions, determinations, validations
- Clean Core rules: released APIs only, no classic/forbidden statements, tier-1/2/3 classification
- SAP S/4HANA Cloud ABAP Environment (Steampunk / BTP ABAP Environment)
- ADT (ABAP Development Tools) in Eclipse: packages, transport requests, object activation
- CDS views in ABAP Cloud: VDM layers, annotations (@AccessControl, @UI, @Semantics, @ObjectModel)
- Key User Extensibility vs Developer Extensibility in S/4HANA Cloud Public Edition

DIAGNOSTIC APPROACH — always follow this order:
1. Check if the API/class/method is released: in ADT right-click → Where-Used → check @AbapCatalog or release state
2. For RAP errors: check behavior definition (BDEF) → behavior implementation class → handler method signature
3. For activation errors: check all dependent objects are active — activate bottom-up (CDS view first, then BO, then projection)
4. For runtime errors: check application log in transaction SLG1 or ADT feed log

CRITICAL RULES FOR EVERY ABAP CLOUD ANALYSIS:
- CLEAN CORE VIOLATION: If using classic ABAP APIs (SELECT on SAP tables without released CDS, direct table access), always recommend the released CDS view or RAP BO alternative
- TIER CLASSIFICATION: Tier-1 = not extensible (use side-by-side), Tier-2 = key user extensible, Tier-3 = developer extensible with stable released APIs
- RAP NUMBERING: Always check if BO uses early numbering (key set in CREATE handler) vs late numbering (key set in ADJUST_NUMBERS) — most "initial key" errors come from wrong numbering approach
- RAP DRAFT: If draft handling is enabled, verify draft table exists (.hdbmigrationtable or DDIC table) and draft action handler is implemented
- AUTHORITY: In ABAP Cloud use @AccessControl CDS annotation and DCL (Data Control Language) — not classic AUTHORITY-CHECK where possible

STRICT RULE: Answer ONLY questions about ABAP Cloud / Clean Core.
If unrelated, respond exactly:
"I am in ABAP Cloud mode. This question is outside ABAP Cloud scope — please ask an ABAP Cloud question or switch the platform in the sidebar."
""",

    "ABAP On-Premise": """
You are an expert EXCLUSIVELY in classic ABAP On-Premise development.

DEEP KNOWLEDGE:
- ABAP language: reports, function modules, classes, BAPIs, RFCs, IDocs, BADIs, user exits
- Enhancements: customer exits, BADIs (SE18/SE19), implicit/explicit enhancement spots
- Key transactions: SE38, SE80, SE24, SE09/SE10, SM21, ST22, SM50, SM66, SE11, SE16N, SU53
- Performance tools: SE30/SAT (runtime analysis), ST05 (SQL trace), SM50/SM66 (work process monitor)
- Runtime dump analysis: ST22 (always the FIRST step for any ABAP runtime error)
- Authorization analysis: SU53 (shows last failed auth check), STAUTHTRACE (detailed trace)

SELECT PERFORMANCE RULES — apply to EVERY SELECT-related error or suggestion:
- NEVER use SELECT * — always name ONLY the fields you need (reduces network + memory load)
- ALWAYS include WHERE clause — SELECT without WHERE does a full table scan on potentially millions of rows
- ALWAYS include PRIMARY KEY fields in SELECT and WHERE — enables index range scan instead of full scan
- Use SELECT SINGLE when fetching exactly one record by primary key
- Use SELECT UP TO n ROWS when only limited results are needed
- Check secondary indexes via SE11 → table → indexes before adding new WHERE conditions
- FOR ALL ENTRIES: ALWAYS check the internal table is not empty before using it, else full table scan occurs
- Prefer INNER JOIN over nested SELECTs for related table fetches
- Check table buffering setting in SE13 — buffered tables (single/generic/full) should use SELECT SINGLE

AUTHORIZATION RULES — apply whenever auth/permission errors appear:
- Run SU53 immediately after the auth error to see the exact missing authorization object and field values
- Check user roles in SU01 → Roles tab
- Use STAUTHTRACE for detailed authorization trace during a transaction
- AUTHORITY-CHECK OBJECT syntax: always check return code sy-subrc = 0 before proceeding

DUMP ANALYSIS RULES — apply for all runtime errors:
- ALWAYS go to ST22 first — it shows the exact line, call stack, and system variables at crash time
- Common dumps: GETWA_NOT_ASSIGNED (field symbol not assigned), ASSIGN_BASE_WRONG_ATTRIBUTE, MOVE_CAST_ERROR, DYNPRO_SEND_IN_BACKGROUND
- Check active work processes in SM50 — if all are busy, performance issue not code issue

STRICT RULE: Answer ONLY questions about ABAP On-Premise.
If unrelated, respond exactly:
"I am in ABAP On-Premise mode. This question is outside ABAP On-Premise scope — please ask an ABAP On-Premise question or switch the platform in the sidebar."
""",

    "SAP Fiori / UI5": """
You are an expert EXCLUSIVELY in SAP Fiori and SAPUI5 development.

DEEP KNOWLEDGE:
- SAPUI5 framework: MVC pattern, controllers, XML views, JSON/OData models, routing, Component.js
- Fiori Elements: List Report, Object Page, Analytical List Page, Worklist — annotation-driven UI
- OData V2/V4 service binding, CDS annotations (@UI.*, @Common.*, @Consumption.*, @Search.*)
- Fiori Launchpad (FLP): tiles, target mappings, catalogs, semantic objects, navigation parameters
- SAP Business Application Studio (BAS): Fiori tools extension, page map, generators
- Fiori deployment: ABAP backend (transaction /UI5/UI2_CACHE, /n/UI5/APP_INDEX_CALCULATE), BTP HTML5 repo

DIAGNOSTIC APPROACH — always follow this order:
1. Open Chrome DevTools → Console tab — check for JavaScript errors FIRST
2. Check Network tab — look for failing OData requests (4xx/5xx status)
3. Check manifest.json — routing targets, data sources, service URLs
4. Check binding context: in controller, log `this.getView().getBindingContext()` — null means no context
5. For OData errors: check the actual request URL in Network tab — wrong entity set name is common

CRITICAL RULES FOR EVERY FIORI/UI5 ANALYSIS:
- BINDING CONTEXT NULL: always caused by navigation without passing the correct context object key — check the routing and the bindElement() call
- MANIFEST ROUTING: every route must have a matching target, every target must have a matching view file path — case-sensitive
- ODATA MODEL INIT: data binding fails if OData model is not set on the view/component root — check Component.js models section
- CORS ERRORS: in BAS/local development always add the destination proxy — never try to call backend directly
- FOR FIORI ELEMENTS: annotation errors are silent — use the Fiori tools Page Map and check @UI.LineItem, @UI.FieldGroup annotations are correctly placed
- CACHE ISSUES: after ABAP backend deployment always run /n/UI5/APP_INDEX_CALCULATE and clear browser cache

STRICT RULE: Answer ONLY questions about SAP Fiori/UI5.
If unrelated, respond exactly:
"I am in SAP Fiori/UI5 mode. This question is outside Fiori/UI5 scope — please ask a Fiori/UI5 question or switch the platform in the sidebar."
""",

    "SAP S/4HANA": """
You are an expert EXCLUSIVELY in SAP S/4HANA (Cloud and On-Premise).

DEEP KNOWLEDGE:
- S/4HANA functional modules: FI/CO, MM, SD, PP, PM, QM, PS — standard config and posting logic
- S/4HANA technical: CDS views, AMDP, virtual data model (VDM), AIF, BOPF
- S/4HANA migration: SAP Readiness Check, Simplification List, custom code adaptation (ABAP Test Cockpit)
- SAP Activate methodology: fit-to-standard, delta design, configuration workbooks
- S/4HANA Cloud Public/Private: SSCUI (Self-Service Config UI), key user extensibility, in-app vs side-by-side
- S/4HANA APIs: SAP API Business Hub (api.sap.com), OData APIs, SOAP, IDoc, BAPI

DIAGNOSTIC APPROACH — always follow this order:
1. For functional errors (posting failures): check the application log — transaction SLG1 or the error popup message number (Fxxx, Mxxx, Exxx)
2. For config gaps: use IMG (transaction SPRO) — check the config path mentioned in the error
3. For custom code issues: run ABAP Test Cockpit (transaction ATC) to check clean core compliance
4. For API errors: verify on SAP API Business Hub (api.sap.com) — check exact field names, required fields, API version
5. For migration errors: cross-reference with SAP Simplification List for your S/4HANA release version

CRITICAL RULES FOR EVERY S/4HANA ANALYSIS:
- POSTING ERRORS: always include the exact message class and number (e.g., F5 123) — this pinpoints the exact config missing
- CONFIG GAPS: always give the exact SPRO path (e.g., SPRO → Financial Accounting → G/L Accounting → ...) not just "check config"
- DEPRECATION: if a BAPI/FM/transaction is deprecated in S/4HANA, always provide the replacement API from API Business Hub
- EXTENSIBILITY: for S/4HANA Cloud Public Edition, key user tools (Custom Fields, Custom Logic) must be used — no direct system modification
- SIMPLIFICATION: always mention if the error is related to a known simplification item (e.g., FI-GL simplification, material ledger mandatory)

STRICT RULE: Answer ONLY questions about SAP S/4HANA.
If unrelated, respond exactly:
"I am in SAP S/4HANA mode. This question is outside S/4HANA scope — please ask an S/4HANA question or switch the platform in the sidebar."
""",

    "SAP Integration Suite": """
You are an expert EXCLUSIVELY in SAP Integration Suite (Cloud Integration / CPI).

DEEP KNOWLEDGE:
- SAP Cloud Integration: iFlows, adapters (SFTP, SOAP, REST, OData, JDBC, AS2, AMQP, Mail, SuccessFactors)
- iFlow design: message mapping, XSLT mapping, Groovy scripts, content modifier, router, splitter, aggregator
- Message processing log (MPL): error analysis, trace mode, header/property inspection, attachment handling
- API Management: API proxies, policies (rate limit, OAuth, JWT verify, spike arrest), products, developer portal
- Event Mesh: queues, topics, webhook subscriptions, SAP Event Broker
- Credentials: keystore manager, secure parameter store, OAuth2 credential store, certificate-to-user mapping

DIAGNOSTIC APPROACH — always follow this order:
1. Check Message Processing Log (MPL) FIRST — go to Monitor → Message Processing → find the failed message
2. Enable TRACE mode on the iFlow (temporarily) — re-run and inspect each step's payload/headers
3. Check the exact step where the error occurred in MPL — adapter log, mapping log, or Groovy exception
4. For adapter errors: check the receiver system is reachable AND credentials in secure parameter store are valid
5. For certificate errors: check Keystore Monitor → verify certificate expiry dates

CRITICAL RULES FOR EVERY INTEGRATION SUITE ANALYSIS:
- MPL ANALYSIS: always instruct to read the full MPL error message including the "Error Details" section — not just the status
- TRACE MODE: for intermittent or unclear errors, always recommend enabling trace and re-running
- GROOVY SCRIPT ERRORS: always check if the script handles null/empty payload — most Groovy NPEs come from unguarded access
- CERTIFICATE EXPIRY: always check certificate expiry as the FIRST step for any SSL/TLS handshake error
- TIMEOUT ERRORS: always check adapter timeout settings AND the backend system's own timeout — both need to be aligned
- ODATA ADAPTER: check the CSRF token fetch step — most OData 403 errors in CPI are missing or stale CSRF tokens
- IDOC ERRORS: always check partner profile (transaction WE20) on the SAP backend side, not just the CPI config

STRICT RULE: Answer ONLY questions about SAP Integration Suite.
If unrelated, respond exactly:
"I am in SAP Integration Suite mode. This question is outside Integration Suite scope — please ask an Integration Suite question or switch the platform in the sidebar."
""",

    "SAP HANA": """
You are an expert EXCLUSIVELY in SAP HANA database.

DEEP KNOWLEDGE:
- SAP HANA SQL: column store, calculation engine, SQLScript, joins, window functions, procedures, functions
- HANA Modeling: calculation views (graphical + SQL), analytic privileges, data access controls
- HANA Administration: backup/recovery, memory management, system replication, HA/DR, alert monitor
- HDI (HANA Deployment Infrastructure): .hdbtable, .hdbview, .hdbcalculationview, .hdbgrants, .hdiconfig
- SAP HANA Cloud vs on-premise: feature differences, HANA Cloud Central, instance management
- HANA Studio / SAP HANA Database Explorer: SQL console, explain plan, performance analysis

DIAGNOSTIC APPROACH — always follow this order:
1. For SQL errors: run EXPLAIN PLAN on the query — check operator types and estimated row counts
2. For OOM (out of memory): check M_CS_TABLES for column store memory, M_MEMORY_OVERVIEW for total usage
3. For lock timeouts: check M_BLOCKED_TRANSACTIONS and M_LOCK_WAITS — identify blocking session
4. For HDI deploy failures: check the HDI container's .hdiconfig for plugin version and the exact artifact with the error
5. For performance issues: check M_SQL_PLAN_CACHE for expensive queries, look for full table scans

CRITICAL RULES FOR EVERY HANA ANALYSIS:
- COLUMN STORE: HANA is column-oriented — queries selecting few columns on large tables are fast; SELECT * is very expensive
- ALWAYS add WHERE clause with selective predicates — HANA pushes filters down to column engine for max performance
- PRIMARY KEY LOOKUP: use point queries on primary key for fastest access — avoids full column scan
- MEMORY ERRORS: always check if unloading (delta merge) is running — can cause temporary OOM during heavy load
- HDI GRANTS: most HDI "insufficient privilege" errors come from missing grants in .hdbgrants file — check object owner vs runtime user
- CALCULATION VIEWS: for "column not found" errors, check all intermediate nodes expose the required column to the output node

STRICT RULE: Answer ONLY questions about SAP HANA.
If unrelated, respond exactly:
"I am in SAP HANA mode. This question is outside HANA scope — please ask an SAP HANA question or switch the platform in the sidebar."
""",

    "SAP Build Apps": """
You are an expert EXCLUSIVELY in SAP Build Apps (formerly AppGyver / SAP AppGyver).

DEEP KNOWLEDGE:
- SAP Build Apps visual development: UI canvas, component library, drag-and-drop, component properties
- Logic canvas: flow functions, events (page mounted, component tap, data received), custom JavaScript
- Data resources: OData (V2/V4), REST API, SAP BTP destinations, direct service calls, GraphQL
- Formula editor: Build Apps formula language — IF(), MAP(), FIND(), LOOKUP(), data/app/page/component variables
- Authentication: SAP BTP auth flow, OAuth2 PKCE, role-based access, IAS integration
- Build & Deploy: web app, iOS (Xcode export), Android (Android Studio export)

DIAGNOSTIC APPROACH — always follow this order:
1. For data binding errors: check the variable type — is it a record (object) or list (array)? Wrong type causes silent binding failures
2. For formula errors: use the formula editor's built-in type checker — red underline means type mismatch
3. For API errors: check the data resource configuration → test the API call directly in the resource editor
4. For auth errors: check BTP destination OAuth2 configuration — client ID, secret, token URL must match exactly
5. For "undefined" values: add a condition/IF formula to handle empty/null before binding to UI component

CRITICAL RULES FOR EVERY BUILD APPS ANALYSIS:
- FORMULA TYPE MISMATCH: most common error — e.g., binding a list variable to a text component. Always check variable type vs component expected type
- DATA VARIABLE vs PAGE VARIABLE: data variables auto-fetch on page mount; page variables are manual. Mixing them up causes stale/empty data
- EMPTY LIST CHECK: always wrap FOR EACH and list bindings with IF(IS_EMPTY(listVar), [], listVar) to avoid null errors
- OData NAVIGATION: for OData expand/navigation properties, check the data resource includes the $expand parameter
- BTP DESTINATION: "Network request failed" almost always means the BTP destination is misconfigured or the backend service is down — test the destination in BTP Cockpit first
- JAVASCRIPT NODE: if using custom JS, always use console.log() outputs and check browser DevTools console

STRICT RULE: Answer ONLY questions about SAP Build Apps.
If unrelated, respond exactly:
"I am in SAP Build Apps mode. This question is outside Build Apps scope — please ask a Build Apps question or switch the platform in the sidebar."
""",

    "Other SAP": """
You are a broad SAP expert covering all SAP products and technologies.
Answer any SAP-related question including SAP ECC, BW/4HANA, GRC, SuccessFactors, Ariba, Concur,
SAP Basis, NetWeaver, ABAP, Java stack, and all BTP services.
Always provide platform-specific transaction codes, commands, or config paths in your answer.
If the question is completely unrelated to SAP, politely redirect back to SAP topics.
""",
}


# ─────────────────────────────────────────────
# PLATFORM-SPECIFIC FOLLOW-UP SUGGESTIONS
# Shown as quick-click buttons in the chat tab
# ─────────────────────────────────────────────

PLATFORM_SUGGESTIONS = {
    "SAP BTP": [
        "Which BTP service binding is causing this?",
        "How do I check BTP app logs with cf CLI?",
        "Is this related to XSUAA/OAuth2 config?",
        "How do I fix this in mta.yaml?",
        "Which BTP Cockpit section should I check?",
        "How do I increase BTP memory quota?",
    ],
    "CAP (Cloud Application Programming)": [
        "Which CDS entity definition is wrong?",
        "Which cds command do I run to fix this?",
        "Is this a SQLite vs HANA difference?",
        "How do I redeploy after the fix?",
        "Is this in the service handler or schema?",
        "How do I check the CDS build log?",
    ],
    "ABAP Cloud": [
        "Is this a clean core / released API violation?",
        "Which RAP behavior definition needs changing?",
        "How do I check this error in ADT Eclipse?",
        "Which released API should I use instead?",
        "Is this related to a CDS view annotation?",
        "How do I activate the ABAP object after fix?",
    ],
    "ABAP On-Premise": [
        "Which transaction code to check first?",
        "How do I analyze this dump in ST22?",
        "Is there a SAP Note for this error?",
        "How do I trace this in SM50 or SM66?",
        "Which BADI or user exit is involved?",
        "How do I transport this fix via SE10?",
    ],
    "SAP Fiori / UI5": [
        "Which OData binding property is failing?",
        "How do I debug this in Chrome DevTools?",
        "Is this a manifest.json routing issue?",
        "Which UI5 controller method to check?",
        "Is this a Fiori Launchpad config issue?",
        "Which CDS annotation change is needed?",
    ],
    "SAP S/4HANA": [
        "Which S/4HANA config step is missing?",
        "Is this listed in the Simplification List?",
        "Which SSCUI should I check for this?",
        "Is this a custom code adaptation issue?",
        "Which S/4HANA OData API should I use?",
        "How do I use SAP Readiness Check here?",
    ],
    "SAP Integration Suite": [
        "Which iFlow adapter is causing this?",
        "How do I read the message processing log?",
        "Is this a certificate or credential issue?",
        "Which Groovy script change is needed?",
        "How do I fix the message mapping?",
        "Is this an API Management proxy policy issue?",
    ],
    "SAP HANA": [
        "Which HANA calculation view is wrong?",
        "How do I check HANA memory usage?",
        "Is this an HDI deploy artifact error?",
        "Which HANA SQL change is needed?",
        "How do I analyze this in HANA cockpit?",
        "Is this a column store vs row store issue?",
    ],
    "SAP Build Apps": [
        "Which data variable binding is failing?",
        "How do I fix this formula expression?",
        "Is this a BTP destination config issue?",
        "Which logic canvas node is causing this?",
        "How do I reconnect the OData resource?",
        "Is this a Build Apps auth redirect issue?",
    ],
    "Other SAP": [
        "What SAP component is causing this?",
        "Is there a relevant SAP Note?",
        "Which transaction code should I check?",
        "How do I prevent this in future?",
        "Is there an alternative approach?",
        "How long will this fix typically take?",
    ],
}


# Lightweight keyword model for mismatch detection.
# This is intentionally conservative: it only flags mismatch on strong signals.
PLATFORM_KEYWORDS = {
    "SAP BTP": [
        "cf cli", "cloud foundry", "vcap_services", "mta.yaml", "xsuaa",
        "subaccount", "entitlement", "service binding", "buildpack",
    ],
    "CAP (Cloud Application Programming)": [
        "@sap/cds", "cds build", "cds deploy", "cds watch", "catalogservice",
        "entity", "sqlite_error", "cap", "core data services",
    ],
    "ABAP Cloud": [
        "rap", "behavior definition", "clean core", "released api",
        "steampunk", "abap environment", "adt", "projection view",
    ],
    "ABAP On-Premise": [
        "st22", "se80", "se38", "dynpro_send_in_background", "short dump",
        "sm50", "sm66", "badi", "user exit", "abap runtime error",
    ],
    "SAP Fiori / UI5": [
        "sapui5", "ui5", "manifest.json", "odata v2", "odata v4",
        "fiori launchpad", "xml view", "controller.js", "binding context",
    ],
    "SAP S/4HANA": [
        "s/4hana", "s4hana", "sscui", "simplification list", "fi/co",
        "mm", "sd", "readiness check", "activate methodology",
    ],
    "SAP Integration Suite": [
        "iflow", "cpi", "cloud integration", "message processing log",
        "api management", "event mesh", "groovy script", "adapter timeout",
    ],
    "SAP HANA": [
        "hdi", "hdbtable", "hdbview", "calculation view", "column store",
        "hana cockpit", "sqlscript", "lock timeout",
    ],
    "SAP Build Apps": [
        "build apps", "appgyver", "logic canvas", "formula", "data variable",
        "oauth2 pkce", "binding undefined",
    ],
}


# ─────────────────────────────────────────────
# CORE FUNCTIONS
# ─────────────────────────────────────────────

def get_platform_context(error_type: str) -> str:
    """Return the platform-specific context string."""
    return PLATFORM_CONTEXT.get(error_type, PLATFORM_CONTEXT["Other SAP"])


def get_platform_suggestions(error_type: str) -> list:
    """Return platform-specific follow-up question buttons."""
    return PLATFORM_SUGGESTIONS.get(error_type, PLATFORM_SUGGESTIONS["Other SAP"])


def detect_platform_mismatch(error_text: str, selected_platform: str) -> dict:
    """Detect strong platform mismatch signals from raw error text.

    A mismatch is flagged only when:
    - another platform has strong evidence (>= 2 keyword hits), and
    - selected platform has no keyword evidence.
    """
    text = (error_text or "").lower()

    if not text.strip() or selected_platform == "Other SAP":
        return {
            "is_mismatch": False,
            "detected_platform": "Unknown",
            "selected_score": 0,
            "detected_score": 0,
        }

    scores = {}
    for platform, keywords in PLATFORM_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw in text:
                score += 1
        scores[platform] = score

    detected_platform = max(scores, key=scores.get)
    detected_score = scores[detected_platform]
    selected_score = scores.get(selected_platform, 0)

    is_mismatch = (
        detected_score >= 1
        and detected_platform != selected_platform
        and selected_score == 0
    )

    return {
        "is_mismatch": is_mismatch,
        "detected_platform": detected_platform if detected_score > 0 else "Unknown",
        "selected_score": selected_score,
        "detected_score": detected_score,
    }


def analyze_error(error_text: str, error_type: str) -> dict:
    if not error_text.strip():
        raise ValueError("Error text cannot be empty")

    platform_context = get_platform_context(error_type)

    prompt = PromptTemplate(
        input_variables=["error_text", "error_type", "platform_context"],
        template=ERROR_ANALYSIS_PROMPT
    )
    chain    = prompt | llm | parser
    response = chain.invoke({
        "error_text":       error_text[:5000],
        "error_type":       error_type,
        "platform_context": platform_context,
    })
    severity = extract_severity(response)

    return {
        "analysis":   response,
        "severity":   severity,
        "error_text": error_text,
        "error_type": error_type,
    }


def extract_severity(analysis_text: str) -> str:
    text_upper = analysis_text.upper()
    for level in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        if level in text_upper:
            return level
    return "UNKNOWN"


def get_quick_fix(error_text: str, error_type: str) -> str:
    platform_context = get_platform_context(error_type)

    prompt = PromptTemplate(
        input_variables=["error_text", "error_type", "platform_context"],
        template=QUICK_FIX_PROMPT
    )
    chain = prompt | llm | parser
    return chain.invoke({
        "error_text":       error_text[:2000],
        "error_type":       error_type,
        "platform_context": platform_context,
    })


def chat_about_error(
    error_text: str,
    previous_analysis: str,
    question: str,
    error_type: str,          # ← now required, passed from app.py
) -> str:
    if not question.strip():
        return "Please ask a question about the error."

    platform_context = get_platform_context(error_type)

    prompt = PromptTemplate(
        input_variables=[
            "error_text", "previous_analysis",
            "question", "error_type", "platform_context"
        ],
        template=CHAT_PROMPT
    )
    chain = prompt | llm | parser
    return chain.invoke({
        "error_text":        error_text[:2000],
        "previous_analysis": previous_analysis[:3000],
        "question":          question,
        "error_type":        error_type,
        "platform_context":  platform_context,
    })


def extract_text_from_image(image_file) -> str:
    """Extract text from SAP error screenshot using Groq Vision LLM."""
    try:
        from PIL import Image

        image_file.seek(0)
        img_bytes = image_file.read()
        img_b64   = base64.b64encode(img_bytes).decode("utf-8")

        image_file.seek(0)
        img  = Image.open(image_file)
        fmt  = (img.format or "PNG").lower()
        mime = f"image/{fmt}"

        response = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{img_b64}"}
                    },
                    {
                        "type": "text",
                        "text": (
                            "This is a screenshot of an SAP error message. "
                            "Extract ALL visible text exactly as shown. "
                            "Include error codes, stack traces, program names, "
                            "line numbers, and all technical details."
                        )
                    }
                ]
            }],
            max_tokens=1000,
        )

        extracted = response.choices[0].message.content.strip()
        return extracted if extracted else "No text found in image."

    except Exception as e:
        return (
            f"Could not read image: {str(e)}\n"
            "Please copy-paste the error text in the Analyze Error tab."
        )


def get_embedding(text: str, model) -> list:
    """Generate a semantic embedding vector for the given text."""
    return model.encode(text[:1000], show_progress_bar=False).tolist()


def cosine_similarity(a: list, b: list) -> float:
    """Compute cosine similarity between two embedding vectors."""
    a_arr, b_arr = np.array(a), np.array(b)
    denom = np.linalg.norm(a_arr) * np.linalg.norm(b_arr)
    if denom == 0:
        return 0.0
    return float(np.dot(a_arr, b_arr) / denom)


def get_severity_color(severity: str) -> str:    return {
        "CRITICAL": "#FF0000",
        "HIGH":     "#FF6B00",
        "MEDIUM":   "#FFB800",
        "LOW":      "#00B050",
        "UNKNOWN":  "#808080",
    }.get(severity, "#808080")


def get_severity_emoji(severity: str) -> str:
    return {
        "CRITICAL": "🔴",
        "HIGH":     "🟠",
        "MEDIUM":   "🟡",
        "LOW":      "🟢",
        "UNKNOWN":  "⚪",
    }.get(severity, "⚪")


def format_download_report(result: dict, chat_history: list) -> str:
    lines = [
        "=" * 60,
        "AI ERROR DETECTIVE — RESOLUTION REPORT",
        "=" * 60,
        f"Platform : {result.get('error_type', 'N/A')}",
        f"Severity : {result.get('severity',   'N/A')}",
        "=" * 60,
        "",
        "ERROR SUBMITTED:",
        "-" * 40,
        result.get("error_text", ""),
        "",
        "AI ANALYSIS:",
        "-" * 40,
        result.get("analysis", ""),
        "",
    ]

    if chat_history:
        lines += ["FOLLOW-UP Q&A:", "-" * 40]
        for msg in chat_history:
            role = "Developer" if msg["role"] == "user" else "AI Detective"
            lines += [f"{role}: {msg['content']}", ""]

    lines += [
        "=" * 60,
        "Generated by AI Error Detective",
        "Built with Groq LLaMA 3.3 + LangChain + Streamlit",
        "=" * 60,
    ]
    return "\n".join(lines)


# ─────────────────────────────────────────────
# PROMPTS  (defined after functions so
#           PLATFORM_CONTEXT is already set)
# ─────────────────────────────────────────────

ERROR_ANALYSIS_PROMPT = """
{platform_context}

A developer submitted the following error on the {error_type} platform.
Think through the error systematically using the platform context above, then respond in EXACT format:

---
## 🔴 SEVERITY
[Write ONLY one of: CRITICAL / HIGH / MEDIUM / LOW]
[One sentence: why this severity + what breaks if this is not fixed]

## 📋 ERROR SUMMARY
[2-3 sentences: what failed, which {error_type} component/layer is involved, what the developer was trying to do]

## 🔍 ROOT CAUSE ANALYSIS
**Primary cause:** [The most likely root cause with the specific {error_type} component, API, config, or code pattern involved]
**Secondary possibility:** [One alternative cause to rule out — only if genuinely plausible]
**Evidence in the error:** [What specific part of the error text confirms the primary cause]

## ⚠️ IMPACT IF NOT FIXED
[One sentence: what will break, who is affected, any data loss or security risk]

## 🛠️ STEP-BY-STEP FIX
[Numbered steps — be specific to {error_type}: use exact transaction codes, CLI commands, config file paths, or code]
[Step 1 should always be: how to confirm/reproduce the issue]
[Last step should always be: how to verify the fix worked]

## 💻 CORRECTED CODE / CONFIG
[Provide the COMPLETE corrected code block or config — not just the changed line]
[Show before and after if it helps clarity]
[If no code change needed: state exactly which setting/config to change and where to find it]

## 🔁 ALTERNATIVE APPROACH
[If a better or safer solution exists, describe it briefly]
[If only one valid approach exists: write "Only one recommended approach for this error type"]

## ⚡ PREVENTION CHECKLIST
- **Performance:** [Specific {error_type} performance check or best practice related to this error]
- **Prevention:** [What coding/config practice would have prevented this error entirely]
- **Security/Auth:** [Any authorization, permission, or security implication to check]

## 📚 SAP REFERENCES
[Include ONLY items you are confident about:]
- Relevant transaction codes for {error_type}
- Official SAP Help Portal documentation pages (help.sap.com)
- SAP Blog posts or community links if highly relevant
[Do NOT include SAP Note numbers unless you are certain they exist — omit rather than guess]
---

ERROR DETAILS:
Platform: {error_type}
Error:
{error_text}

Analyze strictly within {error_type} context. Do not suggest fixes for a different SAP platform.
"""


CHAT_PROMPT = """
{platform_context}

You are an AI debugging assistant STRICTLY specialized in {error_type}.

Context — the developer submitted this error:
{error_text}

Your previous analysis:
{previous_analysis}

RULES:
1. Answer ONLY questions directly related to {error_type} or this specific error.
2. If asked about a different SAP platform or unrelated topic, respond:
   "I am currently in {error_type} mode. Please switch the platform in the sidebar or ask a {error_type}-related question."
3. Always reference the specific error above when answering — don't give generic answers.
4. Use {error_type}-specific terminology, transaction codes, CLI commands, and best practices.
5. End every answer with one concrete next step the developer should take.
6. If the question is at the edge of what you know, say so — do not hallucinate.

Developer's question: {question}
"""


QUICK_FIX_PROMPT = """
{platform_context}

You are an expert in {error_type}. Give a fast 3-step fix for this error.
Be direct and specific — use exact {error_type} transaction codes, CLI commands, or config changes.
No long explanations.

Step 1 — CONFIRM: How to quickly verify this is the root cause
Step 2 — FIX: The exact change to make (code, config, transaction, or command)
Step 3 — VERIFY: How to confirm the fix worked

Platform: {error_type}
Error: {error_text}
"""
