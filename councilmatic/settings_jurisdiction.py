# These are all the settings that are specific to a jurisdiction

###############################
# These settings are required #
###############################

OCD_CITY_COUNCIL_ID = 'ocd-organization/42e23f04-de78-436a-bec5-ab240c1b977c'
CITY_COUNCIL_NAME = 'LA Metro'
OCD_JURISDICTION_ID = 'ocd-jurisdiction/country:us/state:ca/county:los_angeles/transit_authority'
LEGISLATIVE_SESSIONS = ['2014', '2015', '2016'] # the last one in this list should be the current legislative session
CITY_NAME = 'Los Angeles'
CITY_NAME_SHORT = 'LA'

# VOCAB SETTINGS FOR FRONT-END DISPLAY
CITY_VOCAB = {
    'MUNICIPAL_DISTRICT': 'Ward',       # e.g. 'District'
    'SOURCE': 'LA Metro',
    'COUNCIL_MEMBER': 'Board member',       # e.g. 'Council Member'
    'COUNCIL_MEMBERS': 'Board of Directors',      # e.g. 'Council Members'
    'EVENTS': 'Meetings',               # label for the events listing, e.g. 'Events'
}

APP_NAME = 'lametro'


#########################
# The rest are optional #
#########################

# this is for populating meta tags
SITE_META = {
    'site_name' : '',       # e.g. 'Chicago Councilmatc'
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
BOUNDARY_SET = ''           # e.g. 'chicago-wards-2015'

# this is for configuring a map of council districts using data from the posts
# set MAP_CONFIG = None to hide map
MAP_CONFIG = {
    # 'center': [41.8369, -87.6847],
    # 'zoom': 10,
    # 'color': "#54afe8",
    # 'highlight_color': "#C00000",
}


FOOTER_CREDITS = [
    {
        'name':     '', # e.g. 'DataMade'
        'url':      '', # e.g. 'http://datamade.us'
        'image':    '', # e.g. 'datamade-logo.png'
    },
]

# this is the default text in search bars
SEARCH_PLACEHOLDER_TEXT = '' # e.g. 'police, zoning, O2015-7825, etc.'



# these should live in APP_NAME/static/
IMAGES = {
    'favicon': 'images/favicon.ico',
    'logo': 'images/logo.png',
}




# THE FOLLOWING ARE VOCAB SETTINGS RELEVANT TO DATA MODELS, LOGIC
# (this is diff from VOCAB above, which is all for the front end)

# this is the name of the meetings where the entire city council meets
# as stored in legistar
CITY_COUNCIL_MEETING_NAME = 'Board Meeting'

# this is the name of the role of committee chairs, e.g. 'CHAIRPERSON' or 'Chair'
# as stored in legistar
# if this is set, committees will display chairs
COMMITTEE_CHAIR_TITLE = 'Chair'

# this is the anme of the role of committee members,
# as stored in legistar
COMMITTEE_MEMBER_TITLE = 'Member'




# this is for convenience, & used to populate a table
# describing legislation types on the default about page template
LEGISLATION_TYPE_DESCRIPTIONS = [
    {
        'name': 'Agreement',
        'search_term': 'Agreement',
        'fa_icon': 'dollar',
        'html_desc': True,
        'desc': '',
    },
    {
        'name': 'Application',
        'search_term': 'Application',
        'fa_icon': 'dollar',
        'html_desc': True,
        'desc': '',
    },
        {
        'name': 'Appointment',
        'search_term': 'Appointment',
        'fa_icon': 'dollar',
        'html_desc': True,
        'desc': '',
    },
        {
        'name': 'Budget',
        'search_term': 'Budget',
        'fa_icon': 'dollar',
        'html_desc': True,
        'desc': '',
    },
        {
        'name': 'Contract',
        'search_term': 'Contract',
        'fa_icon': 'dollar',
        'html_desc': True,
        'desc': '',
    },
        {
        'name': 'Fare/Tariff/Service Change',
        'search_term': 'Fare/Tariff/Service Change',
        'fa_icon': 'dollar',
        'html_desc': True,
        'desc': '',
    },
        {
        'name': 'Federal Legislation / State Legislation (Position)',
        'search_term': 'Federal Legislation / State Legislation (Position)',
        'fa_icon': 'dollar',
        'html_desc': True,
        'desc': '',
    },
    {
        'name': 'Formula Allocation / Local Return',
        'search_term': 'Formula Allocation / Local Return',
        'fa_icon': 'dollar',
        'html_desc': True,
        'desc': '',
    },
    {
        'name': 'Informational Report',
        'search_term': 'Informational Report',
        'fa_icon': 'dollar',
        'html_desc': True,
        'desc': '',
    },
    {
        'name': 'Minutes',
        'search_term': 'Minutes',
        'fa_icon': 'dollar',
        'html_desc': True,
        'desc': '',
    },
    {
        'name': 'Motion/Motion Response',
        'search_term': 'Motion/Motion Response',
        'fa_icon': 'dollar',
        'html_desc': True,
        'desc': '',
    },
    {
        'name': 'Oral Report/Presentation',
        'search_term': 'Oral Report/Presentation',
        'fa_icon': 'dollar',
        'html_desc': True,
        'desc': '',
    },
    {
        'name': 'Ordinance',
        'search_term': 'Ordinance',
        'fa_icon': 'dollar',
        'html_desc': True,
        'desc': '',
    },
    {
        'name': 'Plan',
        'search_term': 'Plan',
        'fa_icon': 'dollar',
        'html_desc': True,
        'desc': '',
    },
    {
        'name': 'Policy',
        'search_term': 'Policy',
        'fa_icon': 'dollar',
        'html_desc': True,
        'desc': '',
    },
    {
        'name': 'Program',
        'search_term': 'Program',
        'fa_icon': 'dollar',
        'html_desc': True,
        'desc': '',
    },
    {
        'name': 'Project',
        'search_term': 'Project',
        'fa_icon': 'dollar',
        'html_desc': True,
        'desc': '',
    },
    {
        'name': 'Public Hearing',
        'search_term': 'Public Hearing',
        'fa_icon': 'dollar',
        'html_desc': True,
        'desc': '',
    },
    {
        'name': 'Resolution',
        'search_term': 'Resolution',
        'fa_icon': 'dollar',
        'html_desc': True,
        'desc': '',
    },
]


# these keys should match committee slugs
COMMITTEE_DESCRIPTIONS = {
    # e.g. "committee-on-aviation" : "The Committee on Aviation has jurisdiction over matters relating to aviation and airports.",
}

# these blurbs populate the wells on the committees, events, & council members pages
ABOUT_BLURBS = {
    "COMMITTEES" :      "",
    "EVENTS":           "",
    "COUNCIL_MEMBERS":  "",
}

# these override the headshots that are automatically populated
# the keys should match a person's slug
MANUAL_HEADSHOTS = {
    # e.g. 'emanuel-rahm': {'source': 'cityofchicago.org', 'image': 'manual-headshots/emanuel-rahm.jpg' },
}

# notable positions that aren't district representatives, e.g. mayor & city clerk
# keys should match person slugs
EXTRA_TITLES = {
    # e.g. 'emanuel-rahm': 'Mayor',
}
