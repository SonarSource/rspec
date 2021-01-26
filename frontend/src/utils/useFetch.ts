import React from 'react';

export function useFetch<FetchedType>(
    url: string,
    parseJSON=true,
    options?: Record<string, any>
  ): [FetchedType|null, any, boolean] {
  const [response, setResponse] = React.useState<FetchedType|null>(null);
  const [error, setError] = React.useState(null);
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
        setError(exception);
      }
    };
    fetchData();
  }, [url, options, parseJSON]);

  return [ response, error, isLoading ];
}