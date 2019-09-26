# Plots for Big two scores from 2013, regular players only

# Released into the public domain (CC0):
#   https://creativecommons.org/publicdomain/zero/1.0/
# ABSOLUTELY NO WARRANTY, i.e. "GOD SAVE YOU"

# Works in gnuplot 5.0.7

################################################################
# CSV file
################################################################

csv_file = 'big-two-2013-f-11-s.csv'

################################################################
# Function: quantity -> column number
################################################################

column_number(q) = \
  q eq 'player' ? 1 : \
  q eq 'games_played' ? 2 : \
  q eq 'cards_lost' ? 3 : \
  q eq 'games_won' ? 4 : \
  q eq 'games_fried' ? 5 : \
  q eq 'net_score' ? 6 : \
  q eq 'cards_lost_avg' ? 7 : \
  q eq 'games_won_pc' ? 8 : \
  q eq 'games_fried_pc' ? 9 : \
  q eq 'net_score_avg' ? 10 : \
  q eq 'regular' ? 11 : \
  'ERROR: unknown quantity '.q

################################################################
# Functions: quantity -> column and stringcolumn
################################################################

content_column(q) = column(column_number(q))
string_column(q) = stringcolumn(column_number(q))

################################################################
# Function: quantity -> long name of quantity
################################################################

long_name(q) = \
  q eq 'cards_lost_avg' ? 'Average cards lost (c)' : \
  q eq 'games_won_pc' ? 'Proportion of games won (w) / %' : \
  q eq 'games_fried_pc' ? 'Proportion of games fried (f) / %' : \
  q eq 'net_score_avg' ? 'Average zero-sum score (s)' : \
  'ERROR: unknown quantity '.q

################################################################
# Functions: index -> x and y quantities to be plotted
################################################################

# 1. cards_lost_avg VS games_won_pc
# 2. cards_lost_avg VS games_fried_pc
# 3. cards_lost_avg VS net_score_avg
# 4. games_won_pc VS net_score_avg

quantity_x(i) = \
  i <= 3 ? 'cards_lost_avg' : \
  'games_won_pc'

quantity_y(i) = \
  i == 1 ? 'games_won_pc' : \
  i == 2 ? 'games_fried_pc' : \
  'net_score_avg'

################################################################
# Global plot settings
################################################################

set grid
set terminal svg dynamic font 'Helvetica, 16' enhanced background rgb 'white'
set title 'Big two (2013): regular players' font ', 20'
set xlabel font ', 18'
set ylabel font ', 18'
set datafile separator comma

################################################################
# Functions: index -> x and y columns if corresponding player is regular
################################################################

is_regular(dummy) = string_column('regular') eq 'True'

regular_x(i) = is_regular(0) ? content_column(quantity_x(i)) : NaN
regular_y(i) = is_regular(0) ? content_column(quantity_y(i)) : NaN

################################################################
# Functions: index -> x and y columns if corresponding player is combined
################################################################

# (Here 'combined' means the player '*' for all statistics combined.)

is_combined(dummy) = string_column('player') eq '*'

combined_x(i) = is_combined(0) ? content_column(quantity_x(i)) : NaN
combined_y(i) = is_combined(0) ? content_column(quantity_y(i)) : NaN

################################################################
# Function: player -> if corresponding player matches
################################################################

match_player(p) = string_column('player') eq p

################################################################
# Functions: index -> manually tweaks for offsets
################################################################

tweak_x(i) = \
  i == 1 && match_player('Js') ? 0.01 : \
  i == 1 && match_player('T') ? -0.01 : \
  i == 2 && match_player('H') ? -0.08 : \
  i == 2 && match_player('Js') ? 0.015 : \
  i == 2 && match_player('T') ? -0.015 : \
  i == 3 && match_player('H') ? -0.095 : \
  i == 3 && match_player('Js') ? 0.01 : \
  i == 3 && match_player('T') ? -0.095 : \
  i == 4 && match_player('C') ? -0.05 : \
  i == 4 && match_player('Js') ? 0.025 : \
  i == 4 && match_player('T') ? -0.25 : \
  0

tweak_y(i) = \
  i == 1 && match_player('T') ? -0.3 : \
  i == 2 && match_player('H') ? 0.1 : \
  i == 2 && match_player('T') ? -0.4 : \
  i == 3 && match_player('C') ? -0.3 : \
  i == 3 && match_player('H') ? 0.05 : \
  i == 3 && match_player('T') ? -0.35 : \
  i == 4 && match_player('C') ? -0.4 : \
  0

################################################################
# Functions: index, c -> ideal net score and title (for legend)
################################################################

# For plot 3, cards_lost_avg (c) VS net_score_avg (s),
# the ideal relationship is
#   s == T - 4 c,
# or
#   s == 4 (c_* - c),
# where
#   T = 4 c_* is the 4-player total cards lost average, and
#   c_* is the combined cards lost average, i.e. cards_lost_avg for '*'.

ideal_net_score(i, c) = i == 3 ? 4 * (c_star - c) : NaN

ideal_net_score_title(i) = i == 3 ? 's = 4 (c_* - c)' : ''

################################################################
# Plots
################################################################

do for [i = 1:4] {
  
  # Output file name
  svg_file = quantity_x(i) . '-' . quantity_y(i) . '.svg'
  set output svg_file
  set title sprintf('Big two (2013 regular players): plot %d', i)
  
  # Axes labels
  set xlabel long_name(quantity_x(i))
  set ylabel long_name(quantity_y(i))
  
  # Extract x* (combined cards_lost_avg) for plot 3
  if (i == 3) {
    
    # Count number of rows
    stats csv_file matrix nooutput
    num_rows = STATS_size_y
    
    # Extract cards_lost_avg for combined player '*' (last row)
    stats csv_file \
      using column_number('cards_lost_avg') \
      skip (num_rows - 1) \
      nooutput
    c_star = STATS_min
  }
  
  # Plot:
  # (a) combined player data point and label
  # (b) regular player data points
  # (c) regular player labels
  plot \
    \
    ideal_net_score(i, x) \
      linetype rgb 'web-green' \
    title ideal_net_score_title(i) \
    , \
    \
    csv_file \
    using (regular_x(i)) : (regular_y(i)) \
    with \
      point \
        linecolor rgb 'blue' \
        pointtype 6 \
        pointsize 0.8 \
    notitle \
    , \
    \
    csv_file \
    using \
      (regular_x(i) + tweak_x(i)) : \
      (regular_y(i) + tweak_y(i)) : \
      column_number('player') \
    with \
      labels \
        center \
        offset 1.2, 0.3 \
    notitle \
    , \
    \
    csv_file \
    using \
      (combined_x(i)) : \
      (combined_y(i)) : \
      column_number('player') \
    with \
      labels \
        center \
        offset 0.5, -0.2 \
      point \
        linecolor rgb 'red' \
        pointtype 6 \
        pointsize 0.8 \
    notitle
}