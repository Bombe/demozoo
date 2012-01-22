from django.db import models
import urllib, urllib2, hashlib, datetime
from blob_field import BlobField

class Directory(models.Model):
	path = models.CharField(max_length=255)
	is_deleted = models.BooleanField(default=False)
	last_seen_at = models.DateTimeField()
	last_spidered_at = models.DateTimeField(null=True, blank=True)
	parent = models.ForeignKey('Directory', related_name = 'subdirectories', null=True, blank=True)
	
	def __unicode__(self):
		return self.path
	
	@property
	def web_url(self):
		return "http://www.scene.org/dir.php?dir=%s" % urllib.quote(self.path.encode("utf-8"))
	
	def new_files_url(self, days):
		return "http://www.scene.org/newfiles.php?dayint=%s&dir=%s" % (days, urllib.quote(self.path.encode("utf-8")))
	
	@staticmethod
	def parties_root():
		return Directory.objects.get(path = '/parties/')
	
	@staticmethod
	def party_years():
		return Directory.objects.filter(parent = Directory.parties_root)
	
	@staticmethod
	def parties():
		return Directory.objects.filter(parent__in = Directory.party_years)

class FileTooBig(Exception):
	pass

class File(models.Model):
	path = models.CharField(max_length=255)
	is_deleted = models.BooleanField(default=False)
	last_seen_at = models.DateTimeField()
	directory = models.ForeignKey(Directory, related_name = 'files')
	
	def __unicode__(self):
		return self.path
	
	def filename(self):
		return self.path.split('/')[-1]
	
	def fetched_data(self):
		f = urllib2.urlopen('ftp://ftp.scene.org/pub' + self.path)
		file_content = f.read(65537)
		f.close()
		if len(file_content) > 65536:
			raise FileTooBig("Cannot fetch files larger than 64Kb")
		return buffer(file_content)
	
	def fetch(self):
		file_content = self.fetched_data()
		sha1 = hashlib.sha1(file_content).hexdigest()
		
		# if most recent download for this file has the same SHA1 sum, return that (and update
		# the downloaded_at timestamp) rather than creating a new one
		try:
			last_download = self.downloads.order_by('-downloaded_at')[0]
			if last_download.sha1 == sha1:
				last_download.downloaded_at = datetime.datetime.now()
				last_download.save()
				return last_download
		except IndexError:
			pass
		
		download = FileDownload(file=self, downloaded_at=datetime.datetime.now(),
			data=file_content, sha1=sha1)
		download.save()
		return download
	
	@property
	def web_url(self):
		return "http://www.scene.org/file.php?file=%s&fileinfo" % urllib.quote(self.path.encode("utf-8"))

class FileDownload(models.Model):
	file = models.ForeignKey(File, related_name = 'downloads')
	downloaded_at = models.DateTimeField()
	data = BlobField(blank=True, null=True)
	sha1 = models.CharField(max_length=40)
