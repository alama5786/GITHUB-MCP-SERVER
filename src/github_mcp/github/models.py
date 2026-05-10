
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, HttpUrl, field_validator


class GitHubUser(BaseModel):
    """GitHub user model - fields are optional for partial responses."""
    
    login: str
    id: int
    node_id: str
    avatar_url: Optional[HttpUrl] = None
    url: HttpUrl
    html_url: HttpUrl
    type: str
    name: Optional[str] = None
    company: Optional[str] = None
    blog: Optional[str] = None
    location: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    public_repos: Optional[int] = 0
    followers: Optional[int] = 0
    following: Optional[int] = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @field_validator('created_at', 'updated_at', mode='before')
    @classmethod
    def parse_datetime(cls, v):
        """Parse datetime from string, return None if not present."""
        if v is None or v == '':
            return None
        return v


class GitHubRepository(BaseModel):
    """GitHub repository model."""
    
    id: int
    node_id: str
    name: str
    full_name: str
    private: bool = False
    html_url: HttpUrl
    description: Optional[str] = None
    fork: bool = False
    url: HttpUrl
    created_at: datetime
    updated_at: datetime
    pushed_at: datetime
    size: int = 0
    stargazers_count: int = 0
    watchers_count: int = 0
    language: Optional[str] = None
    forks_count: int = 0
    open_issues_count: int = 0
    default_branch: str = "main"
    owner: Optional[GitHubUser] = None
    
    @property
    def is_private_str(self) -> str:
        """Return 'private' or 'public' based on repo visibility."""
        return "private" if self.private else "public"
    
    @property
    def owner_login(self) -> str:
        """Get owner login safely."""
        return self.owner.login if self.owner else "unknown"


class GitHubContent(BaseModel):
    """GitHub file/directory content model."""
    
    type: str
    encoding: Optional[str] = None
    size: int
    name: str
    path: str
    content: Optional[str] = None
    sha: str
    url: HttpUrl
    git_url: Optional[HttpUrl] = None
    html_url: Optional[HttpUrl] = None
    download_url: Optional[HttpUrl] = None


class GitHubCommit(BaseModel):
    """GitHub commit model."""
    
    sha: str
    node_id: str
    commit: Dict[str, Any]
    url: HttpUrl
    html_url: HttpUrl
    author: Optional[GitHubUser] = None
    committer: Optional[GitHubUser] = None
    parents: List[Dict[str, Any]] = []
    
    @property
    def message(self) -> str:
        """Extract commit message."""
        return self.commit.get("message", "")
    
    @property
    def author_name(self) -> str:
        """Extract author name."""
        return self.commit.get("author", {}).get("name", "unknown")


class GitHubIssue(BaseModel):
    """GitHub issue model."""
    
    id: int
    number: int
    title: str
    state: str
    html_url: HttpUrl
    body: Optional[str] = None
    user: GitHubUser
    labels: List[Dict[str, Any]] = []
    assignees: List[GitHubUser] = []
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None


class GitHubPullRequest(BaseModel):
    """GitHub pull request model."""
    
    id: int
    number: int
    title: str
    state: str
    html_url: HttpUrl
    body: Optional[str] = None
    user: GitHubUser
    created_at: datetime
    updated_at: datetime
    merged_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    additions: Optional[int] = None
    deletions: Optional[int] = None
    changed_files: Optional[int] = None
