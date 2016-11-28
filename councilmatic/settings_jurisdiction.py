# These are all the settings that are specific to a jurisdiction

###############################
# These settings are required #
###############################

OCD_CITY_COUNCIL_ID = 'ocd-organization/42e23f04-de78-436a-bec5-ab240c1b977c'
CITY_COUNCIL_NAME = 'LA Metro'
OCD_JURISDICTION_ID = 'ocd-jurisdiction/country:us/state:ca/county:los_angeles/transit_authority'
LEGISLATIVE_SESSIONS = ['2014', '2015', '2016'] # the last one in this list should be the current legislative session
CITY_NAME = 'LA Metro'
CITY_NAME_SHORT = 'LA Metro'

# VOCAB SETTINGS FOR FRONT-END DISPLAY
CITY_VOCAB = {
    'MUNICIPAL_DISTRICT': 'District',       # e.g. 'District'
    'SOURCE': 'LA Metro',
    'COUNCIL_MEMBER': 'Board Member',       # e.g. 'Council Member'
    'COUNCIL_MEMBERS': 'Board of Directors',      # e.g. 'Council Members'
    'EVENTS': 'Meetings',               # label for the events listing, e.g. 'Events'
}

APP_NAME = 'lametro'

#########################
# The rest are optional #
#########################

# this is for populating meta tags
SITE_META = {
    'site_name' : 'LA Metro Councilmatic',       # e.g. 'Chicago Councilmatc'
    'site_desc' : '',       # e.g. 'City Council, demystified. Keep tabs on Chicago legislation, aldermen, & meetings.'
    'site_author' : '',     # e.g. 'DataMade'
    'site_url' : '',        # e.g. 'https://chicago.councilmatic.org'
    'twitter_site': '',     # e.g. '@DataMadeCo'
    'twitter_creator': '',  # e.g. '@DataMadeCo'
}

LEGISTAR_URL = ''           # e.g. 'https://chicago.legistar.com/Legislation.aspx'


# this is for the boundaries of municipal districts, to add
# shapes to posts & ultimately display a map with the council
# member listing. the boundary set should be the relevant
# slug from the ocd api's boundary service
# available boundary sets here: http://ocd.datamade.us/boundary-sets/

BOUNDARY_SET = ['la-metro-supervisory-districts', 'la-metro-committee-districts']


# this is for configuring a map of council districts using data from the posts
# set MAP_CONFIG = None to hide map
MAP_CONFIG = {
    'center': [34.0522, -118.2437],
    'zoom': 10,
    'color': "#54afe8",
    'highlight_color': "#C00000",
}

# FOOTER_CREDITS = [
    # {
    #     'name':     '', # e.g. 'DataMade'
    #     'url':      '', # e.g. 'http://datamade.us'
    #     'image':    '', # e.g. 'datamade-logo.png'
    # },
# ]

# this is the default text in search bars
SEARCH_PLACEHOLDER_TEXT = '' # e.g. 'police, zoning, O2015-7825, etc.'



# these should live in APP_NAME/static/
IMAGES = {
    #'favicon': 'images/favicon.ico',
    'logo': 'images/logo.png',
}




# THE FOLLOWING ARE VOCAB SETTINGS RELEVANT TO DATA MODELS, LOGIC
# (this is diff from VOCAB above, which is all for the front end)

# this is the name of the meetings where the entire city council meets
# as stored in legistar
CITY_COUNCIL_MEETING_NAME = 'Board of Directors'

# this is the name of the role of committee chairs, e.g. 'CHAIRPERSON' or 'Chair'
# as stored in legistar
# if this is set, committees will display chairs
COMMITTEE_CHAIR_TITLE = 'Chair'

# this is the anme of the role of committee members,
# as stored in legistar
COMMITTEE_MEMBER_TITLE = 'Member'




