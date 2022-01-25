
type Fetched = 'json' | 'text';
type FetchResult = {[K in Fetched]?: any};
type FetchFunction = (url: string, opts: any) => Promise<FetchResult>;
type FetchMocker = {mock: FetchFunction,
                    finished: () => Promise<FetchResult[]>,
                    reset: () => void};

/**
 * Creates an object that has a mock `fetch` function. The mock function responds to each url
 * with a promise resolving an object with the provided `json` or `text` field.
 * See `fetchMock` if you are only interested in the mock function.
 *
 * The object also contains `finished` function that returns a promise aggregating
 * all the promises generated in the mock calls. It is useful when you want to make sure
 * all the fetch-related promises are resolved. Use it as:
 *   await fetchMocker.finished();
 * or
 *   fetchMocker.finished().then(() => { expect ... });
 *
 * `reset` function clears all the promises and prepares the object to handle a next test case.
 *
 * @param mockUrls a dictionary url -> value, where url is a string, and the value is
 *        an object containing either `json` or `text` field: {json: ...} or {text: ...}
 * @returns an object containing the `mock` function, `finished` function, and `reset` function.
 */
export function fetchMockObject(mockUrls: Record<string, FetchResult>): FetchMocker {
  let allPromises: Promise<FetchResult>[] = [];
  let reset = function() {
    allPromises = [];
  };
  let finished = function() {
    return Promise.all(allPromises);
  };
  let keeping = function(p: Promise<FetchResult>) {
    allPromises.push(p);
    return p;
  }
  let mock = function(url: string, opts: any) {
    if (url in mockUrls) {
      const response = mockUrls[url];
      if ('json' in response) {
        return keeping(Promise.resolve({json: () => {
          return keeping(Promise.resolve(response.json));
        }}));
      } else {
        return keeping(Promise.resolve({text: () => {
          return keeping(Promise.resolve(response.text));
        }}));
      }
    } else {
      return keeping(Promise.reject(`unexpected url ${url}`));
    }
  };
  return {mock, finished, reset};
}


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
export function fetchMock(mockUrls: Record<string, FetchResult>):FetchFunction {
  return fetchMockObject(mockUrls).mock;
}
