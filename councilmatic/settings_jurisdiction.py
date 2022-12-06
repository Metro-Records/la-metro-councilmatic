from operator import itemgetter

# These are all the settings that are specific to a jurisdiction

###############################
# These settings are required #
###############################

OCD_CITY_COUNCIL_NAME = 'Board of Directors'
CITY_COUNCIL_NAME = 'Metro'
OCD_JURISDICTION_IDS = ['ocd-jurisdiction/country:us/state:ca/county:los_angeles/transit_authority']
LEGISLATIVE_SESSIONS = ['2014', '2015', '2016', '2017', '2018', '2019'] # the last one in this list should be the current legislative session
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
legislation_types = [
    {
        'name': 'Budget',
        'search_term': 'budget',
        'fa_icon': 'dollar',
        'html_id': 'budget',
        'html_desc': True,
        'desc': 'A plan of financial operations for a given period, including proposed expenditures, authorized staffing levels, and a proposed means of financing them. Metro follows a July 1 to June 30 Fiscal Year.  Its annual budgets are typically approved by the Board after a public hearing in May of each year. Individual capital projects over $5 million have a Life of Project (LOP) budget estimate reviewed by the Board of Directors.',
    },
    {
        'name': 'Fare / Tariff / Service Change',
        'search_term': 'fare / tariff / service change',
        'html_id': 'fare-tariff-service-change',
        'fa_icon': 'dollar',
        'html_desc': True,
        'desc': 'Chapter 2-50 of Metro’s Administrative Code (its Ordinances) set the parameters and procedures for holding public hearings in advance of any fare, tariff or major service changes. Fare changes and major service changes require public hearings and Title VI analysis. Minor service changes are continually reviewed and approved with public participation by Metro’s Service Councils for the San Gabriel Valley, San Fernando Valley, Westside, Southbay and Gateway Cities regions of the County.',
    },
    {
        'name': 'Formula Allocation / Local Return',
        'search_term': 'formula allocation / local return',
        'html_id': 'formula-allocation-local-return',
        'fa_icon': 'dollar',
        'html_desc': True,
        'desc': 'Formula Allocation and Local Return are adopted methods for distributing Federal, State and local transit and transportation funding. Funding is allocated to 16 municipal transit operators using audited performance data, and 88 cities in Los Angeles County using population data. The majority of this funding is local sales tax revenues from Proposition A (1980), Proposition C (1990) and Measure R (2008).',
    },
    {
        'name': 'Agreement',
        'search_term': 'agreement',
        'html_id': 'agreement',
        'fa_icon': 'file-text-o',
        'html_desc': True,
        'desc': 'A negotiated arrangement between parties.',
    },
    {
        'name': 'Application',
        'search_term': 'application',
        'html_id': 'application',
        'fa_icon': 'file-text-o',
        'html_desc': True,
        'desc': 'A formal request, usually for state and federal funding programs.',
    },
    {
        'name': 'Contract',
        'search_term': 'contract',
        'html_id': 'contract',
        'fa_icon': 'file-text-o',
        'html_desc': True,
        'desc': 'A written agreement executed by Metro and an individual who or firm which thereby becomes the Contractor. The contract sets forth the rights or obligations of the parties in connection with the furnishing of goods or services, including construction. Contracts over $500,000 require Board approval.',
    },
    {
        'name': 'Informational Report',
        'search_term': 'informational report',
        'html_id': 'informational-report',
        'fa_icon': 'file-text-o',
        'html_desc': True,
        'desc': 'Metro staff will provide various informational reports to the Board of Directors as background to the Agency’s policies, programs, plans, situations and events. Many of these reports are circulated publicly as “Receive and File” reports.',
    },
    {
        'name': 'Federal Legislation / State Legislation (Position)',
        'search_term': 'federal legislation / state legislation (position)',
        'html_id': 'federal-state-legislation',
        'fa_icon': 'file-text-o',
        'html_desc': True,
        'desc': 'Metro’s Government Relations staff seeks Board of Director approval prior to taking a position of “support”, “oppose”, or “work with author” on significant State and Federal legislation.',
    },
    {
        'name': 'Ordinance / Administrative Code',
        'search_term': 'ordinance / administrative code',
        'html_id': 'ordinance-administrative-code',
        'fa_icon': 'file-text-o',
        'html_desc': True,
        'desc': 'Metro as an entity created by the State of California for Los Angeles County has the legal authority to adopt ordinances. Its adopted ordinances are collectively referred to as the Metro Administrative Code. Metro ordinances are enacted pursuant to the ordinance adopting authority granted to the Southern California Rapid Transit District by Public Utilities Code Sections 30273 et seq., and to the Los Angeles Comment [SAR1]: Capitalize Board Report Comment [SAR2]: Items included here are only those where text is edited. All existing types of Board Reports should still be included as is. County Transportation Commission by Public Utilities Code Sections 130103 and 130105. Ordinances include, among others: <br><br>a.) Metro’s Retail Transactions and Use Taxes (Sales Taxes) <br>b.) Transit Court <br>c.) Codes of Conduct <br>d.) Settlement of Claims <br>e.) Public Hearings <br>f.) Contracting <br>g.) Tolls and Enforcement of Toll Violations <br>h.) Parking',
    },
    {
        'name': 'Plan',
        'search_term': 'plan',
        'html_id': 'plan',
        'fa_icon': 'file-text-o',
        'html_desc': True,
        'desc': 'A detailed proposal for achieving public policy goals.  Major Metro plans include the Long Range Transportation Plan, the Short Range Transportation Plan, the Union Station master plans, and subject specific action or strategic plans.',
    },
    {
        'name': 'Policy',
        'search_term': 'policy',
        'html_id': 'policy',
        'fa_icon': 'file-text-o',
        'html_desc': True,
        'desc': 'A course or principle of action adopted by the Board of Directors in carrying out its legal authority and mission. Examples include Metro’s Debt policy, Energy and Sustainability Policy, Alternative Fuel Policy, Film Production, Financial Stability, Formula Allocation Procedures, Holiday Fares, Investment, Metro System Advertising, Procurement, Property Naming, Small Business, Transit Service, and other public policies. Policies remain in effect until modified or repealed by the Board.',
    },
    {
        'name': 'Program',
        'search_term': 'program',
        'html_id': 'program',
        'fa_icon': 'file-text-o',
        'html_desc': True,
        'desc': 'A group of related activities performed by one or more organizational units for the purpose of accomplishing a function for which Metro is responsible.  Examples are the Joint Development Program, Rider Relief Transportation Program, Immediate Needs Transportation Program, Congestion Management Program, Transit Safety Program, Soundwall Program, Vanpool Program and many more.',
    },
    {
        'name': 'Project',
        'search_term': 'project',
        'html_id': 'project',
        'fa_icon': 'file-text-o',
        'html_desc': True,
        'desc': 'A carefully planned enterprise designed to achieve a particular aim. Major projects at Metro usually have a Life of Project (LOP) budget, environmental impact report, preliminary engineering work, and more. Examples would be light rail projects, subway projects, highway projects, bikeway projects, freight and goods movement facilities, information and technology improvements, and other transportation infrastructure for Los Angeles County.',
    },
    {
        'name': 'Appointment',
        'search_term': 'appointment',
        'html_id': 'appointment',
        'fa_icon': 'user',
        'html_desc': True,
        'desc': 'The Board of Directors makes appointments to various committees created for the purpose of collecting and reviewing public input such as the Citizens Advisory Council and the Metro Service Councils, and also to external organizations that include representation from Metro such as Metrolink.',
    },
    {
        'name': 'Minutes',
        'search_term': 'minutes',
        'html_id': 'minutes',
        'fa_icon': 'calendar',
        'html_desc': True,
        'desc': 'The permanent official legal record of the business transacted, resolutions adopted, votes taken, and general proceedings of the Board of Directors. ',
    },
    {
        'name': 'Motion / Motion Response',
        'search_term': 'motion / motion response',
        'html_id': 'motion-response',
        'fa_icon': 'bullhorn',
        'html_desc': True,
        'desc': 'These are issues raised by Board Members during meetings. Motions are usually proposed in writing by one or more Board Members. Motions include background information and a specific directive to staff after the words “I therefore move”, and then voted on. When adopted by the Board with a majority vote, staff is given a specific timeframe to research and respond back.',
    },
    {
        'name': 'Oral Report / Presentation',
        'search_term': 'oral report / presentation',
        'html_id': 'oral-report-presentation',
        'fa_icon': 'bullhorn',
        'html_desc': True,
        'desc': 'Metro staff make public  presentations to the board during public meetings via Powerpoint and oral reports.  These are included in the agendas and meeting webcasts.',
    },

    {
        'name': 'Public Hearing',
        'search_term': 'public hearing',
        'html_id': 'public-hearing',
        'fa_icon': 'bullhorn',
        'html_desc': True,
        'desc': 'Various board actions require a public hearing prior to voting.  These include the adoption of the annual budget, fare changes, major service changes, ordinances, eminent domain actions and others as defined by State/Federal law or board ordinance.',
    },
    {
        'name': 'Resolution',
        'search_term': 'resolution',
        'html_id': 'resolution',
        'fa_icon': 'commenting-o',
        'html_desc': True,
        'desc': 'Certain board actions require the adoption of a board resolution, usually financial and real estate transactions.',
    },
    {
        'name': 'Board Box / Board Correspondence',
        'search_term': 'board box',
        'html_id': 'board-box',
        'fa_icon': 'commenting-o',
        'html_desc': True,
        'desc': 'Formal information communication from Metro staff to the Board, which does not require Board action. Historically, these items were called "Board Box"(es), because a physical box containing each month\'s items was delivered to the Board for review. Because these items are now delivered digitally, their "Board Report Type" designation is "Board Correspondence" so the nature of these items is more clear to the public. We are in the process of importing Board Boxes to this website; in the meantime, please access Board Box/Correspondence items through the <a href="/archive-search">Archive Search</a>. You can also access a directory of Board Correspondence from 2015 to present, by year, <a href="http://boardarchives.metro.net/BoardBox/">here</a>.'
    },
]

