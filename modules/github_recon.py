import requests
import tempfile
import subprocess

github_token = ''
github_headers = {
    'Authorization': 'token ' + github_token
}

emails_list = {}
valid_emails = []
src_code_emails = []
orgs_list = []


def obtain_profile_info(user):
    if github_token:
        response = requests.get('https://api.github.com/users/' + user, headers=github_headers)
    else:
        response = requests.get('https://api.github.com/users/' + user)
    if response.status_code == 404:
        print()
        print(' [!] Username not found')
        exit()
    return response.json()


def obtain_repos(user):
    if github_token:
        response = requests.get('https://api.github.com/users/' + user + '/repos', headers=github_headers)
    else:
        response = requests.get('https://api.github.com/users/' + user + '/repos')
    if response.status_code == 404:
        print()
        print(' [!] Username not found')
        exit()
    return response.json()

def obtain_orgs(user):
    if github_token:
        response = requests.get('https://api.github.com/users/' + user + '/orgs', headers=github_headers)
    else:
        response = requests.get('https://api.github.com/users/' + user + '/orgs')
    return response.json()


def obtain_keys(user):
    if github_token:
        response = requests.get('https://api.github.com/users/' + user + '/keys', headers=github_headers)
    else:
        response = requests.get('https://api.github.com/users/' + user + '/keys')
    return response.json()


def extract_orgs(user):
    orgs = obtain_orgs(user)
    for org in orgs:
        orgs_list.append(org['login'])


def obtain_events(user, page = 1):
    if github_token:
        response = requests.get('https://api.github.com/users/' + user + '/events?per_page=100&page=' + str(page), headers=github_headers)
    else:
        response = requests.get('https://api.github.com/users/' + user + '/events?per_page=100&page=' + str(page))
    return response.json()


def extract_events_leaks(user):
    for i in range(1,20):
        events = obtain_events(user, i)
        if (len(events) == 0):
            break
        for data in events:
            try:
                for info in data['payload']['commits']:
                    info = {info['author']['email']: info['author']['name']}
                    emails_list.update(info)
            except:
                pass

def extract_repos_email_leaks(repos):
    tmpdir = tempfile.TemporaryDirectory()
    tmpdir_name = tmpdir.name
    for repo in repos:
        #don't scan forked repos
        if repo['fork']:
            continue
        repo_clone_url = repo['clone_url']
        repo_name = repo['name']
        clone_out = subprocess.Popen([
            'git',
            'clone',
            repo_clone_url,
            '%s/%s'%(tmpdir_name,repo_name)
            ],
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT)
        clone_out.wait()
        _, stderr = clone_out.communicate()
        stcode = clone_out.returncode
        if(stcode != 0 ):
            print('cloning the project %s failed'%repo_name)
            print(stderr)
            continue
        git_log_out = subprocess.Popen([
            'sh',
            '-c',
            """git --no-pager  log --pickaxe-regex -p --no-color -S '\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,6}\\b'|grep -oE '\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,6}\\b'|grep -v users.noreply.github.com"""
            ],
            cwd = f"{tmpdir_name}/{repo_name}",
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT)
        git_log_out.wait()
        stdout, stderr = git_log_out.communicate()
        result = stdout.decode('utf8').strip().split('\n')
        src_code_emails.append(result)
    tmpdir.cleanup()

def validate_leaked_emails(emails, user_info):
    for email in emails_list:
        if emails[email] == user_info['name']:
            valid_emails.append(email)
