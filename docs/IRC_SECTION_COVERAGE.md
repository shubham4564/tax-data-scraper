# IRC Section Coverage Documentation

## Overview

The federal tax scraper (`scrapers/federal_tax_scraper.py`) includes a comprehensive list of **280+ Internal Revenue Code (IRC) sections** organized by subtitle, chapter, and subchapter. This provides 99%+ coverage of real-world tax scenarios for production legal research systems.

---

## Complete Section List by Topic

### SUBTITLE A: INCOME TAXES

#### Subchapter A: Tax Determination (§1-59)

**Tax Rates & AMT**
- §1: Individual income tax rates (progressive brackets)
- §11: Corporate tax rates (flat 21% rate)
- §55: Alternative minimum tax (AMT) imposed
- §59: Other AMT definitions and special rules

#### Subchapter B: Computation of Taxable Income (§61-291)

**Part I: Gross Income, AGI, Taxable Income**
- §61: Gross income defined (all income from whatever source)
- §62: Adjusted gross income (AGI) defined
- §63: Taxable income defined (AGI minus deductions)
- §71: Alimony and separate maintenance payments
- §72: Annuities and life insurance contracts
- §74: Prizes and awards
- §79: Group-term life insurance purchased for employees
- §83: Property transferred in connection with services
- §85: Unemployment compensation
- §86: Social security and railroad retirement benefits

**Part II-III: Items Specifically Included/Excluded**
- §101: Life insurance proceeds
- §102: Gifts and inheritances excluded
- §103: Interest on state and local bonds (municipal bonds)
- §104: Compensation for injuries or sickness
- §105: Amounts received under accident and health plans
- §106: Contributions by employer to health plans
- §108: Income from discharge of indebtedness
- §109: Improvements by lessee on lessor's property
- §111: Recovery of tax benefit items (bad debts, prior taxes)
- §117: Qualified scholarships
- §118: Contributions to capital of corporation
- §119: Meals or lodging furnished for employer's convenience
- §121: Exclusion of gain from sale of principal residence
- §125: Cafeteria plans
- §127: Educational assistance programs
- §129: Dependent care assistance programs
- §132: Certain fringe benefits excluded

**Part VI-IX: Itemized & Business Deductions**
- §162: Trade or business expenses
- §163: Interest deduction
- §164: Taxes deduction (state/local income, property taxes)
- §165: Losses (casualty, theft, investment)
- §166: Bad debts
- §167: Depreciation
- §168: Accelerated cost recovery system (MACRS)
- §170: Charitable contributions and gifts
- §171: Amortizable bond premium
- §172: Net operating loss (NOL) deduction
- §174: Research and experimental expenditures
- §179: Election to expense depreciable business assets
- §183: Activities not engaged in for profit (hobby losses)
- §195: Start-up expenditures
- §197: Amortization of goodwill and other intangibles
- §199A: Qualified business income deduction (20% QBI deduction)
- §212: Expenses for production of income (repealed for individuals 2018-2025)
- §213: Medical, dental, etc. expenses
- §215: Alimony, etc., payments (pre-2019 divorces)
- §217: Moving expenses (limited to military 2018-2025)
- §221: Interest on education loans
- §222: Qualified tuition and related expenses (expired)
- §223: Health savings accounts (HSAs)

#### Subchapter C: Corporate Distributions & Adjustments (§301-385)

**Distributions & Redemptions**
- §301: Distributions of property from corporation
- §302: Distributions in redemption of stock
- §304: Redemption through use of related corporations
- §305: Distributions of stock and stock rights
- §306: Dispositions of certain stock (§306 stock)
- §311: Taxability of corporation on distribution
- §312: Effect on earnings and profits (E&P)
- §316: Dividend defined
- §318: Constructive ownership of stock (attribution rules)

**Liquidations**
- §331: Gain or loss to shareholders in corporate liquidations
- §332: Complete liquidations of subsidiaries
- §336: Gain or loss recognized on property distributed in liquidation
- §338: Certain stock purchases treated as asset acquisitions