# we want board report types to be in alphabetical order on Metro's About page
LEGISLATION_TYPE_DESCRIPTIONS = sorted(legislation_types, key=itemgetter('name'))

BILL_STATUS_DESCRIPTIONS = {
    'ADOPTED': {
        'definition': 'Item was adopted by a majority vote of the Board.',
        'search_term': 'Adopted'
    },
    'ADOPTED AS AMENDED': {
        'definition': 'Item was adopted as amended by a majority vote of the Board.',
        'search_term': 'Adopted'
    },
    'APPROVED': {
        'definition': 'Item was approved by a majority vote of the Board.',
        'search_term': 'Approved'
    },
    'APPROVED AS AMENDED': {
        'definition': 'Item was approved as amended by a majority vote of the Board.',
        'search_term': 'Approved'
    },
    'APPROVED ON CONSENT CALENDAR': {
        'definition': 'Item was approved on Consent Calendar by a majority vote of the Board.',
        'search_term': 'Approved'
    },
    'CARRIED OVER': {
        'definition': 'Item was carried over to the next Committee or Regular Board Meeting.',
        'search_term': 'Active'
    },
    'FAILED': {
        'definition': 'Item failed due to insufficient votes.',
        'search_term': 'Failed'
    },
    'FORWARDED DUE TO ABSENCES AND CONFLICTS': {
        'definition': 'Item was forwarded from a Committee to the Regular Board Meeting due to absences and conflicts.',
        'search_term': 'Active'
    },
    'FORWARDED WITHOUT RECOMMENDATION': {
        'definition': 'Item was forwarded to the Regular Board Meeting without recommendation.',
        'search_term': 'Active'
    },
    'RECEIVED': {
        'definition': 'Item was received by the Committee or Board. (Oral report)',
        'search_term': 'Received'
    },
    'RECEIVED AND FILED': {
        'definition': 'Item was was received and filed by the Committee or Board.',
        'search_term': 'Received'
    },
    'RECOMMENDED FOR APPROVAL': {
        'definition': 'Committee members recommended that the item be approved by the Full Board.',
        'search_term': 'Active'
    },
    'RECOMMENDED FOR APPROVAL AS AMENDED': {
        'definition': 'Committee members recommended that the item be approved as amended by the Full Board.',
        'search_term': 'Active'
    },
    'REFERRED': {
        'definition': 'Item was referred to another Committee or Full Board.',
        'search_term': 'Active'
    },
    'WITHDRAWN': {
        'definition': 'Item was withdrawn from the agenda.',
        'search_term': 'Withdrawn'
    },
    'NO ACTION TAKEN': {
        'definition': 'No action was taken on the item.',
        'search_term': 'Active'
    },
    'NOT DISCUSSED': {
        'definition': 'Item was not discussed.',
        'search_term': 'Active'
    },
    'APPROVED UNDER RECONSIDERATION': {
        'definition': 'Item was approved when considered a 2nd time.',
        'search_term': 'Approved'
    },
    'FAILED UNDER RECONSIDERATION': {
        'definition': 'Item failed when considered a 2nd time.',
        'search_term': 'Failed'
    },
    'ADOPTED UNDER RECONSIDERATION': {
        'definition': 'Item was adopted when considered a 2nd time.',
        'search_term': 'Adopted'
    },
    'APPROVED AS AMENDED UNDER RECONSIDERATION': {
        'definition': 'Item was approved by a majority vote of the Board as amended when considered a 2nd time.',
        'search_term': 'Approved'
    },
    'ADOPTED AS AMENDED UNDER RECONSIDERATION': {
        'definition': 'Item was adopted by a majority vote of the Board as amended when considered a 2nd time.',
        'search_term': 'Adopted'
    },
}


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
    "EVENTS": "<p>Committee meetings are the first level of review for Metro business matters being brought to the Board of Directors for their review and decision.</p><p>Committee meetings take place on Wednesday and Thursday, the week before a regular, scheduled Board Meeting. A unanimous vote at the Committee level will place an item on the Consent Calendar of the Board of Directors.</p><p>The full Board of Directors typically meets once a month to review presented budgets, contracts, policies and programs, and make decisions about what to adopt, fund and build.</p><p>In addition to the Board of Directors meetings, Metro also has appointed Advisory Committees which meet. <a href='https://www.metro.net/calendar/category/committees-subcommittees/' target='_blank'>Learn more about \"Advisory Committees\" here.</a></p>",
    "COUNCIL_MEMBERS":  "",
}

