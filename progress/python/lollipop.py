# Lollipop chart
# Python script to create a lollipop chart showing the progress status of SDG indicators by goal
# For each goal, there is a series of circles (lollipops) whose sizes indicate the number of indicators in each progress category: Target achieved, On track, Progress made but acceleration needed, Limited progress, or Deterioration

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yaml

import matplotlib as mpl
mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams['font.sans-serif'] = ['Helvetica Neue for SAS']

# Update src with the path to the indicator_calculation_components.yml file that contains the relevant progress data
src = r".\progress\tests\indicator_calculation_components_gif_master_oct21-2025.yml"
outfile_csv = None # Path+name of output csv file with progress statuses by goal
outfile_img = None # Path+name of lollipop chart image output
vertical = True  # Set to True for vertical layout, False for horizontal layout

# Read the indicator_calculation_components.yml file
with open(src, 'r') as file:
    content = yaml.safe_load(file)

# Convert yaml file to dataframe containing goal, progress_status, and score columns
progress = {k: {'goal': k.split('-')[0], 'progress_status': v['progress_status'], 'score': v['score']} for k, v in content.items()}
df = pd.DataFrame.from_dict(progress, orient='index')

# Only keep indicators with progress statuses
df_measured = df.loc[df['progress_status'].isin(['target_achieved', 'substantial_progress', 'moderate_progress', 'limited_progress', 'deterioration'])]

# Define some utility functions for converting between statuses, scores, and chart levels
def status2level(status):
    # Convert a progress status string to a chart level
    # Ex: Deterioration --> 0, Limited progress --> 1, and so on.
    if status == "deterioration":
        return 0
    if status == "limited_progress":
        return 1
    if status == "moderate_progress":
        return 2
    if status == "substantial_progress":
        return 3
    if status == "target_achieved":
        return 4

def score2level(score):
    # Convert a progress score to a chart level
    # Ex: "Deterioration" scores in the range [-5, -2.5[ are converted to 0, "Limited progress" scores in the range [-2.5, 0[ are converted to 1, and so on.
    if score == "target_achieved":
        return 4
    if 2.5 <= score <= 5:
        return 3
    if 0 <= score < 2.5:
        return 2
    if -2.5 <= score < 0:
        return 1
    if -5 <= score < -2.5:
        return 0

# Count the number of indicators falling within each goal-status group
df_by_goal_status = df_measured.groupby(['goal', 'progress_status'])['progress_status'].count().reset_index(name='number')
# Add a column containing the corresponding numeric values of each progress status for the chart 
df_by_goal_status['score'] = [status2level(x) for x in df_by_goal_status['progress_status']]

# Output the dataframe as a csv file
if outfile_csv:
    out = df_by_goal_status[['goal', 'progress_status', 'number']].pivot(index='goal', columns='progress_status', values='number')
    out.index = out.index.astype(int)
    out = out.sort_index(ascending=True)
    out.rename(columns={'deterioration': 'Deterioration', 'limited_progress': 'Limited progress', 'moderate_progress': 'Progress made, but acceleration needed', 'substantial_progress': 'On track', 'target_achieved': 'Target achieved'}, inplace=True)
    out.to_csv(outfile_csv)

# Get a summarized table of progress across all indicators
ntot = df_by_goal_status['number'].sum()
df_summarized = df_by_goal_status.groupby('progress_status')['number'].sum()/ntot*100
df_summarized.rename(index={'deterioration': 'Deterioration', 'limited_progress': 'Limited progress', 'moderate_progress': 'Progress made, but acceleration needed', 'substantial_progress': 'On track', 'target_achieved': 'Target achieved'}, inplace=True)
print(df_summarized)


# Create chart

# Colour of progress status gauge
gauge_colours = {
    'target_achieved': '#93c46c',
    'substantial_progress': '#93c46c',
    'moderate_progress': '#fcbc4c',
    'limited_progress': '#f47c04',
    'deterioration': '#d42c2c'
}

gray = '#898989'

