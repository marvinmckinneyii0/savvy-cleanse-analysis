#!/usr/bin/env python3
"""
Simple GitHub Repository Lister
Lists all your GitHub repositories
"""

import subprocess
import json
from urllib.parse import urlparse

def get_github_credentials():
    """Extract GitHub token and username from git remote URL"""
    try:
        result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                              capture_output=True, text=True, check=True)
        url = result.stdout.strip()
        
        # Extract token
        parsed = urlparse(url)
        token = None
        if '@' in parsed.netloc:
            auth_part = parsed.netloc.split('@')[0]
            if ':' in auth_part:
                token = auth_part.split(':')[1]
        
        # Extract username
        parts = url.split('/')
        username = parts[-2] if len(parts) >= 4 else None
        
        return username, token
    except:
        return None, None

def list_repositories(username, token):
    """List all repositories for the given GitHub user"""
    repos = []
    page = 1
    
    while True:
        # Use curl to fetch repositories
        cmd = [
            'curl', '-s', '-H', f'Authorization: token {token}',
            f'https://api.github.com/users/{username}/repos?per_page=100&page={page}'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            page_repos = json.loads(result.stdout)
            
            if not page_repos or isinstance(page_repos, dict):
                break
                
            repos.extend(page_repos)
            page += 1
            
        except Exception as e:
            print(f"Error fetching repositories: {e}")
            break
    
    return repos

def main():
    # Get GitHub credentials
    username, token = get_github_credentials()
    
    if not token or not username:
        print("Error: Could not extract GitHub credentials from current repository.")
        return
    
    print(f"GitHub User: {username}")
    print(f"Fetching repositories...\n")
    
    # List repositories
    repos = list_repositories(username, token)
    
    if not repos:
        print("No repositories found.")
        return
    
    print(f"Found {len(repos)} repositories:\n")
    print(f"{'#':<4} {'Name':<40} {'Description':<60} {'Private':<8} {'Clone URL'}")
    print("-" * 140)
    
    for i, repo in enumerate(repos, 1):
        name = repo['name'][:39]
        desc = (repo.get('description') or 'No description')[:59]
        private = "Yes" if repo['private'] else "No"
        clone_url = repo['clone_url']
        print(f"{i:<4} {name:<40} {desc:<60} {private:<8} {clone_url}")
    
    print(f"\n\nTo clone a repository, use:")
    print(f"git clone https://x-access-token:{token}@github.com/{username}/REPO_NAME.git")
    
    # Save the list to a file for reference
    with open('/workspace/github_repos_list.json', 'w') as f:
        json.dump(repos, f, indent=2)
    print(f"\nRepository list saved to: /workspace/github_repos_list.json")

if __name__ == "__main__":
    main()