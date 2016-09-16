# coding: utf-8

import re
import sys
import requests
import pprint
import unicodecsv as csv


class Applications:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:28.0) Gecko/20100101 Firefox/28.0',
        'Cookie': '', # Set authorized cookies here
    }

    output = [
        [
            'Team Name',
            'Contact Name',
            'Contact Phone',
            'Contect E-mail',
            'Member Name',
            'Member Height',
            'Member Skill',
        ]
    ]

    def get_url(self, url):
        response = requests.get(url, headers=self.headers)
        return response.content.decode('cp1251').encode('utf-8')

    def load_teams(self):
        data = self.get_url('http://volleymsk.ru/ap/application_list.php')
        result = re.finditer(r'application_raw_view.php\?id=(\d+)#m_c', data)
        for match in result:
            team_id = match.group(1)

            print 'Load %s ...' % team_id
            try:
                self.load_info(team_id)
            except Exception as e:
                print 'Failed: {}'.format(e)
                continue

    def load_info(self, team_id):
        content = self.get_url('http://volleymsk.ru/ap/application_raw_view.php?id={team_id}#m_c'.format(team_id=team_id))

        REGEXP_CONTACT = [
            re.compile(r"<td.*?>.*?Команда.*?</td>\s*\n\s*<td.*><b>(.+)</b>", re.MULTILINE),
            re.compile(r"<td.*?>.*?Контактное лицо.*?</td>\s*\n\s*<td.*><b>(.+)</b>", re.MULTILINE),
            re.compile(r"<td.*?>.*?Контактый телефон.*?</td>\s*\n\s*<td.*><b>(.+)</b>", re.MULTILINE),
            re.compile(r"<td.*?>.*?E-mail.*?</td>\s*\n\s*<td.*><b>(.+)</b>", re.MULTILINE),
        ]

        REGEXP_TEAM = [
                re.compile(r'<td width="90"><b>(.+)</b>.*\n.*'
                           r'<td width="90"><b>(.+)</b>.*\n.*'
                           r'<td width="90"><b>(.+)</b>.*?\n.*?</tr>.*?\n.*?<tr>.*?\n.*?'
                           r'<td>Рост:</td><td><b>(.+)</b>.*\n.*'
                           r'<td>Мастерство:</td><td><b>(.+)</b>'
                           , re.MULTILINE),
        ]

        row = []
        for regexp in REGEXP_CONTACT:
            result = re.search(regexp, content)
            cell = re.sub('<img.*?>', '@', result.group(1))
            row.append(cell)

        team = []
        for regexp in REGEXP_TEAM:
            result = re.finditer(regexp, content)
            for match in result:
                last_name, first_name, middle_name, height, skill = match.groups()
                team.append([
                    ' '.join([last_name, first_name, middle_name]),
                    height,
                    skill,
                ])

        if not team:
            team = [[''] * 3]

        first_member = team.pop(0)
        row += first_member

        self.output.append(row)

        for member in team:
            self.output.append([''] * 4 + member)

        print 'OK'

    def write(self, filename='output.csv'):
        with open(filename, 'wb') as f:
            writer = csv.writer(f, encoding='utf-8', delimiter=';', quoting=csv.QUOTE_ALL)
            for row in self.output:
                writer.writerow(row)


class Teams(Applications):
    def load_teams(self):
        data = self.get_url('http://volleymsk.ru/ap/all_teams.php')

        result = re.finditer(r'<a href="/ap/team.php\?id=(\d+)">&gt;', data)
        for match in result:
            team_id = match.group(1)
            print 'Load %s ...' % team_id
            try:
                self.load_info(team_id)
            except Exception as e:
                print 'Failed: {}'.format(e)
                continue

    def load_info(self, team_id):
        content = self.get_url('http://volleymsk.ru/ap/team.php?id={team_id}'.format(team_id=team_id))

        REGEXP_CONTACT = [
            re.compile(r"<td.*?>.*?Команда.*?</td>\s*\n\s*<td.*><b>(.+)</b>", re.MULTILINE),
            re.compile(r"<td.*?>.*?Контактное лицо.*?</td>\s*\n\s*<td.*><b>(.+)</b>", re.MULTILINE),
            re.compile(r"<td.*?>.*?Контактный телефон.*?</td>\s*\n\s*<td.*><b>(.+)</b>", re.MULTILINE),
            re.compile(r"<td.*?>.*?E-mail.*?</td>\s*\n\s*<td.*><b>(.+)</b>", re.MULTILINE),
        ]

        row = []
        for regexp in REGEXP_CONTACT:
            result = re.search(regexp, content)
            cell = re.sub('<img.*?>', '@', result.group(1))
            row.append(cell)

        result = re.search(r'../ap/members.php\?id=(\d+)', content)
        mid = result.group(1)
        members = self.get_last_members(mid)

        if not members:
            members = [[''] * 3]

        first_member = members.pop(0)
        row += first_member

        self.output.append(row)

        for member in members:
            self.output.append([''] * 4 + member)

    def get_last_members(self, mid):
        print '    load members %s ...' % mid

        content = self.get_url('http://volleymsk.ru/ap/members.php?id={mid}'.format(mid=mid))

        members = []

        REGEXP_MEMBERS = re.compile(r'<td.*?>.*?\n.*?<strong>.*?\n(.+?\n.+?\n.+?\n).*?</strong>.*?\n.*?\n.*?\n.*?'
                                    r'<td.*?>.*?\n.*?Рост:&nbsp;<strong>(.+)</strong>.*?\n.*?'
                                    r'Мастерство:&nbsp;<strong>(.+?)</strong>'
                                    , re.MULTILINE)

        result = re.finditer(REGEXP_MEMBERS, content)
        for match in result:
            name, height, skill = match.groups()
            members.append([
                name.replace('<br>', ' ').replace('\t', '').replace('\n', '').replace('\r', ''),
                height,
                skill,
            ])

        return members


Applications().load_teams().write('applications.csv')
Teams().load_teams().write('teams.csv')
