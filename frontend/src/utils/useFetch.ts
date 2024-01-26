import React from 'react';

export function useFetch<FetchedType>(
    url: string,
    parseJSON=true,
    options?: Record<string, any>
  ): [FetchedType|null, any, boolean] {
  const [response, setResponse] = React.useState<FetchedType|null>(null);
  const [hasError, setHasError] = React.useState(false);
  const [isLoading, setIsLoading] = React.useState(true);

  React.useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch(url, options);
        let content = null;
        if (parseJSON) {
          content = await res.json();
        } else {
          content = await res.text();
        }
        setResponse(content);
        setIsLoading(false)
      } catch (exception) {
        setHasError(true);
      }
    };
    fetchData();
  }, [url, options, parseJSON]);

  return [ response, hasError, isLoading ];
}