MEMBER_BIOS = {
    'ara-j-najarian': 'Ara J. Najarian has served on the Glendale City Council for 12 years and was recently re-elected to his fourth term with the highest number of votes of all candidates.  He has served three terms as Mayor of Glendale.  Before serving on Council Ara was elected to the Glendale Community College Board of Trustees.<br><br>Ara is a regional leader in transportation, holding a seat on the Los Angeles MTA since 2006 and previously serving as MTA Chairman.  Ara also is 2nd Vice Chairman of Metrolink and has served on the Board of Directors since 2007.<br><br>Ara sits on the Board of Directors of the San Fernando Valley Council of Governments, and held the position of Chairman.<br><br>Ara received a B.A in Economics from Occidental College, and his J.D. degree from the University of Southern California Law School.  In his private life, Ara is a practicing attorney in Glendale.  He is married to Palmira Perez, and has two boys.  ',
    'diane-dubois': 'Lakewood City Councilmember and current Metro Board member Diane DuBois was elected to the Board of Directors in 2009 by the 27 Cities of Southeast Los Angeles County that form the Gateway Cities Council of Governments. Councilmember DuBois, a Lakewood Planning and Environment Commissioner for 28 years, was first elected to the city council in 2005. She has been a board member and volunteer of Lakewood Meals-On-Wheels, a board member of the Greater Long Beach Girl Scout Council, a board member of Lakewood Regional Medical Center, the Pan American Association scholarship chair, a member and past president of Soroptimist International of Lakewood/Long Breach, and a volunteer at Pathways Volunteer Hospice.',
    'jacquelyn-dupont-walker': 'Jacquelyn Dupont-Walker is the founding president of the Ward Economic Development Corporation (WEDC) and for 29 years has led the corporation in developing over 280 units of affordable housing, one major shopping mall, encouraging indigenous leadership, creating neighborhood networks, facilitating job creation, conducting asset mapping, and spearheading an intergenerational community building effort. She also chairs the USC Master Plan Advisory Committee where she represents the residents of the West Adams district. Mrs. Dupont-Walker also chairs the Exposition Park Strategic Plan and is Vice-Chair of the Baldwin Hills Conservancy.<br><br> In addition to WEDC, Mrs. Dupont-Walker serves as the AME Church International Social Action Officer and on a host of other civic organizations. As a lifelong member of the AME Church, Mrs. Dupont-Walker created AME V-Alert (voter mobilization plan). She is an officer of Ward AME Church in Los Angeles where she serves on the Board of Stewards, and also the Lay and Missionary ministries and chairs the Social Action Commission.',
    'eric-garcetti': 'Eric Garcetti is the 42nd Mayor of Los Angeles. His “back to basics” agenda is focused on job creation and solving everyday problems for L.A. residents.<br><br>Mr. Garcetti was elected four times by his peers to serve as President of the Los Angeles City Council from 2006 to 2012. From 2001 until taking office as Mayor, he served as the Councilmember representing the 13th District which includes Hollywood, Echo Park, Silver Lake, and Atwater Village -- all of which were dramatically revitalized under Mr. Garcetti leadership.<br><br>Mr. Garcetti was raised in the San Fernando Valley and earned his B.A. and M.A. from Columbia University. He studied as a Rhodes Scholar at Oxford and the London School of Economics, and taught at Occidental College and USC. A fourth generation Angelino, he and his wife, Amy Elaine Wakeland, have a young daughter. He is a Lieutenant in the U.S. Navy reserve and is an avid jazz pianist and photographer.',
    'mark-ridley-thomas': 'Since he was overwhelmingly elected to the Los Angeles County Board of Supervisors in 2008, and reelected in 2012 and 2016, Mark Ridley-Thomas has distinguished himself as an effective leader for more than two million Second District residents, tackling such critical issues as homelessness, voting rights, affordable quality education, living wage, police accountability, healthcare for all, and more. First elected to public office in 1991, he served with distinction on the Los Angeles City Council for nearly a dozen years, departing as Council President pro Tempore. He later served in the California State Assembly, where he chaired the Jobs, Economic Development and Economy Committee, and in the California State Senate, where he chaired its Committee on Business, Professions and Economic Development.',
    'sheila-kuehl': 'Supervisor Sheila James Kuehl, representing Los Angeles County\'s Third District, was elected on November 4, 2014, assumed office on December 1, 2014 and is currently the Chair of the Board of Supervisors.<br><br>In her first three years on the Board, she has undertaken or collaborated in a number of initiatives and motions to improve the quality of life and reform systems in the County, including increasing the minimum wage, creating a Sheriff\'s Oversight Commission, providing unprecedented funding and services for our homeless population and those trying to find and keep affordable housing, increasing services and support for relative caregivers for our foster children, supporting the creation of the Office of Child Protection, creating oversight of the Probation Department, innovating on issues of water conservation and recycling, creating a County-led Community Choice Aggregation (CCA) JPA to bring green power choices to County residents, protecting our arts venues and productions, spurring the construction and re-opening of the John Anson Ford Theatres, reforming both our adult and juvenile justice systems to emphasize and enhance “second chance” and anti-recidivism programs, including the opening of Campus Kilpatrick, a state-of-the-art juvenile justice facility that emphasizes rehabilitation and preparation for a constructive future, protection of the Santa Monica Mountains, as well as the Coast, kicking off a Women and Girls Initiative to build toward a County-wide collaboration on needed changes and programs in all County departments and services, bringing together three County health departments into a new Agency model to break down barriers to service for those who need physical health, mental health and substance abuse treatment, bringing a focus in County Departments on better serving and supporting our LGBTQ youth who comprise almost 20% of our foster kids, and much more.<br><br>She is also Chair of the Board of Commissioners of First 5, LA, First Vice Chair of the Board of Directors of Metro, Vice Chair of the Board of the new CCA and Chair of the Countywide Criminal Justice Coordination Committee.<br><br>Supervisor Kuehl served eight years in the State Senate and six years in the State Assembly. She was the Founding Director of the Public Policy Institute at Santa Monica College and, in 2012, was Regents\' Professor in Public Policy at UCLA.<br><br>She was the first woman in California history to be named Speaker Pro Tempore of the Assembly, and the first openly gay or lesbian person to be elected to the California Legislature. She served as chair of the Senate Health and Human Services Committee, Natural Resources and Water Committee, and Budget Subcommittee on Water, Energy and Transportation, as well as the Assembly Judiciary Committee.<br><br>She authored 171 bills that were signed into law, including legislation to establish paid family leave, establish nurse to patient ratios in hospitals; protect the Santa Monica Mountains and prohibit discrimination on the basis of gender and disability in the workplace and sexual orientation in education. She fought to establish true universal health insurance in California.<br><br>Prior to her election to the Legislature, as a public-interest attorney Supervisor Kuehl drafted and fought to get into California law more than 40 pieces of legislation relating to children, families, women, and domestic violence. She was a law professor at Loyola, UCLA and USC Law Schools and co-founded and served as managing attorney of the California Women\'s Law Center.<br><br>Supervisor Kuehl graduated from Harvard Law School in 1978. In her youth, she was known for her portrayal of the irrepressible Zelda Gilroy in the television series, “The Many Loves of Dobie Gillis.”',
    'james-butts': 'James Butts has 44 years of public safety and municipal government experience. He holds a Bachelor of Science Degree in Business from California State University at LA and a Masters Degree in Business from California Polytechnic University at Pomona. He served 19 years in the Inglewood Police Department rising to the rank of Deputy Chief.  In 1991 Butts was appointed to serve as Chief of Police for the City of Santa Monica where he served 15 years and was the first African American and youngest person to earn that rank in Santa Monica. In 2006, he was appointed as an Assistant General Manager of the Los Angeles World Airport system, where he oversaw Public Safety and Counterterrorism. He took LAX to a number 1 security ranking nationwide by the TSA in 2009.  On January 11, 2011, James T. Butts, Jr., was elected as the City of Inglewood’s 12th mayor. In less than 5 years his strategic leadership and operational expertise catapulted the City national prominence as home to MSG and the LA Rams. In 2014 Mayor Butts was reelected receiving 83% of the votes cast – the highest margin of victory in Inglewood electoral history.',
    'hilda-l-solis': 'Supervisor Hilda L. Solis was sworn in as Los Angeles County Supervisor for the First District of Los Angeles County on December 1, 2014.<br><br>Prior to becoming Supervisor she served as Secretary of Labor. Supervisor Solis was confirmed on February 24, 2009, becoming the first Latina to serve in the United States Cabinet. Before that, Supervisor Solis represented the 32nd Congressional District in California, a position she held from 2001 to 2009.<br><br>In the Congress, Supervisor Solis\' priorities included expanding access to affordable health care, protecting the environment, and improving the lives of working families. A recognized leader on clean energy jobs, she authored the Green Jobs Act which provided funding for “green” collar job training for veterans, displaced workers, at risk youth, and individuals in families under 200 percent of the federal poverty line.<br><br>In 2007, Supervisor Solis was appointed to the Commission on Security and Cooperation in Europe (the Helsinki Commission), as well as the Mexico — United States Interparliamentary Group. In June 2007, Solis was elected Vice Chair of the Helsinki Commission’s General Committee on Democracy, Human Rights and Humanitarian Questions. She was the only U.S. elected official to serve on this Committee.<br><br>A nationally recognized leader on the environment, Supervisor Solis became the first woman to receive the John F. Kennedy Profile in Courage Award in 2000 for her pioneering work on environmental justice issues. Her California environmental justice legislation, enacted in 1999, was the first of its kind in the nation to become law.<br><br>Supervisor Solis graduated from California State Polytechnic University, Pomona, and earned a Master of Public Administration from the University of Southern California. A former federal employee, she worked in the Carter White House Office of Hispanic Affairs and was later appointed as a management analyst with the Office of Management and Budget in the Civil Rights Division.',
    'carrie-bowen': 'Carrie Bowen was appointed to the Metro Board by California Governor Jerry Brown. Carrie has worked for the Department of Transportation for approximately 25 years and was appointed to her current position, Director of the California Department of Transportation District 7 (Los Angeles and Ventura Counties), in 2014. Bowen is responsible for planning, construction, operation and maintenance of the State freeway and highway system in the region. She oversees a construction program of more than $1 billion, a system that handles more than 100,000 million vehicle miles traveled daily, and 2,500 employees. Previously, Bowen was the District 10 (Stockton) Director. She began her career with Caltrans as an Associate Environmental Planner and rose to the position of Deputy District Director for the Central Region Environmental Division, overseeing Caltrans’ environmental work in 20 counties and staff in four districts. During this time, Caltrans prepared for the implementation of the National Environmental Protection Act Delegation and Bowen was instrumental in its success.<br><br> Her vision for the future of transportation is to build strong relationships with local partners; utilize her skills and knowledge acquired through 25 years of diverse experience, including skills to creatively resolve issues, motivate employees, manage tasks and deliver a successful program; and continue to strive to improve the quality of California’s transportation systems, improve and enhance the environment and support smart growth and sustainable approaches to resolve our infrastructure needs.',
    'paul-krekorian': 'Born and raised in the San Fernando Valley, Paul Krekorian has spent more than a decade in public service. Since 2010, he has served on the Los Angeles City Council where his leadership as Chairman of the Budget and Finance Committee helped guide the City through the Great Recession and toward greater economic promise. Paul is also Chairman of the Ad Hoc Committee on Job Creation, the Vice Chair of the Housing Committee, and sits on the Energy, Climate Change and Environmental Justice Committee; the Trade Travel and Tourism Committee; the Ad Hoc Committee on the 2028 Olympics; the Executive Employee Relations Committee and the Board of Referred Powers.<br><br>In addition to serving on the Metro Board of Directors, Paul also serves on the boards of Metrolink, and the San Fernando Valley Council of Governments.<br><br>Paul graduated from Reseda\'s Cleveland High School before earning his B.A. in Political Science from the University of Southern California and a law degree from UC Berkeley. Upon graduating, he spent two decades practicing business, entertainment, and property litigation.<br><br>In 2006, after three years on the Burbank Board of Education, Paul won election to the California State Assembly, representing the 43rd District. Paul is the first Armenian-American to be elected to public office in the City of Los Angeles.',
    'mike-bonin': 'Mike Bonin was elected to represent the 11th District on the Los Angeles City Council in 2013, and three weeks later was appointed to the Metro Board of Directors by Mayor Eric Garcetti. Bonin is the Chair of the Council\'s Transportation Committee and the Vice Chair of the Trade, Travel, and Tourism Committee, which oversees LAX International Airport and the Port of Los Angeles. In addition to his transportation portfolio, he also serves on the Council\'s Homelessness and Poverty Committee and Budget and Finance Committee. A former newspaper reporter, Mike graduated from Harvard University in 1989 with a B.A. in United States History.',
    'john-fasana': 'John Fasana is the Mayor of the City of Duarte, and is one of four City Selection Committee representatives elected to the 13-member Metro Board of Directors. He has served on the Metro Board since its inception in 1993, and previously served as Metro Board Chair from 2001 to 2002. He currently serves as Chairperson of the Ad hoc Congestion, Highways and Roads Committee, and is a member of the Finance and Budget Committee, System Safety and Operations Committee and the Executive Management Committee. During his tenure on the Metro Board, he has tirelessly worked with his colleagues in Sacramento and Washington DC to obtain several billion dollars for LA County residents for critically needed multimodal congestion relief projects.<br><br>Mr. Fasana was first elected to the Duarte City Council in November 1987, and reelected in 1991, 1995, 1999, 2003, 2007 and 2011, and reappointed in 2015. He served as Mayor in 1990, 1997, 2003 and 2009. As a Councilmember he has promoted Duarte\'s interests in transportation, community services and environmental protection.<br><br>Mr. Fasana has also served on the Board of the San Gabriel Valley Council of Governments (COG) since its inception, representing 31 cities and over 2 million residents working together to solve regional issues; and in the past, served on Foothill Transit\'s Board. In 2015 he retired from his 35-year career with Southern California Edison. John is a graduate of Whittier College. He and his wife, Kris, have three adult children, all of whom were educated in Duarte\'s public schools, and two sons-in-law.',
    'robert-garcia': 'Dr. Robert Garcia, 40, is an educator and the 28th Mayor of Long Beach. He is one the youngest mayors of any large city in America and has taken a leadership role in shaping the City of Long Beach into an innovative, sustainable hub for economic development, technology, and education.<br><br>Mayor Garcia is a Board Member on the Los Angeles County Metropolitan Transportation Authority (Metro) representing the Gateway City Council of Governments. He is a first-generation college graduate, holding a Master\'s Degree from the University of Southern California, a Doctorate in Higher Education from Cal State Long Beach (where he also earned his Bachelor\'s in Communication), and is an accomplished educator.<br><br>He was born in Lima, Peru, and immigrated to the United States at age 5 with his family and became a citizen at age 21. Mayor Garcia is fluent in both Spanish and English.',
    'janice-hahn': 'Janice Hahn was elected to the Los Angeles County Board of Supervisors in November 2016. She represents the 4th district which stretches from Marina del Rey through the beach cities, the Palos Verdes Peninsula, the Harbor Area, Long Beach, through the Gateway Cities and east to Diamond Bar.<br><br>In her short time on the Board, Supervisor Hahn has already established herself as a leader in the struggle to end the current homelessness crisis, a champion for communities plagued by pollution and health problems, and a dynamic new voice on the Metro Board of Directors.<br><br>Supervisor Janice Hahn inherited a passion for public service from her late father, Supervisor Kenneth Hahn, who held public office in Los Angeles County for fifty years and who left behind an incredible legacy of service. Before being elected to the Board of Supervisors, Janice Hahn served for ten years on the Los Angeles City Council and for five and a half years in Congress.<br><br>While in Washington, she served on the House Homeland Security Committee, Committee on Small Business, and the Committee on Transportation and Infrastructure. She earned nationwide recognition for founding the PORTS Caucus and recruited over 100 of her fellow House colleagues to advocate for ports issues and infrastructure. She has been a leader on efforts to rebuild our national freight infrastructure system, level the playing field for small business owners, and reducing gang violence in our communities. During her time in Congress, Hahn had a reputation for working to find common ground across the political aisle on behalf of the American people.',
    'kathryn-barger': 'Kathryn Barger has served on the Metro Board since 2016, when she was elected to the Los Angeles County Board of Supervisors, representing the Fifth District. Kathryn is a lifelong resident of the Fifth District who began her career in public service as a student intern in the office of Supervisor Michael D. Antonovich while earning her BA in Communications from Ohio Wesleyan University. She rose to become his Chief Deputy Supervisor in 2001, where she served until her election to the Board.<br><br>During the course of her county career as the Chief Policy Advisor on Health, Mental Health, Social Service and Children\'s issues, Kathryn provided leadership to deliver efficient and effective services and programs that have significantly improved the quality of life for foster children, seniors, veterans, the disabled and the mentally ill.<br><br>Committed to keeping our neighborhoods and communities safe, she has worked with state and federal leaders along with our County District Attorney\'s office, Sheriff, and other law enforcement agencies to implement tough laws and vital public safety initiatives.',
    'shirley-choate': 'As Acting Caltrans District 7 Director, Shirley Choate is responsible for assisting the District Director in ensuring the sustainability and livability of the State Highway system in Los Angeles and Ventura counties. Through planning, construction, operation and maintenance, she helps facilitate the movement of people, goods and services in a safe and efficient manner. Shirley is also responsible for the oversight of internal operations which includes 2,700 employees in the divisions of Administration, Construction, Design, Environmental Planning and Engineering, External Affairs, Maintenance, Operations, Planning, Programming/Project Management and Right of Way.<br><br>Shirley is championing innovation in policies and practices for the District and its employees. She is also developing strong, collaborative partnerships with local and regional agencies that will enhance the District\'s economy and livability.<br><br>Shirley has worked for Caltrans for over 35 years. She has spent 18 of those years as the Deputy District Director for Districts 2 and 7. She has also taken on the role of acting Division Chief for Transportation Planning and acting Assistant Division Chief of Construction. Her extensive civil service experience includes the planning, designing and construction of hundreds of transportation projects worth over $4 billion. She oversees more than $475 million in personnel and operating expenses.<br><br>Her performance-based approach has significantly improved the delivery of capital outlay commitments and, under her leadership, the program was awarded the 2006 Caltrans Capital Delivery Award for "Best Overall Delivery" and the 2008 Caltrans "Best Overall Project Management" award.<br><br>Shirley graduated from UC Berkeley with a BS in Civil Engineering in 1982 and received a Master\'s Certificate in Project Management from The George Washington University-School of Business and Public Management in 2002. She is a registered Civil Engineer (Professional Engineer or P.E.) in the State of California as well as a certified Project Management Professional (P.M.P.).',
    'phil-washington': 'Phillip A. Washington was unanimously selected CEO of the Los Angeles County Metropolitan Transportation Authority (LA Metro) by the LA Metro Board of Directors on March 12, 2015.<br><br>As LA Metro CEO, Washington manages a total balanced budget of $6.6 billion for FY19, is responsible for overseeing $15+ billion in capital projects, providing oversight of an agency of nearly 11,000 employees and transports 1.4 million boarding passengers daily, riding on a fleet of 2,000 clean-air buses and six rail lines. LA Metro is also the lead transportation planning and programming agency for LA County. As such, it is a major construction agency that oversees bus, rail, highway and other mobility-related building projects – together representing the largest modern public works program in North America.<br><br><a href="http://media.metro.net/board/images/biography-ceo-washington.pdf" target="_blank"><i class="fa fa-download"></i> Download the biography for Metro CEO Phillip A. Washington</a>',
    'john-bulinski': 'John Bulinski, District 7 Director, for the California Department of Transportation (Caltrans), which encompasses metropolitan Los Angeles and bucolic Ventura counties. John oversees transportation systems in a dynamic region that boasts 25% of California’s population, an annual construction program of more than $2 billion, and some of the most innovative solutions to help move people and goods through Southern California and as part of the 5th largest economy in the world, throughout the rest of the world. John places a high priority on collaboration, community, and employee engagement.<br><br>John has more than 29 years of service with Caltrans. In John’s most recent appointment, District 8 Director, John oversaw roadway activities within Riverside and San Bernardino counties. Prior to John’s service as District 8 Director, John served as the District 2 Director for Caltrans in Northern California from 2008 - 2015. In this capacity, he was responsible for overseeing projects in nine counties in the Northeastern part of California.<br><br>John is a licensed professional engineer and is a graduate of Humboldt State University with a Bachelor of Science Degree in Environmental Engineering.<br><br>John and his wife, Jan, have three children — Rachael, William, and Logan along with six grandchildren. Outside of the office John enjoys family time, woodworking, racquetball, softball, fishing, bicycling, and camping.',
    'tony-tavares': 'Tony Tavares was appointed in November 2020 as Director of the California Department of Transportation (Caltrans) District 7, which encompasses Los Angeles and Ventura counties. As District 7 Director, he oversees transportation systems in a dynamic region that boasts 25% of California’s population; an annual construction program of more than $2 billion; and some of the most innovative solutions to help move people and goods through Southern California (part of the 5th largest economy in the world) throughout the rest of the world.<br /><br /> Tavares’ vision is a modern multimodal transportation system that builds on strong local partnerships and works together with all stakeholders to achieve a shared goal of toward zero deaths (Vison Zero). All local communities and organizations must be heard and share in the development of Caltrans projects, and he encourages a Caltrans culture of creative thinking, innovation, and stakeholder engagement in delivering transportation solutions.<br /><br /> Most recently, he served as Caltrans Bay Area Director (District 4) where he was instrumental in implementing California’s landmark Senate Bill 1 (SB1), the Road Repair and Accountability Act. Tavares also led Caltrans’ visions as he served on several boards of regional transportation planning agencies, joint powers authorities and transit development.<br /><br /> From 2010 to 2018, Tavares served as the statewide Division Chief for Maintenance. There, he directed 7,000 multi-disciplinary professional employees with an annual budget allocation of almost $2.2 billion. In the first year of SB1, he also delivered over $1 billion in pavement, bridge and culvert projects.',
    'holly-j-mitchell': 'On November 3, 2020, Supervisor Holly J. Mitchell was elected to serve the Second District of Los Angeles County. Throughout her career in public service, Supervisor Mitchell has always worked with the understanding – that creating a California where all residents can thrive – means investing in the communities, small businesses, families and children of LA County.<br /><br />Having authored and passed over 90 laws in the California Legislature, Supervisor Mitchell brings an extensive public policy record to the Board of Supervisors. Many of her bills have been at the forefront of expanding healthcare access, addressing systemic racism, and championing criminal justice reform.<br /><br />During her tenure in the California State Legislature, Supervisor Mitchell represented the 54th District for three years as an Assemblymember and later served seven years as State Senator for the 30th District.<br /><br />As State Senator, she also held the distinction of being the first African American to serve as Chair of the Senate Budget and Fiscal Review Committee. In this capacity, she led the passage of state budgets each totaling over $200 billion for the fifth largest economy in the world.<br /><br />Prior to serving in elected office, Supervisor Mitchell was CEO of Crystal Stairs, California’s largest nonprofit dedicated to child and family development. In this role, she ensured that families across Los Angeles County gained access to child care and poverty prevention resources. Before leading Crystal Stairs, she gained formidable experience in crafting public policy both as a former Senate district field representative and legislative advocate at the Western Center for Law and Poverty.<br /><br />Supervisor Mitchell’s leadership has been recognized by over 100 community and business groups. She was recently honored as a 2020 Visionary by Oprah Winfrey’s O Magazine for making California the first state in the nation to ban natural hair discrimination with The CROWN Act.<br /><br />As Supervisor, Mitchell is proud to serve the two million residents of the Second District which includes the neighborhood she grew up in, Leimert Park, and the following cities: Carson, Compton, Culver City, Gardena, Hawthorne, Inglewood, Lawndale, Lynwood, parts of Los Angeles, and dozens of unincorporated communities.<br /><br />Supervisor Mitchell is a University of California at Riverside Highlander, a CORO Foundation Fellow and mother to Ryan.',
    'fernando-dutra': 'Fernando Dutra was elected in April 2018 to represent District 4 for four years after being elected citywide in April 2014 to a four-year term. Fernando was initially appointed by the City Council in August 2012 to fill the remaining term of the Council seat vacated by Greg Nordbak.<br /><br />Fernando and his wife, Mary, have three children—Sara, Megan, and Eric. The Dutras have lived in Whittier since 1987. Fernando is President of Allwest Development Company and holds licenses for general building contractor and general engineering.<br /><br />Fernando served as a Member of the Planning Commission for six years from 2006 to 2012 and has served as Chairman of the Commission. Prior to his term on the Planning Commission, he served for six years on the Design Review Board. He has chaired the Metro Light Rail Extension Project Washington Boulevard Coalition; sits on the Whittier YMCA Board of Directors; and has served on the St. Gregory Parish Board. Fernando serves on the League of California Cities\' Housing, Community & Economic Development Policy Committee. On March 8, 2021, Fernando was appointed to the Los Angeles County Metro Board and serves on the Finance, Budget and Audit Committee and MTA Construction Committee.',
    'tim-sandoval': 'Tim Sandoval moved to Pomona when he was just nine years old. Even as a child, he knew that a community as richly diverse as Pomona was capable of amazing things. As Pomona High’s class speaker, he defended the character of the school and the surrounding community in an impassioned year-end speech. He attended Montvue Elementary, Emerson Middle School, and Pomona High School before finishing his education at University of California, Riverside.<br /><br />After graduating, Tim returned to Pomona to help others in our community to access college as well. He led Pomona Valley Community Development Center’s youth programs, and then taught English at a nearby school. In 2001, Tim became a founding member of Bright Prospect, a mentoring organization that has helped more than two thousand low-income youth become part of the first generation of their family to complete their Bachelor’s degrees. Many of these youth come to share Tim’s passion for Pomona, returning after college to give back to the community.<br /><br />Tim has proudly served as Pomona Mayor since 2016 and was recently re-elected in Nov. 2020. As Mayor, he has championed initiatives geared toward breathing new life into the community. This includes reinstatement of Pomona’s annual State of the City Address at the Fox Theater which has become an increasingly popular community celebration – highlighting the City’s accomplishments of the past year and outlining visionary goals for the future of Pomona; Pomona Beautiful clean-ups throughout the City each Tuesday and Saturday morning; and the Mayor’s Gala benefiting the Pomona Public Library. Tim actively represents Pomona outside of the City’s boundaries, serving on several regional boards, including his positions as the Chair to the Board of Directors for the Metro Gold Line Foothill Extension Construction Authority and the Vice-Chair for the Alameda Corridor East (ACE). His most recent appointment in 2021 to the Metropolitan Transportation Authority (MTA) Board of Directors allows him to represent the San Gabriel Valley’s interests as they pertain to regional public transportation.',
    'stephanie-wiggins': 'The Los Angeles County Metropolitan Transportation Authority’s (Metro) Board of Directors voted to hire Stephanie Wiggins as Metro’s CEO on April 8, 2021. A lifelong trailblazer and champion of equity and inclusion, Ms. Wiggins will be the first woman – and first African American woman – to lead Metro in the agency’s history, which dates to 1993. The appointment as CEO is a homecoming for Ms. Wiggins who served as Deputy CEO of Metro until December 2018.<br /><br />Before rejoining Metro as CEO in June 2021, Ms. Wiggins served for two and a half years as CEO of Metrolink. Metrolink is the nation’s third largest passenger rail system covering 538 route-miles throughout Southern California. At Metrolink, Ms. Wiggins managed an annual budget of $793 million at an agency that employs 282 fulltime employees. She was the first woman and first African American to lead the 28-year-old organization.<br /><br />At Metrolink, Ms. Wiggins adeptly navigated the disruption caused by COVID-19 with a customer-first approach while upholding its foundational value of safety. Ms. Wiggins led the development of a Recovery Plan to reimagine the delivery of Metrolink service in a post-COVID-19 environment, driven by insights gathered from surveys with customers and employees. She demonstrated her commitment to developing new ideas to better serve the core ridership of essential workers who use Metrolink to connect to their jobs on the frontlines of the pandemic with safe, and reliable transportation.<br /><br />With a deep and genuine commitment to equity, diversity and inclusion, Ms. Wiggins strives to provide all people living in Southern California equal access to mobility to get to work, school, healthcare and leisure activities. Achieving that goal depends on leading an organization that is as diverse and inclusive as the region it serves.<br /><br />As Deputy CEO of Metro, she assisted the CEO in providing leadership and formulating and achieving strategic public transportation objectives, including the passage of Measure M, a half-cent sales tax approved by 71 percent of voters in LA County. She also established the Women and Girls Governing Council. During her tenure at Metro, Ms. Wiggins also served as the Executive Director of Vendor/Contract Management, where she implemented procurement streamlining initiatives and greatly expanded Metro’s utilization of small and historically underutilized businesses. Prior to that role, Ms. Wiggins was the Executive Officer and Project Director of the Congestion Reduction/ExpressLanes Program where she launched the first high occupancy toll lanes in LA County, the I-10 and I-110 Express Lanes, which improved travel times and travel reliability on two of the County’s most congested freeway corridors.<br /><br />Prior to Metro, Ms. Wiggins served as Regional Programs Director for the Riverside County Transportation Commission (RCTC) and oversaw transit, commuter rail, rideshare, goods movement and rail capital projects.<br /><br />Ms. Wiggins began her career in transportation when she accepted a temporary assignment at the San Bernardino County Transportation Authority and fell in love with the mission of the agency. The six-month temporary assignment turned into more than four years at SBCTA.<br /><br />She received her Bachelor of Arts degree in Business Administration from Whittier College in 1992 and in 2007 earned a Master of Business Administration from the USC Marshall School of Business.<br /><br />Ms. Wiggins is a self-proclaimed “military brat” whose father made his career in the Air Force. She credits her childhood experience of moving from military base to base and country to country for teaching her the importance of diversity.<br /><br />Ms. Wiggins is the founding president of the Inland Empire Chapter of Women’s Transportation Seminar. She is the recipient of many awards including the 2020 National League of Railway Women’s Woman of the Year award. She is a Board Member of the Los Angeles Chapter of Friends of the Children, the Southern California Chapter of the American Heart Association, and a member of the Whittier College Board of Trustees.',
    "lindsey-horvath": "",
}
# notable positions that aren't district representatives, e.g. mayor & city clerk
# keys should match person slugs
EXTRA_TITLES = {
    # e.g. 'emanuel-rahm': 'Mayor',
}

USING_NOTIFICATIONS = False

# Set this to True to show online public comment links while meetings are ongoing
USING_ECOMMENT = False
