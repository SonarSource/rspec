import fs from 'fs';
import { process_incomplete_rspecs, PullRequest } from '../pullRequestIndexing';
import Git from 'nodegit';
import 'setimmediate';

jest.mock('@octokit/rest', () => {
  return {Octokit: function() {
    this.rest = {pulls: {list: jest.fn(() => {
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

beforeEach(() => {
  Git.Clone.clone = jest.fn();
  let repo = {
    config: () => ({ setString: (name: string, value: string) => {} }),
    fetch: (remote: string) => {},
    getBranch: (name: string) => {},
    checkoutRef: (ref) => {}
  };
  Git.Clone.clone.mockReturnValueOnce(repo);

  fs.existsSync = jest.fn((fname) => {
    return fname.includes('rules/S');
  });
})


describe('pull request enumeration', () => {
  test('clones repository and lists only relevant PRs', () => {
    const nonExistingDir = 'not-existing-directory';
    let processedPRs = [];
    return process_incomplete_rspecs(nonExistingDir, (srcDir: string, pr: PullRequest) => {
      processedPRs.push(pr.pull_id);
    }).then(() => {
      expect(Git.Clone.clone.mock.calls.length).toBe(1);
      expect(Git.Clone.clone.mock.calls[0][1]).toBe(nonExistingDir);
      expect(processedPRs).toHaveLength(2);
      expect(processedPRs).toContain(1);
      expect(processedPRs).toContain(42);
    });
  });
});

