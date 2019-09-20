#!/usr/bin/python

import subprocess

def big_two_call(scores_file, args_list = []):
  subprocess.call(['python', 'big-two-stats.py', scores_file] + args_list)

# For scores.txt
big_two_call('scores')

# For test/test.txt
args_list_list = [
  [],
  ['20190100'],
  ['20190101'],
  ['20190102'],
  ['20190103', '20190103'],
  ['20190104', '20190104'],
  ['20190104', '20190104', '-f', '11'],
  ['-s']  
]
for args_list in args_list_list:
  big_two_call('test/test', args_list)