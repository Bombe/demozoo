# Parsers for results text files in various formats.
# Each one returns a list of (ranking, title, author, score) tuples

import re


# Tab-separated values
def tsv(results_text):
	rows = []
	result_lines = results_text.split('\n')
	for line in result_lines:
		fields = [field.strip() for field in line.split('\t')] + ['', '', '', '']
		placing, title, byline, score = fields[0:4]
		rows.append((placing, title, byline, score))
	return rows


def partymeister(results_text, author_separator=' - '):
	lines = results_text.split('\n')
	# use first text line to establish column positions
	ranking_indent = None
	score_indent = None
	title_indent = None

	for line in lines:
		match = re.match(r'(\s*)(\S+)(\s+)(\S+)(\s+)(\S)', line)
		if not match:
			continue
		ranking_indent = len(match.group(1))
		score_indent = ranking_indent + len(match.group(2)) + len(match.group(3))
		title_indent = score_indent + len(match.group(4)) + len(match.group(5))
		break

	if ranking_indent == None:
		# no usable result lines found at all
		return []

	# now loop over the lines properly, compiling a list of [ranking, score, title_and_author] lists
	rough_rows = []
	last_ranking = None
	for line in lines:
		# check indent level of this line
		match = re.match(r'(\s*)\S', line)
		if not match:
			continue
		indent = len(match.group(1))

		if indent < score_indent:
			# something (i.e. a ranking) exists to the left of the score, so start a new row
			match = re.match(r'(\s*)(\S+)(\s+)(\S+)(\s+)(\S.*)', line)
			if not match:
				continue
			rough_rows.append([match.group(2), match.group(4), match.group(6)])
			last_ranking = match.group(2)
		elif indent < title_indent:
			# something (i.e. a score) exists to the left of the title;
			# treat this as a new row with the same ranking as the previous entry
			if last_ranking == None:
				continue
			match = re.match(r'(\s*)(\S+)(\s+)(\S.*)', line)
			if not match:
				continue
			rough_rows.append([last_ranking, match.group(2), match.group(4)])
		else:
			# text starts at the same indent level as the title;
			# treat this as a continuation of the previous entry
			if len(rough_rows) == 0:
				continue
			print "appending to: %s" % repr(rough_rows[-1][2])
			rough_rows[-1][2] += ' ' + line.strip()

	# now clean up individual fields and build the final row set
	final_rows = []
	for ranking, score, title_and_author in rough_rows:
		ranking = re.sub(r'\.$', '', ranking)  # strip trailing dot
		if re.match(r'[Oo\d]+$', ranking):
			# replace any oh-so-l33t letter 'o's within numbers by digit '0',
			# and remove leading zeroes
			ranking = re.sub(r'[Oo]', '0', ranking)
			ranking = re.sub(r'^0+', '', ranking)

		# split title and author on the final occurrence of the separator string,
		# on the assumption that titles are more likely to have an embedded ' - ' or ' by '
		# than author strings
		title_and_author_list = title_and_author.split(author_separator)
		if len(title_and_author_list) > 1:
			title = author_separator.join(title_and_author_list[:-1])
			author = title_and_author_list[-1]
		else:
			title = title_and_author_list[0]
			author = ''

		final_rows.append((ranking, title, author, score))

	return final_rows
