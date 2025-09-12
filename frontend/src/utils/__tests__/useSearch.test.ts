import { useSearch } from '../useSearch';
import { renderHook } from '@testing-library/react-hooks';
import lunr from 'lunr';
import { vi } from 'vitest';

function fetchMock(url, opts) {
  const storeDataUrl = '/rspec/rules/rule-index-store.json';
  if (url === storeDataUrl) {
    return Promise.resolve({
      json: () =>
        Promise.resolve(['first rule', 'second rule', 'third rule']),
    });
  } else {
    return Promise.resolve({
      json: () =>
        Promise.resolve({
          data: opts,
        }),
    });
  }
}

describe('search hook', () => {
  beforeEach(() => {
    vi.spyOn(global, 'fetch').mockImplementation(fetchMock);
  });

  afterEach(() => {
    vi.mocked(global.fetch).mockClear();
  });

  test('notifies when search is ready', async () => {
    vi.spyOn(lunr.Index, 'load').mockImplementation(() => ({query: () => []}));
    const { result, waitForNextUpdate } = renderHook(() => useSearch('42', null, null, [], [], 10, 1));
    expect(result.current.error).toBeNull();
    expect(result.current.loading).toBe(true);
    await waitForNextUpdate();
    expect(result.current.error).toBeNull();
    expect(result.current.loading).toBe(false);
    vi.mocked(lunr.Index.load).mockClear();
  });

  test('fails on query parsing error', async () => {
    vi.spyOn(lunr.Index, 'load').mockImplementation(() => ({query: () => {
      throw new lunr.QueryParseError('message here');
    }}));
    const { result, waitForNextUpdate } = renderHook(() => useSearch('42', null, null, [], [], 10, 1));
    expect(result.current.error).toBeNull();
    await waitForNextUpdate();
    expect(result.current.error).toBe('message here');
    vi.mocked(lunr.Index.load).mockClear();
  });

  test('returns the found rules', async () => {
    vi.spyOn(lunr.Index, 'load').mockImplementation(() => ({query: () => [{ref: 0}, {ref: 2}]}));
    const { result, waitForNextUpdate } = renderHook(() => useSearch('42', null, null, [], [], 10, 1));
    await waitForNextUpdate();
    expect(result.current.error).toBeNull();
    expect(result.current.results).toContain('first rule');
    expect(result.current.results).not.toContain('second rule');
    expect(result.current.results).toContain('third rule');
    expect(result.current.results).toHaveLength(2);
    vi.mocked(lunr.Index.load).mockClear();
  });

});
