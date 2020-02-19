#!/usr/bin/python

import subprocess

def big_two_call(scores_file, args_list = []):
  subprocess.call(['python', 'big2.py', scores_file] + args_list)

# For scores.txt
big_two_call('scores')

# For test/test.txt
args_list_list = [
  [],
  ['-e', '20190100'],
  ['-e', '20190101'],
  ['-e', '20190102'],
  ['-s', '20190103', '-e', '20190103'],
  ['-s', '20190104', '-e', '20190104'],
  ['-s', '20190104', '-e', '20190104', '-f', '11'],
  ['--sep'],
  ['-s', '20190105', '-e', '20190105']
]
for args_list in args_list_list:
  big_two_call('test/test', args_list)
