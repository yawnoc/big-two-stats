#!/usr/bin/python

"""
----------------------------------------------------------------
big2.py
----------------------------------------------------------------

Parse the Big Two scores in {scores file}.txt and return a CSV of statistics:
  big2.py {scores file}.txt

Optional argument -s or --start for start date (default 0):
  big2.py {...} -s {start date}

Optional argument -e or --end for end date (default 10 ** 8):
  big2.py {...} -e {end date}

Optional argument -f or --fry for frying threshold (default 10):
  big2.py {...} -f {frying threshold}

Optional flag --sep for displaying regular players separately:
  big2.py {...} --sep

Released into the public domain (CC0):
  <https://creativecommons.org/publicdomain/zero/1.0/>
ABSOLUTELY NO WARRANTY, i.e. "GOD SAVE YOU"

Specifications for plain-text file of Big Two scores:

1. Hash (#) comments out the remainder of a line
2. Date is specified by a line of digits {yyyymmdd}
    2.1 Extra digits are permitted but ignored
3. Players are specified by a line {P1} {P2} {P3} {P4}
    3.1 Whitespace can be any non-newline whitespace
    3.2 Player names cannot begin with a digit
    3.3 Player names cannot contain whitespace
    3.4 Player names cannot contain commas
    3.5 Player names cannot contain asterisks
4. Losses (cards remaining) are specified by a line {L1} {L2} {L3} {L4}
    4.1 Whitespace can be any non-newline whitespace
    4.2 Use suffix t if a player takes on all losses
        (for not playing high enough or failing to announce "last card")
5. Any other non-comment non-whitespace text is invalid
"""


from collections import OrderedDict
import argparse
import re


DEFAULT_START_DATE = 0
DEFAULT_END_DATE = 10 ** 8
DEFAULT_FRY_MIN = 10



def add_player(stats_dict, player):
  """
  Add a player to a dictionary of statistics.
  """
  
  # If player has no previous record
  if player not in stats_dict:
    
    # Provide a clean slate of additive statistics
    stats_dict[player] = {stat: 0 for stat in stat_list_additive()}


def stat_list_additive():
  """
  Return list of the additive statistics (rates).
  """
  
  return [
    'games_played',
    'cards_lost',
    'games_won',
    'games_fried',
    'net_score'
  ]

def stat_list_rates():
  """
  Return list of the non-additive statistics.
  """
  
  return [
    'cards_lost_avg',
    'games_won_pc',
    'games_fried_pc',
    'net_score_avg'
  ]



def dict_to_csv(stats_dict, separate_regular):
  """
  Convert a dictionary of statistics to a CSV string.
  """
  
  # List of all statistics
  stat_list = stat_list_additive() + stat_list_rates()
  
  # Create combined player '*' for combined statistics of all players
  add_player(stats_dict, '*')
  
  # Compute combined additive statistics
  for stat in stat_list_additive():
    stats_dict['*'][stat] = sum(
      stats_dict[player][stat] for player in stats_dict
    )
  
  # If no games have been played, rates are indeterminate
  if stats_dict['*']['games_played'] == 0:
    for stat in stat_list_rates():
      stats_dict['*'][stat] = float('nan')
    
  # Otherwise compute rates (non-additive statistics) for all players
  else:
    for player in stats_dict:
      p = stats_dict[player]
      p['cards_lost_avg'] = p['cards_lost'] / p['games_played']
      p['games_won_pc'] = p['games_won'] / p['games_played'] * 100
      p['games_fried_pc'] = p['games_fried'] / p['games_played'] * 100
      p['net_score_avg'] = p['net_score'] / p['games_played']
  
  # If regular players are to be displayed separately
  if separate_regular:
    
    # Add field for whether a player is regular
    stat_list += ['regular']
    
    # Compute quarter of all games played
    # Note: {all games played} == {combined games won},
    # whereas 4 * {all games played} == {combined games played}
    games_played_quarter = stats_dict['*']['games_won'] / 4
    
    # Each player is regular if games played is at least this
    for player in stats_dict:
      p = stats_dict[player]
      p['regular'] = p['games_played'] >= games_played_quarter
  
  # Sort dictionary by average cards lost (before rounding below)
  # with tie breaking by player name
  stats_dict_sorted = OrderedDict(
    sorted(
      stats_dict.items(),
      key = lambda x: (x[1]['cards_lost_avg'], x[0])
    )
  )
  
  # Remove combined player from sorted dictionary
  del stats_dict_sorted['*']
  
  # Round rates to sensible number of decimal places
  for player in stats_dict:
    p = stats_dict[player]
    p['cards_lost_avg'] = round(p['cards_lost_avg'], 2)
    p['games_won_pc'] = round(p['games_won_pc'], 1)
    p['games_fried_pc'] = round(p['games_fried_pc'], 1)
    p['net_score_avg'] = round(p['net_score_avg'], 2)
  
  # Headings for CSV string of statistics
  stats_csv = list_to_csv_line(['player'] + stat_list)
  
  # Player's row of statistics to be appended
  def stats_csv_row(player):
    return list_to_csv_line(
      [player] + [str(stats_dict[player][stat]) for stat in stat_list]
    )
  
  # If regular players are to be displayed separately
  if separate_regular:
    
    # Separate rows for regular players from those for non-regular players
    # but sort each group by average cards lost
    stats_csv_regular = ''
    stats_csv_non_regular = ''
    for player in stats_dict_sorted:
      if stats_dict[player]['regular']:
        stats_csv_regular += stats_csv_row(player)
      else:
        stats_csv_non_regular += stats_csv_row(player)
    
    # Append regular players' rows to CSV
    stats_csv += stats_csv_regular
    
    # Append non-regular players' rows to CSV
    stats_csv += stats_csv_non_regular
  
  # Otherwise
  else:
    
    # Append all (non-combined) players' rows sorted by average cards lost
    for player in stats_dict_sorted:
      stats_csv += stats_csv_row(player)
  
  # Append combined player's row (combined statistics of all players)
  stats_dict['*']['regular'] = ''
  stats_csv += stats_csv_row('*')
  
  return stats_csv