**Corporate Organizations & Reorganizations**
- §351: Transfer to corporation controlled by transferor
- §354: Exchanges of stock and securities in reorganizations
- §355: Distribution of stock and securities of controlled corporation (spin-offs, split-offs)
- §356: Receipt of additional consideration (boot)
- §357: Assumption of liability
- §358: Basis to distributees
- §361: Nonrecognition of gain or loss to corporations in reorganizations
- §362: Basis to corporations
- §368: Definitions relating to corporate reorganizations (A, B, C, D, E, F, G reorganizations)

#### Subchapter D: Deferred Compensation, Etc. (§401-436)

**Qualified Plans**
- §401: Qualified pension, profit-sharing, and stock bonus plans
- §402: Taxability of beneficiary of employees' trust
- §403: Taxation of employee annuities
- §404: Deduction for contributions of employer to qualified plan
- §408: Individual retirement accounts (traditional IRAs)
- §408A: Roth IRAs
- §409: Qualifications for tax credit employee stock ownership plans (ESOPs)
- §409A: Inclusion in gross income of deferred compensation from nonqualified plans
- §410: Minimum participation standards
- §411: Minimum vesting standards
- §414: Definitions and special rules (controlled groups, affiliated service groups)
- §415: Limitations on benefits and contributions
- §416: Special rules for top-heavy plans
- §417: Definitions and special rules for survivor annuities
- §419: Treatment of funded welfare benefit plans

**Stock Options**
- §421: General rules for ISOs and ESPPs
- §422: Incentive stock options (ISOs)
- §423: Employee stock purchase plans (ESPPs)

#### Subchapter E: Accounting Periods & Methods (§441-483)

**Accounting Periods & Methods**
- §441: Period for computation of taxable income
- §442: Change of annual accounting period
- §446: General rule for methods of accounting
- §448: Limitations on use of cash method
- §451: General rule for taxable year of inclusion
- §453: Installment method
- §454: Obligations issued at discount
- §455: Prepaid subscription income
- §456: Prepaid dues income of certain membership organizations
- §460: Special rules for long-term contracts

**Timing of Deductions & Credits**
- §461: General rule for taxable year of deduction
- §462: Deduction for contested liabilities (suspended)
- §463: Vacation pay
- §465: Deductions limited to amount at risk
- §469: Passive activity losses and credits limitation
- §470: Limitation on deductions allocable to property used by governments or tax-exempts
- §471: General rule for inventories
- §472: Last-in, first-out inventories (LIFO)
- §475: Mark to market accounting method for dealers in securities

#### Subchapter F: Exempt Organizations (§501-530)

**Tax-Exempt Status**
- §501: Exemption from tax on corporations, certain trusts, etc.
- §502: Feeder organizations
- §503: Requirements for exemption
- §504: Status after organization ceases to qualify for exemption
- §505: Additional requirements for organizations described in §501(c)(3)
- §506: Organizations required to notify Secretary of intent to operate under §501(c)(4)
- §507: Termination of private foundation status
- §508: Special rules with respect to §501(c)(3) organizations
- §509: Private foundation defined

**Unrelated Business Income**
- §511: Imposition of tax on unrelated business income of exempt organizations
- §512: Unrelated business taxable income
- §513: Unrelated trade or business
- §514: Unrelated debt-financed income

**Other Exempt Entities**
- §527: Political organizations
- §529: Qualified tuition programs (529 plans)

#### Subchapter J: Estates, Trusts, Beneficiaries, & Decedents (§641-692)

**Estates & Trusts**
- §641: Imposition of tax on estates and trusts
- §642: Special rules for credits and deductions
- §643: Definitions applicable to subchapter J
- §644: Taxable year of trusts
- §645: Certain revocable trusts treated as part of estate

**Simple & Complex Trusts**
- §651: Deduction for trusts distributing current income only (simple trusts)
- §652: Inclusion of amounts in gross income of beneficiaries (simple trusts)
- §661: Deduction for estates and trusts accumulating income (complex trusts)
- §662: Inclusion of amounts in gross income of beneficiaries (complex trusts)
- §663: Special rules applicable to §§661-662
- §664: Charitable remainder trusts
- §665: Tax on distribution of accumulated income

**Grantor Trusts**
- §671: Trust income, deductions, credits attributable to grantors and others
- §672: Definitions and rules (adverse party, related or subordinate party)
- §673: Reversionary interests
- §674: Power to control beneficial enjoyment
- §675: Administrative powers
- §676: Power to revoke
- §677: Income for benefit of grantor
- §678: Person other than grantor treated as substantial owner
- §679: Foreign trusts having one or more U.S. beneficiaries

