import { useFetch } from '../useFetch';
import { renderHook } from '@testing-library/react-hooks';
import { vi } from 'vitest';

function fetchMock(url, opts) {
  return Promise.resolve({
    json: () => (
      Promise.resolve({
        data: opts,
      })),
  });
}

describe('url fetching', () => {
  beforeEach(() => {
    vi.spyOn(global, 'fetch').mockImplementation(fetchMock);
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  test('notifies when loaded', async () => {
    const { result, waitForNextUpdate } = renderHook(() => useFetch('funny.url'));
    expect(result.current[2]).toBe(true);
    await waitForNextUpdate();
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(result.current[2]).toBe(false);
  });

  test('forwards the response', async () => {
    const response = "it's o'right";
    const { result, waitForNextUpdate } = renderHook(() => useFetch('funny.url', true, response));
    await waitForNextUpdate();
    expect(result.current[0]).toStrictEqual({data: response});
  });

  test('fails when not expecting but getting json', async () => {
    const { result, waitForNextUpdate } = renderHook(() => useFetch('funny.url', false));
    expect(result.current[1]).toBeFalsy();
    await waitForNextUpdate();
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(result.current[1]).not.toBeFalsy();
  });

  test('fails when fetch throws', async () => {
    vi.spyOn(global, 'fetch').mockImplementation(() => Promise.reject(new Error()));
    const { result, waitForNextUpdate } = renderHook(() => useFetch('funny.url', false));
    expect(result.current[1]).toBeFalsy();
    await waitForNextUpdate();
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(result.current[1]).not.toBeFalsy();
  });
});
