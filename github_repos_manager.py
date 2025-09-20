#!/usr/bin/env python3
"""
GitHub Repository Manager
This script helps you list and clone your GitHub repositories
"""

import subprocess
import json
import os
import sys
from urllib.parse import urlparse

def get_github_token():
    """Extract GitHub token from git remote URL"""
    try:
        result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                              capture_output=True, text=True, check=True)
        url = result.stdout.strip()
        parsed = urlparse(url)
        if '@' in parsed.netloc:
            auth_part = parsed.netloc.split('@')[0]
            if ':' in auth_part:
                return auth_part.split(':')[1]
    except:
        pass
    return None

def get_github_username():
    """Extract GitHub username from git remote URL"""
    try:
        result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                              capture_output=True, text=True, check=True)
        url = result.stdout.strip()
        # Extract username from URL like: https://...@github.com/username/repo
        parts = url.split('/')
        if len(parts) >= 4:
            return parts[-2]
    except:
        pass
    return None

def list_repositories(username, token):
    """List all repositories for the given GitHub user"""
    print(f"\nFetching repositories for user: {username}")
    print("-" * 50)
    
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
            
            if not page_repos:
                break
                
            repos.extend(page_repos)
            page += 1
            
        except Exception as e:
            print(f"Error fetching repositories: {e}")
            break
    
    return repos

def display_repositories(repos):
    """Display repositories in a formatted table"""
    if not repos:
        print("No repositories found.")
        return
    
    print(f"\nFound {len(repos)} repositories:\n")
    print(f"{'#':<4} {'Name':<40} {'Description':<50} {'Private':<8}")
    print("-" * 110)
    
    for i, repo in enumerate(repos, 1):
        name = repo['name'][:39]
        desc = (repo.get('description') or 'No description')[:49]
        private = "Yes" if repo['private'] else "No"
        print(f"{i:<4} {name:<40} {desc:<50} {private:<8}")

def clone_repository(repo, token, target_dir):
    """Clone a specific repository"""
    clone_url = repo['clone_url']
    # Insert token into URL
    if token and 'github.com' in clone_url:
        clone_url = clone_url.replace('https://', f'https://x-access-token:{token}@')
    
    repo_name = repo['name']
    target_path = os.path.join(target_dir, repo_name)
    
    if os.path.exists(target_path):
        print(f"Repository '{repo_name}' already exists at {target_path}")
        return False
    
    print(f"\nCloning '{repo_name}' to {target_path}...")
    
    try:
        subprocess.run(['git', 'clone', clone_url, target_path], check=True)
        print(f"Successfully cloned '{repo_name}'")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error cloning repository: {e}")
        return False

def main():
    # Get GitHub credentials
    token = get_github_token()
    username = get_github_username()
    
    if not token or not username:
        print("Error: Could not extract GitHub credentials from current repository.")
        print("Make sure you're in a GitHub repository with proper authentication.")
        sys.exit(1)
    
    # List repositories
    repos = list_repositories(username, token)
    
    if not repos:
        print("No repositories found or error occurred.")
        sys.exit(1)
    
    display_repositories(repos)
    
    # Interactive mode
    while True:
        print("\n" + "=" * 50)
        print("Options:")
        print("1. Clone a repository by number")
        print("2. Clone all repositories")
        print("3. Refresh repository list")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            try:
                repo_num = int(input("Enter repository number to clone: "))
                if 1 <= repo_num <= len(repos):
                    repo = repos[repo_num - 1]
                    
                    # Ask for target directory
                    default_dir = "/workspace/github_repos"
                    target_dir = input(f"Target directory [{default_dir}]: ").strip() or default_dir
                    
                    # Create directory if it doesn't exist
                    os.makedirs(target_dir, exist_ok=True)
                    
                    clone_repository(repo, token, target_dir)
                else:
                    print("Invalid repository number.")
            except ValueError:
                print("Invalid input. Please enter a number.")
        
        elif choice == '2':
            confirm = input("Are you sure you want to clone ALL repositories? (yes/no): ").strip().lower()
            if confirm == 'yes':
                default_dir = "/workspace/github_repos"
                target_dir = input(f"Target directory [{default_dir}]: ").strip() or default_dir
                os.makedirs(target_dir, exist_ok=True)
                
                success_count = 0
                for i, repo in enumerate(repos, 1):
                    print(f"\n[{i}/{len(repos)}] ", end='')
                    if clone_repository(repo, token, target_dir):
                        success_count += 1
                
                print(f"\n\nCloned {success_count} out of {len(repos)} repositories.")
        
        elif choice == '3':
            repos = list_repositories(username, token)
            display_repositories(repos)
        
        elif choice == '4':
            print("Exiting...")
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()