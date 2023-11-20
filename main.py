import logging
import unicodedata
import string
import re
import pycurl
from io import BytesIO
import ipaddress
from urllib.parse import urlparse, unquote
import socket
from fastapi import FastAPI


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


app = FastAPI()


@app.get("/")
async def root():
	return {"message": "Hello World"}



@app.get("/get0")
async def get0(url: str):
	log.info(f"get {url=}")
	result,filename = fetch_file_with_pycurl(url)
	if filename is None:
		filename = "file.txt"
	filename = clean_filename(filename)
	return dict(content=result.decode('utf-8'), filename=filename)


@app.get("/get")
async def get(url: str):
	log.info(f"get {url=}")
	try:
		result,filename = fetch_file_with_pycurl(url)
		if filename is None:
			filename = "file.txt"
		filename = clean_filename(filename)
		return dict(content=result.decode('utf-8'), filename=filename)

	except Exception as e:
		return dict(error=str(e))
	

def fetch_file_with_pycurl(url, max_redirects=3):
	"""
	Fetches a file from a given URL using PyCurl, but only if the URL's IP address is global.
	Does not follow redirects automatically but checks each new location with is_global().

	Returns:
	- str or bytes: The content of the file if the URL is global and within redirect limits, otherwise an error message.
	"""
	if max_redirects < 0:
		raise Exception("Exceeded maximum number of redirects.")

	# Parse the URL to get the hostname
	parsed_url = urlparse(url)

	if parsed_url is None or parsed_url.netloc is None or parsed_url.netloc == "":
		raise Exception("The URL could not be parsed.")

	hostname = parsed_url.hostname

	if hostname is None:
		ip = ipaddress.ip_address(parsed_url.netloc)
	else:
		# Resolve the hostname to an IP address
		ip = ipaddress.ip_address(socket.gethostbyname(hostname))

	# Check if the IP is a global address
	if not ip.is_global or ip.is_multicast or ip.is_reserved or ip.is_unspecified or ip.is_loopback or ip.is_link_local or ip.is_private:
		raise Exception("The URL does not resolve to a global IP address.")

	# Initialize PyCurl
	c = pycurl.Curl()
	c.setopt(c.URL, url)
	c.setopt(c.FOLLOWLOCATION, False)  # Do not follow redirects automatically
	
	c.setopt(pycurl.NOSIGNAL, 1)
	c.setopt(pycurl.USERAGENT, 'Mozilla/5.0')

	# Get the port from the URL
	port = parsed_url.port
	if port is None:
		if parsed_url.scheme == "http":
			port = 80
		elif parsed_url.scheme == "https":
			port = 443
		else:
			raise Exception("The URL does not specify a port and the scheme is not HTTP or HTTPS.")
	
	# force the translation of the hostname to the IP address
	c.setopt(c.RESOLVE, [f"{hostname}:{port}:{ip}"])
	
	# Set options to capture headers
	headers = BytesIO()
	c.setopt(c.HEADERFUNCTION, headers.write)

	# Prepare a buffer to store the response
	buffer = BytesIO()
	c.setopt(c.WRITEDATA, buffer)


	log.info(f"get: {repr(parsed_url)}")

	# Perform the request
	c.perform()

	# Check for HTTP response code to detect redirect
	if 300 <= c.getinfo(pycurl.HTTP_CODE) < 400 and max_redirects > 0:
		redirect_url = c.getinfo(pycurl.REDIRECT_URL)
		c.close()
		return fetch_file_with_pycurl(redirect_url, max_redirects - 1)  # Recursive call for the new URL

	# Get content-disposition header
	headers_value = headers.getvalue().decode('iso-8859-1')
	filename = get_filename_from_cd(headers_value)

	if not filename:
		# Fallback to URL path
		filename = unquote(urlparse(url).path.split('/')[-1])

	# Close the cURL session and return the content
	c.close()
	return buffer.getvalue(), filename 


def get_filename_from_cd(cd):
	"""
	Get filename from content-disposition header.
	"""
	if not cd:
		return None
	fname = re.findall('filename="(.+)"', cd)
	if len(fname) == 0:
		return None
	return unquote(fname[0])


def clean_filename(filename):
	"""
	Url: https://gist.github.com/wassname/1393c4a57cfcbf03641dbc31886123b8
	"""

	valid_filename_chars = "-_.%s%s" % (string.ascii_letters, string.digits)
	char_limit = 30
	filename = filename.replace(' ', '_')

	# keep only valid ascii chars
	cleaned_filename = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore').decode()

	# keep only whitelisted chars
	cleaned_filename = ''.join(c for c in cleaned_filename if c in valid_filename_chars)
	if len(cleaned_filename) > char_limit:
		print("Warning, filename truncated because it was over {}. Filenames may no longer be unique".format(char_limit))
	return cleaned_filename[:char_limit]



if __name__ == "__main__":
	import uvicorn
	uvicorn.run(app, port=6457)