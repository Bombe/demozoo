import re, urlparse

class BaseUrl():
	def __init__(self, param):
		self.param = param
	
	tests = [
		lambda urlstring, url: urlstring # always match, return full url
	]
	canonical_format = "%s"
	
	@classmethod
	def match(cls, *args):
		for test in cls.tests:
			m = test(*args)
			if m:
				return cls(m)
	
	def __str__(self):
		return self.canonical_format % self.param

def regex_match(pattern, flags = None):
	regex = re.compile(pattern, flags)
	def match_fn(urlstring, url):
		m = regex.match(urlstring)
		if m:
			return m.group(1)
	return match_fn

def querystring_match(pattern, varname, flags = None, othervars = {}):
	regex = re.compile(pattern, flags)
	def match_fn(urlstring, url):
		if regex.match(urlstring):
			querystring = urlparse.parse_qs(url.query)
			try:
				for (key, val) in othervars.items():
					if querystring[key][0] != val:
						return None
				return querystring[varname][0]
			except KeyError:
				return None
	return match_fn

class TwitterAccount(BaseUrl):
	canonical_format = "http://twitter.com/%s"
	tests = [
		regex_match(r'https?://(?:www\.)?twitter\.com/#!/([^/]+)', re.I),
		regex_match(r'https?://(?:www\.)?twitter\.com/([^/]+)', re.I),
	]

class SceneidAccount(BaseUrl):
	canonical_format = "http://www.pouet.net/user.php?who=%s"
	tests = [
		querystring_match(r'https?://(?:www\.)?pouet\.net/user\.php', 'who', re.I),
	]

class PouetGroup(BaseUrl):
	canonical_format = "http://www.pouet.net/groups.php?which=%s"
	tests = [
		querystring_match(r'https?://(?:www\.)?pouet\.net/groups\.php', 'which', re.I),
	]

class SlengpungUser(BaseUrl):
	canonical_format = "http://www.slengpung.com/v3/show_user.php?id=%s"
	tests = [
		querystring_match(r'https?://(?:www\.)?slengpung\.com/v3/show_user\.php', 'id', re.I),
	]

class AmpAuthor(BaseUrl):
	canonical_format = "http://amp.dascene.net/detail.php?view=%s"
	tests = [
		querystring_match(r'https?://amp\.dascene\.net/detail\.php', 'view', re.I),
	]

class CsdbScener(BaseUrl):
	canonical_format = "http://noname.c64.org/csdb/scener/?id=%s"
	tests = [
		querystring_match(r'https?://noname\.c64\.org/csdb/scener/', 'id', re.I),
		querystring_match(r'https?://(?:www\.)?csdb\.dk/csdb/scener/', 'id', re.I),
	]

class NectarineArtist(BaseUrl):
	canonical_format = "http://www.scenemusic.net/demovibes/artist/%s/"
	tests = [
		regex_match(r'https?://(?:www\.)scenemusic\.net/demovibes/artist/(\d+)', re.I),
	]

class BitjamAuthor(BaseUrl):
	canonical_format = "http://www.bitfellas.org/e107_plugins/radio/radio.php?search&q=%s&type=author&page=1"
	tests = [
		querystring_match(r'https?://(?:www\.)bitfellas\.org/e107_plugins/radio/radio\.php\?search', 'q', re.I),
	]

class ArtcityArtist(BaseUrl):
	canonical_format = "http://artcity.bitfellas.org/index.php?a=artist&id=%s"
	tests = [
		querystring_match(r'https?://artcity\.bitfellas\.org/index\.php', 'id', re.I, othervars = {'a': 'artist'}),
	]

class MobygamesDeveloper(BaseUrl):
	canonical_format = "http://www.mobygames.com/developer/sheet/view/developerId,%s/"
	tests = [
		regex_match(r'https?://(?:www\.)mobygames\.com/developer/sheet/view/developerId\,(\d+)', re.I),
	]

class AsciiarenaArtist(BaseUrl):
	canonical_format = "http://www.asciiarena.com/info_artist.php?artist=%s&sort_by=filename"
	tests = [
		querystring_match(r'https?://(?:www\.)asciiarena\.com/info_artist\.php', 'artist', re.I),
	]

def grok_scener_link(urlstring):
	url = urlparse.urlparse(urlstring)
	link_types = [
		TwitterAccount, SceneidAccount, SlengpungUser, AmpAuthor,
		CsdbScener, NectarineArtist, BitjamAuthor, ArtcityArtist,
		MobygamesDeveloper, AsciiarenaArtist, PouetGroup,
		BaseUrl,
	]
	for link_type in link_types:
		link = link_type.match(urlstring, url)
		if link:
			return link

def grok_group_link(urlstring):
	url = urlparse.urlparse(urlstring)
	link_types = [
		TwitterAccount, PouetGroup,
		BaseUrl,
	]
	for link_type in link_types:
		link = link_type.match(urlstring, url)
		if link:
			return link
