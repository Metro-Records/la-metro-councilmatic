# These are all the settings that are specific to a jurisdiction

###############################
# These settings are required #
###############################

OCD_CITY_COUNCIL_ID = 'ocd-organization/42e23f04-de78-436a-bec5-ab240c1b977c'
CITY_COUNCIL_NAME = 'Metro'
OCD_JURISDICTION_IDS = ['ocd-jurisdiction/country:us/state:ca/county:los_angeles/transit_authority']
LEGISLATIVE_SESSIONS = ['2014', '2015', '2016', '2017', '2018'] # the last one in this list should be the current legislative session
CITY_NAME = 'Metro'
CITY_NAME_SHORT = 'Metro'

# VOCAB SETTINGS FOR FRONT-END DISPLAY
CITY_VOCAB = {
    'MUNICIPAL_DISTRICT': 'District',       # e.g. 'District'
    'SOURCE': 'Metro',
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
    'site_name' : 'Metro Board',       # e.g. 'Chicago Councilmatc'
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

BOUNDARY_SET = ['la-metro-supervisory-districts', 'la-metro-committee-districts', 'city-of-la']

MAP_CONFIG = {
    'center': [34.0522, -118.2437],
    'zoom': 10,
    'color': "#54afe8",
    'highlight_color': '#eb6864'
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
        'desc': 'Chapter 2-50 of Metro’s Administrative Code (its Ordinances) set the parameters and procedures for holding public hearings in advance of any fare, tariff or major service changes. Fare changes and major service changes require public hearings and Title VI analysis. Minor service changes are continually reviewed and approved with public participation by Metro’s Service Councils for the San Gabriel Valley, San Fernando Valley, Westside, Southbay and Gateway Cities regions of the County.',
    },
    {
        'name': 'Formula Allocation / Local Return',
        'search_term': 'formula allocation / local return',
        'fa_icon': 'dollar',
        'html_desc': True,
        'desc': 'Formula Allocation and Local Return are adopted methods for distributing Federal, State and local transit and transportation funding. Funding is allocated to 16 municipal transit operators using audited performance data, and 88 cities in Los Angeles County using population data. The majority of this funding is local sales tax revenues from Proposition A (1980), Proposition C (1990) and Measure R (2008).',
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
        'desc': 'A written agreement executed by Metro and an individual who or firm which thereby becomes the Contractor. The contract sets forth the rights or obligations of the parties in connection with the furnishing of goods or services, including construction. Contracts over $500,000 require Board approval.',
    },
    {
        'name': 'Informational Report',
        'search_term': 'informational report',
        'fa_icon': 'file-text-o',
        'html_desc': True,
        'desc': 'Metro staff will provide various informational reports to the Board of Directors as background to the Agency’s policies, programs, plans, situations and events. Many of these reports are circulated publicly as “Receive and File” reports.',
    },
    {
        'name': 'Federal Legislation / State Legislation (Position)',
        'search_term': 'federal legislation / state legislation (position)',
        'fa_icon': 'file-text-o',
        'html_desc': True,
        'desc': 'Metro’s Government Relations staff seeks Board of Director approval prior to taking a position of “support”, “oppose”, or “work with author” on significant State and Federal legislation.',
    },
    {
        'name': 'Ordinance / Administrative Code',
        'search_term': 'ordinance / administrative code',
        'fa_icon': 'file-text-o',
        'html_desc': True,
        'desc': 'Metro as an entity created by the State of California for Los Angeles County has the legal authority to adopt ordinances. Its adopted ordinances are collectively referred to as the Metro Administrative Code. Metro ordinances are enacted pursuant to the ordinance adopting authority granted to the Southern California Rapid Transit District by Public Utilities Code Sections 30273 et seq., and to the Los Angeles Comment [SAR1]: Capitalize Board Report Comment [SAR2]: Items included here are only those where text is edited. All existing types of Board Reports should still be included as is. County Transportation Commission by Public Utilities Code Sections 130103 and 130105. Ordinances include, among others: <br><br>a.) Metro’s Retail Transactions and Use Taxes (Sales Taxes) <br>b.) Transit Court <br>c.) Codes of Conduct <br>d.) Settlement of Claims <br>e.) Public Hearings <br>f.) Contracting <br>g.) Tolls and Enforcement of Toll Violations <br>h.) Parking',
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
        'desc': 'A course or principle of action adopted by the Board of Directors in carrying out its legal authority and mission. Examples include Metro’s Debt policy, Energy and Sustainability Policy, Alternative Fuel Policy, Film Production, Financial Stability, Formula Allocation Procedures, Holiday Fares, Investment, Metro System Advertising, Procurement, Property Naming, Small Business, Transit Service, and other public policies. Policies remain in effect until modified or repealed by the Board.',
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
        'desc': 'A carefully planned enterprise designed to achieve a particular aim. Major projects at Metro usually have a Life of Project (LOP) budget, environmental impact report, preliminary engineering work, and more. Examples would be light rail projects, subway projects, highway projects, bikeway projects, freight and goods movement facilities, information and technology improvements, and other transportation infrastructure for Los Angeles County.',
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
        'desc': 'These are issues raised by Board Members during meetings. Motions are usually proposed in writing by one or more Board Members. Motions include background information and a specific directive to staff after the words “I therefore move”, and then voted on. When adopted by the Board with a majority vote, staff is given a specific timeframe to research and respond back.',
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
    {   'name': 'Board Box',
        'search_term': 'board box',
        'fa_icon': 'commenting-o',
        'html_desc': True,
        'desc': "Formal information communication to the Board not requiring actions. We are in the process of importing Board Boxes to this website; in the meantime, please access Board Box items through the <a href='http://search3.metro.net/search?access=p&output=xml_no_dtd&site=Board_Archives&ie=UTF-8&client=BoardArchive&proxystylesheet=BoardArchive&proxycustom=%3CHOME/%3E' target='_blank'>Board Archive</a>."
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
    "EVENTS": "<p>Committee meetings are the first level of review for Metro business matters being brought to the Board of Directors for their review and decision.</p><p>Committee meetings take place on Wednesday and Thursday, the week before a regular, scheduled Board Meeting. A unanimous vote at the Committee level will place an item on the Consent Calendar of the Board of Directors.</p><p>The full Board of Directors typically meets once a month to review presented budgets, contracts, policies and programs, and make decisions about what to adopt, fund and build.</p>",
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
    'carrie-bowen-af5a8ab39aad': {'source': '', 'image': 'manual-headshots/carrie-bowen.jpg'},
    'paul-krekorian-6946f7e6401b': {'source': '', 'image': 'manual-headshots/paul-krekorian.jpg'},
    'mike-bonin-00ef9b2a3527': {'source': '', 'image': 'manual-headshots/mike-bonin.jpg'},
    'john-fasana-f9f830cb255d': {'source': '', 'image': 'manual-headshots/john-fasana.jpg'},
    'kathryn-barger-52be67cf2369': {'source': '', 'image': 'manual-headshots/kathryn-barger.jpg' },
    'janice-hahn-4682bb5db3dd': {'source': '', 'image': 'manual-headshots/janice-hahn.jpg' },
    'robert-garcia-3d501fbcf51c': {'source': '', 'image': 'manual-headshots/robert-garcia.jpg' },
    'shirley-choate-03b7445fec78': {'source': '', 'image': 'manual-headshots/shirley-choate.jpg' },
    'phil-washington-2daf84e096e2': {'source': '', 'image': 'manual-headshots/phil-washington.jpg'},
}

MEMBER_BIOS = {
    'ara-najarian-a9c58166e1da': 'Ara Najarian has served on the Glendale City Council for 12 years and was recently re-elected to his fourth term with the highest number of votes of all candidates.  He has served three terms as Mayor of Glendale.  Before serving on Council Ara was elected to the Glendale Community College Board of Trustees.<br><br>Ara is a regional leader in transportation, holding a seat on the Los Angeles MTA since 2006 and previously serving as MTA Chairman.  Ara also is 2nd Vice Chairman of Metrolink and has served on the Board of Directors since 2007.<br><br>Ara sits on the Board of Directors of the San Fernando Valley Council of Governments, and held the position of Chairman.<br><br>Ara received a B.A in Economics from Occidental College, and his J.D. degree from the University of Southern California Law School.  In his private life, Ara is a practicing attorney in Glendale.  He is married to Palmira Perez, and has two boys.  ',
    'diane-dubois-69f4999a6bff': 'Lakewood City Councilmember and current Metro Board member Diane DuBois was elected to the Board of Directors in 2009 by the 27 Cities of Southeast Los Angeles County that form the Gateway Cities Council of Governments. Councilmember DuBois, a Lakewood Planning and Environment Commissioner for 28 years, was first elected to the city council in 2005. She has been a board member and volunteer of Lakewood Meals-On-Wheels, a board member of the Greater Long Beach Girl Scout Council, a board member of Lakewood Regional Medical Center, the Pan American Association scholarship chair, a member and past president of Soroptimist International of Lakewood/Long Breach, and a volunteer at Pathways Volunteer Hospice.',
    'jacquelyn-dupont-walker-851703b7b19d': 'Jacquelyn Dupont-Walker is the founding president of the Ward Economic Development Corporation (WEDC) and for 29 years has led the corporation in developing over 280 units of affordable housing, one major shopping mall, encouraging indigenous leadership, creating neighborhood networks, facilitating job creation, conducting asset mapping, and spearheading an intergenerational community building effort. She also chairs the USC Master Plan Advisory Committee where she represents the residents of the West Adams district. Mrs. Dupont-Walker also chairs the Exposition Park Strategic Plan and is Vice-Chair of the Baldwin Hills Conservancy.<br><br> In addition to WEDC, Mrs. Dupont-Walker serves as the AME Church International Social Action Officer and on a host of other civic organizations. As a lifelong member of the AME Church, Mrs. Dupont-Walker created AME V-Alert (voter mobilization plan). She is an officer of Ward AME Church in Los Angeles where she serves on the Board of Stewards, and also the Lay and Missionary ministries and chairs the Social Action Commission.',
    'eric-garcetti-55692d5b2974': 'Eric Garcetti is the 42nd Mayor of Los Angeles. His “back to basics” agenda is focused on job creation and solving everyday problems for L.A. residents.<br><br>Mr. Garcetti was elected four times by his peers to serve as President of the Los Angeles City Council from 2006 to 2012. From 2001 until taking office as Mayor, he served as the Councilmember representing the 13th District which includes Hollywood, Echo Park, Silver Lake, and Atwater Village -- all of which were dramatically revitalized under Mr. Garcetti leadership.<br><br>Mr. Garcetti was raised in the San Fernando Valley and earned his B.A. and M.A. from Columbia University. He studied as a Rhodes Scholar at Oxford and the London School of Economics, and taught at Occidental College and USC. A fourth generation Angelino, he and his wife, Amy Elaine Wakeland, have a young daughter. He is a Lieutenant in the U.S. Navy reserve and is an avid jazz pianist and photographer.',
    'mark-ridley-thomas-0a007970f029': 'Mark Ridley-Thomas was elected Los Angeles County Supervisor for the Second District in 2008, and currently serves as Chairman of the Board of Supervisors. He previously served the 26th District in the California State Senate, where he chaired the Senate’s Committee on Business, Professions and Economic Development and its two subcommittees on Professional Sports and Entertainment, and The Economy, Workforce Preparation and Development. He also served on the Senate Appropriations, Energy, Utilities and Communications, Health and Public Safety committees.  He served on the Los Angeles City Council starting in 1991 for nearly a dozen years, departing as Council President pro Tempore, and served two terms in the California State Assembly, where he chaired the Assembly Democratic Caucus.',
    'michael-antonovich-cf1d45635033': '',
    'don-knabe-bff1c136c0d9': '',
    'sheila-kuehl-9c9abd7a6ff8': 'LA County Supervisor Sheila James Kuehl represents LA County’s Third District. She serves as the Second Vice Chair of the LA Metro Board. Throughout a two-decade career as a state Assemblymember and Senator, an LA County Supervisor and Metro Board member, she has been a strong and vocal champion of public transportation.<br><br>She served eight years in the State Senate and six years in the State Assembly. She was one of the earliest supporters of the Expo Authority, and authored the state legislation that created the Exposition Line Authority. She currently sits on the Expo Authority Board.<br><br>She was the first woman in California history to be named Speaker Pro Tempore of the Assembly, and the first openly gay or lesbian person to be elected to the California Legislature. Kuehl served as chair of the Senate Health and Human Services Committee, Natural Resources and Water Committee, and Budget Subcommittee on Water, Energy and Transportation, as well as the Assembly Judiciary Committee. She authored 171 bills that were signed into law.<br><br>Prior to her election to the Legislature, as a public-interest attorney, Kuehl drafted and fought to get into California law more than 40 pieces of legislation relating to children, families, women, and domestic violence. She was a law professor at Loyola, UCLA and USC Law Schools and co-founded and served as managing attorney of the California Women’s Law Center. Supervisor Kuehl graduated from Harvard Law School in 1978<br><br>In her youth, she was known for her portrayal of the irrepressible Zelda Gilroy in the television series, “The Many Loves of Dobie Gillis.”',
    'james-butts-dc85ae14f195': 'James Butts has 44 years of public safety and municipal government experience. He holds a Bachelor of Science Degree in Business from California State University at LA and a Masters Degree in Business from California Polytechnic University at Pomona. He served 19 years in the Inglewood Police Department rising to the rank of Deputy Chief.  In 1991 Butts was appointed to serve as Chief of Police for the City of Santa Monica where he served 15 years and was the first African American and youngest person to earn that rank in Santa Monica. In 2006, he was appointed as an Assistant General Manager of the Los Angeles World Airport system, where he oversaw Public Safety and Counterterrorism. He took LAX to a number 1 security ranking nationwide by the TSA in 2009.  On January 11, 2011, James T. Butts, Jr., was elected as the City of Inglewood’s 12th mayor. In less than 5 years his strategic leadership and operational expertise catapulted the City national prominence as home to MSG and the LA Rams. In 2014 Mayor Butts was reelected receiving 83% of the votes cast – the highest margin of victory in Inglewood electoral history.',
    'hilda-l-solis-b1533a264870': 'Hilda Solis was elected as Los Angeles County Supervisor for the First District of Los Angeles County in 2014. Prior to becoming Supervisor, Solis was confirmed as Secretary of Labor in 2009, becoming the first Latina to serve in the United States Cabinet. Before that, Solis represented the 32nd Congressional District in California, a position she held from 2001 to 2009. Solis graduated from California State Polytechnic University, Pomona, and earned a Master of Public Administration from the University of Southern California. A former federal employee, she worked in the Carter White House Office of Hispanic Affairs and was later appointed as a management analyst with the Office of Management and Budget in the Civil Rights Division.',
    'carrie-bowen-af5a8ab39aad': 'Carrie Bowen was appointed to the Metro Board by California Governor Jerry Brown. Carrie has worked for the Department of Transportation for approximately 25 years and was appointed to her current position, Director of the California Department of Transportation District 7 (Los Angeles and Ventura Counties), in 2014. Bowen is responsible for planning, construction, operation and maintenance of the State freeway and highway system in the region. She oversees a construction program of more than $1 billion, a system that handles more than 100,000 million vehicle miles traveled daily, and 2,500 employees. Previously, Bowen was the District 10 (Stockton) Director. She began her career with Caltrans as an Associate Environmental Planner and rose to the position of Deputy District Director for the Central Region Environmental Division, overseeing Caltrans’ environmental work in 20 counties and staff in four districts. During this time, Caltrans prepared for the implementation of the National Environmental Protection Act Delegation and Bowen was instrumental in its success.<br><br> Her vision for the future of transportation is to build strong relationships with local partners; utilize her skills and knowledge acquired through 25 years of diverse experience, including skills to creatively resolve issues, motivate employees, manage tasks and deliver a successful program; and continue to strive to improve the quality of California’s transportation systems, improve and enhance the environment and support smart growth and sustainable approaches to resolve our infrastructure needs.',
    'paul-krekorian-6946f7e6401b': 'Born and raised in the San Fernando Valley, Paul Krekorian has spent more than a decade in public service. Since 2010, he has served on the Los Angeles City Council where his leadership as Chairman of the Budget and Finance Committee helped guide the City through the Great Recession and toward greater economic promise. Paul is also Chairman of the Ad Hoc Committee on Job Creation, the Vice Chair of the Entertainment and Facilities Committee, and sits on the Economic Development Committee, Trade, Commerce and Technology Committee, Executive Employee Relations Committee and the Board of Referred Powers.<br><br>In addition to serving on the Metro Board of Directors, Paul also serves on the boards of Metrolink, and the San Fernando Valley Council of Governments.<br><br>Paul graduated from Reseda’s Cleveland High School before earning his B.A. in Political Science from the University of Southern California and a law degree from UC Berkeley. Upon graduating, he spent two decades practicing business, entertainment, and property litigation. <br><br>In 2006, after three years on the Burbank Board of Education, Paul won election to the California State Assembly, representing the 43rd District. Paul is the first Armenian-American to be elected to public office in the City of Los Angeles.',
    'mike-bonin-00ef9b2a3527': 'Mike Bonin was elected to represent the 11th District on the Los Angeles City Council in 2013, and three weeks later was appointed to the Metro Board of Directors by Mayor Eric Garcetti. Bonin is also the Chair of the Council’s Transportation Committee, and vice chair of the Metro Expo Line Construction Authority. In addition to his transportation portfolio, Mike is vice-chair of the council committee that oversees LAX International Airport. He also serves on the Council’s Homelessness and Poverty Committee, Budget and Finance Committee and Public Safety Committee. A former newspaper reporter, Mike graduated from Harvard University in 1989 with a B.A. in United States History.',
    'john-fasana-f9f830cb255d': 'John Fasana is a City Councilmember, the Los Angeles County Metropolitan Transportation Authority Board Chairperson, and is one of four City Selection Committee appointees to the 13-member Metro Board of Directors. He has represented the San Gabriel Valley on the Metro Board since its inception in 1993 and previously served as Metro Board Chair from 2001 to 2002. He also currently serves as the Executive Management Committee Chairperson. During his tenure on the Metro Board, he has tirelessly worked with his colleagues in Sacramento and Washington DC to obtain several billion dollars for LA County residents for critically needed multimodal congestion relief projects.<br><br>Mr. Fasana was first elected to the Duarte City Council in November 1987, and reelected in 1991, 1995, 1999, 2003, 2007 and 2011, and reappointed in 2015. He served as Mayor in 1990, 1997, 2003 and 2009. As a Councilmember, he has promoted Duarte\'s interests in transportation, community services, and environmental protection.<br><br>Mr. Fasana has also served on the Board of the San Gabriel Valley Council of Governments (COG) since its inception, representing 31 cities and over 2 million residents working together to solve regional issues and in the past served on Foothill Transit’s Board. In 2015, he retired from his 35 year career with Southern California Edison. John is a graduate of Whittier College, he and his wife Kris have three adult children, all of whom were educated in Duarte’s public schools and two sons-in-law.',
    'robert-garcia-3d501fbcf51c': 'Dr. Robert Garcia is an accomplished educator and the 28th Mayor of Long Beach. He was elected on June 3rd, 2014, becoming the youngest person ever to hold that office. Mayor Garcia has taken a leadership role in balancing the city budget, reforming pensions, expanding park space, and investing in technology, and is committed to moving Long Beach forward by attracting tech and green jobs, creating new educational partnerships, and rebuilding the city’s aging streets, sidewalks and alleys.<br><br>Garcia has been a member of the public policy and communications faculty at the University of Southern California, and taught Communication Studies at both California State University, Long Beach and Long Beach City College. His passion for education led him to pursue a Doctorate in Higher Education, which he was awarded in 2010 after publishing his dissertation on California\'s Master Plan for Education. The Mayor also holds a Master\'s Degree in Communication Management from the University of Southern California and a Bachelor\'s Degree in Communication Studies from California State University, Long Beach.<br><br>In 2007, Garcia co-founded and launched the Long Beach Post, a Long Beach based media website and newspaper. By the time he left the company in 2013, the small business had grown into an important source for community information and has more than 45,000 online subscribers. As Vice Mayor and First District Councilmember, a position he held from 2009-2014, Garcia served as the Chair of the Long Beach Public Safety Committee and the Long Beach Housing Authority, and on both the Federal Legislative and State Legislative Council Committees. He also served on the California Coastal Commission from January, 2013 until taking office as Mayor of Long Beach.<br><br>The Mayor was born in Lima, Peru, and immigrated to the United States at age 5 with his family. He grew up in Covina, California and was raised by three strong women in his life - his mother, grandmother and aunt. Garcia was the first person in his family to attend and graduate college. While at CSULB, Robert was elected student body president.<br><br>Mayor Garcia has been named one of Long Beach\'s "Most Innovative Minds" by Long Beach Magazine, to the Advocate Magazine\'s 40 Under 40 List in 2010, and to Instinct Magazine\'s Leading Men in 2009. He was the recipient of the 2014 Vanguard Leadership award from Equality California. Garcia lives in downtown Long Beach.',
    'janice-hahn-4682bb5db3dd': 'Janice Hahn has served on the Metro Board since 2016, when she was elected to the Los Angeles County Board of Supervisors, representing District Four. She previously served in Congress as the representative for California\'s 44th congressional district (2013-2016) and 36th congressional district (2011-2012). Before she was elected to Congress in 2011, Hahn served eight years on the Los Angeles City Council representing the Harbor Area, District 15.<br><br>Prior to her career in public service, Hahn worked in the private sector. She attended Abilene Christian University in Texas, earning a bachelor of science in education in 1974. She taught at the Good News Academy, a private school in Westchester from 1974 to 1978. Her other work in the private sector has included Public Affairs Region Manager at Southern California Edison from 1995 to 2000, Vice President for Prudential Securities in Public Finance, Director of Community Outreach for Western Waste Industries, and Director of Marketing for the Alexander Haagen Company.',
    'kathryn-barger-52be67cf2369': 'Kathryn Barger has served on the Metro Board since 2016, when she was elected to the Los Angeles County Board of Supervisors, representing the Fifth District. Kathryn is a lifelong resident of the Fifth District who began her career in public service as a student intern in the office of Supervisor Michael D. Antonovich while earning her BA in Communications from Ohio Wesleyan University. She rose to become his Chief Deputy Supervisor in 2001, where she served until her election to the Board.<br><br>During the course of her county career as the Chief Policy Advisor on Health, Mental Health, Social Service and Children\'s issues, Kathryn provided leadership to deliver efficient and effective services and programs that have significantly improved the quality of life for foster children, seniors, veterans, the disabled and the mentally ill.<br><br>Committed to keeping our neighborhoods and communities safe, she has worked with state and federal leaders along with our County District Attorney\'s office, Sheriff, and other law enforcement agencies to implement tough laws and vital public safety initiatives.',
    'shirley-choate-03b7445fec78': 'As Acting Caltrans District 7 Director, Shirley Choate is responsible for assisting the District Director in ensuring the sustainability and livability of the State Highway system in Los Angeles and Ventura counties. Through planning, construction, operation and maintenance, she helps facilitate the movement of people, goods and services in a safe and efficient manner. Shirley is also responsible for the oversight of internal operations which includes 2,700 employees in the divisions of Administration, Construction, Design, Environmental Planning and Engineering, External Affairs, Maintenance, Operations, Planning, Programming/Project Management and Right of Way.<br><br>Shirley is championing innovation in policies and practices for the District and its employees. She is also developing strong, collaborative partnerships with local and regional agencies that will enhance the District\'s economy and livability.<br><br>Shirley has worked for Caltrans for over 35 years. She has spent 18 of those years as the Deputy District Director for Districts 2 and 7. She has also taken on the role of acting Division Chief for Transportation Planning and acting Assistant Division Chief of Construction. Her extensive civil service experience includes the planning, designing and construction of hundreds of transportation projects worth over $4 billion. She oversees more than $475 million in personnel and operating expenses.<br><br>Her performance-based approach has significantly improved the delivery of capital outlay commitments and, under her leadership, the program was awarded the 2006 Caltrans Capital Delivery Award for "Best Overall Delivery" and the 2008 Caltrans "Best Overall Project Management" award.<br><br>Shirley graduated from UC Berkeley with a BS in Civil Engineering in 1982 and received a Master\'s Certificate in Project Management from The George Washington University-School of Business and Public Management in 2002. She is a registered Civil Engineer (Professional Engineer or P.E.) in the State of California as well as a certified Project Management Professional (P.M.P.).',
    'phil-washington-2daf84e096e2': 'Phillip A. Washington was unanimously selected CEO of the Los Angeles County Metropolitan Transportation Authority (LA Metro) by the LA Metro Board of Directors on March 12, 2015.<br><br>As LA Metro CEO, Washington manages a total balanced budget of $6.6 billion for FY19, is responsible for overseeing $15+ billion in capital projects, providing oversight of an agency of nearly 11,000 employees and transports 1.4 million boarding passengers daily, riding on a fleet of 2,000 clean-air buses and six rail lines. LA Metro is also the lead transportation planning and programming agency for LA County. As such, it is a major construction agency that oversees bus, rail, highway and other mobility-related building projects – together representing the largest modern public works program in North America.<br><br><a href="http://media.metro.net/board/images/biography-ceo-washington.pdf" target="_blank"><i class="fa fa-download"></i> Download the biography for Metro CEO Phillip A. Washington</a>',
}
# notable positions that aren't district representatives, e.g. mayor & city clerk
# keys should match person slugs
EXTRA_TITLES = {
    # e.g. 'emanuel-rahm': 'Mayor',
}

USING_NOTIFICATIONS = False