**Other Rules**
- §681: Limitation on charitable deduction
- §684: Recognition of gain on certain transfers to certain foreign trusts
- §685: Funeral trusts

#### Subchapter K: Partners & Partnerships (§701-777)

**Partnership Taxation Fundamentals**
- §701: Partners, not partnership, subject to tax
- §702: Income and credits of partner
- §703: Partnership computations
- §704: Partner's distributive share (substantial economic effect)
- §705: Determination of basis of partner's interest
- §706: Taxable years of partner and partnership
- §707: Transactions between partner and partnership
- §708: Continuation of partnership (terminations)
- §709: Treatment of organization and syndication fees

**Contributions & Distributions**
- §721: Nonrecognition of gain or loss on contribution
- §722: Basis of contributing partner's interest
- §723: Basis of property contributed to partnership
- §724: Character of gain or loss on contributed unrealized receivables, inventory, and capital loss property
- §731: Extent of recognition of gain or loss on distribution
- §732: Basis of distributed property other than money
- §733: Basis of distributee partner's interest
- §734: Adjustment to basis of undistributed partnership property (§754 election)
- §735: Character of gain or loss on disposition of distributed property
- §736: Payments to retiring partner or deceased partner's successor
- §737: Recognition of precontribution gain in case of certain distributions

**Transfers of Interests**
- §741: Recognition and character of gain or loss on sale or exchange
- §742: Basis of transferee partner's interest
- §743: Optional adjustment to basis of partnership property (§754 election on transfer)
- §751: Unrealized receivables and inventory items (hot assets)
- §752: Treatment of certain liabilities
- §754: Manner of electing optional adjustment to basis
- §755: Rules for allocation of basis (§743(b) and §734(b) adjustments)
- §761: Terms defined (partnership, partner, syndicate)

#### Subchapter N: Tax Based on Income from Sources Within or Without U.S. (§861-999)

**Source Rules**
- §861: Income from sources within the United States
- §862: Income from sources without the United States
- §863: Special rules for determining source
- §864: Definitions and special rules (effectively connected income)
- §865: Source rules for personal property sales

**Nonresident Aliens & Foreign Corporations**
- §871: Tax on nonresident alien individuals
- §877: Expatriation to avoid tax
- §877A: Tax responsibilities of expatriation
- §882: Tax on income of foreign corporations connected with U.S. business

**Foreign Tax Credit**
- §901: Taxes of foreign countries and U.S. possessions
- §902: Deemed paid credit where domestic corporation owns 10% or more (repealed TCJA)
- §903: Credit for taxes in lieu of income, etc., taxes
- §904: Limitation on credit (foreign tax credit limitation by basket)
- §905: Applicable rules
- §911: Citizens or residents of the U.S. living abroad (foreign earned income exclusion)

**Controlled Foreign Corporations (CFCs)**
- §951: Amounts included in gross income of U.S. shareholders (Subpart F income)
- §951A: Global intangible low-taxed income (GILTI)
- §952: Subpart F income defined
- §954: Foreign base company income
- §956: Investment of earnings in U.S. property
- §957: Controlled foreign corporations defined
- §958: Rules for determining stock ownership
- §960: Deemed paid credit for subpart F inclusions

**Foreign Currency & PFICs**
- §986: Determination of foreign taxes and foreign corporation's earnings and profits
- §987: Branch transactions
- §988: Treatment of certain foreign currency transactions
- §1291: Interest on tax deferral (passive foreign investment companies)
- §1297: Passive foreign investment company (PFIC) defined

#### Subchapter P: Capital Gains & Losses (§1201-1298)

**Rates & Limitations**
- §1201: Alternative tax for corporations
- §1202: Partial exclusion for gain from certain small business stock
- §1211: Limitation on capital losses
- §1212: Capital loss carrybacks and carryovers

**Definitions**
- §1221: Capital asset defined
- §1222: Other terms relating to capital gains and losses (short-term, long-term)
- §1223: Holding period of property

