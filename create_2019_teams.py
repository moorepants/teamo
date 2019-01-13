#!/usr/bin/env python

from random import shuffle

import yaml
import pandas

from teamo import (rank_projects, rank_projects_weighted, populate_projects,
                   populate_students, compute_num_teams, Team)

PATH_TO_ROSTER = '/home/moorepants/Drive/Teaching/EME185/2018/rosters/roster-for-team-selection.csv'
PATH_TO_CATME = '/home/moorepants/Drive/Teaching/EME185/2018/projects/catme-data.csv'
PATH_TO_PROJ_DIR = '/home/moorepants/Websites/eme185-website/content/pages/projects'
PATH_TO_FIXED = '/home/moorepants/Drive/Teaching/EME185/2018/projects/fixed-teams.yml'
MIN_TEAM_SIZE = 4
MAX_NUM_TEAMS = 22  # only have 11 tables in each section
MAX_NUM_TEAMS_PER_SECTION = 11

catme = pandas.read_csv(PATH_TO_CATME)
roster = pandas.read_csv(PATH_TO_ROSTER)

projects = populate_projects(PATH_TO_PROJ_DIR)
students = populate_students(roster, catme)

num_teams, max_in_team, num_larger_teams = \
    compute_num_teams(len(students), MIN_TEAM_SIZE, MAX_NUM_TEAMS)
msg = 'There will be {} teams of {} and {} teams of {}.'
print(msg.format(num_teams - num_larger_teams, MIN_TEAM_SIZE, num_larger_teams,
                 MIN_TEAM_SIZE + 1))

print(rank_projects(students, projects))
rankings = rank_projects_weighted(students, projects)
print(rankings)

available_pool = [students[n] for n in list(roster['Name'])]

# Add predetermined teams and remove them from the available pool.
with open(PATH_TO_FIXED, 'r') as f:
    fixed_teams = yaml.load(f)
for proj_id, members in fixed_teams.items():
    projects[proj_id].team = Team([students[m] for m in members])
    for m in members:
        available_pool.remove(students[m])

# 1. Drop the hydrofoil because only four of the boat team members voted for
# it and I'd have to mentor more.
# Bump up strap because Dick will be such a good mentor, students don't
# understand how good of a project this will be and it had plenty of votes.

# this gives the order with fewest votes first
fixed_ids = list(fixed_teams.keys())
without_fixed = rankings.iloc[~rankings.index.isin(fixed_ids)]
dont_rank = ['hydrofoil', 'pool', 'strap']
selected_by_rank = without_fixed.iloc[~without_fixed.index.isin(dont_rank)]
selected_ids = list(selected_by_rank.sort_values('votes').
                    tail(num_teams - len(fixed_ids) - 1).index) + fixed_ids + ['strap']

selected_ids = list(rankings.loc[selected_ids].sort_values('votes').index)
selected = [projects[p_id] for p_id in selected_ids]

# For students that didn't fill out the survey, give them the last five
# projects.
for name, student in students.items():
    if not student.selections:  # didn't fill out survey
        student.selections = [p.id for p in selected[:5]]

# Populate each project's team with up to three members from the pool.


def sort_by_project_rank(people, proj_id):
    def sort_score(person):
        idx = person.selections.index(proj_id)
        return 5 - idx
    return sorted(people, key=sort_score, reverse=True)

section_proj_count = {'A02': 0, 'A03': 0}

for project in selected:

    #print(20 * "=")
    #print(project)
    #print(20 * "=")

    if not project.team:
        project.team = Team()

    people_who_selected = [student for student in available_pool if
                           student.chose_project(project.id)]
    #print('{} people selected this project'.format(len(people_who_selected)))
    # NOTE : shuffle() gives some randomization for the order of people who
    # ranked equivilantly
    shuffle(people_who_selected)
    people_who_selected = sort_by_project_rank(people_who_selected, project.id)

    used = []
    for i, person in enumerate(people_who_selected):
        # TODO : if three (or four) males on team, don't add woman

        if project.team.num_members() > MIN_TEAM_SIZE - 1:
            break

        if person not in used:
            if project.team.num_members() == 0:
                proj_section = person.original_section
                if section_proj_count[proj_section] >= MAX_NUM_TEAMS_PER_SECTION:
                    pass
                else:
                    project.team.members.append(person)
                #print('Added first person:', person)
            else:
                #print('females', project.team.num_females())
                if project.team.has_only_one_female():
                    # try to pick one more woman first
                    nonmales = [s for s in people_who_selected[i:]
                                if s.gender != 'Male' and s.can_attend(proj_section)]
                    if nonmales:
                        for nonmale in nonmales:
                            project.team.members.append(nonmale)
                            used.append(nonmale)
                            #print('Added second female:', nonmale)
                            break  # from nonmales for loop (only add one femal)
                    else:
                        if person.can_attend(proj_section):
                            project.team.members.append(person)
                            #print('Couldnt add female so added:', person)
                else:
                    if person.can_attend(proj_section):
                        project.team.members.append(person)
                        #print('Added:', person)

    for member in project.team.members:
        try:
            available_pool.remove(member)
        except:  # fixed team member already removed from pool
            pass

    section_proj_count[proj_section] += 1

# tried to fill them starting with their favorite choice here, doesn't seem to
# work well and has lots of remainders
#a02_only = []
#a03_only = []
#either_sec = []
#for person in available_pool.copy():
    #if person.willing_to_switch:
        #either_sec.append(person)
    #elif person.original_section == 'A02':
        #a02_only.append(person)
    #elif person.original_section == 'A03':
        #a03_only.append(person)
#
#shuffle(a02_only)
#shuffle(a03_only)
#shuffle(either_sec)
#
#for person in a02_only:
    #for proj_id in set(person.selections).intersection([p.id for p in selected]):
        #proj = projects[proj_id]
        #if proj.team.section() == 'A02' and proj.team.num_members() < 5:
            #proj.team.members.append(person)
            #break
#
#for person in a03_only:
    #for proj_id in set(person.selections).intersection([p.id for p in selected]):
        #proj = projects[proj_id]
        #if proj.team.section() == 'A02' and proj.team.num_members() < 5:
            #proj.team.members.append(person)
            #break
#
#for person in a03_only:
    #for proj_id in set(person.selections).intersection([p.id for p in selected]):
        #proj = projects[proj_id]
        #if proj.team.num_members() < 5:
            #proj.team.members.append(person)
            #break

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
            if projects[proj_id].team.num_members() < 5:
                projects[proj_id].team.members.append(person)
                available_pool.remove(person)
                break

section_students = {'A02': 0, 'A03': 0}
for proj_id, project in projects.items():
    if project.team:
        section_students[project.team.section()] += project.team.num_members()
        print(project)

print(section_proj_count)
print(section_students)
print("Remaining: {}".format(len(available_pool)))
print('Counts of the teams.')
print([v.team.num_members() for k, v in projects.items() if v.team])

print('The remainders.')
for person in available_pool:
    print(person)

final_student_names = []
final_project_ids = []
final_sections = []
for proj in selected:
    for person in proj.team.members:
        final_project_ids.append(proj.id)
        final_student_names.append(person.name)
        final_sections.append(proj.team.section())

matches = pandas.DataFrame({'Project': final_project_ids,
                            'Section': final_sections},
                           index=final_student_names).sort_index()
matches.to_csv('project-matches.csv')

# TODO : This script isn't quite working. It is not honoring the section and
# section switch for every student!!