if vertical is False:
    # Set up figure oriented in horizontal/wide layout
    fig, ax = plt.subplots(figsize=(15,8))

    # Add Goal icons
    for x in range(1,18):
        # get path to Goal icon
        img = r".\assets\E SDG Icons WEB\E-WEB-Goal-{:02d}.png".format(x)
        # Add Goal icon to plot
        ab = mpl.offsetbox.AnnotationBbox(mpl.offsetbox.OffsetImage(plt.imread(img), zoom=0.033), (x, 4.5), frameon=False, zorder=4)
        ax.add_artist(ab)

    # Add lollipops
    for goal in df_by_goal_status.groupby('goal'):
        # Add lines connecting the lollipop circles
        ax.vlines(int(goal[0]), min(goal[1].score), max(goal[1].score),
                color=gray, linewidth=1,
                zorder=1)
        # Add lollipop circles (coloured by goal)
        # ax.scatter(goal[1]['goal'].astype(int), goal[1]['score'], s=60*goal[1]['number']**1.65, 
        #            facecolor=sdg_palette['Goal'+goal[0]], edgecolor='white', linewidth=1,
        #            zorder=3)
        # ax.scatter(goal[1]['goal'].astype(int), goal[1]['score'], s=50*goal[1]['number']**1.75, 
        #            facecolor='None', edgecolor='white', linewidth=2,
        #            zorder=5)

    # Add lollipop circles (coloured by progress status)
    nmax = df_by_goal_status['number'].max()
    for status in df_by_goal_status.groupby('progress_status'):
        ax.scatter(status[1]['goal'].astype(int), status[1]['score'], s=60*status[1]['number']**1.65,
                facecolor=gauge_colours[status[0]], edgecolor='w', linewidth=1,
                zorder=3)
        # Add concentric circles to show number of indicators more clearly
        # for x in range(1,nmax):
        #     # if any(status[1]['number'] > x):
        #         ax.scatter(status[1].loc[status[1]['number'] > x]['goal'].astype(int), status[1].loc[status[1]['number'] > x]['score'], s=60*x**1.65,
        #                    facecolor='None', edgecolor='w', linewidth=1,
        #                    zorder=3)

    # Mark the average goal progress
    # m = mpl.markers.MarkerStyle(marker='s')
    # m._transform = m.get_transform().scale(1.75, 0.25)
    # ax.scatter(df_by_goal.index, df_by_goal['level'], 
    #            marker=m, c=sdg_palette.values(), s=500, linewidth=0, edgecolor='w',
    #            zorder=4)

    # Chart formatting
    ax.set_ylim(-0.5,5)
    ax.set_xlim(0.5,17.5)
    ax.set_yticks([4, 3, 2, 1, 0])
    ax.set_xticks([])
    ax.tick_params(pad=40, length=0)
    ax.set_yticklabels(["Target achieved", "On track", "Progress made,\nbut acceleration\nneeded", "Limited progress", "Deterioration"], ha='center')

    # Create custom legend
    legend_elements = [mpl.lines.Line2D([0], [0], marker='o', color='None', markerfacecolor='k', markeredgecolor='w', markersize=np.sqrt(60*x**1.65)) for x in range(1,nmax+1)]
    # Position of legend may need to be adjusted depending on the number of legend elements
    ax.legend(title='Number of indicators', handles=legend_elements, labels=[str(x) for x in range(1,nmax+1)], ncols=nmax, frameon=False, bbox_to_anchor=(0.55,0), loc='center')
    ax.get_legend().get_title().set_position((-250, -20))

    # Add line between On track and Progress made but acceleration needed categories
    # ax.hlines(2.5, 0, 18, color='#CCCCCC', linewidth=5, zorder=1)

    ax.grid(axis='y', linestyle=':', color='#CCCCCC', zorder=1)
    ax.spines[['bottom', 'top', 'right', 'left']].set_visible(False)
    if outfile_img:
        fig.savefig(outfile_img)
    else:
        fig.show()

else:
    # Setup figure oriented in vertical/tall layout
    fig, ax = plt.subplots(figsize=(8,13))

    # Add Goal icons
    for y in range(1,18):
        # get path to Goal icon
        img = r".\assets\E SDG Icons WEB\E-WEB-Goal-{:02d}.png".format(y)
        # Add Goal icon to plot
        ab = mpl.offsetbox.AnnotationBbox(mpl.offsetbox.OffsetImage(plt.imread(img), zoom=0.033), (-0.75, y), frameon=False, zorder=4)
        ax.add_artist(ab)

    # Add lollipops
    for goal in df_by_goal_status.groupby('goal'):
        ax.hlines(int(goal[0]), min(goal[1].score), max(goal[1].score),
                color=gray, linewidth=1,
                zorder=1)

    nmax = df_by_goal_status['number'].max()
    for status in df_by_goal_status.groupby('progress_status'):
        ax.scatter(status[1]['score'], status[1]['goal'].astype(int), s=60*status[1]['number']**1.65,
                facecolor=gauge_colours[status[0]], edgecolor='white', linewidth=1,
                zorder=3)

    # Mark the average goal progress
    # m = mpl.markers.MarkerStyle(marker='s')
    # m._transform = m.get_transform().scale(1.75, 0.25)
    # ax.scatter(df_by_goal['level'], df_by_goal.index, 
    #            marker=m, c=sdg_palette.values(), s=500, linewidth=0, edgecolor='w',
    #            zorder=4)

    # Chart formatting
    ax.set_xlim(-0.75,4.25)
    ax.set_ylim(17.5, 0.5)
    ax.set_xticks([4, 3, 2, 1, 0])
    ax.set_yticks([])
    ax.tick_params(pad=5, length=0)
    ax.set_xticklabels(["Target achieved", "On track", "Progress made,\nbut acceleration\nneeded", "Limited progress", "Deterioration"], ha='center')
    ax.xaxis.set_ticks_position('top')

    legend_elements = [mpl.lines.Line2D([0], [0], marker='o', color='None', markerfacecolor='k', markeredgecolor='w', markersize=np.sqrt(60*x**1.65)) for x in range(1,nmax+1)]
    # Position of legend may need to be adjusted depending on the number of legend elements
    ax.legend(title='Number of indicators', handles=legend_elements, labels=[str(x) for x in range(1,nmax+1)], ncols=nmax, frameon=False, bbox_to_anchor=(0.6,1.1), loc='center')
    ax.get_legend().get_title().set_position((-250, -20))

    ax.grid(axis='x', linestyle=':', color='#CCCCCC', zorder=1)
    ax.spines[['bottom', 'top', 'right', 'left']].set_visible(False)
    fig.tight_layout()
    if outfile_img:
        fig.savefig(outfile_img)
    else:
        fig.show()