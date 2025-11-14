import fs from 'fs';
import { 
  processIncompleteRspecs,
  PullRequest, 
  createGitHubClient,
  setupRepository,
  parseRuleId,
  processRule,
  fetchAndProcessPRs,
  GitHubPullData
} from '../pullRequestIndexing';
import { simpleGit } from 'simple-git';
import { Octokit } from '@octokit/rest';
import 'setimmediate';
import { vi } from 'vitest';

vi.mock('@octokit/rest', () => {
  return {Octokit: function() {
    this.rest = {pulls: {list: vi.fn(() => {
      return { data: [
        { title: 'Irrelevant S832' },
        { title: 'Create rule S343: Be friendly',
          html_url: 'https://pull.request/url',
          head: {ref: 'gh:rspec/branches/friendly-branch'},
          number: 42, },
        { title: 'Create rule S01, and friends',
          html_url: 'example.com',
          head: {ref: 'gh:rspec/branches/some-other-branch'},
          number: 1, },
      ] }
    })}};
  }};
});

vi.mock('simple-git', () => ({
  simpleGit: vi.fn(() => ({
    clone: vi.fn(),
    addConfig: vi.fn(),
    fetch: vi.fn(),
    checkout: vi.fn()
  }))
}));

beforeEach(() => {
  const mockGit = {
    clone: vi.fn(),
    addConfig: vi.fn(),
    fetch: vi.fn(),
    checkout: vi.fn()
  };
  
  vi.mocked(simpleGit).mockReturnValue(mockGit);

  vi.spyOn(fs, 'existsSync').mockImplementation((fname) => {
    return fname.replace(/\\/g, '/').includes('rules/S');
  });
});

afterEach(() => {
  vi.restoreAllMocks();
});


describe('createGitHubClient', () => {
  let originalToken: string | undefined;

  beforeEach(() => {
    originalToken = process.env.GITHUB_TOKEN;
  });

  afterEach(() => {
    process.env.GITHUB_TOKEN = originalToken;
  });

  test('creates authenticated client when token is available', () => {
    process.env.GITHUB_TOKEN = 'test-token';
    const client = createGitHubClient();
    expect(client).toBeInstanceOf(Octokit);
  });

  test('creates unauthenticated client when token is not available', () => {
    delete process.env.GITHUB_TOKEN;
    const client = createGitHubClient();
    expect(client).toBeInstanceOf(Octokit);
  });
});

describe('setupRepository', () => {
  const mockGitRoot = {
    clone: vi.fn()
  };
  const mockRepo = {
    addConfig: vi.fn(),
    fetch: vi.fn()
  };

  beforeEach(() => {
    vi.mocked(simpleGit).mockImplementation((dir?: string) => {
      return dir ? mockRepo : mockGitRoot;
    });
  });

  test('clones repository when .git does not exist', async () => {
    const tmpDir = '/tmp/test-repo';
    vi.spyOn(fs, 'existsSync').mockReturnValue(false);
    
    const repo = await setupRepository(tmpDir);
    
    expect(mockGitRoot.clone).toHaveBeenCalledWith(
      expect.stringContaining('github.com/SonarSource/rspec'),
      tmpDir
    );
    expect(mockRepo.addConfig).toHaveBeenCalledWith(
      'remote.origin.fetch',
      '+refs/pull/*/head:refs/remotes/origin/pr/*'
    );
    expect(mockRepo.fetch).toHaveBeenCalledWith('origin');
    expect(repo).toBe(mockRepo);
  });

  test('skips cloning when .git already exists', async () => {
    const tmpDir = '/tmp/existing-repo';
    vi.spyOn(fs, 'existsSync').mockReturnValue(true);
    
    await setupRepository(tmpDir);
    
    expect(mockGitRoot.clone).not.toHaveBeenCalled();
    expect(mockRepo.addConfig).toHaveBeenCalled();
    expect(mockRepo.fetch).toHaveBeenCalled();
  });
});

describe('parseRuleId', () => {
  test('extracts rule ID from valid PR title', () => {
    expect(parseRuleId('Create rule S1234: Some description')).toBe('S1234');
    expect(parseRuleId('Create rule S999')).toBe('S999');
  });

  test('returns null for invalid PR title', () => {
    expect(parseRuleId('Update rule S1234')).toBeNull();
    expect(parseRuleId('Create S1234')).toBeNull();
    expect(parseRuleId('Irrelevant title')).toBeNull();
  });
});