# this is for convenience, & used to populate a table
# describing legislation types on the default about page template
# the 'search_term' should be lowercase with spaces before and after backslashes
LEGISLATION_TYPE_DESCRIPTIONS = [
    {
        'name': 'Budget',
        'search_term': 'budget',
        'fa_icon': 'dollar',
        'html_desc': True,
        'desc': 'A plan of financial operations for a given period, including proposed expenditures, authorized staffing levels, and a proposed means of financing them. Metro follows a July 1 to June 30 Fiscal Year.  Its annual budgets are typically approved by the Board after a public hearing in May of each year. Individual capital projects over $5 million have a Life of Project (LOP) budget estimate reviewed by the Board of Directors.',
    },
    {
        'name': 'Fare/Tariff/Service Change',
        'search_term': 'fare / tariff / service change',
        'fa_icon': 'dollar',
        'html_desc': True,
        'desc': 'Chapter 2-50 of Metro’s Administrative Code, its Ordinances, set the parameters and procedures for holding public hearings in advance of any fare, tariff or major service changes. Fare changes and major service changes require public hearings and Title VI analysis.  Minor service changes are continually reviewed and approved with public participation by Metro’s Service Councils for the San Gabriel Valley, San Fernando Valley, Westside, Southbay and Gateway Cities areas of the County.',
    },
    {
        'name': 'Formula Allocation / Local Return',
        'search_term': 'formula allocation / local return',
        'fa_icon': 'dollar',
        'html_desc': True,
        'desc': 'Formula Allocation and Local Return are adopted methods for distributing Federal, State and local transit and transportation funding.  Funding is allocated to sixteen municipal transit operators using audited performance data, and 88 cities in Los Angeles County using population data.  The majority of this funding is local sales tax revenues from Proposition A (1980), Proposition C (1990) and Measure R (2008).',
    },
    {
        'name': 'Agreement',
        'search_term': 'agreement',
        'fa_icon': 'file-text-o',
        'html_desc': True,
        'desc': 'A negotiated arrangement between parties.',
    },
    {
        'name': 'Application',
        'search_term': 'application',
        'fa_icon': 'file-text-o',
        'html_desc': True,
        'desc': 'A formal request, usually for state and federal funding programs.',
    },
    {
        'name': 'Contract',
        'search_term': 'contract',
        'fa_icon': 'file-text-o',
        'html_desc': True,
        'desc': 'A written agreement executed by Metro and an individual or firm which thereby becomes the Contractor. The contract sets forth the rights or obligations of the parties in connection with the furnishing of goods or services, including construction. Contracts over $500,000 required Board approval.',
    },
    {
        'name': 'Informational Report',
        'search_term': 'informational report',
        'fa_icon': 'file-text-o',
        'html_desc': True,
        'desc': 'Metro staff will provide various informational reports to the Board of Directors as background to the policies, programs, plans, situations and events.  Many of these are circulated publicly as “Receive and File” reports.',
    },
    {
        'name': 'Federal Legislation / State Legislation (Position)',
        'search_term': 'federal legislation / state legislation (position)',
        'fa_icon': 'file-text-o',
        'html_desc': True,
        'desc': 'Metro’s Government Relations staff seeks Board of Director approval prior to taking a position of “support”, “oppose”, or “work with author” on significant State and Federal legislation.',
    },
    {
        'name': 'Ordinance',
        'search_term': 'ordinance',
        'fa_icon': 'file-text-o',
        'html_desc': True,
        'desc': 'Metro as an entity created by the State of California for Los Angeles County has the legal authority to adopt ordinances.  Its adopted ordinances are collectively referred to as the Metro Administrative Code.  Ordinances are enacted pursuant to the ordinance adopting authority granted to the Southern California Rapid Transit District by Public Utilities Code Sections 30273 et seq., and to the Los Angeles County Transportation Commission by Public Utilities Code Sections 130103 and 130105. Ordinances include Metro’s Retail Transactions and Use Taxes (Sales Taxes), Transit Court, Codes of Conduct, Settlement of Claims, Public Hearings, Contracting, Tolls and Enforcement of Toll Violations, Parking and more.',
    },
    {
        'name': 'Plan',
        'search_term': 'plan',
        'fa_icon': 'file-text-o',
        'html_desc': True,
        'desc': 'A detailed proposal for achieving public policy goals.  Major Metro plans include the Long Range Transportation Plan, the Short Range Transportation Plan, the Union Station master plans, and subject specific action or strategic plans.',
    },
    {
        'name': 'Policy',
        'search_term': 'policy',
        'fa_icon': 'file-text-o',
        'html_desc': True,
        'desc': 'A course or principle of action adopted by the board of directors in carrying out its legal authority and mission. Examples include Metro’s Debt policy, Energy and Sustainability Policy, Alternative Fuel Policy, Film Production, Financial Stability, Formula Allocation Procedures, Holiday Fares, Investment, Metro System Advertising, Procurement, Property Naming, Small Business, Transit Service, and other public policies.  Policies remain in effect until modified or repealed by the Board.',
    },
    {
        'name': 'Program',
        'search_term': 'program',
        'fa_icon': 'file-text-o',
        'html_desc': True,
        'desc': 'A group of related activities performed by one or more organizational units for the purpose of accomplishing a function for which Metro is responsible.  Examples are the Joint Development Program, Rider Relief Transportation Program, Immediate Needs Transportation Program, Congestion Management Program, Transit Safety Program, Soundwall Program, Vanpool Program and many more.',
    },
    {
        'name': 'Project',
        'search_term': 'project',
        'fa_icon': 'file-text-o',
        'html_desc': True,
        'desc': 'A carefully planned enterprise designed to achieve a particular aim.  Major projects at Metro usually have a Life of Project (LOP) budget, environmental impact reports, preliminary engineering work, and more.  Examples would be light rail projects, the subway project, highway projects, bikeway projects, freight and goods movement facilities, information and technology improvements, and other transportation infrastructure for Los Angeles County.',
    },
    {
        'name': 'Appointment',
        'search_term': 'appointment',
        'fa_icon': 'user',
        'html_desc': True,
        'desc': 'The Board of Directors makes appointments to various committees created for the purpose of collecting and reviewing public input such as the Citizens Advisory Council and the Metro Service Councils, and also to external organizations that include representation from Metro such as Metrolink.',
    },
    {
        'name': 'Minutes',
        'search_term': 'minutes',
        'fa_icon': 'calendar',
        'html_desc': True,
        'desc': 'The permanent official legal record of the business transacted, resolutions adopted, votes taken, and general proceedings of the Board of Directors. ',
    },
    {
        'name': 'Motion/Motion Response',
        'search_term': 'motion / motion response',
        'fa_icon': 'bullhorn',
        'html_desc': True,
        'desc': 'These are issues raised by the Board members directly during meetings.  Motions are usually proposed in writing by one or more board members. Motions include background information and a specific directive to staff after the words “I therefore move”, and then voted on.  When adopted by the Board with a majority vote, staff is given a specific timeframe to research and respond back.',
    },
    {
        'name': 'Oral Report/Presentation',
        'search_term': 'oral report / presentation',
        'fa_icon': 'bullhorn',
        'html_desc': True,
        'desc': 'Metro staff make public  presentations to the board during public meetings via Powerpoint and oral reports.  These are included in the agendas and meeting webcasts.',
    },

    {
        'name': 'Public Hearing',
        'search_term': 'public hearing',
        'fa_icon': 'bullhorn',
        'html_desc': True,
        'desc': 'Various board actions require a public hearing prior to voting.  These include the adoption of the annual budget, fare changes, major service changes, ordinances, eminent domain actions and others as defined by State/Federal law or board ordinance.',
    },
    {
        'name': 'Resolution',
        'search_term': 'resolution',
        'fa_icon': 'commenting-o',
        'html_desc': True,
        'desc': 'Certain board actions require the adoption of a board resolution, usually financial and real estate transactions.',
    },
]


