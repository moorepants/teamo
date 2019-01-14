#!/usr/bin/env python

from random import shuffle

import yaml
import pandas

from teamo import (rank_projects, rank_projects_weighted, populate_projects,
                   populate_students, compute_num_teams, Team)

YEAR = '2019'

# roster-for-team-selection.csv should be generated from the latest
# photorosters.ucdavis.edu download with columns: Student ID, Section, Email,
# Name
PATH_TO_ROSTER = '/home/moorepants/Drive/Teaching/EME185/{}/rosters/roster-for-team-selection.csv'.format(YEAR)

# catme-data.csv is first of the three sections in the CATME download file. I
# typically have to manually edit some of the mistakes or missing data from
# students.
PATH_TO_CATME = '/home/moorepants/Drive/Teaching/EME185/{}/projects/catme-data.csv'.format(YEAR)

PATH_TO_PROJ_DIR = '/home/moorepants/Websites/eme185-website/content/pages/projects'

# fixed-teams.yml includes any apriori placements into teams, i.e. I choose
# them manually.
PATH_TO_FIXED = '/home/moorepants/Drive/Teaching/EME185/{}/projects/fixed-teams.yml'.format(YEAR)

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

print('Raw Project Rankings:')
print(rank_projects(students, projects))

rankings = rank_projects_weighted(students, projects)
print('Weight Project Rankings:')
print(rankings)

available_pool = [students[n] for n in list(roster['Name'])]

# Add students to teams that were chosen apriori. If the team is full then
# remove the project from the list of available projects.
with open(PATH_TO_FIXED, 'r') as f:
    populated_teams = yaml.load(f)
for proj_id, members in populated_teams.items():
    projects[proj_id].team = Team([students[m] for m in members])
    for m in members:
        available_pool.remove(students[m])

fixed_ids = [k for k in populated_teams
             if len(projects[k].team.members) >= max_in_team]

print('These teams are full:')
print(fixed_ids)

# aeration: selected for A01
# wasteconvey: selected for A01
# rowsys: lower of the two from the same sponsor
# microtantium: lower of the 5 submitted by same sponsor
# catfemur: lower of the 5 submitted by same sponsor
projs_to_remove = ['wasteconvey',
                   'aeration',
                   'rowsys',
                   'microtitanium',
                   'catfemur']

# remove the fixed teams and the selected removals
remaining_proposals = rankings.iloc[~rankings.index.isin(fixed_ids +
                                                         projs_to_remove)]

selected_ids = list(remaining_proposals.sort_values('votes').
                    tail(num_teams - len(fixed_ids)).index) + fixed_ids
selected_ids = list(rankings.loc[selected_ids].sort_values('votes').index)
selected = [projects[p_id] for p_id in selected_ids]

print('Selected projects:')
for i, proj in enumerate(reversed(selected)):
    print(i + 1, proj.id)

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


def get_people_who_selected(project):
    people_who_selected = [student for student in available_pool if
                           student.chose_project(project.id)]
    #print('{} people selected this project'.format(len(people_who_selected)))
    # NOTE : shuffle() gives some randomization for the order of people who
    # ranked equivilantly
    shuffle(people_who_selected)
    return sort_by_project_rank(people_who_selected, project.id)

for project in selected:

    #print(20 * "=")
    #print(project)
    #print(20 * "=")

    if not project.team:
        project.team = Team()

    people_who_selected = get_people_who_selected(project)

    used = []
    for i, person in enumerate(people_who_selected):
        # TODO : if three (or four) males on team, don't add woman

        # fill up to 3 members
        if project.team.num_members() > MIN_TEAM_SIZE - 1:
            break

        if person not in used:
            if project.team.num_members() == 0:
                project.team.add_member(person)
                proj_section = project.team.section()
                if section_proj_count[proj_section] >= MAX_NUM_TEAMS_PER_SECTION:
                    pass
            else:
                proj_section = project.team.section()
                #print('females', project.team.num_females())
                if project.team.has_only_one_female():
                    # try to pick one more woman first
                    nonmales = [s for s in people_who_selected[i:]
                                if s.gender != 'Male' and s.can_attend(proj_section)]
                    if nonmales:
                        for nonmale in nonmales:
                            if person.can_attend(proj_section):
                                project.team.add_member(nonmale)
                                used.append(nonmale)
                                #print('Added second female:', nonmale)
                                break  # from nonmales for loop (only add one femal)
                    else:
                        if person.can_attend(proj_section):
                            project.team.add_member(person)
                            #print('Couldnt add female so added:', person)
                else:
                    if person.can_attend(proj_section):
                        project.team.add_member(person)
                        #print('Added:', person)

    for member in project.team.members:
        try:
            available_pool.remove(member)
        except:  # fixed team member already removed from pool
            pass

    section_proj_count[proj_section] += 1

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
                projects[proj_id].team.add_member(person)
                available_pool.remove(person)
                break

section_students = {'A02': 0, 'A03': 0}
for proj_id, project in projects.items():
    if project.team:
        section_students[project.team.section()] += project.team.num_members()
        print(project)

# ensure that students can be in the project section
for project in selected:
    for member in project.team.members:
        if not member.can_attend(project.team.section()):
            print("{} can't be in section {}".format(member, project.section))

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
