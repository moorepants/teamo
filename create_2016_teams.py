#!/usr/bin/env python

import os
from collections import Counter
from random import shuffle, choice

import pandas as pd
import yaml

from parse_rst import parse_document

PROJECT_DIR = '/home/moorepants/Websites/eme185-website/content/pages/projects'
NUM_SELECTED = 28


class Person(object):

    def __init__(self, name, original_section=None, willing_to_switch=None,
                 gender=None, selections=None):
        self.name = name
        self.original_section = original_section
        self.willing_to_switch = willing_to_switch
        self.gender = gender
        self.selections = selections

    def __str__(self):
        s = "Name: {}\n".format(self.name)
        s += "Gender: {}\n".format(self.gender)
        s += "Original Section: {}\n".format(self.original_section)
        s += "Willing to switch: {}\n".format(self.willing_to_switch)
        if self.selections is not None:
            s += "Selections: {}\n".format(", ".join(self.selections))
        return s

    def can_attend(self, section):
        if self.original_section == section or self.willing_to_switch:
            return True
        else:
            return False


class Project(object):
    def __init__(self, id, title, team=None):
        self.id = id
        self.title = title
        self.team = team

    def __str__(self):
        s = "[{}] {}\n".format(self.id, self.title)
        if self.team:
            s += "=" * len(s) + "\n"
            s += "Team size: {}\n".format(self.team.num_members())
            s += "Members: {}\n".format("; ".join([m.name for m in self.team.members]))
            s += "Genders: {}\n".format(", ".join([m.gender if m.gender else 'None' for m in self.team.members]))
            s += "Section: {}\n".format(self.team.section())
        return s


class Team(object):

    def __init__(self, members=None):
        if members is None:
            self.members = []
        else:
            self.members = members

    def num_members(self):
        return len(self.members)

    def section(self):
        num_a02 = 0
        num_a03 = 0
        found_no = False
        for member in self.members:
            if member.original_section == 'A02':
                num_a02 += 1
            if member.original_section == 'A03':
                num_a03 += 1
            if member.willing_to_switch == 'No':
                section = member.original_section
                found_no = True

        if not found_no:
            if num_a02 > num_a03:
                section = 'A02'
            elif num_a03 > num_a02:
                section = 'A03'
            else:
                section = choice(['A02', 'A03'])

        return section


def populate_projects():
    field_names_and_parsers = {
        'title': str,
        'org': str,
        'website': str,
        'skills': lambda s: [skill.strip() for skill in str(s).split(',')],
        'location': str,
        'id': str,
        'status': str,
        'template': str,
    }
    projects = {}
    for rst_file in os.listdir(PROJECT_DIR):
        with open(os.path.join(PROJECT_DIR, rst_file), 'r') as f:
            data = parse_document(f.read(), field_names_and_parsers)
            project = Project(data.metadata['id'], data.metadata['title'])
            projects[project.id] = project

    projects['MUS1'] = Project('MUS1', 'Solar Car Batter Enclosure')
    return projects


def populate_students(roster, catme_data):
    students = {}
    for name in roster['Name']:
        row = catme_data[catme_data['Name'] == name]
        if len(row) == 0:
            person = Person(name)
        else:
            try:
                selections = row['Project Choice'].iloc[0].split(',')
            except AttributeError: # np.nan
                selections = []
            person = Person(name,
                            row['Section'].iloc[0],
                            True if row['Studio Switch'].iloc[0] == 'Yes' else False,
                            row['Gender with Other'].iloc[0],
                            selections)
        students[person.name] = person
    return students


def rank_projects(students, projects):

    all_votes = []
    for name, person in students.items():
        if person.selections is not None:
            all_votes += person.selections
    c = Counter(all_votes)
    votes = pd.DataFrame(c.most_common(), columns=['id', 'votes'])
    votes.index = votes['id']
    del votes['id']
    zero_votes = set(projects.keys()).difference(set(votes.index))
    z = pd.DataFrame([0] * len(zero_votes),
                     columns=['votes'],
                     index=list(zero_votes))
    votes = votes.append(z)
    titles = pd.Series([p.title for p in projects.values()],
                       index=projects.keys())
    votes['title'] = titles

    return votes

catme_data = pd.read_csv('catme-data.csv')
catme_wo_na = catme_data.dropna()
roster = pd.read_csv('roster.csv')

projects = populate_projects()
students = populate_students(roster, catme_data)
available_pool = [students[n] for n in list(roster['Name'])]
votes = rank_projects(students, projects)
# this gives the order with fewest votes first
selected_ids = list(votes.sort('votes').tail(NUM_SELECTED).index)
selected = [projects[p_id] for p_id in selected_ids]

# Add predetermined teams.
with open('fixed-teams.yml', 'r') as f:
    fixed_teams = yaml.load(f)
for proj_id, members in fixed_teams.items():
    projects[proj_id].team = Team([students[m] for m in members])

# Remove these folks from the pool.
for proj_id, project in projects.items():
    if project.team:
        for person in project.team.members:
            available_pool.remove(person)

# Populate each project's team with up to three members from the pool.
for project in selected:

    idxs = catme_wo_na['Project Choice'].str.contains(project.id)
    people_who_selected = [students[n] for n in list(catme_wo_na[idxs]['Name'])]
    shuffle(people_who_selected)

    if not project.team:
        project.team = Team()

    for person in people_who_selected:
        # break from the loop once 4 people are assigned
        if project.team.num_members() > 3:
            break

        # TODO: one female is in the group try to add a second one

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
    #print(possible)
    #print([projects[p].team.num_members() for p in possible])
    if possible:
        for proj_id in possible:
            if projects[proj_id].team.num_members() < 4:
                projects[proj_id].team.members.append(person)
                #print('Added {}'.format(person.name))
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
