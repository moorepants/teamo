#!/usr/bin/env python

from random import shuffle

import yaml
import pandas

from teamo import (rank_projects, populate_projects, populate_students,
                   compute_num_teams, Team)

PATH_TO_ROSTER = '/home/moorepants/Drive/EME185/2017/projects/roster.csv'
PATH_TO_CATME = '/home/moorepants/Drive/EME185/2017/projects/catme-data.csv'
PATH_TO_PROJ_DIR = '/home/moorepants/Websites/eme185-website/content/pages/projects'
PATH_TO_FIXED = '/home/moorepants/Drive/EME185/2017/projects/fixed-teams.yml'
MIN_TEAM_SIZE = 4

catme = pandas.read_csv(PATH_TO_CATME)
roster = pandas.read_csv(PATH_TO_ROSTER)

projects = populate_projects(PATH_TO_PROJ_DIR)
students = populate_students(roster, catme)

num_teams, max_in_team, num_larger_teams = \
    compute_num_teams(len(students), MIN_TEAM_SIZE)
msg = 'There will be {} teams of {} and {} teams of {}.'
print(msg.format(num_teams - num_larger_teams, MIN_TEAM_SIZE, num_larger_teams,
                 MIN_TEAM_SIZE + 1))

rankings = rank_projects(students, projects)

# Add predetermined teams.
with open(PATH_TO_FIXED, 'r') as f:
    fixed_teams = yaml.load(f)
for proj_id, members in fixed_teams.items():
    projects[proj_id].team = Team([students[m] for m in members])

# Remove these folks from the pool.
available_pool = [students[n] for n in list(roster['Name'])]
for proj_id, project in projects.items():
    if project.team:
        for person in project.team.members:
            available_pool.remove(person)

# this gives the order with fewest votes first
fixed_ids = list(fixed_teams.keys())
without_fixed = rankings.iloc[~rankings.index.isin(fixed_ids)]
selected_ids = list(without_fixed.sort('votes').tail(num_teams -
                                                     len(fixed_ids)).index) + fixed_ids
# Barabara prefers the water table project.
selected_ids.remove('fruit')
selected_ids.append('watertab')
selected_ids = list(rankings.loc[selected_ids].sort('votes').index)
selected = [projects[p_id] for p_id in selected_ids]

# Populate each project's team with up to three members from the pool.
for project in selected:

    if not project.team:
        project.team = Team()

    idxs = catme['2017 Project Choice'].str.contains(project.id)
    people_who_selected = [students[n] for n in list(catme[idxs]['Name'])]

    # If the team has only one female then put the female choices up front.
    if project.team.has_only_one_female:
        people_who_selected = sorted(people_who_selected,
                                     key=lambda p: 0 if p.gender in
                                     ['Female', 'Other/Prefer not to answer'] else 1)
    else:
        shuffle(people_who_selected)

    for person in people_who_selected:
        if project.team.num_members() > MIN_TEAM_SIZE - 1:
            break

        add = False
        if project.team.num_members == 0 and person in available_pool:
            add == True
        elif person in available_pool:
            if person.can_attend(project.team.section()):
                add = True
        if add:
            project.team.members.append(person)
            available_pool.remove(person)

for person in available_pool.copy():
    possible = []
    for project in selected:
        if person.can_attend(project.team.section()):
            possible.append(project.id)
    possible = list(set(possible).intersection(set(person.selections)))
    num_in_possible = [projects[p].team.num_members() for p in possible]
    possible = [x for (y, x) in sorted(zip(num_in_possible, possible))]
    if possible:
        for proj_id in possible:
            if projects[proj_id].team.num_members() < 4:
                projects[proj_id].team.members.append(person)
                available_pool.remove(person)
                break

section_students = {'A02': 0, 'A03': 0}
for proj_id, project in projects.items():
    if project.team:
        section_students[project.team.section()] += project.team.num_members()
        print(project)

print(section_students)
print("Remaining: {}".format(len(available_pool)))
print([v.team.num_members() for k, v in projects.items() if v.team])

for person in available_pool:
    print(person.original_section)
    print(person.willing_to_switch)
