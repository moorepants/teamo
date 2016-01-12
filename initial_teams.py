#!/usr/bin/env python

import os
from collections import Counter, defaultdict
from random import shuffle, choice

import pandas as pd
import yaml

from parse_rst import parse_document

PROJECT_DIR = '/home/moorepants/Websites/eme185-website/content/pages/projects'
NUM_SELECTED = 26


class Person(object):

    def __init__(self, name, original_section, willing_to_switch,
                 gender, project_selections, team=None):
        self.name = name
        self.original_section = original_section
        self.willing_to_switch = willing_to_switch
        self.gender = gender
        self.team = team


class Project(object):
    def __init__(self, id, title):
        self.id = id
        self.name = title


class Team(object):

    def __init__(self, members, project):
        self.members = members
        self.project = project

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


def choose_section(sections, switches):
    num_a02 = 0
    num_a03 = 0
    found_no = False
    for sec, sw in zip(sections, switches):
        if sec == 'A02':
            num_a02 += 1
        if sec == 'A03':
            num_a03 += 1
        if sw == 'No':
            section = sec
            found_no = True

    if not found_no:
        if num_a02 > num_a03:
            section = 'A02'
        elif num_a03 > num_a02:
            section = 'A03'
        else:
            section = choice(['A02', 'A03'])

    return section


def print_projects():

    team_sections = []
    num_students = {'A02': 0, 'A03': 0}

    for proj_id, assignment in project_assignments.items():
        try:
            s = "Project: {}".format(titles[proj_id])
        except:
            s = "Project: {}".format(proj_id)
        print(s)
        print("=" * len(s))
        print(assignment)
        genders = []
        races = []
        sections = []
        switch = []
        for person in assignment:
            row = catme_data[catme_data['Name'] == person]
            try:
                genders.append(row['Gender with Other'].iloc[0])
                races.append(row['Race'].iloc[0])
                sections.append(row['Section'].iloc[0])
                switch.append(row['Studio Switch'].iloc[0])
            except IndexError:
                pass
        print(genders)
        print(races)
        print(sections)
        print(switch)
        team_section = choose_section(sections, switch)
        team_sections.append(team_section)
        num_students[team_section] += len(assignment)
        print(team_section)
        print("\n")

    c = Counter(team_sections)
    print(c)
    print(num_students)


def print_num_in_team(project_assignments):
    print([len(v) for k, v in project_assignments.items()])


def populate_projects():
    projects = {}
    for rst_file in os.listdir(PROJECT_DIR):
        with open(os.path.join(PROJECT_DIR, rst_file), 'r') as f:
            data = parse_document(f.read(), field_names_and_parsers)
            project = Project(data.metadata['id'], data.metadata['title'])
            projects[project.id] = project
    return projects


def populate_students(roster, catme_data):
    students = {}
    for name in roster['Name']:
        row = catme_data[catme_data['Name'] == name]
        try:
            selections = row['Project Choice'].iloc[0].split(',')
        except ValueError:
            selections = None
        person = Person(name,
                        row['Section'].iloc[0],
                        True if row['Studio Switch'].iloc[0] == 'Yes' else False,
                        row['Gender'].iloc[0],
                        selections)
        students[person.name] = person
    return students


def rank_projects(projects):

    all_votes = []
    for proj_id, project in projects.items():
        if project.selections is not None:
            all_votes += project.selections
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
roster = pd.read_csv('roster.csv')

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

project_list = {}
for rst_file in os.listdir(PROJECT_DIR):
    with open(os.path.join(PROJECT_DIR, rst_file), 'r') as f:
        data = parse_document(f.read(), field_names_and_parsers)
        project_list[data.metadata['id']] = data.metadata['title']

available_pool = list(roster['Name'])

# Add extra data to CATME
# add the students who wanted the battery enclosure

# Count the project choices and see which ones were selected the most.
choices = catme_data['Project Choice']
choices = choices.str.split(',')
all_votes = []
for ch in choices:
    try:
        all_votes += ch
    except:
        pass
c = Counter(all_votes)
votes = pd.DataFrame(c.most_common(), columns=['id', 'votes'])
votes.index = votes['id']
del votes['id']
zero_votes = set(project_list.keys()).difference(set(votes.index))
z = pd.DataFrame([0, 0, 0],
                 columns=['votes'],
                 index=list(zero_votes))
votes = votes.append(z)
titles = pd.Series(list(project_list.values()), index=project_list.keys())
votes['title'] = titles

# this gives the order with fewest votes first
selected = list(votes.sort('votes').tail(NUM_SELECTED).index)

catme_wo_na = catme_data.dropna()

with open('fixed-teams.yml', 'r') as f:
    fixed_teams = yaml.load(f)

project_assignments = defaultdict(list)

# Add predetermined teams.
project_assignments.update(fixed_teams)
for proj_id, team in project_assignments.items():
    for person in team:
        available_pool.remove(person)

# Starting with the projects with the fewest votes.
for project in selected:
    idxs = catme_wo_na['Project Choice'].str.contains(project)
    people_who_selected = list(catme_wo_na[idxs]['Name'])
    shuffle(people_who_selected)
    for person in people_who_selected:

        # break from the loop once 4 people are assigned
        if len(project_assignments[project]) > 3:
            break

        section = catme_data['Section'][catme_data['Name'] == person].iloc[0]
        willing_to_switch = catme_data['Studio Switch'][catme_data['Name'] == person].iloc[0]

        try:
            last_person = project_assignments[project][-1]
        except IndexError:
            teams_section = section
        else:
            teams_section = catme_data['Section'][catme_data['Name'] == last_person].iloc[0]

        # TODO: one female is in the group try to add a second one
        if person in available_pool and (section == teams_section or
                                         willing_to_switch == 'Yes'):
            project_assignments[project].append(person)
            available_pool.remove(person)

for person in available_pool.copy():
    try:
        selections = catme_data['Project Choice'][catme_data['Name'] == person].iloc[0].split(',')
    except IndexError: # not in survey
        pass
    except AttributeError:  # missing survey data
        pass
    else:
        section = catme_data['Section'][catme_data['Name'] == person].iloc[0]
        willing_to_switch = catme_data['Studio Switch'][catme_data['Name'] == person].iloc[0]
        possible = list(set(selected).intersection(set(selections)))
        for p in possible:
            teams_section = choose_section(sections, switches)

        print(possible)
        # sort them in order of fewest
        num_in_possible = [len(project_assignments[p]) for p in possible]
        possible = [x for (y, x) in sorted(zip(num_in_possible, possible))]
        print(possible)
        i = 0
        num_in_team = len(project_assignments[possible[i]])
        while num_in_team >= 4:
            try:
                num_in_team = len(project_assignments[possible[i]])
            except IndexError:
                i -= 1
                break
            else:
                i += 1
        project_assignments[possible[i]].append(person)
        available_pool.remove(person)
        print('Added {} to {}.'.format(person, titles[possible[0]]))

print_projects()

print_num_in_team(project_assignments)
