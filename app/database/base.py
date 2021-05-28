# APP/DATABASE/BASE.PY

# ##PYTHON IMPORTS
import datetime

# ##LOCAL IMPORTS

from .. import session as SESSION
from ..models import ArtistUrl, Artist, Label, Description, Illust, IllustUrl, TwitterData, Tag

# ##FUNCTIONS

from ..logical.utility import GetCurrentTime

### CREATE ###

def CreateArtistFromParameters(params, site_id):
    current_time = GetCurrentTime()
    data = {
        'site_id': site_id,
        'site_artist_id': params['site_artist_id'],
        'requery': current_time + datetime.timedelta(days=1),
        'created': current_time,
        'updated': current_time,
    }
    data['site_created'] = params['site_created'] if 'site_created' in params else None
    artist = Artist(**data)
    SESSION.add(artist)
    SESSION.commit()
    if 'names' in params:
        for name in params['names']:
            AddArtistName(artist, name)
    if 'site_accounts' in params:
        for account in params['site_accounts']:
            AddArtistSiteAccount(artist, account)
    if 'profiles' in params:
        for profile in params['profiles']:
            AddArtistProfile(artist, profile)
    if 'webpages' in params:
        AddArtistWebpages(artist, params['webpages'])
    return artist


def CreateIllustFromParameters(params, site_id):
    current_time = GetCurrentTime()
    data = {
        'site_id': site_id,
        'site_illust_id': params['site_illust_id'],
        'requery': current_time + datetime.timedelta(days=1),
        'artist_id': params['artist_id'],
        'pages': params['pages'],
        'created': current_time,
        'updated': current_time,
    }
    data['score'] =  params['score'] if 'score' in params else None
    data['site_created'] = params['site_created'] if 'site_created' in params else None
    illust = Illust(**data)
    SESSION.add(illust)
    SESSION.commit()
    AddSiteData(illust, params)
    if 'descriptions' in params:
        for description in params['descriptions']:
            AddIllustDescription(illust, description)
    if 'tags' in params:
        AddIllustTags(illust, params['tags'])
    if 'urls' in params:
        AddIllustUrls(illust, params['urls'])
    if 'videos' in params:
        AddIllustUrls(illust, params['videos'])
    return illust


### ADD ###


def AddSiteData(illust, params):
    print("AddSiteData")
    data = {
        'illust_id': illust.id,
        'retweets': params['retweets'] if 'retweets' in params else None,
        'replies': params['replies'] if 'replies' in params else None,
        'quotes': params['quotes'] if 'quotes' in params else None,
    }
    site_data = TwitterData(**data)
    SESSION.add(site_data)
    SESSION.commit()


def AddIllustDescription(illust, description_text):
    current_descriptions = [descr.body for descr in illust.descriptions]
    if description_text in current_descriptions:
        return
    descr = Description.query.filter_by(body=description_text).first()
    if descr is None:
        descr = Description(body=description_text)
    illust.descriptions.append(descr)
    SESSION.add(illust)
    SESSION.commit()


def AddIllustTags(illust, taglist):
    print("AddIllustTags")
    tags = GetDBTags(taglist)
    if len(tags):
        illust.tags.extend(tags)
        SESSION.add(illust)
        SESSION.commit()


def GetDBTags(taglist):
    print("GetDBTags")
    def FindOrCommitTag(name):
        tag = Tag.query.filter_by(name=name).first()
        if tag is None:
            tag = Tag(name=name)
            SESSION.add(tag)
            SESSION.commit()
        return tag
    taglist = [tag.lower() for tag in set(taglist)]
    dbtags = []
    for tag in taglist:
        dbtags.append(FindOrCommitTag(tag))
    if len(dbtags):
        SESSION.commit()
    return dbtags


def AddIllustUrls(illust, url_list):
    print("AddIllustUrls")
    illust_urls = []
    for url_data in url_list:
        url_data['illust_id'] = illust.id
        illust_url = IllustUrl(**url_data)
        illust_urls.append(illust_url)
    if len(illust_urls) > 0:
        SESSION.add_all(illust_urls)
        SESSION.commit()
    return illust_urls


def AddArtistName(artist, name_text):
    print("AddArtistName")
    current_names = [label.name for label in artist.names]
    if name_text in current_names:
        return False
    lbl = Label.query.filter_by(name=name_text).first()
    if lbl is None:
        lbl = Label(name=name_text)
    artist.names.append(lbl)
    SESSION.commit()
    print("Added artist name:", name_text)
    return True


def AddArtistSiteAccount(artist, site_account_text):
    print("AddArtistSiteAccount")
    current_site_accounts = [label.name for label in artist.site_accounts]
    if site_account_text in current_site_accounts:
        return False
    lbl = Label.query.filter_by(name=site_account_text).first()
    if lbl is None:
        lbl = Label(name=site_account_text)
    artist.site_accounts.append(lbl)
    SESSION.commit()
    print("Added artist account:", site_account_text)
    return True


def AddArtistProfile(artist, profile_text):
    print("AddArtistProfile")
    current_profiles = [descr.body for descr in artist.profiles]
    if profile_text in current_profiles:
        return False
    descr = Description.query.filter_by(body=profile_text).first()
    if descr is None:
        descr = Description(body=profile_text)
    artist.profiles.append(descr)
    SESSION.commit()
    print("Added artist profile.")
    return True


def AddArtistWebpages(artist, webpages, commit=True):
    print("AddArtistWebpages")
    artist_urls = []
    new_urls = []
    for url in webpages:
        artist_url = ArtistUrl.query.filter_by(artist_id=artist.id, url=url).first()
        if artist_url is None:
            data = {
                'artist_id': artist.id,
                'url': url,
                'active': True,
            }
            artist_url = ArtistUrl(**data)
            new_urls.append(artist_url)
        artist_urls.append(artist_url)
    if commit and len(new_urls):
        SESSION.add_all(new_urls)
        SESSION.commit()
        print("Added artist webpages:", [webpage.url for webpage in new_urls])
    return artist_urls