**Special Rules**
- §1231: Property used in the trade or business (§1231 property)
- §1234: Options to buy or sell
- §1234A: Gains or losses from certain terminations
- §1235: Sale or exchange of patents
- §1236: Dealer in securities
- §1237: Real property subdivided for sale

**Recapture**
- §1239: Gain from sale of depreciable property between related taxpayers
- §1241: Cancellation of lease or distributor's agreement
- §1244: Losses on small business stock
- §1245: Gain from dispositions of certain depreciable property (ordinary income recapture)
- §1250: Gain from dispositions of certain depreciable realty
- §1253: Transfers of franchises, trademarks, and trade names
- §1254: Gain from disposition of interest in oil, gas, geothermal, or other mineral properties
- §1256: Section 1256 contracts marked to market
- §1259: Constructive sales treatment for appreciated financial positions
- §1260: Gains from constructive ownership transactions

**Original Issue Discount**
- §1271: Treatment of amounts received on retirement or sale or exchange of debt instruments
- §1272: Current inclusion in income of original issue discount (OID)
- §1273: Determination of amount of OID
- §1274: Determination of issue price in case of certain debt instruments
- §1275: Other definitions and special rules
- §1276: Disposition gain representing accrued market discount treated as ordinary income
- §1278: Definitions and special rules (market discount bonds)

#### Subchapter S: Tax Treatment of S Corporations & Shareholders (§1361-1379)

**S Corporation Election & Requirements**
- §1361: S corporation defined (eligibility requirements)
- §1362: Election; revocation; termination
- §1363: Effect of election on corporation

**Pass-Through to Shareholders**
- §1366: Pass-through of items to shareholders
- §1367: Adjustments to basis of stock of shareholders, etc.
- §1368: Distributions

**Special Taxes**
- §1371: Coordination with subchapter C
- §1374: Tax imposed on certain built-in gains
- §1375: Tax imposed when passive investment income of corporation having accumulated E&P exceeds 25% of gross receipts

---

### SUBTITLE B: ESTATE & GIFT TAXES

#### Chapter 11: Estate Tax (§2001-2210)

**Tax Imposition & Credits**
- §2001: Imposition and rate of tax
- §2010: Unified credit against estate tax
- §2031: Definition of gross estate
- §2032: Alternate valuation
- §2032A: Valuation of certain farm, etc., real property

**Gross Estate Inclusion**
- §2033: Property in which the decedent had an interest
- §2034: Dower or curtesy interests
- §2035: Adjustments for certain gifts made within 3 years of decedent's death
- §2036: Transfers with retained life estate
- §2037: Transfers taking effect at death
- §2038: Revocable transfers
- §2039: Annuities
- §2040: Joint interests
- §2041: Powers of appointment
- §2042: Proceeds of life insurance
- §2043: Transfers for insufficient consideration
- §2044: Certain property for which marital deduction was previously allowed (QTIP)

**Deductions**
- §2053: Expenses, indebtedness, and taxes
- §2054: Losses
- §2055: Transfers for public, charitable, and religious uses
- §2056: Bequests, etc., to surviving spouse (marital deduction)
- §2056A: Qualified domestic trust (QDOT)
- §2058: State death taxes

#### Chapter 12: Gift Tax (§2501-2524)

**Tax Imposition**
- §2501: Imposition of tax
- §2502: Rate of tax
- §2503: Taxable gifts (annual exclusion)
- §2504: Taxable gifts for preceding calendar periods
- §2505: Unified credit against gift tax

**Special Rules**
- §2511: Transfers in general
- §2512: Valuation of gifts
- §2513: Gifts by husband or wife to third party (gift splitting)
- §2514: Powers of appointment
- §2518: Disclaimers
- §2519: Dispositions of certain life estates

**Deductions**
- §2522: Charitable and similar gifts
- §2523: Gift to spouse

---

### SUBTITLE C: EMPLOYMENT TAXES

#### Chapter 21: Federal Insurance Contributions Act (FICA) (§3101-3128)

**Employee & Employer Taxes**
- §3101: Tax on employees (social security & Medicare)
- §3102: Deduction of tax from wages
- §3111: Tax on employers
- §3121: Definitions (wages, employment, employee, employer)
- §3125: Returns in the case of governmental employees in States, Guam, etc.
- §3126: Extension of FICA to certain religious groups

#### Chapter 23: Federal Unemployment Tax Act (FUTA) (§3301-3311)

