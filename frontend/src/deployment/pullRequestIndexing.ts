import fs from 'fs';
import path from 'path';
import { Octokit } from '@octokit/rest';
import { simpleGit, SimpleGit } from 'simple-git';
import { logger as rootLogger } from './deploymentLogger';

const logger = rootLogger.child({ source: path.basename(__filename) })

export interface PullRequest {
  rspec_id: string,
  url: string,
  branch: string,
  pull_id: number
}

export interface GitHubPullData {
  title: string;
  html_url: string;
  head: { ref: string };
  number: number;
}

/**
 * Initialize GitHub Octokit client with optional authentication
 */
export function createGitHubClient(): Octokit {
  return process.env.GITHUB_TOKEN ?
    new Octokit({userAgent: 'rspec-tools', auth: process.env.GITHUB_TOKEN}) :
    new Octokit({userAgent: 'rspec-tools'});
}

/**
 * Setup Git repository - clone if needed and configure PR refs
 */
export async function setupRepository(tmpRepoDir: string): Promise<SimpleGit> {
  const git = simpleGit();
  
  if (!fs.existsSync(path.join(tmpRepoDir, '.git'))) {
    const repoUrl = process.env.GITHUB_TOKEN 
      ? `https://${process.env.GITHUB_TOKEN}@github.com/SonarSource/rspec/`
      : 'https://github.com/SonarSource/rspec/';
    await git.clone(repoUrl, tmpRepoDir);
  }
  
  const repo = simpleGit(tmpRepoDir);
  await repo.addConfig('remote.origin.fetch', '+refs/pull/*/head:refs/remotes/origin/pr/*');
  await repo.fetch('origin');
  
  return repo;
}

/**
 * Parse PR title to extract rule ID if it matches the pattern
 */
export function parseRuleId(title: string): string | null {
  const found = /^Create rule (S\d+)/.exec(title);
  return found ? found[1] : null;
}

/**
 * Process a single rule from a PR
 */
export function processRule(
  tmpRepoDir: string,
  pullData: GitHubPullData,
  ruleId: string,
  callback: (srcDir: string, pr: PullRequest) => void
): void {
  const pull: PullRequest = {
    rspec_id: ruleId,
    url: pullData.html_url,
    branch: pullData.head.ref,
    pull_id: pullData.number
  };
  
  const ruleDir = path.join(tmpRepoDir, 'rules', pull.rspec_id);
  if (fs.existsSync(ruleDir)) {
    try {
      callback(ruleDir, pull);
    } catch (e) {
      logger.error(`Failed to process PR (${pull.url}), it will be skipped (${e})`);
    }
  } else {
    logger.error(`No rule dir rules/${pull.rspec_id} is found for the PR#${pull.pull_id}: ${pull.url}`);
  }
}

/**
 * Fetch and process all PRs that create new rules
 */
export async function fetchAndProcessPRs(
  octokit: Octokit,
  repo: SimpleGit,
  tmpRepoDir: string,
  callback: (srcDir: string, pr: PullRequest) => void
): Promise<void> {
  let page = 1;
  const perPage = 100;
  let fetchNext = true;
  
  while (fetchNext) {
    const { data } = await octokit.rest.pulls.list({
      owner: 'SonarSource',
      repo: 'rspec',
      state: 'open',
      per_page: perPage,
      page
    });

    for (const pullData of data) {
      const ruleId = parseRuleId(pullData.title);
      if (!ruleId) {
        continue;
      }

      await repo.checkout(`origin/pr/${pullData.number}`);
      processRule(tmpRepoDir, pullData, ruleId, callback);
    }

    ++page;
    fetchNext = (data.length === perPage);
  }
}

/**
 * Fetch all the open pull requests that add new rules (start with "Create rule Sxxx").
 * Call the "process" callback for each such rule.
 * @param tmpRepoDir Path to the temporary directory with a throw-away clone of the rspec repository.
 *                   if the repository does not exist, it will clone it first.
 * @param callback A callback to process each rule. Takes two arguments:
 *                srcDir - the path to the incomplete rule found in the corresponding PR.
 *                pr - the pull request attributes that might be useful to process the rule.
 */
export async function processIncompleteRspecs(
  tmpRepoDir: string,
  callback: (srcDir: string, pr: PullRequest) => void
): Promise<void> {
  const octokit = createGitHubClient();
  const repo = await setupRepository(tmpRepoDir);
  await fetchAndProcessPRs(octokit, repo, tmpRepoDir, callback);
}
