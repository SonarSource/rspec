
type Fetched = 'json' | 'text';
type FetchResult = {[K in Fetched]?: any};

/**
 * Creates a mock `fetch` function. The returned function responds to each url
 * with a promise resolving an object with the provided `json` or `text` field.
 * can be used as
 *   jest.spyOn(global, 'fetch').mockImplementation(fetchMock(mockUrls));
 *
 * @param mockUrls a dictionary url -> value, where url is a string, and the value is
 *        an object containing either `json` or `text` field: {json: ...} or {text: ...}
 * @returns a function that can be passed to replace the implementaion of `fetch`.
 */
export function fetchMock(mockUrls: Record<string, FetchResult>):(url: string, opts: any) => Promise<FetchResult> {
  return function(url, opts) {
    if (url in mockUrls) {
      const response = mockUrls[url];
      if ('json' in response) {
        return Promise.resolve({json: () => Promise.resolve(response.json)});
      } else {
        return Promise.resolve({text: () => Promise.resolve(response.text)});
      }
    } else {
      return Promise.reject(`unexpected url ${url}`);
    }
  };
}