def list_to_csv_line(list_):
  """
  Convert a list to a string for a line of a CSV.
  """
  
  return ','.join(list_) + '\n'


def file_to_dict(file_name, start_date, end_date, fry_min):
  """
  Generate a dictionary of stats from a file of Big Two scores.
  """
  
  ################################################################
  # For frying
  ################################################################
  def fry(loss):
    if fry_min <= loss < 13:
      loss *= 2
    if loss == 13:
      loss *= 3
    return loss
  
  ################################################################
  # For raising exceptions
  ################################################################
  def raise_exception(message):
    raise Exception(
      f'LINE {line_num} OF {file_name}.txt INVALID: {message}'
    )
  
  ################################################################
  # Regular expression for line specifying player names
  ################################################################
  name_pattern = r'([^\s0-9,\*][^\s,\*]*)'
  space_pattern = r'\s+'
  names_regex = re.compile(
    '^'
    + 3 * (name_pattern + space_pattern)
    + name_pattern
    + '$'
  )
  
  ################################################################
  # Regular expression for line specifying losses
  ################################################################
  loss_pattern = r'([0-9]+)(t?)'
  space_pattern = r'\s+'
  losses_regex = re.compile(
    '^'
    + 3 * (loss_pattern + space_pattern)
    + loss_pattern
    + '$'
  )
  
  # Import .txt file as string
  with open(f'{file_name}.txt', 'r', encoding='utf-8') as txt_file:
    txt_file_string = txt_file.read()
  
  # Whether the start date has been reached
  start_reached = True
  
  # Whether the end date has been exceeded
  end_exceeded = False
  
  # Initialise dictionary
  stats_dict = {}
  
  # Line-by-line:
  for line_num, line in enumerate(txt_file_string.splitlines(), 1):
    
    # Strip comments
    line = re.sub(r'#[\s\S]*', '', line)
    
    # Strip leading and trailing whitespace
    line = re.sub(r'^\s+', '', line)
    line = re.sub(r'\s+$', '', line)
    
    # If line specifies date
    if line.isdigit():
      
      # Extract first 8 digits {yyyymmdd}
      yyyymmdd = int(line[:8])
      
      # Whether the start date has been reached
      start_reached = yyyymmdd >= start_date
      
      # Whether the end date has been exceeded
      end_exceeded = yyyymmdd > end_date
      
      # Go to next line
      continue
      
    # If within date range
    if start_reached and not end_exceeded:
      
      # If line specifies player names
      names_match = names_regex.match(line)
      if names_match:
        
        # Set list of players
        player_list = [names_match.group(n) for n in range(1, 5)]
        
        # Check for duplicate players
        if len(player_list) != len(set(player_list)):
          raise_exception('duplicate player')
        
        # Add players to dictionary of statistics
        for player in player_list:
          add_player(stats_dict, player)
        
        # Go to next line
        continue
      
      # If line specifies losses
      losses_match = losses_regex.match(line)
      if losses_match:
        
        # Players must already have been specified
        if 'player_list' not in locals():
          raise_exception('players must be specified before losses')
        
        # Update players' games played
        for player in player_list:
          stats_dict[player]['games_played'] += 1
        
        # Set list of losses
        loss_list = [int(losses_match.group(n)) for n in range(1, 9, 2)]
        if not all([0 <= loss <= 13 for loss in loss_list]):
          raise_exception('cards lost must be between 0 and 13 inclusive')
        
        # Winner
        if loss_list.count(0) != 1:
          raise_exception('exactly one player must win')
        
        # Update winner's games won
        winner = player_list[loss_list.index(0)]
        stats_dict[winner]['games_won'] += 1
        
        # Set list of fry counts
        fry_list = [int(loss >= fry_min) for loss in loss_list]
        
        # Adjust losses for frying
        loss_list = [fry(loss) for loss in loss_list]
        
        # Parse specification for a player taking on all losses
        take_on_list = [losses_match.group(n) for n in range(2, 9, 2)]
        take_on_len = len(''.join(take_on_list))
        
        # At most one player can take on all losses
        if take_on_len > 1:
          raise_exception('at most one player can take on all losses')
        
        # If specified, make player take on all losses
        if take_on_len == 1:
          take_on_index = take_on_list.index('t')
          non_take_on_index_list = [n for n in range(4) if n != take_on_index]
          fry_list[take_on_index] = sum(fry_list)
          loss_list[take_on_index] = sum(loss_list)
          for n in non_take_on_index_list:
            fry_list[n] = 0
            loss_list[n] = 0
        
        # Compute net scores (i.e. zero-sum gambling scores)
        # Suppose players A, B, C, D have losses a, b, c, d.
        # Without loss of generality consider player A:
        #   Player A pays a to each of the other 3 players
        #   Player A receives a total of (b + c + d) from the other players
        # Thus Player A has a net score of
        #   (b + c + d) - 3 a = (a + b + c + d) - 4 a = T - 4 a
        # where T = (a + b + c + d) is the total of all losses.
        total_losses = sum(loss_list)
        net_score_list = [total_losses - 4 * loss for loss in loss_list]
          
        # Update players' cards lost, games fried and net scores
        for n, player in enumerate(player_list):
          p = stats_dict[player]
          p['cards_lost'] += loss_list[n]
          p['games_fried'] += fry_list[n]
          p['net_score'] += net_score_list[n]
        
        # Go to next line
        continue
      
      # Otherwise if the line is non-empty, it is invalid
      if line != '':
        raise_exception(
          'does not properly specify one of date, players or losses'
        )
      
    # (If the start date has not been reached, ignore the line)
    
  return stats_dict