describe('processRule', () => {
  const mockCallback = vi.fn();
  const tmpDir = '/tmp/repo';
  const pullData: GitHubPullData = {
    title: 'Create rule S123',
    html_url: 'https://github.com/pr/123',
    head: { ref: 'feature-branch' },
    number: 123
  };

  beforeEach(() => {
    mockCallback.mockReset();
  });

  test('processes rule when directory exists', () => {
    vi.spyOn(fs, 'existsSync').mockReturnValue(true);
    
    processRule(tmpDir, pullData, 'S123', mockCallback);
    
    expect(mockCallback).toHaveBeenCalledWith(
      '/tmp/repo/rules/S123',
      {
        rspec_id: 'S123',
        url: 'https://github.com/pr/123',
        branch: 'feature-branch',
        pull_id: 123
      }
    );
  });

  test('skips processing when directory does not exist', () => {
    vi.spyOn(fs, 'existsSync').mockReturnValue(false);
    
    processRule(tmpDir, pullData, 'S123', mockCallback);
    
    expect(mockCallback).not.toHaveBeenCalled();
  });

  test('handles callback errors gracefully', () => {
    vi.spyOn(fs, 'existsSync').mockReturnValue(true);
    mockCallback.mockImplementation(() => {
      throw new Error('Processing failed');
    });
    
    expect(() => {
      processRule(tmpDir, pullData, 'S123', mockCallback);
    }).not.toThrow();
    
    expect(mockCallback).toHaveBeenCalled();
  });
});

describe('fetchAndProcessPRs', () => {
  const mockOctokit = {
    rest: {
      pulls: {
        list: vi.fn()
      }
    }
  };
  const mockRepo = {
    checkout: vi.fn()
  };
  const mockCallback = vi.fn();

  beforeEach(() => {
    mockCallback.mockReset();
    mockRepo.checkout.mockReset();
    vi.spyOn(fs, 'existsSync').mockReturnValue(true);
  });

  test('processes multiple pages of PRs', async () => {
    mockOctokit.rest.pulls.list
      .mockResolvedValueOnce({
        data: Array(100).fill({
          title: 'Create rule S100',
          html_url: 'https://pr.url',
          head: { ref: 'branch' },
          number: 100
        })
      })
      .mockResolvedValueOnce({
        data: [{
          title: 'Create rule S101',
          html_url: 'https://pr.url',
          head: { ref: 'branch' },
          number: 101
        }]
      });

    await fetchAndProcessPRs(mockOctokit as any, mockRepo as any, '/tmp/repo', mockCallback);

    expect(mockOctokit.rest.pulls.list).toHaveBeenCalledTimes(2);
    expect(mockCallback).toHaveBeenCalledTimes(101);
  });

  test('filters out non-rule PRs', async () => {
    mockOctokit.rest.pulls.list.mockResolvedValueOnce({
      data: [
        { title: 'Create rule S123', html_url: 'url', head: { ref: 'branch' }, number: 1 },
        { title: 'Update documentation', html_url: 'url', head: { ref: 'branch' }, number: 2 },
        { title: 'Create rule S124', html_url: 'url', head: { ref: 'branch' }, number: 3 }
      ]
    });

    await fetchAndProcessPRs(mockOctokit as any, mockRepo as any, '/tmp/repo', mockCallback);

    expect(mockCallback).toHaveBeenCalledTimes(2);
    expect(mockRepo.checkout).toHaveBeenCalledWith('origin/pr/1');
    expect(mockRepo.checkout).toHaveBeenCalledWith('origin/pr/3');
    expect(mockRepo.checkout).not.toHaveBeenCalledWith('origin/pr/2');
  });
});

describe('pull request enumeration (integration)', () => {
  test('clones repository and lists only relevant PRs', async () => {
    const nonExistingDir = 'not-existing-directory';
    let processedPRs: number[] = [];
    
    await processIncompleteRspecs(nonExistingDir, (srcDir: string, pr: PullRequest) => {
      processedPRs.push(pr.pull_id);
    });
    
    expect(simpleGit().clone).toHaveBeenCalledTimes(1);
    expect(simpleGit().clone).toHaveBeenCalledWith(expect.any(String), nonExistingDir);
    expect(processedPRs).toHaveLength(2);
    expect(processedPRs).toContain(1);
    expect(processedPRs).toContain(42);
  });
});