# these keys should match committee slugs
COMMITTEE_DESCRIPTIONS = {
    'ad-hoc-congestion-reduction-committee': '',
    'ad-hoc-regional-rail-committee': '',
    'ad-hoc-sustainability-committee': '',
    'ad-hoc-transit-policing-oversight-committee': '',
    'construction-committee-ebbc3e5b8887': 'The Construction Committee mainly discusses matters related to the building and engineering of Metro\'s transportation infrastructure program.',
    'executive-management-committee-d77e7614390e': 'The Executive Management Committee mainly discusses matters related to public policies, legislative matters at the local, state and federal level, reviews, staffing, professional services, and strategic relationships with other governmental entities.',
    'finance-budget-and-audit-committee-e4f63e08fbc7': 'The Finance, Budget and Audit Committee mainly discusses the annual budget, financial statements, performance measures, financing, bonding, funding programs, management and financial audits, special reviews, audit plans, risk management, insurance policies, fare policy, revenues, investments, eminent domain, and real estate transactions.',
    'planning-and-programming-committee-40a7385ee8be': 'The Planning and Programming Committee mainly discusses matters related to Metro\'s transportation programs, long range and short range plans for all modes of transportation, strategic plans, environmental impacts and clearances for future projects, grant applications, Metro\'s Call for Projects program, countywide transportation improvements, and related policies, as well as Metro\'s local regional relationships.',
    'system-safety-security-and-operations-committee-3f0031984ba5': ' The System Saftey, Security and Operations Committee mainly discusses matters related to the transit system operated by Metro and all its related supporting needs.  Service design and service changes, fuel, parts and supplies, material and inventory items, transit vehicles and rail cars, security and surveillance systems, policing, uniforms, all safety related matters, and nominations to Metro\'s local service councils.'
}