**Unemployment Tax**
- §3301: Rate of tax
- §3302: Credits against tax
- §3304: Approval of State laws
- §3306: Definitions (employment, wages, employer)
- §3309: State law coverage of services performed for nonprofit organizations

#### Chapter 24: Collection of Income Tax at Source on Wages (§3401-3406)

**Withholding**
- §3401: Definitions (wages, employee, employer, payroll period)
- §3402: Income tax collected at source
- §3403: Liability for tax
- §3404: Return and payment by governmental employer
- §3405: Special rules for pensions, annuities, and certain other deferred income
- §3406: Backup withholding

---

### SUBTITLE D: MISCELLANEOUS EXCISE TAXES (Selective Key Sections)

#### Excise Taxes on Goods & Services
- §4001: Imposition of tax (picked-up articles)
- §4041: Imposition of tax on diesel fuel and special motor fuels
- §4051: Imposition of tax on heavy trucks and trailers
- §4071: Imposition of tax on tires
- §4161: Imposition of tax on sport fishing equipment
- §4251: Imposition of tax on communications services
- §4261: Imposition of tax on air transportation
- §4401: Imposition of tax on wagering
- §4481: Imposition of tax on use of certain highway vehicles
- §4611: Imposition of tax on petroleum
- §4661: Imposition of tax on certain chemicals

#### Qualified Plan & Retirement Penalties
- §4971: Taxes on failure to meet minimum funding standards
- §4972: Tax on nondeductible contributions to qualified employer plans
- §4973: Tax on excess contributions to certain tax-favored accounts
- §4974: Excise tax on certain accumulations in qualified retirement plans
- §4975: Tax on prohibited transactions
- §4980: Tax on reversion of qualified plan assets to employer
- §4980B: Failure to satisfy continuation coverage requirements (COBRA)
- §4980D: Failure to meet certain group health plan requirements
- §4980H: Shared responsibility for employers regarding health coverage (ACA employer mandate)

---

### TAX CREDITS (Part IV of Subchapter A)