def main(args):
  
  # File name
  file_name = args.file_name
  
  # Remove trailing "." or ".txt" if provided
  file_name = re.sub(r'\.(txt)?$', '', file_name)
  
  # Export file name
  file_name_export = file_name
  
  # Start date
  start_date = args.start_date
  if start_date != DEFAULT_START_DATE:
    file_name_export += f'-s_{start_date}'
  
  # End date
  end_date = args.end_date
  if end_date != DEFAULT_END_DATE:
    file_name_export += f'-e_{end_date}'
  
  # Frying threshold
  fry_min = args.fry_min
  if not 0 < fry_min < 13:
    raise Exception(
      'Frying threshold must be a positive integer less than 13'
    )
  if fry_min != DEFAULT_FRY_MIN:
    file_name_export += f'-f_{fry_min}'
  
  # Separate regular
  separate_regular = args.separate_regular
  if separate_regular:
    file_name_export += '-sep'
  
  # Generate dictionary of statistics from file
  stats_dict = file_to_dict(file_name, start_date, end_date, fry_min)
  
  # Convert into CSV string of statistics
  stats_csv = dict_to_csv(stats_dict, separate_regular)
  
  # Export .csv file
  with open(f'{file_name_export}.csv', 'w', encoding='utf-8') as csv_file:
    csv_file.write(stats_csv)


if __name__ == '__main__':
  
  # Description
  parser = argparse.ArgumentParser(
    description='Generates Big Two statistics'
  )
  
  # Arguments
  parser.add_argument(
    'file_name',
    help='File name of Big Two scores file.',
    metavar='file_name[.[txt]]'
  )
  parser.add_argument(
    '-s',
    '--start',
    dest='start_date',
    help=f'Start date (default {DEFAULT_START_DATE})',
    nargs='?',
    default=DEFAULT_START_DATE,
    type=int
  )
  parser.add_argument(
    '-e',
    '--end',
    dest='end_date',
    help=f'End date (default {DEFAULT_END_DATE})',
    nargs='?',
    default=DEFAULT_END_DATE,
    type=int
  )
  parser.add_argument(
    '-f',
    '--fry',
    dest='fry_min',
    help=f'Frying threshold (default {DEFAULT_FRY_MIN})',
    nargs='?',
    default=DEFAULT_FRY_MIN,
    type=int
  )
  parser.add_argument(
    '--sep',
    dest='separate_regular',
    action='store_true',
    help=(
      'Flag for displaying regular players '
      '(those who have played at least 1 in 4 games) separately'
    )
  )
  
  # Run
  main(parser.parse_args())