# these blurbs populate the wells on the committees, events, & council members pages
ABOUT_BLURBS = {
    "COMMITTEES" :      "",
    "EVENTS":           "",
    "COUNCIL_MEMBERS":  "",
}

MANUAL_HEADSHOTS = {
    'ara-najarian-a9c58166e1da': {'source': '', 'image': 'manual-headshots/ara-najarian.jpg' },
    'diane-dubois-69f4999a6bff': {'source': '', 'image': 'manual-headshots/diane-dubois.jpg'},
    'jacquelyn-dupont-walker-851703b7b19d': {'source': '', 'image': 'manual-headshots/jacquelyn-dupont-walker.jpg'},
    'eric-garcetti-55692d5b2974': {'source': '', 'image': 'manual-headshots/eric-garcetti.jpg'},
    'mark-ridley-thomas-0a007970f029': {'source': '', 'image': 'manual-headshots/mark-ridley-thomas.jpg'},
    'michael-antonovich-cf1d45635033': {'source': '', 'image': 'manual-headshots/michael-antonovich.jpg'},
    'don-knabe-bff1c136c0d9': {'source': '', 'image': 'manual-headshots/don-knabe.jpg'},
    'sheila-kuehl-9c9abd7a6ff8': {'source': '', 'image': 'manual-headshots/sheila-kuehl.jpg'},
    'james-butts-dc85ae14f195': {'source': '', 'image': 'manual-headshots/james-butts.jpg'},
    'hilda-l-solis-b1533a264870': {'source': '', 'image': 'manual-headshots/hilda-l-solis.jpg'},
    'carrie-bowen-42b40b4f42e1': {'source': '', 'image': 'manual-headshots/carrie-bowen.jpg'},
    'paul-krekorian-6946f7e6401b': {'source': '', 'image': 'manual-headshots/paul-krekorian.jpg'},
    'mike-bonin-00ef9b2a3527': {'source': '', 'image': 'manual-headshots/mike-bonin.jpg'},
    'john-fasana-f9f830cb255d': {'source': '', 'image': 'manual-headshots/john-fasana.jpg'},
}

# notable positions that aren't district representatives, e.g. mayor & city clerk
# keys should match person slugs
EXTRA_TITLES = {
    # e.g. 'emanuel-rahm': 'Mayor',
}

USING_NOTIFICATIONS = False