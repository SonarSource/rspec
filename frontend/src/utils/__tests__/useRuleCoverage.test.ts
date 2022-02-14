import { useRuleCoverage } from '../useRuleCoverage';
import { renderHook } from '@testing-library/react-hooks';
import lunr from 'lunr';
import { fetchMock } from '../../testutils';

describe('search hook', () => {
  beforeEach(() => {
    let mockUrls = {};
    mockUrls[`${process.env.PUBLIC_URL}/covered_rules.json`] = {json:
      {'ABAP': {'S100': 'ver1', 'S200': 'ver2'},
       'C': {'S100': 'c1', 'S234': {'since': 'c2', 'until': 'c3'}}}
    };
    jest.spyOn(global, 'fetch').mockImplementation(fetchMock(mockUrls));
  });

  afterEach(() => {
    global.fetch.mockClear();
  });

  test('reports appropriate argument errors', async () => {
    const { result, waitForNextUpdate } = renderHook(() => useRuleCoverage());
    expect(result.current.ruleCoverage('abap', [], null)).toBe('Loading');
    await waitForNextUpdate();
    expect(result.current.ruleCoverage('English', [], null)).toBe('Nonsupported language');
    expect(result.current.ruleCoverage('abap', [], null)).toBe('Not Covered');
  });

  test('reports the fetch errors', async () => {
    global.fetch.mockImplementation(() => {
      return Promise.reject(Error('expected error'));
    });
    const { result, waitForNextUpdate } = renderHook(() => useRuleCoverage());
    expect(result.current.ruleCoverage('abap', [], null)).toBe('Loading');
    await waitForNextUpdate();
    expect(result.current.ruleCoverage('abap', [], null)).toBe('Failed Loading');
  });

  test('notifies when search is ready', async () => {
    const { result, waitForNextUpdate } = renderHook(() => useRuleCoverage());
    await waitForNextUpdate();
    const coveredRules = result.current.ruleCoverage('abap', ['S100', 'S1234'], (x, v) => x + ":" + v);
    expect(coveredRules).toStrictEqual(['ABAP:ver1']);
  });

  test('provides coverage for all languages', async () => {
    const { result, waitForNextUpdate } = renderHook(() => useRuleCoverage());
    await waitForNextUpdate();
    const coveredRules = result.current.allLangsRuleCoverage(['S100', 'S1234'], (x, v) => x + ":" + v);
    expect(coveredRules).toHaveLength(2);
    expect(coveredRules).toContain('ABAP:ver1');
    expect(coveredRules).toContain('C:c1');
  });

  test('provides coverage for all languages', async () => {
    const { result, waitForNextUpdate } = renderHook(() => useRuleCoverage());
    await waitForNextUpdate();
    expect(result.current.ruleStateInAnalyzer('cfamily', ['S100'])).toBe('covered');
    expect(result.current.ruleStateInAnalyzer('cfamily', ['S200'])).toBe('targeted');
    expect(result.current.ruleStateInAnalyzer('cfamily', ['S234'])).toBe('removed');
  });

  test('reports for nonexisting language', async () => {
    const original = console.error;
    console.error = jest.fn();
    fetch.mockImplementation(fetchMock({})); // eclipse the covered_rules.json

    const { result, waitForNextUpdate } = renderHook(() => useRuleCoverage());
    await waitForNextUpdate();
    expect(result.current.ruleStateInAnalyzer('english', ['S100'])).toBe('targeted');
    expect(console.error).toHaveBeenCalledTimes(1);

    console.error = original;
  });
});