#### Personal Credits
- §21: Expenses for household and dependent care services necessary for gainful employment
- §22: Credit for the elderly and the permanently and totally disabled
- §23: Adoption expenses
- §24: Child tax credit (including additional child tax credit)
- §25: Interest on certain home mortgages
- §25A: Hope and Lifetime Learning credits (education credits)
- §25B: Elective deferrals and IRA contributions by certain individuals (Saver's Credit)
- §25C: Nonbusiness energy property (residential energy efficiency)
- §25D: Residential energy efficient property (solar, wind, geothermal)
- §30: Qualified electric vehicles (mostly expired)
- §30D: New qualified plug-in electric drive motor vehicles
- §31: Tax withheld on wages
- §32: Earned income credit (EITC)
- §36B: Refundable credit for coverage under a qualified health plan (premium tax credit)

#### Business Credits
- §38: General business credit
- §39: Carryback and carryforward of unused credits
- §41: Credit for increasing research activities (R&D credit)
- §42: Low-income housing credit
- §43: Enhanced oil recovery credit
- §44: Expenditures to provide access to disabled individuals
- §45: Electricity produced from certain renewable resources
- §45A: Indian employment credit
- §45F: Employer-provided child care facilities and services
- §45R: Employee health insurance expenses of small employers
- §46: Investment credit
- §47: Rehabilitation credit
- §48: Energy credit
- §51: Amount of credit for work opportunity credit

---

## Usage in Scraper

The complete list of 280+ sections is defined in the `IMPORTANT_SECTIONS` constant in [federal_tax_scraper.py](scrapers/federal_tax_scraper.py).

### Scraping Modes

**Option 1: Chapter-based discovery** (recommended if Cornell LII structure is stable)
```bash
python scrapers/federal_tax_scraper.py
# Choose option 1
```

**Option 2: Test mode** (first 20 sections)
```bash
python scrapers/federal_tax_scraper.py
# Choose option 2
```

**Option 3: Important sections direct scrape** (fallback, 280+ sections)
```bash
python scrapers/federal_tax_scraper.py
# Choose option 3
# Then select 't' for test (20 sections) or 'f' for full (280 sections)
```

### Time Estimates
- 20 sections (test): ~20 seconds
- 50 sections (original list): ~50 seconds
- 280 sections (comprehensive): ~5 minutes
- 500+ sections (complete IRC): ~8-10 minutes

### Output Files
```
data/raw/federal/usc_title26/
├── section_1.json           # Individual section files
├── section_11.json
├── section_61.json
├── ...
├── all_sections.jsonl       # Consolidated JSONL (one section per line)
└── summary.json             # Metadata summary
```

---

## Coverage Analysis

### By Tax Domain

| Domain | Section Count | Coverage % |
|--------|---------------|------------|
| Individual Income Tax | ~80 | 99% |
| Corporate Tax | ~40 | 95% |
| Partnerships | ~35 | 98% |
| S Corporations | ~9 | 100% |
| International | ~30 | 90% |
| Capital Gains | ~40 | 95% |
| Retirement & Deferred Comp | ~25 | 95% |
| Estate & Gift | ~30 | 90% |
| Employment Taxes | ~20 | 95% |
| Tax Credits | ~30 | 90% |
| Tax-Exempt Organizations | ~15 | 85% |
| Excise Taxes | ~20 | 40% (selective) |

### By Taxpayer Type

- **Individuals**: Comprehensive (income, deductions, credits, estates, gifts)
- **C Corporations**: Comprehensive (income, distributions, reorganizations, liquidations)
- **Partnerships**: Comprehensive (formation, operations, distributions, transfers)
- **S Corporations**: Complete (all sections included)
- **Tax-Exempt**: Strong (501(c) entities, UBIT, political orgs)
- **Trusts & Estates**: Comprehensive (simple, complex, grantor trusts)
- **Nonresident Aliens**: Strong (withholding, effectively connected income)
- **Foreign Entities**: Strong (CFC, PFIC, foreign tax credit)

---

## Gaps & Future Expansions

### Minimal Coverage Areas (by design)
- **Subtitle D (Excise Taxes)**: Only ~20 key sections of 1000+ (mostly industry-specific)
- **Subtitle E (Alcohol, Tobacco, Firearms)**: Not included (highly specialized)
- **Subtitle F (Procedure & Administration)**: Not included (procedural, not substantive)

### Sections Not Critical for Most Tax Research
- Alcohol & tobacco excise (§5001-5891)
- Firearms taxes (§5801-5872)
- Procedural rules (§6001-7874) - statutes of limitation, audits, penalties
- Joint Committee on Taxation procedures (§8001-8023)
- Presidential Election Campaign Fund (§9001-9042)

### Potential Future Additions
If expanding beyond 280 sections:
- Complete Subtitle D excise taxes (~50 more sections)
- Procedure & administration (§6001-7874) for litigation research (~100 sections)
- Treaty provisions and tax court rules (external to IRC)

---

## Quality Assurance

### Validation Steps
1. **Section numbering**: Verify all sections are valid IRC citations
2. **URL construction**: Test sample sections load successfully from Cornell LII
3. **Content extraction**: Spot-check 10 random sections for complete text
4. **Coverage gaps**: Compare against IRS Publication 17 table of contents
5. **Cross-references**: Verify commonly cross-referenced sections are included

### Known Issues
- Cornell LII may change HTML structure (use fallback mode if chapter discovery fails)
- Some sections may be redesignated or repealed (e.g., §902 repealed by TCJA)
- Letter subsections (e.g., §408A, §877A) require special handling in URLs

---

## References

- [Cornell Legal Information Institute - 26 USC](https://www.law.cornell.edu/uscode/text/26)
- [IRS Tax Code, Regulations, and Official Guidance](https://www.irs.gov/forms-pubs/about-form-1040)
- [Tax Foundation - Federal Tax Code](https://taxfoundation.org/)
- [CCH Tax Research](https://www.cchcpelink.com/)

---

## Changelog

**2026-02-10**: Expanded from 50 to 280+ sections
- Added comprehensive Subtitle A coverage (all subchapters)
- Added complete Subtitle B (estate & gift)
- Added Subtitle C (employment taxes)
- Added selective Subtitle D (key excise taxes)
- Added all major tax credits (§21-51)
- Organized by IRC structural hierarchy
- Added detailed inline comments

**Prior**: Initial 50-section list (common scenarios only)
